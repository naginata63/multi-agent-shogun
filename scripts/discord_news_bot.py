#!/usr/bin/env python3
"""
discord_news_bot.py — AI NEWS Discord Bot
- Top3をEmbed形式で配信（queue/discord_pending.jsonを監視）
- 続いて全記事を個別Embedで配信（OGPサムネイル+星スコア+カテゴリ色）
- 👍👎⭐リアクション収集 → queue/genai_feedback.yaml に蓄積
- discord_bot.envがなければスキップ（graceful degradation）
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import tasks

# --- プロジェクトルート ---
PROJECT_ROOT = Path(__file__).parent.parent
PENDING_FILE = PROJECT_ROOT / "queue" / "discord_pending.json"
FEEDBACK_FILE = PROJECT_ROOT / "queue" / "genai_feedback.yaml"
ENV_FILE = PROJECT_ROOT / "config" / "discord_bot.env"

# カテゴリ色マッピング
CATEGORY_COLORS = {
    "🤖": 0x3498DB,  # 青
    "📢": 0x2ECC71,  # 緑
    "🛠️": 0xE67E22,  # オレンジ
    "💰": 0xF1C40F,  # 金
    "📄": 0x95A5A6,  # グレー
}
DEFAULT_COLOR = 0x7F8C8D


# --- 環境変数読み込み（discord_bot.envから） ---
def load_env_file(env_path: Path) -> bool:
    """discord_bot.envを読み込んでos.environに設定。ファイルなければFalse返却。"""
    if not env_path.exists():
        return False
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)
    return True


if not load_env_file(ENV_FILE):
    print("[discord_news_bot] config/discord_bot.env が見つかりません。Bot起動をスキップします。", file=sys.stderr)
    print("[discord_news_bot] 手順: config/discord_bot.env を作成してトークンとチャンネルIDを設定してください。", file=sys.stderr)
    sys.exit(0)

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
CHANNEL_ID_STR = os.environ.get("DISCORD_NEWS_CHANNEL_ID", "")

if not TOKEN or TOKEN == "YOUR_TOKEN_HERE":
    print("[discord_news_bot] DISCORD_BOT_TOKEN が未設定です。Bot起動をスキップします。", file=sys.stderr)
    sys.exit(0)

if not CHANNEL_ID_STR or CHANNEL_ID_STR == "YOUR_CHANNEL_ID_HERE":
    print("[discord_news_bot] DISCORD_NEWS_CHANNEL_ID が未設定です。Bot起動をスキップします。", file=sys.stderr)
    sys.exit(0)

try:
    CHANNEL_ID = int(CHANNEL_ID_STR)
except ValueError:
    print(f"[discord_news_bot] DISCORD_NEWS_CHANNEL_ID が数値ではありません: {CHANNEL_ID_STR}", file=sys.stderr)
    sys.exit(1)

# --- Discord クライアント設定 ---
intents = discord.Intents.default()
intents.guild_reactions = True
bot = discord.Client(intents=intents)


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [discord_bot] {msg}", flush=True)


# --- フィードバック保存 ---
def save_feedback(message_id: int, user_id: int, emoji: str, action: str):
    """リアクションをqueue/genai_feedback.yamlに追記。"""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"- message_id: {message_id}\n"
        f"  user_id: {user_id}\n"
        f"  emoji: \"{emoji}\"\n"
        f"  action: \"{action}\"\n"
        f"  timestamp: \"{datetime.now(timezone.utc).isoformat()}\"\n"
    )
    if not FEEDBACK_FILE.exists():
        FEEDBACK_FILE.write_text("feedbacks:\n" + entry)
    else:
        with open(FEEDBACK_FILE, "a") as f:
            f.write(entry)
    log(f"feedback saved: msg={message_id} emoji={emoji} action={action}")


# --- Top3 Embed構築 ---
def build_top3_embed(text: str, date: str) -> discord.Embed:
    """Top3テキストからDiscord Embedを構築。"""
    lines = [l for l in text.strip().splitlines() if l.strip()]
    title_line = lines[0] if lines else f"📰 AI Top3 ({date})"

    embed = discord.Embed(
        title=title_line,
        color=0x3498DB,
        timestamp=datetime.now(timezone.utc),
    )

    # 1⃣ 2⃣ 3⃣ で始まる行を各フィールドに
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith(("1⃣", "2⃣", "3⃣")):
            embed.add_field(name=stripped, value="", inline=False)

    full_url = "http://localhost:8580/"
    for line in lines:
        if line.startswith("全文:"):
            full_url = line.replace("全文:", "").strip()
            break

    embed.set_footer(text=f"👍有用 👎不要 ⭐最高 | フィードバック歓迎 | 全文: {full_url}")
    return embed


# --- 個別トピック Embed構築 ---
def build_topic_embed(topic: dict, date: str) -> discord.Embed:
    """1記事分のDiscord Embedを構築。"""
    title = topic.get("title", "（タイトルなし）")
    category = topic.get("category", "📄")
    score = topic.get("score", 0)
    summary = topic.get("summary", "")
    url = topic.get("url", "")
    ogp_image = topic.get("ogp_image")

    color = CATEGORY_COLORS.get(category, DEFAULT_COLOR)
    stars = "★" * score + "☆" * (5 - score)

    embed = discord.Embed(
        title=f"{category} {title}",
        description=summary[:300] + ("…" if len(summary) > 300 else ""),
        color=color,
        url=url if url else None,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_footer(text=f"{stars}  |  {date}")

    if ogp_image:
        embed.set_thumbnail(url=ogp_image)

    return embed


# --- 全記事配信 ---
async def send_daily_news(text: str, topics: list, date: str):
    """Top3 Embed + 全トピック個別Embedを配信。"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        log(f"ERROR: チャンネルID {CHANNEL_ID} が見つかりません")
        return

    # 1. Top3まとめEmbed（リアクション付き）
    top3_embed = build_top3_embed(text, date)
    top3_msg = await channel.send(embed=top3_embed)
    for emoji in ["👍", "👎", "⭐"]:
        await top3_msg.add_reaction(emoji)
        await asyncio.sleep(0.3)
    log(f"Top3送信完了: message_id={top3_msg.id}")

    if not topics:
        log("topics空のため個別Embed送信スキップ")
        return

    # 2. 全記事個別Embed（1秒間隔、rate limit対策）
    log(f"個別Embed配信開始: {len(topics)}件")
    for i, topic in enumerate(topics):
        embed = build_topic_embed(topic, date)
        await channel.send(embed=embed)
        await asyncio.sleep(1.0)  # rate limit: 30msg/60s対策

    log(f"全記事配信完了: {len(topics)}件 date={date}")


# --- discord_pending.json 監視ループ ---
@tasks.loop(seconds=60)
async def check_pending():
    """queue/discord_pending.json を監視して配信。"""
    if not PENDING_FILE.exists():
        return

    try:
        with open(PENDING_FILE) as f:
            pending = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f"WARN: discord_pending.json 読み込み失敗: {e}")
        return

    if not isinstance(pending, dict):
        return

    if pending.get("posted", True):
        return

    text = pending.get("text", "")
    date = pending.get("date", datetime.now().strftime("%Y-%m-%d"))
    topics = pending.get("topics", [])

    if not text:
        log("WARN: discord_pending.json に text がありません")
        return

    log(f"pending検知: date={date} topics={len(topics)}件 → 配信開始")
    await send_daily_news(text, topics, date)

    # posted: true に更新
    pending["posted"] = True
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)


# --- イベントハンドラ ---
@bot.event
async def on_ready():
    log(f"Logged in as {bot.user} (id={bot.user.id})")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        log(f"配信チャンネル確認: #{channel.name}")
    else:
        log(f"WARN: チャンネルID {CHANNEL_ID} が見つかりません（招待済みか確認してください）")
    check_pending.start()


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if bot.user and payload.user_id == bot.user.id:
        return
    if payload.channel_id != CHANNEL_ID:
        return
    save_feedback(payload.message_id, payload.user_id, str(payload.emoji), "add")


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if bot.user and payload.user_id == bot.user.id:
        return
    if payload.channel_id != CHANNEL_ID:
        return
    save_feedback(payload.message_id, payload.user_id, str(payload.emoji), "remove")


if __name__ == "__main__":
    log("Discord AI NEWS Bot 起動中...")
    bot.run(TOKEN)
