#!/usr/bin/env python3
"""
stt_merge.py - Multi-STT auto merge pipeline

Merges AssemblyAI (base) + Deepgram (gap fill) + Gemini SRT (speaker ID)
into a single merged JSON with word-level timestamps and speaker labels.

Usage:
    python3 scripts/stt_merge.py \
        --assemblyai path/to/assemblyai_words.json \
        --deepgram path/to/deepgram_words.json \
        --gemini path/to/gemini_speaker.srt \
        --output path/to/merged.json \
        --report path/to/merge_report.yaml
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path


def detect_timestamp_unit(raw_words: list[dict]) -> str:
    """
    Detect whether timestamps are in milliseconds or seconds.
    Returns 'ms' or 's'.

    Heuristic: if max(start) > 100000, already ms (no conversion needed).
    Otherwise, values are seconds and must be multiplied by 1000.

    Rationale: a 27-hour video in seconds has max_start ~= 100000s.
    Any audio clip in ms with max_start <= 100000ms would be <= 100 seconds,
    which is impractically short for this use-case.
    """
    if not raw_words:
        return "s"
    max_start = max(float(w.get("start", 0)) for w in raw_words)
    return "ms" if max_start > 100000 else "s"


def load_assemblyai(path: str) -> list[dict]:
    """Load AssemblyAI words JSON. Returns list of word dicts with start/end in ms."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Support both raw list and wrapped {"words": [...]} format
    if isinstance(data, list):
        raw_words = data
    else:
        raw_words = data.get("words", [])
    unit = detect_timestamp_unit(raw_words)
    result = []
    for w in raw_words:
        text = w.get("text") or w.get("word") or ""
        start_raw = float(w.get("start", 0))
        end_raw = float(w.get("end", 0))
        if unit == "s":
            start_ms = int(start_raw * 1000)
            end_ms = int(end_raw * 1000)
        else:
            start_ms = int(start_raw)
            end_ms = int(end_raw)
        result.append({
            "text": text,
            "start": start_ms,
            "end": end_ms,
            "confidence": float(w.get("confidence", 0.0)),
            "source": "assemblyai",
            "speaker": w.get("speaker") or None,
        })
    return result


def load_deepgram(path: str) -> list[dict]:
    """Load Deepgram words JSON. Returns list of word dicts with start/end in ms."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        raw_words = data
    else:
        raw_words = data.get("words", [])
    unit = detect_timestamp_unit(raw_words)
    result = []
    for w in raw_words:
        text = w.get("word") or w.get("text") or ""
        start_raw = float(w.get("start", 0))
        end_raw = float(w.get("end", 0))
        if unit == "s":
            start_ms = int(start_raw * 1000)
            end_ms = int(end_raw * 1000)
        else:
            start_ms = int(start_raw)
            end_ms = int(end_raw)
        result.append({
            "text": text,
            "start": start_ms,
            "end": end_ms,
            "confidence": float(w.get("confidence", 0.0)),
            "source": "deepgram",
            "speaker": None,
        })
    return result


def srt_time_to_ms(timestr: str) -> int:
    """Convert SRT timestamp '00:00:01,234' to milliseconds."""
    m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", timestr.strip())
    if not m:
        return 0
    h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return h * 3600000 + mi * 60000 + s * 1000 + ms


def load_gemini_srt(path: str) -> list[dict]:
    """
    Load Gemini SRT with speaker labels.
    Returns list of {start_ms, end_ms, speaker, text}.
    Speaker format: '[speaker_key]: text' or '[speaker_key] text'.
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    entries = []
    blocks = re.split(r"\n\n+", content.strip())
    speaker_pattern = re.compile(r"^\[([^\]]+)\]:?\s*(.*)")

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        # Line 0: sequence number
        # Line 1: timestamps
        # Lines 2+: text
        time_match = re.match(r"(.+?) --> (.+)", lines[1])
        if not time_match:
            continue
        start_ms = srt_time_to_ms(time_match.group(1))
        end_ms = srt_time_to_ms(time_match.group(2))

        text_lines = lines[2:]
        full_text = " ".join(text_lines).strip()
        speaker = None
        sm = speaker_pattern.match(full_text)
        if sm:
            speaker = sm.group(1).strip()
            full_text = sm.group(2).strip()

        entries.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "speaker": speaker,
            "text": full_text,
        })

    return entries


def detect_gaps(words: list[dict], gap_threshold_ms: int = 500) -> list[dict]:
    """Detect gaps >= gap_threshold_ms between consecutive words."""
    gaps = []
    for i in range(1, len(words)):
        prev_end = words[i - 1]["end"]
        curr_start = words[i]["start"]
        gap = curr_start - prev_end
        if gap >= gap_threshold_ms:
            gaps.append({
                "start_ms": prev_end,
                "end_ms": curr_start,
                "duration_ms": gap,
            })
    return gaps


def fill_gaps_with_deepgram(
    base_words: list[dict],
    dg_words: list[dict],
    gap_threshold_ms: int = 500,
) -> tuple[list[dict], int, list[dict]]:
    """
    Fill gaps in base_words using Deepgram words.
    Returns (merged_words, filled_count, unfilled_gaps).
    """
    merged = list(base_words)
    filled_count = 0
    unfilled_gaps = []
    gap_threshold_ms = gap_threshold_ms

    # Sort both by start
    merged.sort(key=lambda w: w["start"])
    dg_sorted = sorted(dg_words, key=lambda w: w["start"])

    result = []
    i = 0
    while i < len(merged):
        result.append(merged[i])
        if i + 1 < len(merged):
            gap_start = merged[i]["end"]
            gap_end = merged[i + 1]["start"]
            gap_dur = gap_end - gap_start
            if gap_dur >= gap_threshold_ms:
                # Find Deepgram words that fall within this gap
                fill_words = [
                    w for w in dg_sorted
                    if w["start"] >= gap_start and w["end"] <= gap_end
                ]
                if fill_words:
                    # Propagate nearest AssemblyAI speaker to Deepgram gap-fill words
                    inherited_speaker = merged[i].get("speaker")
                    fill_words = [dict(w, speaker=inherited_speaker) for w in fill_words]
                    result.extend(fill_words)
                    filled_count += 1
                else:
                    unfilled_gaps.append({
                        "start_ms": gap_start,
                        "end_ms": gap_end,
                        "duration_ms": gap_dur,
                    })
        i += 1

    return result, filled_count, unfilled_gaps


def assign_speakers(
    words: list[dict],
    gemini_entries: list[dict],
) -> tuple[list[dict], int]:
    """
    Assign speaker IDs to words based on Gemini SRT entries.
    Uses mid-point of each word to find matching Gemini entry.
    If multiple matches, prefer the narrowest interval.
    Returns (words_with_speakers, speaker_match_count).
    """
    speaker_match_count = 0
    for word in words:
        mid = (word["start"] + word["end"]) / 2
        # Find all matching Gemini entries
        matches = [
            e for e in gemini_entries
            if e["start_ms"] <= mid <= e["end_ms"]
        ]
        if matches:
            # Prefer narrowest interval (most specific)
            best = min(matches, key=lambda e: e["end_ms"] - e["start_ms"])
            word["speaker"] = best["speaker"]
            if best["speaker"] is not None:
                speaker_match_count += 1
    return words, speaker_match_count


def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp '00:00:01,234'."""
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(words: list[dict], max_duration_ms: int = 5000) -> str:
    """
    Generate SRT content from merged words.

    Grouping rules:
    - Consecutive words with the same speaker → one entry
    - Speaker change → new entry
    - Entry duration exceeds max_duration_ms → split at next punctuation or force-split

    SRT format:
        1
        00:00:35,200 --> 00:00:38,100
        [dozle]: みんな、ちょっと上を見てくれ、上を。
    """
    if not words:
        return ""

    SPLIT_CHARS = {"。", "！", "？", ".", "!", "?", "、"}

    entries = []
    # Group words into SRT entries
    group_words: list[dict] = []
    current_speaker = words[0].get("speaker")

    def flush_group(gwords: list[dict]) -> None:
        if not gwords:
            return
        speaker = gwords[0].get("speaker")
        start_ms = gwords[0]["start"]
        end_ms = gwords[-1]["end"]
        text = " ".join(w["text"] for w in gwords if w.get("text"))
        text = text.strip()
        label = f"[{speaker}]: " if speaker else ""
        entries.append((start_ms, end_ms, f"{label}{text}"))

    for word in words:
        sp = word.get("speaker")
        if not group_words:
            group_words = [word]
            current_speaker = sp
            continue

        # Speaker change → flush current group
        if sp != current_speaker:
            flush_group(group_words)
            group_words = [word]
            current_speaker = sp
            continue

        # Duration check: would this word exceed max_duration_ms?
        group_start = group_words[0]["start"]
        if word["end"] - group_start > max_duration_ms:
            # Try to split at punctuation in current group
            split_idx = None
            for i in range(len(group_words) - 1, -1, -1):
                if any(group_words[i]["text"].endswith(c) for c in SPLIT_CHARS):
                    split_idx = i
                    break
            if split_idx is not None and split_idx < len(group_words) - 1:
                flush_group(group_words[:split_idx + 1])
                group_words = group_words[split_idx + 1:] + [word]
            else:
                flush_group(group_words)
                group_words = [word]
            current_speaker = sp
            continue

        group_words.append(word)

    flush_group(group_words)

    # Render SRT
    lines = []
    for idx, (start_ms, end_ms, text) in enumerate(entries, 1):
        lines.append(str(idx))
        lines.append(f"{ms_to_srt_time(start_ms)} --> {ms_to_srt_time(end_ms)}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def estimate_total_duration(words: list[dict], given_ms: int = 0) -> int:
    if given_ms > 0:
        return given_ms
    if not words:
        return 0
    return max(w["end"] for w in words)


def compute_coverage_pct(words: list[dict], total_duration_ms: int) -> float:
    """Compute rough word coverage: total word span / total duration."""
    if total_duration_ms == 0:
        return 0.0
    span = sum(w["end"] - w["start"] for w in words)
    return min(100.0, span / total_duration_ms * 100)


def main():
    parser = argparse.ArgumentParser(
        description="Merge AssemblyAI + Deepgram + Gemini SRT into unified word-level JSON"
    )
    parser.add_argument("--assemblyai", required=True, help="AssemblyAI words JSON path")
    parser.add_argument("--deepgram", required=True, help="Deepgram words JSON path")
    parser.add_argument("--gemini", required=False, default=None,
                        help="Gemini Speaker SRT path（廃止済み・互換用に残存）")
    parser.add_argument("--output", required=True, help="Output merged JSON path")
    parser.add_argument("--report", required=True, help="Output quality report YAML path")
    parser.add_argument("--video-id", default="", help="Video ID (default: inferred from filename)")
    parser.add_argument("--total-duration", type=int, default=0,
                        help="Total audio duration in ms (default: inferred from last word)")
    parser.add_argument("--gap-threshold", type=int, default=500,
                        help="Gap threshold in ms to trigger Deepgram fill (default: 500)")
    parser.add_argument("--no-srt", action="store_true",
                        help="Suppress SRT output (default: output SRT alongside JSON)")
    args = parser.parse_args()

    # Infer video_id from output path if not given
    video_id = args.video_id
    if not video_id:
        stem = Path(args.output).stem
        video_id = stem.split("_")[-1] if "_" in stem else stem

    print(f"[stt_merge] Video: {video_id}")

    # Step 1: Load AssemblyAI as base
    print("[stt_merge] Loading AssemblyAI words...")
    ai_words = load_assemblyai(args.assemblyai)
    print(f"  AssemblyAI: {len(ai_words)} words")

    # Step 2: Load Deepgram for gap filling
    print("[stt_merge] Loading Deepgram words...")
    dg_words = load_deepgram(args.deepgram)
    print(f"  Deepgram: {len(dg_words)} words")

    # Step 3: Load Gemini SRT for speaker IDs (optional)
    if args.gemini:
        print("[stt_merge] Loading Gemini SRT...")
        gemini_entries = load_gemini_srt(args.gemini)
        print(f"  Gemini: {len(gemini_entries)} entries")
    else:
        print("[stt_merge] Gemini SRT未指定: 話者ラベルなしで実行")
        gemini_entries = []

    # Detect gaps in AssemblyAI baseline
    gaps_before = detect_gaps(ai_words, args.gap_threshold)
    print(f"[stt_merge] Gaps >= {args.gap_threshold}ms before fill: {len(gaps_before)}")

    # Compute baseline coverage
    total_duration_ms = estimate_total_duration(ai_words, args.total_duration)
    coverage_before = compute_coverage_pct(ai_words, total_duration_ms)

    # Step 4: Fill gaps with Deepgram
    print("[stt_merge] Filling gaps with Deepgram...")
    merged_words, filled_count, unfilled_gaps = fill_gaps_with_deepgram(
        ai_words, dg_words, args.gap_threshold
    )
    deepgram_fill_count = len(merged_words) - len(ai_words)
    print(f"  Filled {filled_count} gap(s), added {deepgram_fill_count} Deepgram words")
    print(f"  Unfilled gaps: {len(unfilled_gaps)}")

    # Compute post-merge coverage
    coverage_after = compute_coverage_pct(merged_words, total_duration_ms)

    # Step 5: Assign speaker IDs from Gemini
    print("[stt_merge] Assigning speaker IDs from Gemini SRT...")
    merged_words, speaker_match_count = assign_speakers(merged_words, gemini_entries)
    total_words = len(merged_words)
    without_speaker = sum(1 for w in merged_words if w.get("speaker") is None)
    with_speaker = total_words - without_speaker
    speaker_id_pct = with_speaker / total_words * 100 if total_words > 0 else 0
    print(f"  Speaker assigned: {with_speaker}/{total_words} ({speaker_id_pct:.1f}%)")

    # Build speaker distribution
    speaker_dist: dict[str, int] = {}
    for w in merged_words:
        sp = w.get("speaker") or "null"
        speaker_dist[sp] = speaker_dist.get(sp, 0) + 1

    # Build output JSON
    output_data = {
        "words": merged_words,
        "metadata": {
            "video_id": video_id,
            "total_duration_ms": total_duration_ms,
            "assemblyai_words": len(ai_words),
            "deepgram_fill_words": deepgram_fill_count,
            "total_words": total_words,
            "coverage_pct": round(coverage_after, 2),
            "gap_count": len(gaps_before),
            "unfilled_gaps": unfilled_gaps,
            "speaker_id_pct": round(speaker_id_pct, 2),
            "speaker_distribution": speaker_dist,
        },
    }

    # Write output JSON
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"[stt_merge] Output: {args.output}")

    # Write SRT output (default: alongside JSON, same path with .srt extension)
    if not args.no_srt:
        srt_path = str(Path(args.output).with_suffix(".srt"))
        srt_content = generate_srt(merged_words)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"[stt_merge] SRT output: {srt_path}")

    # Build quality report YAML (manual serialization to avoid pyyaml dependency)
    source_ai = sum(1 for w in merged_words if w["source"] == "assemblyai")
    source_dg = sum(1 for w in merged_words if w["source"] == "deepgram")

    unfilled_list_yaml = ""
    for g in unfilled_gaps:
        unfilled_list_yaml += (
            f"          - {{start_ms: {g['start_ms']}, "
            f"end_ms: {g['end_ms']}, "
            f"duration_ms: {g['duration_ms']}}}\n"
        )
    if not unfilled_list_yaml:
        unfilled_list_yaml = "          []\n"

    report_yaml = f"""\
merge_report:
  video_id: {video_id}
  total_duration_ms: {total_duration_ms}
  coverage:
    before_merge_pct: {coverage_before:.2f}
    after_merge_pct: {coverage_after:.2f}
    improvement_pct: {coverage_after - coverage_before:.2f}
  gaps:
    total_before: {len(gaps_before)}
    filled_by_deepgram: {filled_count}
    remaining_unfilled: {len(unfilled_gaps)}
    unfilled_list:
{unfilled_list_yaml}\
  speaker_id:
    total_words: {total_words}
    with_speaker: {with_speaker}
    without_speaker: {without_speaker}
    coverage_pct: {speaker_id_pct:.2f}
  source_breakdown:
    assemblyai: {source_ai}
    deepgram: {source_dg}
"""

    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(report_yaml)
    print(f"[stt_merge] Report: {args.report}")

    print("[stt_merge] Done.")
    print(f"  AssemblyAI: {len(ai_words)} words")
    print(f"  Deepgram fill: {deepgram_fill_count} words")
    print(f"  Total: {total_words} words")
    print(f"  Coverage: {coverage_before:.1f}% → {coverage_after:.1f}%")
    print(f"  Speaker ID: {speaker_id_pct:.1f}%")


if __name__ == "__main__":
    main()
