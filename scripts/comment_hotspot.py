#!/usr/bin/env python3
"""
comment_hotspot.py — YouTubeコメントのタイムスタンプからショートポイント候補を自動抽出

使い方:
    python3 scripts/comment_hotspot.py <video_id> [--top N] [--output report.json]

例:
    python3 scripts/comment_hotspot.py HvpVBlzwQiw
    python3 scripts/comment_hotspot.py HvpVBlzwQiw --top 15 --output work/hotspot.json

出力:
    - Top N ホットスポット（開始時刻・コメント数・代表コメント・感情ラベル・スコア）
    - JSON + 人間可読テキスト両方

注意:
    - Gemini API不使用。感情分析はClaude CLI Opus 4.6
    - YouTube APIクオータ: commentThreads.list は 1unit/リクエスト
    - 認証: projects/dozle_kirinuki/token.json（既存OAuth流用）
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
TOKEN_PATH = PROJECT_DIR / "token.json"
CLIENT_SECRET_PATH = PROJECT_DIR / "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

BUCKET_SECONDS = 30  # ヒートマップのバケット幅（秒）
MERGE_GAP = 2        # 隣接バケット結合の最大ギャップ（バケット数）


def get_credentials():
    """OAuth2認証情報を取得"""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_PATH.exists():
                print(f"[hotspot] エラー: {CLIENT_SECRET_PATH} が見つかりません")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
            auth_url, _ = flow.authorization_url(prompt="select_account")
            print(f"\n[hotspot] 以下のURLをブラウザで開いて認証してください:")
            print(f"  {auth_url}")
            print()
            creds = flow.run_local_server(port=0, prompt="select_account")

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"[hotspot] 認証トークン保存: {TOKEN_PATH}")

    return creds


def fetch_all_comments(youtube, video_id):
    """YouTube Data API v3 でコメントを全件取得"""
    comments = []
    next_page_token = None
    page = 0

    while True:
        page += 1
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "order": "relevance",
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        resp = youtube.commentThreads().list(**params).execute()
        items = resp.get("items", [])
        for item in items:
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": top["textDisplay"],
                "likeCount": top.get("likeCount", 0),
                "publishedAt": top.get("publishedAt", ""),
            })

        next_page_token = resp.get("nextPageToken")
        print(f"[hotspot] ページ {page}: {len(items)}件取得（累計 {len(comments)}件）")

        if not next_page_token:
            break

    return comments


def parse_timestamps(text):
    """コメントからタイムスタンプを抽出して秒に変換"""
    pattern = r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b'
    matches = re.findall(pattern, text)
    seconds_list = []
    for m in matches:
        h, mn, s = m
        if s:
            total = int(h) * 3600 + int(mn) * 60 + int(s)
        else:
            # HH:MM or MM:SS の判定
            # 先頭が2桁かつ0-59ならMM:SS、そうでなければHH:MM
            first = int(h)
            second = int(mn)
            if first <= 59 and second <= 59:
                # MM:SS として解釈
                total = first * 60 + second
            else:
                total = first * 3600 + second * 60
        # 0:00 は冒頭への言及が多く除外しない（有効タイムスタンプ）
        seconds_list.append(total)
    return seconds_list


def build_heatmap(comments):
    """
    バケット単位のヒートマップを構築。
    Returns:
        bucket_counts: dict[bucket_id] -> count
        bucket_comments: dict[bucket_id] -> list of comment texts
    """
    bucket_counts = defaultdict(int)
    bucket_comments = defaultdict(list)

    for c in comments:
        ts_list = parse_timestamps(c["text"])
        for ts in ts_list:
            bucket = ts // BUCKET_SECONDS
            bucket_counts[bucket] += 1
            bucket_comments[bucket].append(c["text"])

    return bucket_counts, bucket_comments


def merge_hotspots(bucket_counts, bucket_comments, top_n=10):
    """
    高密度バケットを結合してホットスポット区間を作る。
    Returns: list of hotspot dicts, sorted by count desc
    """
    if not bucket_counts:
        return []

    # 全バケットをソート
    sorted_buckets = sorted(bucket_counts.keys())

    # 隣接バケットをグループ化（MERGE_GAP以内のギャップは結合）
    groups = []
    current_group = [sorted_buckets[0]]
    for b in sorted_buckets[1:]:
        if b - current_group[-1] <= MERGE_GAP:
            current_group.append(b)
        else:
            groups.append(current_group)
            current_group = [b]
    groups.append(current_group)

    hotspots = []
    for group in groups:
        total_count = sum(bucket_counts[b] for b in group)
        all_comments = []
        for b in group:
            all_comments.extend(bucket_comments[b])

        start_sec = group[0] * BUCKET_SECONDS
        end_sec = (group[-1] + 1) * BUCKET_SECONDS

        hotspots.append({
            "start_sec": start_sec,
            "end_sec": end_sec,
            "start_time": sec_to_str(start_sec),
            "end_time": sec_to_str(end_sec),
            "comment_count": total_count,
            "comments": all_comments,
            "top_comments": sorted(all_comments, key=len, reverse=True)[:5],
        })

    # コメント数降順でソート
    hotspots.sort(key=lambda x: x["comment_count"], reverse=True)
    return hotspots[:top_n * 3]  # 後でスコアリング後にTop Nに絞る


def sec_to_str(sec):
    """秒を HH:MM:SS または MM:SS に変換"""
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def analyze_emotion_claude(hotspots):
    """
    Claude CLI Opus 4.6 で各ホットスポットの感情分析を行う。
    感情ラベル: 笑い / 感動 / 驚き / ツッコミ / その他
    ショート向きスコア（笑い・ツッコミ=高得点）
    """
    if not hotspots:
        return hotspots

    # 全ホットスポットを1回のClaudeに投げる（APIコスト節約）
    entries = []
    for i, hs in enumerate(hotspots):
        comments_text = "\n".join(f"  - {c[:100]}" for c in hs["top_comments"][:5])
        entries.append(
            f"[区間{i+1}] {hs['start_time']}〜{hs['end_time']} ({hs['comment_count']}件)\n"
            f"{comments_text}"
        )

    prompt = (
        "以下はYouTube動画の各時間区間に集中したコメント群です。\n"
        "各区間について:\n"
        "1. 感情ラベル（笑い/感動/驚き/ツッコミ/その他）を1つ選ぶ\n"
        "2. ショート動画向きスコア（0-10）を付ける（笑い・ツッコミ=高得点, その他=低得点）\n"
        "3. 代表コメント1件（20字以内に要約）\n\n"
        "回答形式（JSONのみ、余分なテキスト不要）:\n"
        '[\n'
        '  {"index": 1, "emotion": "笑い", "score": 9, "summary": "要約文"},\n'
        '  ...\n'
        ']\n\n'
        "以下が区間データ:\n\n"
        + "\n\n".join(entries)
    )

    print(f"[hotspot] Claude CLI で感情分析中（{len(hotspots)}区間）...")

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-opus-4-6"],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout.strip()

        # JSONブロックを抽出
        json_match = re.search(r'\[.*?\]', output, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
            for item in analysis:
                idx = item["index"] - 1
                if 0 <= idx < len(hotspots):
                    hotspots[idx]["emotion"] = item.get("emotion", "その他")
                    hotspots[idx]["score"] = item.get("score", 5)
                    hotspots[idx]["summary"] = item.get("summary", "")
        else:
            print(f"[hotspot] 警告: Claude出力からJSONを抽出できませんでした")
            print(f"[hotspot] 出力: {output[:500]}")
            # デフォルト値をセット
            for hs in hotspots:
                hs.setdefault("emotion", "その他")
                hs.setdefault("score", 5)
                hs.setdefault("summary", "")

    except subprocess.TimeoutExpired:
        print("[hotspot] 警告: Claude CLI タイムアウト。感情ラベルなしで続行")
        for hs in hotspots:
            hs.setdefault("emotion", "その他")
            hs.setdefault("score", 5)
            hs.setdefault("summary", "")
    except Exception as e:
        print(f"[hotspot] 警告: Claude CLI エラー: {e}。感情ラベルなしで続行")
        for hs in hotspots:
            hs.setdefault("emotion", "その他")
            hs.setdefault("score", 5)
            hs.setdefault("summary", "")

    return hotspots


def format_report(hotspots, video_id, top_n):
    """人間可読テキストレポートを生成"""
    lines = [
        f"=== YouTubeコメント ホットスポット分析 ===",
        f"動画ID: {video_id}",
        f"Top {top_n} ショートポイント候補",
        "",
    ]
    for rank, hs in enumerate(hotspots[:top_n], 1):
        emotion = hs.get("emotion", "?")
        score = hs.get("score", "?")
        summary = hs.get("summary", "")
        lines.append(
            f"#{rank}  {hs['start_time']}〜{hs['end_time']}"
            f"  コメント{hs['comment_count']}件"
            f"  [{emotion}] スコア:{score}/10"
        )
        if summary:
            lines.append(f"     → {summary}")
        for c in hs["top_comments"][:3]:
            lines.append(f"     「{c[:60]}{'...' if len(c)>60 else ''}」")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="YouTubeコメントからショートポイント候補を自動抽出")
    parser.add_argument("video_id", help="YouTube動画ID（例: HvpVBlzwQiw）")
    parser.add_argument("--top", type=int, default=10, help="Top N候補を表示（デフォルト: 10）")
    parser.add_argument("--output", help="JSON出力ファイルパス（省略可）")
    args = parser.parse_args()

    video_id = args.video_id
    top_n = args.top

    print(f"[hotspot] 動画ID: {video_id}  Top {top_n}候補を抽出します")

    # 認証
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    # Step 1: コメント全件取得
    print("[hotspot] Step 1: コメント取得中...")
    comments = fetch_all_comments(youtube, video_id)
    print(f"[hotspot] 合計 {len(comments)} 件取得完了")

    if not comments:
        print("[hotspot] コメントが0件です。動画IDを確認してください。")
        sys.exit(1)

    # Step 2: タイムスタンプ抽出 + ヒートマップ
    print("[hotspot] Step 2: タイムスタンプ抽出中...")
    bucket_counts, bucket_comments = build_heatmap(comments)
    ts_count = sum(bucket_counts.values())
    print(f"[hotspot] タイムスタンプ付きコメント: {ts_count}件 → {len(bucket_counts)}バケット")

    if ts_count == 0:
        print("[hotspot] タイムスタンプ付きコメントが0件です。動画にタイムスタンプコメントがない可能性があります。")
        sys.exit(1)

    # Step 3: ホットスポット検出
    print("[hotspot] Step 3: ホットスポット検出中...")
    hotspots = merge_hotspots(bucket_counts, bucket_comments, top_n=top_n)
    print(f"[hotspot] {len(hotspots)}区間を候補として検出")

    # Step 4: 感情分析（Claude CLI）
    print("[hotspot] Step 4: 感情分析中（Claude CLI Opus 4.6）...")
    hotspots = analyze_emotion_claude(hotspots)

    # スコア + コメント数で最終ランク付け
    for hs in hotspots:
        hs["final_rank_score"] = hs.get("score", 5) * 10 + hs["comment_count"]
    hotspots.sort(key=lambda x: x["final_rank_score"], reverse=True)

    # Step 5: 出力
    print("[hotspot] Step 5: 出力...")
    report_text = format_report(hotspots, video_id, top_n)
    print("\n" + report_text)

    # JSON出力
    output_data = {
        "video_id": video_id,
        "total_comments": len(comments),
        "timestamp_comments": ts_count,
        "hotspots": [
            {
                "rank": i + 1,
                "start_time": hs["start_time"],
                "end_time": hs["end_time"],
                "start_sec": hs["start_sec"],
                "end_sec": hs["end_sec"],
                "comment_count": hs["comment_count"],
                "emotion": hs.get("emotion", "その他"),
                "score": hs.get("score", 5),
                "summary": hs.get("summary", ""),
                "top_comments": hs["top_comments"][:3],
            }
            for i, hs in enumerate(hotspots[:top_n])
        ],
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"[hotspot] JSON保存: {out_path}")

    return output_data


if __name__ == "__main__":
    main()
