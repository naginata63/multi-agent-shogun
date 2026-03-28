#!/usr/bin/env python3
"""
create_hotspot_summary.py — 全動画hotspot JSONを集約してsummary作成

使い方:
    python3 scripts/create_hotspot_summary.py --output work/hotspot_summary.json
"""

import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
WORK_DIR = BASE_DIR / "work"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="work/hotspot_summary.json")
    args = parser.parse_args()

    hotspot_files = sorted(WORK_DIR.glob("hotspot_*.json"))
    # Exclude the summary file itself
    hotspot_files = [f for f in hotspot_files if f.name != "hotspot_summary.json"]

    print(f"[summary] 読み込み対象: {len(hotspot_files)}件")

    all_entries = []
    skipped = []

    for f in hotspot_files:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        video_id = data.get("video_id", f.stem.replace("hotspot_", ""))
        hotspots = data.get("hotspots", [])
        total_comments = data.get("total_comments", 0)
        ts_comments = data.get("timestamp_comments", 0)

        if not hotspots:
            skipped.append(video_id)
            continue

        # Top 5のみ抽出
        for hs in hotspots[:5]:
            all_entries.append({
                "video_id": video_id,
                "start_time": hs.get("start_time", ""),
                "end_time": hs.get("end_time", ""),
                "start_sec": hs.get("start_sec", 0),
                "end_sec": hs.get("end_sec", 0),
                "comment_count": hs.get("comment_count", 0),
                "emotion": hs.get("emotion", "その他"),
                "score": hs.get("score", 5),
                "summary": hs.get("summary", ""),
                "rank_in_video": hs.get("rank", 1),
            })

    # スコア降順でソート
    all_entries.sort(key=lambda x: x["score"] * 10 + x["comment_count"], reverse=True)

    # 動画ごとのTop1も集計
    per_video_top = {}
    for entry in all_entries:
        vid = entry["video_id"]
        if vid not in per_video_top:
            per_video_top[vid] = entry

    summary = {
        "total_videos": len(hotspot_files),
        "videos_with_hotspots": len(per_video_top),
        "videos_no_timestamps": skipped,
        "top_hotspots_all": all_entries[:50],  # 全動画横断Top50
        "per_video_top1": list(per_video_top.values()),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[summary] 保存: {out_path}")
    print(f"[summary] 対象動画: {len(hotspot_files)}本 / ホットスポットあり: {len(per_video_top)}本 / タイムスタンプなし: {len(skipped)}本")
    print(f"[summary] 総エントリ数（Top5/動画）: {len(all_entries)}件")
    print(f"\n--- 全動画横断 Top10 ---")
    for i, e in enumerate(all_entries[:10], 1):
        print(f"#{i} [{e['video_id']}] {e['start_time']}〜{e['end_time']} [{e['emotion']}] score:{e['score']} comments:{e['comment_count']}")
        if e['summary']:
            print(f"   → {e['summary']}")


if __name__ == "__main__":
    main()
