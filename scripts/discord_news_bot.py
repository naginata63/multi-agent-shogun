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
MESSAGE_MAP_FILE = PROJECT_ROOT / "queue" / "discord_message_map.json"
ENV_FILE = PROJECT_ROOT / "config" / "discord_bot.env"
SENT_DIR = PROJECT_ROOT / "queue" / "discord_sent"

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


# --- メッセージマップ操作 ---
def load_message_map() -> dict:
    """queue/discord_message_map.json を読み込む。"""
    if MESSAGE_MAP_FILE.exists():
        try:
            return json.loads(MESSAGE_MAP_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_message_map(mapping: dict):
    """queue/discord_message_map.json を書き込む。"""
    MESSAGE_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    MESSAGE_MAP_FILE.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")


def register_message(message_id: int, title: str, category: str, date: str):
    """メッセージID→記事情報のマッピングを保存。"""
    mapping = load_message_map()
    mapping[str(message_id)] = {"title": title, "category": category, "date": date}
    save_message_map(mapping)


# --- フィードバック保存 ---
def save_feedback(message_id: int, user_id: int, emoji: str, action: str):
    """リアクションをqueue/genai_feedback.yamlに追記。"""
    # メッセージマップからタイトルを取得
    mapping = load_message_map()
    info = mapping.get(str(message_id), {})
    title = info.get("title", "")
    category = info.get("category", "")

    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"- message_id: {message_id}\n"
        f"  user_id: {user_id}\n"
        f"  emoji: \"{emoji}\"\n"
        f"  action: \"{action}\"\n"
        f"  title: {json.dumps(title, ensure_ascii=False)}\n"
        f"  category: \"{category}\"\n"
        f"  timestamp: \"{datetime.now(timezone.utc).isoformat()}\"\n"
    )
    if not FEEDBACK_FILE.exists():
        FEEDBACK_FILE.write_text("feedbacks:\n" + entry)
    else:
        with open(FEEDBACK_FILE, "a") as f:
            f.write(entry)
    log(f"feedback saved: msg={message_id} emoji={emoji} action={action} title={title[:30]}")


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
    # score は ★ の数（1-5）なのでそのまま使う
    star_count = max(0, min(5, score))
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

    if url:
        embed.add_field(name="🔗 ソース", value=f"[記事を読む]({url})", inline=False)

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

    # スコア降順ソート
    topics = sorted(topics, key=lambda t: t.get('score', 0), reverse=True)

    # 全記事個別Embed（1秒間隔、rate limit対策）
    log(f"個別Embed配信開始: {len(topics)}件")
    for topic in topics:
        embed = build_topic_embed(topic, date)
        msg = await channel.send(embed=embed)
        # ⭐/👎リアクションを自動付与
        for emoji in ["⭐", "👎"]:
            await msg.add_reaction(emoji)
            await asyncio.sleep(0.3)
        # メッセージID→記事タイトルのマッピングを記録
        title = topic.get("title", "")
        category = topic.get("category", "")
        register_message(msg.id, title, category, date)
        await asyncio.sleep(1.0)  # rate limit: 30msg/60s対策

    log(f"全記事配信完了: {len(topics)}件 date={date}")


# --- discord_pending.json 監視ループ ---
@tasks.loop(seconds=60)
async def check_pending():
    """queue/discord_pending.json を監視して配信。日付キー辞書形式対応。"""
    if not PENDING_FILE.exists():
        return

    try:
        with open(PENDING_FILE, encoding="utf-8") as f:
            pending = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f"WARN: discord_pending.json 読み込み失敗: {e}")
        return

    if not isinstance(pending, dict):
        return

    # 新形式（日付キー辞書）か旧形式（単一オブジェクト）か判定
    if "date" in pending and "topics" in pending and not any(
        isinstance(v, dict) and "topics" in v for v in pending.values() if isinstance(v, dict)
    ):
        # 旧形式: 単一オブジェクトをリスト化して処理
        entries = [pending]
    else:
        # 新形式: 日付キー辞書
        entries = [v for v in pending.values() if isinstance(v, dict) and "topics" in v]

    updated = False
    for entry in entries:
        if entry.get("posted", True):
            continue

        date = entry.get("date", datetime.now().strftime("%Y-%m-%d"))
        topics = entry.get("topics", [])

        # 日付ベースの重複送信防止
        SENT_DIR.mkdir(parents=True, exist_ok=True)
        sent_flag = SENT_DIR / f"{date}.flag"
        if sent_flag.exists():
            log(f"既送信済み date={date} → スキップ（重複投稿防止）")
            entry["posted"] = True
            updated = True
            continue

        log(f"pending検知: date={date} topics={len(topics)}件 → 配信開始")
        await send_daily_news(topics, date)

        entry["posted"] = True
        sent_flag.touch()
        updated = True
        log(f"送信済みフラグ作成: {sent_flag}")

    if updated:
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
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
