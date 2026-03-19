#!/usr/bin/env python3
"""
youtube_analytics_snapshot.py — YouTube日次レポート自動取得スクリプト

毎日5:57にcrontabから実行:
    57 5 * * * cd /home/murakami/multi-agent-shogun && venv/bin/python3 scripts/youtube_analytics_snapshot.py >> projects/dozle_kirinuki/analytics/cron.log 2>&1

手動実行:
    cd /home/murakami/multi-agent-shogun
    source venv/bin/activate
    python3 scripts/youtube_analytics_snapshot.py
"""

import json
import os
import re
import subprocess
import sys
import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent  # /home/murakami/multi-agent-shogun
PROJECT_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
ANALYTICS_DIR = PROJECT_DIR / "analytics"
TOKEN_PATH = PROJECT_DIR / "token.json"
CLIENT_SECRET_PATH = PROJECT_DIR / "client_secret.json"
NTFY_SCRIPT = BASE_DIR / "scripts" / "ntfy.sh"

# ブランドアカウント（毎日ドズル社切り抜き）のチャンネルID
CHANNEL_ID = "UCiyY9PX64Nat6sd2vUhrTDQ"

# Analytics APIスコープを追加
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

TODAY = datetime.date.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
# Analytics APIは1-2日遅延あり。直近14日分（2日前まで）
ANALYTICS_END = (TODAY - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
ANALYTICS_START = (TODAY - datetime.timedelta(days=16)).strftime("%Y-%m-%d")


def get_credentials():
    """OAuth2認証情報を取得。Analytics APIスコープが不足している場合は再認証を促す"""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())
                print("[analytics] トークン更新完了")
            except Exception as e:
                print(f"[analytics] トークン更新失敗: {e}")
                creds = None

        if not creds:
            if not CLIENT_SECRET_PATH.exists():
                print(f"[analytics] エラー: {CLIENT_SECRET_PATH} が見つかりません")
                sys.exit(1)
            print("[analytics] 新規認証が必要です（Analytics APIスコープ追加のため）")
            print("  以下URLをブラウザで開いてください:")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
            auth_url, _ = flow.authorization_url(prompt="select_account")
            print(f"  {auth_url}")
            creds = flow.run_local_server(port=0, prompt="select_account")
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
            print(f"[analytics] 認証トークン保存: {TOKEN_PATH}")

    return creds


def get_channel_stats(youtube):
    """チャンネル統計（Data API）"""
    res = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=CHANNEL_ID
    ).execute()

    if not res.get("items"):
        print("[analytics] 警告: チャンネル情報が取得できませんでした")
        return {}

    item = res["items"][0]
    stats = item["statistics"]
    uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]
    return {
        "name": item["snippet"]["title"],
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "uploads_playlist_id": uploads_playlist_id,
    }


def get_all_video_ids(youtube, uploads_playlist_id):
    """アップロードプレイリストから全動画IDを取得（quota節約）"""
    video_ids = []
    page_token = None

    while True:
        params = {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token

        res = youtube.playlistItems().list(**params).execute()
        for item in res.get("items", []):
            vid = item["contentDetails"]["videoId"]
            video_ids.append(vid)

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return video_ids


def get_video_details(youtube, video_ids):
    """動画詳細統計（Data API）- 50件ずつバッチ取得"""
    videos = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        res = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(batch)
        ).execute()

        for item in res.get("items", []):
            stats = item["statistics"]
            snippet = item["snippet"]
            duration_sec = parse_duration(item["contentDetails"]["duration"])
            videos.append({
                "id": item["id"],
                "title": snippet["title"],
                "duration_sec": duration_sec,
                "duration_str": format_duration(duration_sec),
                "published_at": snippet["publishedAt"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "dislikes": int(stats.get("dislikeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })

    return sorted(videos, key=lambda x: x["views"], reverse=True)


def parse_duration(iso_duration):
    """ISO 8601 duration (PT#H#M#S) を秒数に変換"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def format_duration(sec):
    """秒数を人間が読める形式に変換"""
    if sec < 60:
        return f"{sec}s"
    elif sec < 3600:
        return f"{sec // 60}:{sec % 60:02d}"
    else:
        return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def is_short(video):
    """ショート判定: 3分以下"""
    return video["duration_sec"] <= 180


def get_daily_stats(analytics):
    """日別統計（Analytics API）"""
    res = analytics.reports().query(
        ids=f"channel=={CHANNEL_ID}",
        startDate=ANALYTICS_START,
        endDate=ANALYTICS_END,
        metrics="views,estimatedMinutesWatched,averageViewDuration,likes,subscribersGained",
        dimensions="day",
        sort="day"
    ).execute()

    rows = res.get("rows", [])
    return [
        {
            "date": row[0],
            "views": int(row[1]),
            "watch_minutes": int(row[2]),
            "avg_view_sec": int(row[3]),
            "likes": int(row[4]),
            "subs_gained": int(row[5]),
        }
        for row in rows
    ]


def get_per_video_analytics(analytics, videos):
    """動画別平均視聴時間・周回率（Analytics API）- ショート動画対象"""
    shorts = [v for v in videos if is_short(v)]
    if not shorts:
        return []

    # Analytics APIはフィルタに最大200件まで指定可能
    # ショート動画IDリストをカンマ区切りで指定
    short_ids = [v["id"] for v in shorts]

    # 50件ずつバッチ処理（フィルタ文字列の長さ制限対策）
    duration_map = {v["id"]: v["duration_sec"] for v in shorts}
    title_map = {v["id"]: v["title"] for v in videos}

    all_rows = []
    batch_size = 50
    for i in range(0, len(short_ids), batch_size):
        batch = short_ids[i:i+batch_size]
        filters = "video==" + ",".join(batch)
        try:
            res = analytics.reports().query(
                ids=f"channel=={CHANNEL_ID}",
                startDate=ANALYTICS_START,
                endDate=ANALYTICS_END,
                metrics="views,estimatedMinutesWatched,averageViewDuration",
                dimensions="video",
                filters=filters,
                sort="-views"
            ).execute()
            all_rows.extend(res.get("rows", []))
        except Exception as e:
            print(f"  [警告] per_video_analytics バッチ{i//batch_size+1} 失敗: {e}")
            continue

    results = []
    for row in all_rows:
        vid_id = row[0]
        views = int(row[1])
        estimated_minutes = int(row[2])
        avg_view_sec = int(row[3])
        duration_sec = duration_map.get(vid_id, 0)
        loop_rate = round(avg_view_sec / duration_sec, 3) if duration_sec > 0 else None
        results.append({
            "id": vid_id,
            "title": title_map.get(vid_id, ""),
            "duration_sec": duration_sec,
            "avg_view_sec": avg_view_sec,
            "loop_rate": loop_rate,
            "views": views,
            "estimated_minutes": estimated_minutes,
        })

    return sorted(results, key=lambda x: x["views"], reverse=True)


def get_traffic_sources(analytics):
    """トラフィックソース（Analytics API）"""
    res = analytics.reports().query(
        ids=f"channel=={CHANNEL_ID}",
        startDate=ANALYTICS_START,
        endDate=ANALYTICS_END,
        metrics="views,estimatedMinutesWatched",
        dimensions="insightTrafficSourceType",
        sort="-views"
    ).execute()

    rows = res.get("rows", [])
    total_views = sum(int(r[1]) for r in rows) or 1

    return [
        {
            "source": row[0],
            "views": int(row[1]),
            "watch_minutes": int(row[2]),
            "pct": round(int(row[1]) / total_views * 100),
        }
        for row in rows
    ]


def load_prev_raw():
    """前日のraw.jsonを読み込む"""
    prev_date = (TODAY - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    prev_path = ANALYTICS_DIR / f"{prev_date}_raw.json"
    if prev_path.exists():
        with open(prev_path) as f:
            return json.load(f)
    return None


def calc_video_diff(videos, prev_raw):
    """動画別再生数・いいねの前日比を計算"""
    if not prev_raw:
        return {}
    prev_videos = {v["id"]: v for v in prev_raw.get("videos", [])}
    diffs = {}
    for v in videos:
        vid = v["id"]
        if vid in prev_videos:
            diffs[vid] = {
                "views": v["views"] - prev_videos[vid]["views"],
                "likes": v["likes"] - prev_videos[vid]["likes"],
            }
    return diffs


def run_claude_analysis(channel_stats, videos, daily_stats, traffic_sources, video_diffs):
    """Claude CLI Opus 4.6でLLM分析"""
    top_videos = videos[:5]
    recent_daily = daily_stats[-5:] if daily_stats else []

    # 前日比サマリー
    total_view_diff = sum(d["views"] for d in video_diffs.values())
    total_like_diff = sum(d["likes"] for d in video_diffs.values())

    data_summary = f"""チャンネル: 毎日ドズル社切り抜き（ドズル社のマイクラ動画の切り抜きチャンネル）
登録者数: {channel_stats.get('subscribers', 0)}
総再生数: {channel_stats.get('total_views', 0)}
動画数: {channel_stats.get('video_count', 0)}

前日比:
- 総再生数変化: +{total_view_diff}
- 総いいね数変化: +{total_like_diff}

直近日別統計（直近{len(recent_daily)}日）:
{json.dumps(recent_daily, ensure_ascii=False, indent=2)}

トップ5動画（再生数順）:
{json.dumps([{
    'title': v['title'],
    'views': v['views'],
    'likes': v['likes'],
    'duration': v['duration_str'],
    'view_diff': video_diffs.get(v['id'], {}).get('views', 'N/A'),
} for v in top_videos], ensure_ascii=False, indent=2)}

トラフィックソース（上位5件）:
{json.dumps(traffic_sources[:5], ensure_ascii=False, indent=2)}
"""

    prompt = f"""あなたはYouTubeチャンネル「毎日ドズル社切り抜き」のアナリストです。
以下の日次データを分析し、日本語で所感と戦略示唆を出してください。

{data_summary}

以下の形式で出力してください（マークダウン形式）:

### 好調な点
- (具体的な数値を引用しながら箇条書き)

### 課題
- (具体的な数値を引用しながら箇条書き)

### 戦略示唆
1. (番号付きリスト、具体的なアクション)
"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-opus-4-6"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[Claude CLI エラー (return code {result.returncode})]\n{result.stderr[:500]}"
    except subprocess.TimeoutExpired:
        return "[Claude CLI タイムアウト（120秒）]"
    except FileNotFoundError:
        return "[Claude CLI が見つかりません: `which claude` で確認してください]"
    except Exception as e:
        return f"[Claude CLI 実行失敗: {e}]"


def send_ntfy_if_needed(channel_stats, video_diffs, prev_raw, videos):
    """ntfy通知（条件: 再生+500以上 or 登録+1以上 or いいね+10以上）"""
    if not prev_raw:
        return

    prev_subs = prev_raw.get("channel", {}).get("subscribers", 0)
    sub_diff = channel_stats.get("subscribers", 0) - prev_subs

    total_view_diff = sum(d["views"] for d in video_diffs.values())
    total_like_diff = sum(d["likes"] for d in video_diffs.values())

    if total_view_diff < 500 and sub_diff < 1 and total_like_diff < 10:
        return

    # トップ動画（前日比最大）
    top_vid_id = max(video_diffs.items(), key=lambda x: x[1]["views"])[0] if video_diffs else None
    top_vid_title = ""
    if top_vid_id:
        for v in videos:
            if v["id"] == top_vid_id:
                top_vid_views = v["views"]
                top_vid_title = f" トップ:{v['title'][:15]}{top_vid_views:,}再生"
                break

    msg_parts = ["📊 日次レポート:"]
    if total_view_diff > 0:
        msg_parts.append(f"再生+{total_view_diff:,}")
    if sub_diff > 0:
        msg_parts.append(f"登録+{sub_diff}")
    if total_like_diff > 0:
        msg_parts.append(f"いいね+{total_like_diff}")
    if top_vid_title:
        msg_parts.append(top_vid_title)

    msg = " ".join(msg_parts)

    try:
        subprocess.run(
            ["bash", str(NTFY_SCRIPT), msg],
            timeout=15,
            check=False
        )
        print(f"[analytics] ntfy通知送信: {msg}")
    except subprocess.TimeoutExpired:
        print("[analytics] ntfy通知タイムアウト")
    except Exception as e:
        print(f"[analytics] ntfy通知失敗: {e}")


def generate_report(channel_stats, videos, daily_stats, traffic_sources,
                    video_diffs, prev_raw, llm_analysis, per_video_analytics=None):
    """レポートMarkdown生成"""
    lines = []
    lines.append(f"# YouTube Analytics Snapshot — {DATE_STR}")
    lines.append("")
    lines.append(f"取得日時: {TODAY.strftime('%Y-%m-%d')} JST")
    lines.append(f"Analytics APIデータ範囲: {ANALYTICS_START}〜{ANALYTICS_END}（1-2日遅延あり）")
    lines.append(f"Data API（リアルタイム再生数等）: {DATE_STR}時点")
    lines.append("")
    lines.append("---")
    lines.append("")

    # チャンネル概要
    prev_subs = prev_raw["channel"]["subscribers"] if prev_raw else None
    if prev_subs is not None:
        sub_diff = channel_stats.get("subscribers", 0) - prev_subs
        sub_diff_str = f"（前日比: {sub_diff:+d}）"
    else:
        sub_diff_str = ""

    lines.append("## チャンネル概要")
    lines.append("")
    lines.append("| 指標 | 値 |")
    lines.append("|------|-----|")
    lines.append(f"| チャンネル名 | {channel_stats.get('name', '—')} |")
    lines.append(f"| 登録者数 | {channel_stats.get('subscribers', 0)}{sub_diff_str} |")
    lines.append(f"| 総再生回数 | {channel_stats.get('total_views', 0):,}（※ショートの再生はData APIカウントと差異あり） |")
    lines.append(f"| 動画数 | {channel_stats.get('video_count', 0)} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 日別統計
    lines.append(f"## 日別統計（Analytics API: {ANALYTICS_START[5:]}〜{ANALYTICS_END[5:]}）")
    lines.append("")

    if daily_stats:
        lines.append("| 日付 | 再生 | 視聴分 | 平均秒 | いいね | 登録+ |")
        lines.append("|------|------|--------|--------|--------|-------|")
        total_v = total_w = total_l = total_s = 0
        for row in daily_stats:
            date_short = row["date"][5:]  # MM-DD
            lines.append(f"| {date_short} | {row['views']} | {row['watch_minutes']} | {row['avg_view_sec']}s | {row['likes']} | {row['subs_gained']} |")
            total_v += row["views"]
            total_w += row["watch_minutes"]
            total_l += row["likes"]
            total_s += row["subs_gained"]
        lines.append(f"| **合計** | **{total_v}** | **{total_w}** | — | **{total_l}** | **{total_s}** |")
    else:
        lines.append("*日別統計なし（Analytics APIスコープ不足または取得失敗）*")

    lines.append("")
    lines.append("---")
    lines.append("")

    # トラフィックソース
    lines.append(f"## トラフィックソース（Analytics API: {ANALYTICS_START[5:]}〜{ANALYTICS_END[5:]}）")
    lines.append("")

    if traffic_sources:
        lines.append("| ソース | 再生 | 視聴分 | 割合 |")
        lines.append("|--------|------|--------|------|")
        for src in traffic_sources:
            lines.append(f"| {src['source']} | {src['views']} | {src['watch_minutes']} | {src['pct']}% |")
    else:
        lines.append("*トラフィックソースなし（Analytics APIスコープ不足または取得失敗）*")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 動画別統計
    shorts = [v for v in videos if is_short(v)]
    highlights = [v for v in videos if not is_short(v)]

    lines.append(f"## 動画別リアルタイム統計（Data API: {DATE_STR}時点）")
    lines.append("")

    lines.append("### ショート（再生数順）")
    lines.append("")
    lines.append("| タイトル | ID | 再生 | 前日比 | いいね | 低評価 | コメ | 尺 |")
    lines.append("|----------|-----|------|--------|--------|--------|------|-----|")
    for v in shorts:
        diff = video_diffs.get(v["id"], {})
        diff_views = diff.get("views", None)
        if diff_views is not None:
            diff_str = f"+{diff_views}" if diff_views >= 0 else str(diff_views)
        else:
            diff_str = "—"
        lines.append(
            f"| {v['title']} | {v['id']} | {v['views']:,} | {diff_str} | "
            f"{v['likes']} | {v['dislikes']} | {v['comments']} | {v['duration_str']} |"
        )

    lines.append("")
    lines.append("### ハイライト（長尺）")
    lines.append("")
    lines.append("| タイトル | ID | 再生 | 前日比 | いいね | 尺 |")
    lines.append("|----------|-----|------|--------|--------|-----|")
    for v in highlights:
        diff = video_diffs.get(v["id"], {})
        diff_views = diff.get("views", None)
        if diff_views is not None:
            diff_str = f"+{diff_views}" if diff_views >= 0 else str(diff_views)
        else:
            diff_str = "—"
        lines.append(
            f"| {v['title']} | {v['id']} | {v['views']:,} | {diff_str} | "
            f"{v['likes']} | {v['duration_str']} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ショート動画 周回率
    if per_video_analytics:
        lines.append(f"## ショート動画 周回率（Analytics API: {ANALYTICS_START[5:]}〜{ANALYTICS_END[5:]}）")
        lines.append("")
        lines.append("※ loop_rate = 平均視聴秒 / 動画尺。1.0以上でループ再生あり")
        lines.append("")
        lines.append("| タイトル | ID | 尺 | 平均視聴秒 | 周回率 | 再生 | 視聴分 |")
        lines.append("|----------|-----|-----|-----------|--------|------|--------|")
        for v in per_video_analytics:
            loop_str = f"{v['loop_rate']:.2f}x" if v["loop_rate"] is not None else "—"
            loop_flag = " 🔁" if v["loop_rate"] is not None and v["loop_rate"] >= 1.0 else ""
            lines.append(
                f"| {v['title'][:20]} | {v['id']} | {v['duration_sec']}s | "
                f"{v['avg_view_sec']}s | {loop_str}{loop_flag} | {v['views']:,} | {v['estimated_minutes']:,} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

    # AI分析
    lines.append("## AI分析")
    lines.append("")
    lines.append(llm_analysis)
    lines.append("")

    return "\n".join(lines)


def setup_crontab():
    """crontabに5:57登録（既に登録済みならスキップ）"""
    cron_entry = (
        "57 5 * * * cd /home/murakami/multi-agent-shogun && "
        "venv/bin/python3 scripts/youtube_analytics_snapshot.py >> "
        "projects/dozle_kirinuki/analytics/cron.log 2>&1"
    )

    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = result.stdout if result.returncode == 0 else ""

    if "youtube_analytics_snapshot.py" in current:
        print("[analytics] crontab: 既に登録済み")
        return

    new_crontab = current.rstrip("\n") + "\n" + cron_entry + "\n"
    subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
    print(f"[analytics] crontab登録完了: {cron_entry}")


def main():
    print(f"[analytics] YouTube Analytics Snapshot — {DATE_STR}")
    print(f"[analytics] Analytics範囲: {ANALYTICS_START}〜{ANALYTICS_END}")
    print("[analytics] 認証中...")

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    analytics = None
    try:
        analytics = build("youtubeAnalytics", "v2", credentials=creds)
        print("[analytics] Analytics API接続OK")
    except Exception as e:
        print(f"[analytics] 警告: Analytics API初期化失敗: {e}")
        print("  → 日別統計・トラフィックソースはスキップします")

    # チャンネル統計
    print("[analytics] チャンネル統計取得中...")
    channel_stats = get_channel_stats(youtube)
    if not channel_stats:
        print("[analytics] エラー: チャンネル統計取得失敗")
        sys.exit(1)
    print(f"  登録者: {channel_stats['subscribers']} / 総再生: {channel_stats['total_views']:,} / 動画: {channel_stats['video_count']}本")

    # 全動画統計
    print("[analytics] 全動画統計取得中...")
    uploads_playlist_id = channel_stats.pop("uploads_playlist_id")
    video_ids = get_all_video_ids(youtube, uploads_playlist_id)
    print(f"  動画ID取得: {len(video_ids)}本")
    videos = get_video_details(youtube, video_ids)
    print(f"  動画詳細取得完了: {len(videos)}本")

    # 日別統計
    daily_stats = []
    if analytics:
        print("[analytics] 日別統計取得中...")
        try:
            daily_stats = get_daily_stats(analytics)
            print(f"  {len(daily_stats)}日分取得")
        except Exception as e:
            print(f"  [警告] 日別統計取得失敗: {e}")
            print("  → Analytics APIのyt-analytics.readonlyスコープが必要かもしれません")
            print("    token.jsonを削除して再認証してください: rm projects/dozle_kirinuki/token.json")

    # トラフィックソース
    traffic_sources = []
    if analytics:
        print("[analytics] トラフィックソース取得中...")
        try:
            traffic_sources = get_traffic_sources(analytics)
            print(f"  {len(traffic_sources)}件取得")
        except Exception as e:
            print(f"  [警告] トラフィックソース取得失敗: {e}")

    # ショート動画 周回率
    per_video_analytics = []
    if analytics:
        print("[analytics] ショート動画 周回率取得中...")
        try:
            per_video_analytics = get_per_video_analytics(analytics, videos)
            print(f"  {len(per_video_analytics)}本取得")
            for v in per_video_analytics[:5]:
                loop_str = f"{v['loop_rate']:.2f}x" if v["loop_rate"] is not None else "N/A"
                print(f"    {v['id']}: 平均{v['avg_view_sec']}s / {v['duration_sec']}s = {loop_str}")
        except Exception as e:
            print(f"  [警告] 周回率取得失敗: {e}")

    # 前日比計算
    prev_raw = load_prev_raw()
    if prev_raw:
        print(f"[analytics] 前日データ読み込み完了")
    else:
        print("[analytics] 前日データなし（初回実行）")
    video_diffs = calc_video_diff(videos, prev_raw)

    # raw JSON保存
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    raw_data = {
        "date": DATE_STR,
        "channel": channel_stats,
        "videos": videos,
        "daily_stats": daily_stats,
        "traffic_sources": traffic_sources,
        "per_video_analytics": per_video_analytics,
    }
    raw_path = ANALYTICS_DIR / f"{DATE_STR}_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"[analytics] raw JSON保存: {raw_path}")

    # LLM分析
    print("[analytics] Claude Opus 4.6でLLM分析中...")
    llm_analysis = run_claude_analysis(channel_stats, videos, daily_stats, traffic_sources, video_diffs)
    print("[analytics] LLM分析完了")

    # レポート生成
    report = generate_report(channel_stats, videos, daily_stats, traffic_sources,
                             video_diffs, prev_raw, llm_analysis, per_video_analytics)
    report_path = ANALYTICS_DIR / f"{DATE_STR}_snapshot.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[analytics] レポート保存: {report_path}")

    # ntfy通知
    send_ntfy_if_needed(channel_stats, video_diffs, prev_raw, videos)

    # crontab登録
    setup_crontab()

    print("[analytics] 完了!")
    print(f"  レポート: {report_path}")
    print(f"  raw JSON: {raw_path}")


if __name__ == "__main__":
    main()
