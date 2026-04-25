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
    projects/dozle_kirinuki/work/cmd_lang_batch/lang_before.json  — before state
    projects/dozle_kirinuki/work/cmd_lang_batch/lang_after.json   — after state (dry-run: copy of before)
    projects/dozle_kirinuki/work/cmd_lang_batch/lang_update_log.txt — detailed log
    projects/dozle_kirinuki/work/cmd_lang_batch/revert/   — revert outputs (when revert sub-command)
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

import yaml

BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
TOKEN_PATH = PROJECT_DIR / "token.json"
CLIENT_SECRET_PATH = PROJECT_DIR / "client_secret.json"
OUTPUT_DIR = PROJECT_DIR / "work" / "cmd_lang_batch"

# 単一情報源: projects/dozle_kirinuki/context/youtube_channel.yaml
with open(PROJECT_DIR / "context" / "youtube_channel.yaml", "r", encoding="utf-8") as _f:
    CHANNEL_ID = yaml.safe_load(_f)["brand"]["channel_id"]

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


def update_video_lang(service, video_id, snippet_data, lang="ja", audio_lang=None):
    """Update a single video's defaultLanguage and defaultAudioLanguage."""
    if audio_lang is None:
        audio_lang = lang
    snippet = {
        "title": snippet_data["title"],
        "description": snippet_data["description"],
        "categoryId": snippet_data["categoryId"],
        "defaultLanguage": lang,
        "defaultAudioLanguage": audio_lang,
    }
    body = {
        "id": video_id,
        "snippet": snippet,
    }
    if snippet_data["tags"]:
        body["snippet"]["tags"] = snippet_data["tags"]

    resp = service.videos().update(
        part="snippet",
        body=body,
    ).execute()

    return resp


def do_revert(args):
    """Revert language settings from lang_before.json."""
    before_path = OUTPUT_DIR / "lang_before.json"
    if not before_path.exists():
        print(f"[ERROR] {before_path} not found")
        sys.exit(1)

    with open(before_path, "r", encoding="utf-8") as f:
        before = json.load(f)

    revert_output = OUTPUT_DIR / "revert"
    revert_output.mkdir(parents=True, exist_ok=True)

    # Exclude QharlfIueqI (uncertain state)
    exclude = {"QharlfIueqI"}

    # Identify revert targets: videos whose original lang was not ja
    targets = []
    for vid, sn in before.items():
        if vid in exclude:
            print(f"[SKIP] {vid} (excluded)")
            continue
        orig_dl = sn.get("defaultLanguage")
        orig_dal = sn.get("defaultAudioLanguage")
        if orig_dl != "ja" or orig_dal != "ja":
            targets.append((vid, orig_dl, orig_dal))

    print(f"[INFO] Revert targets: {len(targets)} videos (excluded: {len(exclude)})")

    if not targets:
        print("[INFO] No revert targets found")
        return

    print(f"[INFO] Authenticating...")
    service = get_service()

    # Fetch current state of target videos
    target_ids = [t[0] for t in targets]
    current = get_video_snippets(service, target_ids)

    # Save before-revert state
    before_revert_path = revert_output / "before_revert.json"
    with open(before_revert_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Before-revert state saved: {before_revert_path}")

    if args.dry_run:
        print("[DRY-RUN] Would revert:")
        for vid, orig_dl, orig_dal in targets:
            cur = current.get(vid, {})
            print(f"  {vid}: dl={cur.get('defaultLanguage')}->{orig_dl}, dal={cur.get('defaultAudioLanguage')}->{orig_dal}")
        return

    # Perform revert
    updated = []
    failed = []
    quota_used = 0
    log_lines = []
    log_lines.append(f"Revert started: {datetime.now().isoformat()}")
    log_lines.append(f"Targets: {len(targets)}")

    for i, (vid, orig_dl, orig_dal) in enumerate(targets):
        cur = current.get(vid, {})
        log_lines.append(
            f"[{i+1}/{len(targets)}] {vid}: "
            f"dl={cur.get('defaultLanguage')}->{orig_dl}, "
            f"dal={cur.get('defaultAudioLanguage')}->{orig_dal}"
        )
        print(f"[{i+1}/{len(targets)}] Reverting {vid}...")

        try:
            update_video_lang(service, vid, cur, lang=orig_dl, audio_lang=orig_dal)
            updated.append(vid)
            quota_used += 50
            log_lines.append(f"  -> OK (quota: {quota_used})")
        except Exception as e:
            failed.append({"videoId": vid, "error": str(e)})
            log_lines.append(f"  -> FAILED: {e}")
            print(f"  -> FAILED: {e}")

        if i < len(targets) - 1:
            time.sleep(0.5)

    # Fetch after-revert state
    print("[INFO] Fetching after-revert state...")
    after = get_video_snippets(service, target_ids)
    after_revert_path = revert_output / "after_revert.json"
    with open(after_revert_path, "w", encoding="utf-8") as f:
        json.dump(after, f, ensure_ascii=False, indent=2)

    # Save log
    log_lines.append(f"\nRevert completed: {datetime.now().isoformat()}")
    log_lines.append(f"Updated: {len(updated)}, Failed: {len(failed)}, Quota: {quota_used}")
    log_path = revert_output / "revert_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": "revert",
        "total_targets": len(targets),
        "updated": len(updated),
        "failed": len(failed),
        "quota_used": quota_used,
        "failed_details": failed if failed else None,
    }
    report_path = revert_output / "revert_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] Reverted: {len(updated)}, Failed: {len(failed)}, Quota: {quota_used}/10000")
    print(f"[DONE] Report: {report_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--revert", action="store_true",
                        help="Revert language settings from lang_before.json")
    args = parser.parse_args()

    if args.revert:
        do_revert(args)
        return

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
