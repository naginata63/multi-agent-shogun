#!/usr/bin/env python3
"""
discord_news_bot.py — AI NEWS Discord Bot
- 全記事を個別Embedで配信（queue/discord_pending.jsonを監視）
- 👍👎リアクション収集 → queue/genai_feedback.yaml に蓄積
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
    star_count = round(score / 20) if score > 0 else 0
    stars = "★" * star_count + "☆" * (5 - star_count)

    embed = discord.Embed(
        title=f"{category} {title}",
        description=summary[:300] + ("…" if len(summary) > 300 else ""),
        color=color,
        url=url if url else None,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_author(name="📰 GenAI Daily", url="https://genai-daily.pages.dev/")
    embed.set_footer(text=f"{stars}  |  {date}")

    if ogp_image and len(ogp_image) <= 2048:
        embed.set_image(url=ogp_image)

    return embed


# --- 全記事配信 ---
async def send_daily_news(topics: list, date: str):
    """全トピック個別Embedを配信。"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        log(f"ERROR: チャンネルID {CHANNEL_ID} が見つかりません")
        return

    if not topics:
        log("topics空のため個別Embed送信スキップ")
        return

    # 全記事個別Embed（1秒間隔、rate limit対策）
    log(f"個別Embed配信開始: {len(topics)}件")
    for topic in topics:
        embed = build_topic_embed(topic, date)
        msg = await channel.send(embed=embed)
        for emoji in ["👍", "👎"]:
            await msg.add_reaction(emoji)
            await asyncio.sleep(0.3)
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

    date = pending.get("date", datetime.now().strftime("%Y-%m-%d"))
    topics = pending.get("topics", [])

    log(f"pending検知: date={date} topics={len(topics)}件 → 配信開始")
    await send_daily_news(topics, date)

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
