#!/usr/bin/env python3
"""
audit_video_index_consistency.py — CSV vs scene_index_v2 突合 + quality_status 分類

使い方:
    python3 scripts/audit_video_index_consistency.py
    python3 scripts/audit_video_index_consistency.py --update-csv
    python3 scripts/audit_video_index_consistency.py --index-dir data/scene_index_v2 --csv projects/dozle_kirinuki/data/dozle_video_list.csv
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# A-F single-letter speakers = unconverted speaker labels
ALPHABET_SPEAKERS = {"A", "B", "C", "D", "E", "F"}


def load_index_metadata(index_dir: Path) -> dict:
    """chunks_metadata.json から video_id → set(speakers) を構築。"""
    meta_path = index_dir / "chunks_metadata.json"
    if not meta_path.exists():
        print(f"ERROR: {meta_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    vid_speakers = defaultdict(set)
    for entry in metadata:
        vid = entry.get("video_id", "")
        for spk in entry.get("speakers", []):
            vid_speakers[vid].add(spk)

    return dict(vid_speakers)


def load_csv_video_ids(csv_path: Path) -> list:
    """CSV から video_id リストを返す（BOM 付き UTF-8 対応）。"""
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found", file=sys.stderr)
        sys.exit(1)

    raw = csv_path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(raw.splitlines())
    video_ids = []
    for row in reader:
        vid = row.get("video_id", "").strip()
        if vid:
            video_ids.append(vid)
    return video_ids


def classify(vid: str, speakers: set | None, csv_vids: set) -> str:
    """video_id の quality_status を判定。"""
    indexed = speakers is not None

    if indexed and vid not in csv_vids:
        return "csv_outdated"
    if not indexed and vid in csv_vids:
        return "index_missing"
    if not indexed:
        return "index_missing"

    has_alpha = bool(speakers & ALPHABET_SPEAKERS)
    if has_alpha:
        return "violation_alphabet"
    return "ok"


def main():
    parser = argparse.ArgumentParser(
        description="CSV vs scene_index_v2 突合 + quality_status 分類"
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=Path("data/scene_index_v2"),
        help="scene_index_v2 ディレクトリ (default: data/scene_index_v2)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("projects/dozle_kirinuki/data/dozle_video_list.csv"),
        help="dozle_video_list.csv パス",
    )
    parser.add_argument(
        "--update-csv",
        action="store_true",
        help="CSV の quality_status 列を更新",
    )
    args = parser.parse_args()

    index_dir = args.index_dir.resolve()
    csv_path = args.csv.resolve()

    vid_speakers = load_index_metadata(index_dir)
    csv_vids_list = load_csv_video_ids(csv_path)
    csv_vids = set(csv_vids_list)

    # 全 video_id を統合
    all_vids = sorted(set(vid_speakers.keys()) | csv_vids)

    results = {}
    counts = defaultdict(int)

    for vid in all_vids:
        speakers = vid_speakers.get(vid)
        status = classify(vid, speakers, csv_vids)
        results[vid] = {
            "status": status,
            "speakers": sorted(speakers) if speakers else [],
        }
        counts[status] += 1

    # 結果表示
    print(f"{'Video ID':<16} {'Status':<22} {'Speakers'}")
    print("-" * 70)
    for vid in all_vids:
        r = results[vid]
        spk_str = ", ".join(r["speakers"]) if r["speakers"] else "-"
        print(f"{vid:<16} {r['status']:<22} {spk_str}")

    # サマリ
    print()
    print("=== Summary ===")
    for status in ["ok", "violation_alphabet", "index_missing", "csv_outdated"]:
        print(f"  {status:<22} {counts.get(status, 0)}")
    print(f"  {'TOTAL':<22} {len(all_vids)}")

    # CSV 更新
    if args.update_csv:
        raw = csv_path.read_text(encoding="utf-8-sig")
        reader = csv.DictReader(raw.splitlines())
        fieldnames = reader.fieldnames or []
        if "quality_status" not in fieldnames:
            fieldnames.append("quality_status")

        rows = []
        for row in reader:
            vid = row.get("video_id", "").strip()
            if vid in results:
                row["quality_status"] = results[vid]["status"]
            else:
                row["quality_status"] = "index_missing"
            rows.append(row)

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\nCSV updated: {csv_path}")


if __name__ == "__main__":
    main()
