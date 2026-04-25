#!/usr/bin/env python3
"""
cta_comment.py — チャンネル公開済み動画へのCTA自動コメント投稿・更新

処理フロー:
  1. YouTube Data APIでチャンネルの全公開動画一覧を取得
  2. 各動画で自チャンネルのトップレベルコメント有無を確認
  3. コメントがなければCTAコメントを投稿
  4. コメントがあれば新文言に更新（--update指定時）

Usage:
  python3 cta_comment.py              # CTA未投稿動画にのみ投稿
  python3 cta_comment.py --update     # 既存CTAコメントを新文言に一括更新
  python3 cta_comment.py --dry-run    # 更新対象件数のみ確認（実際は更新しない）
  python3 cta_comment.py --update --dry-run
"""

import argparse
import os
import sys
import time

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

# 単一情報源: projects/dozle_kirinuki/context/youtube_channel.yaml
import yaml
_CHANNEL_YAML = os.path.join(PROJECT_DIR, "context", "youtube_channel.yaml")
with open(_CHANNEL_YAML, "r", encoding="utf-8") as _f:
    _ch_cfg = yaml.safe_load(_f)
CHANNEL_ID = _ch_cfg["brand"]["channel_id"]
CTA_COMMENT = _ch_cfg["cta_comment"].rstrip("\n")


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


def get_public_videos(youtube) -> list[str]:
    """チャンネルの全公開済み動画 video_id 一覧を返す（最新順）"""
    video_ids = []
    page_token = None

    while True:
        res = youtube.search().list(
            part="id",
            channelId=CHANNEL_ID,
            type="video",
            order="date",
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in res.get("items", []):
            video_ids.append(item["id"]["videoId"])

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return video_ids


def has_own_comment(youtube, video_id: str, my_channel_id: str) -> tuple:
    """自チャンネルのトップレベルコメントを検索。

    Returns:
        (found, comment_id, comment_text) — found=Trueでコメント情報を返す
        コメント取得エラー時は (True, None, None) を返しスキップ扱いにする
    """
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
            return True, None, None

        for thread in res.get("items", []):
            author_id = (
                thread["snippet"]["topLevelComment"]["snippet"]
                .get("authorChannelId", {})
                .get("value", "")
            )
            if author_id == my_channel_id:
                comment_id = thread["snippet"]["topLevelComment"]["id"]
                comment_text = thread["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
                return True, comment_id, comment_text

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return False, None, None


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


def update_cta_comment(youtube, comment_id: str) -> str:
    """既存コメントを新CTA文言に更新し、comment_id を返す"""
    res = youtube.comments().update(
        part="snippet",
        body={
            "id": comment_id,
            "snippet": {"textOriginal": CTA_COMMENT},
        },
    ).execute()
    return res["id"]


def main():
    parser = argparse.ArgumentParser(description="CTAコメント投稿・更新")
    parser.add_argument("--update", action="store_true",
                        help="既存CTAコメントを新文言に一括更新")
    parser.add_argument("--dry-run", action="store_true",
                        help="対象件数確認のみ（実際の投稿・更新はしない）")
    args = parser.parse_args()

    youtube = get_service()

    # 自チャンネル確認
    me = youtube.channels().list(part="snippet", mine=True).execute()
    my_channel_id = me["items"][0]["id"]
    ch_title = me["items"][0]["snippet"]["title"]
    print(f"[cta] チャンネル: {ch_title} ({my_channel_id})")

    videos = get_public_videos(youtube)
    print(f"[cta] 公開動画: {len(videos)} 件を確認")
    if args.dry_run:
        print("[cta] *** DRY-RUN モード（投稿・更新は行わない）***")
    if args.update:
        print("[cta] *** UPDATE モード（既存コメントを新文言に更新）***")

    posted = 0
    updated = 0
    already = 0
    skipped = 0
    errors = 0

    for video_id in videos:
        found, comment_id, comment_text = has_own_comment(youtube, video_id, my_channel_id)

        if found and comment_id is None:
            # コメント取得エラー → スキップ
            skipped += 1
            continue

        if found:
            # 既存コメントあり
            if args.update:
                if comment_text.strip() == CTA_COMMENT.strip():
                    print(f"  {video_id}: 既に最新文言（スキップ）")
                    already += 1
                else:
                    if args.dry_run:
                        print(f"  {video_id}: 更新対象 [{comment_id}]")
                        updated += 1
                    else:
                        try:
                            update_cta_comment(youtube, comment_id)
                            print(f"  {video_id}: コメント更新完了")
                            updated += 1
                            time.sleep(1)  # API rate limit対策
                        except Exception as e:
                            print(f"  {video_id}: 更新エラー: {e}")
                            errors += 1
            else:
                print(f"  {video_id}: コメント済み（スキップ）")
                already += 1
        else:
            # コメントなし → 新規投稿
            if args.dry_run:
                print(f"  {video_id}: 新規投稿対象")
                posted += 1
            else:
                try:
                    new_id = post_cta_comment(youtube, video_id)
                    print(f"  {video_id}: CTAコメント投稿完了 ({new_id})")
                    posted += 1
                    time.sleep(1)  # API rate limit対策
                except Exception as e:
                    print(f"  {video_id}: 投稿エラー: {e}")
                    errors += 1

    mode_label = "[dry-run] " if args.dry_run else ""
    print(f"\n[cta] {mode_label}完了")
    print(f"  新規投稿: {posted} 件")
    if args.update:
        print(f"  更新: {updated} 件")
    print(f"  最新文言済み: {already} 件")
    print(f"  スキップ: {skipped} 件")
    if errors:
        print(f"  エラー: {errors} 件")


if __name__ == "__main__":
    main()
