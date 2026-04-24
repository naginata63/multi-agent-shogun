#!/usr/bin/env python3
"""
youtube_lang_batch_update.py — YouTube videos defaultLanguage/defaultAudioLanguage batch update

Usage:
    cd /home/murakami/multi-agent-shogun
    source venv/bin/activate
    python3 scripts/youtube_lang_batch_update.py [--dry-run] [--batch-size N] [--offset N]

Options:
    --dry-run      Show what would change without updating
    --batch-size N Process only N videos (default: all)
    --offset N     Skip first N videos (for resuming)

Output:
    work/cmd_1459/lang_before.json  — before state
    work/cmd_1459/lang_after.json   — after state (dry-run: copy of before)
    work/cmd_1459/lang_update_log.txt — detailed log
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
TOKEN_PATH = PROJECT_DIR / "token.json"
CLIENT_SECRET_PATH = PROJECT_DIR / "client_secret.json"
OUTPUT_DIR = BASE_DIR / "work" / "cmd_1459"

CHANNEL_ID = "UCiyY9PX64Nat6sd2vUhrTDQ"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload",
]


def get_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            print("[ERROR] Token invalid and no refresh token. Re-auth required.")
            sys.exit(1)

    return build("youtube", "v3", credentials=creds)


def get_all_video_ids(service):
    """Get all video IDs from channel uploads playlist."""
    # Get uploads playlist ID
    ch_resp = service.channels().list(
        part="contentDetails",
        id=CHANNEL_ID,
    ).execute()

    if not ch_resp.get("items"):
        print(f"[ERROR] Channel {CHANNEL_ID} not found")
        sys.exit(1)

    uploads_playlist = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    video_ids = []
    page_token = None
    while True:
        pl_resp = service.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in pl_resp.get("items", []):
            vid = item["contentDetails"].get("videoId")
            if vid:
                video_ids.append(vid)

        page_token = pl_resp.get("nextPageToken")
        if not page_token:
            break

    return video_ids


def get_video_snippets(service, video_ids):
    """Get snippet + localization for all videos (batched in 50s)."""
    snippets = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = service.videos().list(
            part="snippet",
            id=",".join(batch),
        ).execute()

        for item in resp.get("items", []):
            vid = item["id"]
            sn = item["snippet"]
            snippets[vid] = {
                "title": sn.get("title", ""),
                "description": sn.get("description", ""),
                "tags": sn.get("tags", []),
                "categoryId": sn.get("categoryId", ""),
                "defaultLanguage": sn.get("defaultLanguage"),
                "defaultAudioLanguage": sn.get("defaultAudioLanguage"),
            }

    return snippets


def update_video_lang(service, video_id, snippet_data):
    """Update a single video's defaultLanguage and defaultAudioLanguage to ja."""
    body = {
        "id": video_id,
        "snippet": {
            "title": snippet_data["title"],
            "description": snippet_data["description"],
            "categoryId": snippet_data["categoryId"],
            "defaultLanguage": "ja",
            "defaultAudioLanguage": "ja",
        }
    }
    if snippet_data["tags"]:
        body["snippet"]["tags"] = snippet_data["tags"]

    resp = service.videos().update(
        part="snippet",
        body=body,
    ).execute()

    return resp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Authenticating...")
    service = get_service()

    print(f"[INFO] Fetching video list for channel {CHANNEL_ID}...")
    video_ids = get_all_video_ids(service)
    print(f"[INFO] Found {len(video_ids)} videos")

    # Apply offset and batch-size
    video_ids = video_ids[args.offset:]
    if args.batch_size > 0:
        video_ids = video_ids[:args.batch_size]
    print(f"[INFO] Processing {len(video_ids)} videos (offset={args.offset})")

    print("[INFO] Fetching current snippet data...")
    before = get_video_snippets(service, video_ids)

    # Save before state
    before_path = OUTPUT_DIR / "lang_before.json"
    with open(before_path, "w", encoding="utf-8") as f:
        json.dump(before, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Before state saved: {before_path}")

    # Identify videos needing update
    need_update = []
    already_ja = []
    for vid in video_ids:
        sn = before.get(vid, {})
        if sn.get("defaultLanguage") == "ja" and sn.get("defaultAudioLanguage") == "ja":
            already_ja.append(vid)
        else:
            need_update.append(vid)

    print(f"[INFO] Already ja: {len(already_ja)}, Need update: {len(need_update)}")

    if args.dry_run:
        print("[DRY-RUN] No updates performed")
        after_path = OUTPUT_DIR / "lang_after.json"
        with open(after_path, "w", encoding="utf-8") as f:
            json.dump(before, f, ensure_ascii=False, indent=2)

        report = {
            "timestamp": datetime.now().isoformat(),
            "mode": "dry-run",
            "total_videos": len(video_ids),
            "already_ja": len(already_ja),
            "would_update": len(need_update),
            "quota_estimate": len(need_update) * 50,
        }
        report_path = OUTPUT_DIR / "lang_update_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[DRY-RUN] Report saved: {report_path}")
        return

    # Perform updates
    updated = []
    failed = []
    quota_used = 0
    log_lines = []

    for i, vid in enumerate(need_update):
        sn = before.get(vid, {})
        log_lines.append(
            f"[{i+1}/{len(need_update)}] {vid}: "
            f"lang={sn.get('defaultLanguage')} audio={sn.get('defaultAudioLanguage')} -> ja"
        )
        print(f"[{i+1}/{len(need_update)}] Updating {vid}...")

        try:
            update_video_lang(service, vid, sn)
            updated.append(vid)
            quota_used += 50
            log_lines.append(f"  -> OK (quota: {quota_used})")
        except Exception as e:
            failed.append({"videoId": vid, "error": str(e)})
            log_lines.append(f"  -> FAILED: {e}")
            print(f"  -> FAILED: {e}")

        # Brief pause to avoid rate limiting
        if i < len(need_update) - 1:
            time.sleep(0.5)

    # Fetch after state
    print("[INFO] Fetching after state...")
    after = get_video_snippets(service, video_ids)
    after_path = OUTPUT_DIR / "lang_after.json"
    with open(after_path, "w", encoding="utf-8") as f:
        json.dump(after, f, ensure_ascii=False, indent=2)

    # Save log
    log_path = OUTPUT_DIR / "lang_update_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    # Summary report
    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": "live",
        "total_videos": len(video_ids),
        "already_ja": len(already_ja),
        "updated": len(updated),
        "failed": len(failed),
        "quota_used": quota_used,
        "quota_limit_daily": 10000,
        "failed_details": failed if failed else None,
    }
    report_path = OUTPUT_DIR / "lang_update_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] Updated: {len(updated)}, Failed: {len(failed)}, Quota: {quota_used}/10000")
    print(f"[DONE] Report: {report_path}")
    print(f"[DONE] Before: {before_path}")
    print(f"[DONE] After: {after_path}")


if __name__ == "__main__":
    main()
