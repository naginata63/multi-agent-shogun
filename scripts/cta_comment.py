#!/usr/bin/env python3
"""
cta_comment.py — チャンネル公開済み動画へのCTA自動コメント投稿

処理フロー:
  1. YouTube Data APIでチャンネルの公開済み動画一覧を取得（最新50件）
  2. 各動画で自チャンネルのトップレベルコメント有無を確認
  3. コメントがなければCTAコメントを投稿
"""

import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# dozle_kirinuki プロジェクト（認証トークン置き場）
PROJECT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "projects", "dozle_kirinuki"
)
TOKEN_PATH = os.path.join(PROJECT_DIR, "token.json")
CLIENT_SECRET_PATH = os.path.join(PROJECT_DIR, "client_secret.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# 毎日ドズル社切り抜きチャンネル ID
CHANNEL_ID = "UCiyY9PX64Nat6sd2vUhrTDQ"

# CTAコメント定型文（youtube_uploader.py の CTA_COMMENT と同一）
CTA_COMMENT = "明日も面白いシーン切り抜きます！見逃したくない人はチャンネル登録✂️"


def get_service():
    if not os.path.exists(TOKEN_PATH):
        print(f"[cta] エラー: token.json が見つかりません: {TOKEN_PATH}", file=sys.stderr)
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print("[cta] トークン更新完了")

    return build("youtube", "v3", credentials=creds)


def get_public_videos(youtube, max_results: int = 50) -> list[str]:
    """チャンネルの公開済み動画 video_id 一覧を返す（最新順）"""
    video_ids = []
    page_token = None
    remaining = max_results

    while remaining > 0:
        res = youtube.search().list(
            part="id",
            channelId=CHANNEL_ID,
            type="video",
            order="date",
            maxResults=min(remaining, 50),
            pageToken=page_token,
        ).execute()

        for item in res.get("items", []):
            video_ids.append(item["id"]["videoId"])

        page_token = res.get("nextPageToken")
        remaining -= len(res.get("items", []))
        if not page_token:
            break

    return video_ids


def has_own_comment(youtube, video_id: str, my_channel_id: str) -> bool:
    """自チャンネルのトップレベルコメントが既にあれば True を返す"""
    page_token = None
    while True:
        try:
            kwargs = dict(part="snippet", videoId=video_id, maxResults=100)
            if page_token:
                kwargs["pageToken"] = page_token
            res = youtube.commentThreads().list(**kwargs).execute()
        except Exception as e:
            # コメント無効化動画など → スキップ扱い（二重投稿防止）
            print(f"  [skip] コメント取得エラー ({video_id}): {e}")
            return True

        for thread in res.get("items", []):
            author_id = (
                thread["snippet"]["topLevelComment"]["snippet"]
                .get("authorChannelId", {})
                .get("value", "")
            )
            if author_id == my_channel_id:
                return True

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return False


def post_cta_comment(youtube, video_id: str) -> str:
    """CTAコメントを投稿し、comment_id を返す"""
    res = youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {"textOriginal": CTA_COMMENT}
                },
            }
        },
    ).execute()
    return res["id"]


def main():
    youtube = get_service()

    # 自チャンネル確認
    me = youtube.channels().list(part="snippet", mine=True).execute()
    my_channel_id = me["items"][0]["id"]
    ch_title = me["items"][0]["snippet"]["title"]
    print(f"[cta] チャンネル: {ch_title} ({my_channel_id})")

    videos = get_public_videos(youtube)
    print(f"[cta] 公開動画: {len(videos)} 件を確認")

    posted = 0
    skipped = 0
    for video_id in videos:
        if has_own_comment(youtube, video_id, my_channel_id):
            print(f"  {video_id}: コメント済み（スキップ）")
            skipped += 1
        else:
            comment_id = post_cta_comment(youtube, video_id)
            print(f"  {video_id}: CTAコメント投稿完了 ({comment_id})")
            posted += 1

    print(f"[cta] 完了 — 投稿: {posted} 件 / スキップ: {skipped} 件")


if __name__ == "__main__":
    main()
