#!/usr/bin/env python3
"""
merged JSONのwordsから実名ラベル付きSRTを再生成するスクリプト
"""
import argparse
import json
import sys
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))
from stt_merge import generate_srt

WORK_BASE = os.path.join(os.path.dirname(__file__))
SRT_CAND = os.path.join(WORK_BASE, 'srt_and_candidates')

TARGETS = [
    {
        "video_id": "sQQ1t9OQl2c",
        "merged_json": os.path.join(SRT_CAND, "merged_sQQ1t9OQl2c.json"),
        "output_srt": os.path.join(SRT_CAND, "merged_sQQ1t9OQl2c.srt"),
        "orig_dir": os.path.join(WORK_BASE, "20260320_おらふイングリッシュ翻訳してくだサーイ！！【マイクラ】"),
        "orig_srt": "merged_sQQ1t9OQl2c.srt",
    },
    {
        "video_id": "2W2HZr2L-nI",
        "merged_json": os.path.join(WORK_BASE, "20260319_都道府県が使える世界でエンドラ討伐", "merged_2W2HZr2L-nI.json"),
        "output_srt": os.path.join(SRT_CAND, "merged_2W2HZr2L-nI.srt"),
        "orig_dir": os.path.join(WORK_BASE, "20260319_都道府県が使える世界でエンドラ討伐"),
        "orig_srt": "merged_2W2HZr2L-nI.srt",
    },
    {
        "video_id": "iuAP6rAoGFk",
        "merged_json": os.path.join(SRT_CAND, "merged_iuAP6rAoGFk.json"),
        "output_srt": os.path.join(SRT_CAND, "merged_iuAP6rAoGFk.srt"),
        "orig_dir": os.path.join(WORK_BASE, "20260312_最強のハンターがいる世界でエンドラ討伐【マイクラ】"),
        "orig_srt": "merged_iuAP6rAoGFk.srt",
    },
]


def regen_srt(target: dict) -> dict:
    vid = target["video_id"]
    print(f"\n=== {vid} ===")

    with open(target["merged_json"], encoding="utf-8") as f:
        data = json.load(f)

    words = data.get("words", [])
    print(f"  words: {len(words)}")

    speakers = set(w.get("speaker") for w in words if w.get("speaker"))
    print(f"  speakers: {speakers}")

    srt_content = generate_srt(words)
    lines = srt_content.strip().split('\n')
    print(f"  SRT lines: {len(lines)}")

    # srt_and_candidates/に書き込み
    with open(target["output_srt"], "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"  Wrote: {target['output_srt']}")

    # 元ディレクトリにもコピー
    orig_path = os.path.join(target["orig_dir"], target["orig_srt"])
    if os.path.isdir(target["orig_dir"]):
        shutil.copy2(target["output_srt"], orig_path)
        print(f"  Copied: {orig_path}")
    else:
        print(f"  WARNING: orig_dir not found: {target['orig_dir']}")

    # 検証: 実名ラベルがあるか
    known = ["dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"]
    found = {k: srt_content.count(f"[{k}]") for k in known}
    found = {k: v for k, v in found.items() if v > 0}
    print(f"  Named labels: {found}")
    named_count = sum(found.values())
    print(f"  Total named entries: {named_count}")

    return {"video_id": vid, "speakers": list(speakers), "named_count": named_count, "ok": named_count > 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="merged JSONのwordsから実名ラベル付きSRTを再生成")
    parser.add_argument("--input", help="merged JSONパス（指定時は単一ファイル処理）")
    parser.add_argument("--output", help="SRT出力パス（--inputと一緒に使用）")
    parser.add_argument("--targets", nargs="+", metavar="VIDEO_ID",
                        help="処理対象のvideo_idを指定（未指定時はTARGETSリスト全件）")
    args = parser.parse_args()

    if args.input:
        # 単一ファイルモード
        if not args.output:
            print("ERROR: --input を指定する場合は --output も必要です", file=sys.stderr)
            sys.exit(1)
        video_id = os.path.splitext(os.path.basename(args.input))[0]
        if video_id.startswith("merged_"):
            video_id = video_id[len("merged_"):]
        target = {
            "video_id": video_id,
            "merged_json": args.input,
            "output_srt": args.output,
            "orig_dir": "",
            "orig_srt": "",
        }
        r = regen_srt(target)
        status = "OK" if r["ok"] else "FAIL"
        print(f"\n[{status}] {r['video_id']}: speakers={r['speakers']}, named_count={r['named_count']}")
        sys.exit(0 if r["ok"] else 1)
    else:
        # デフォルト: TARGETSリスト全処理（--targetsで絞り込み可能）
        selected = TARGETS
        if args.targets:
            selected = [t for t in TARGETS if t["video_id"] in args.targets]
            if not selected:
                print(f"ERROR: 指定されたvideo_idがTARGETSに見つかりません: {args.targets}", file=sys.stderr)
                sys.exit(1)
        results = []
        for t in selected:
            r = regen_srt(t)
            results.append(r)

        print("\n=== SUMMARY ===")
        all_ok = True
        for r in results:
            status = "OK" if r["ok"] else "FAIL"
            print(f"  [{status}] {r['video_id']}: speakers={r['speakers']}, named_count={r['named_count']}")
            if not r["ok"]:
                all_ok = False

        sys.exit(0 if all_ok else 1)
