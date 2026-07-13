#!/usr/bin/env python3
"""
元動画の字幕テロップをOCR検出して自動ぼかし

Usage:
    python3 scripts/blur_subtitles.py <input_video> [--output <path>] [--sample-interval 1.0] [--min-confidence 0.5]
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path

import cv2
import numpy as np

# preflight: easyocr は本スクリプト実行時に必須。未導入なら起動時に分かりやすいエラーにする
try:
    import easyocr
except ImportError as _e:
    raise ImportError(
        "easyocr がインストールされていません。"
        "`pip install easyocr` で導入してから再実行してください。"
    ) from _e


def detect_text_regions(video_path: str, sample_interval: float = 1.0, min_confidence: float = 0.5):
    """1秒ごとにフレームを抽出してOCRでテキスト領域を検出"""
    # モジュール先頭で import 済み (preflight)。モデルロード（重い）は関数内で遅延実行
    reader = easyocr.Reader(['ch_sim', 'en'], verbose=False)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[OCR] Video: {width}x{height} @ {fps:.1f}fps, {total_frames} frames")

    sample_step = max(1, int(fps * sample_interval))
    all_boxes = []  # [(time_sec, [boxes])]
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_step == 0:
            t = frame_idx / fps
            results = reader.readtext(frame)
            boxes = []
            for (bbox, text, conf) in results:
                if conf >= min_confidence:
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    x1, y1 = int(min(xs)), int(min(ys))
                    x2, y2 = int(max(xs)), int(max(ys))
                    # Expand box slightly
                    pad_x = int((x2 - x1) * 0.05)
                    pad_y = int((y2 - y1) * 0.15)
                    x1 = max(0, x1 - pad_x)
                    y1 = max(0, y1 - pad_y)
                    x2 = min(width, x2 + pad_x)
                    y2 = min(height, y2 + pad_y)
                    boxes.append((x1, y1, x2, y2, text, conf))
            if boxes:
                all_boxes.append((t, boxes))
                print(f"  [{t:.1f}s] {len(boxes)} text regions: {[b[4][:20] for b in boxes]}")

        frame_idx += 1

    cap.release()
    print(f"[OCR] Sampled {frame_idx // sample_step} frames, found text in {len(all_boxes)} frames")
    return all_boxes, fps, width, height


def consolidate_regions(all_boxes, width, height, min_occurrence_ratio=0.15):
    """複数フレームで繰り返し現れる領域を統合（テロップは固定位置にあり続ける）"""
    if not all_boxes:
        return []

    # Grid-based clustering: divide frame into cells and count text occurrences
    cell_h = height // 8
    cell_w = width // 8

    # Count how many frames had text in each grid cell
    cell_counts = {}
    total_samples = len(all_boxes)

    for t, boxes in all_boxes:
        for (x1, y1, x2, y2, text, conf) in boxes:
            # Which cells does this box cover?
            cy1 = y1 // cell_h
            cy2 = y2 // cell_h
            cx1 = x1 // cell_w
            cx2 = x2 // cell_w
            for cy in range(cy1, cy2 + 1):
                for cx in range(cx1, cx2 + 1):
                    cell_counts[(cy, cx)] = cell_counts.get((cy, cx), 0) + 1

    # Find cells with high occurrence ratio (persistent text = subtitles)
    threshold = total_samples * min_occurrence_ratio
    persistent_cells = {k: v for k, v in cell_counts.items() if v >= threshold}

    if not persistent_cells:
        # Fallback: use all detected regions (blur wherever text was found)
        print("[Consolidate] No persistent regions found, using all detected boxes")
        merged = []
        for t, boxes in all_boxes:
            for (x1, y1, x2, y2, text, conf) in boxes:
                merged.append((x1, y1, x2, y2))
        return _merge_overlapping(merged)

    # Build rectangles from persistent cells
    cell_rects = []
    for (cy, cx) in persistent_cells:
        cell_rects.append((cx * cell_w, cy * cell_h, (cx + 1) * cell_w, (cy + 1) * cell_h))

    # Merge overlapping rectangles
    merged = _merge_overlapping(cell_rects)

    # Expand each merged region to cover actual text boxes
    expanded = []
    for (mx1, my1, mx2, my2) in merged:
        # Find actual text boxes within this cell region
        ex1, ey1, ex2, ey2 = mx1, my1, mx2, my2
        for t, boxes in all_boxes:
            for (bx1, by1, bx2, by2, text, conf) in boxes:
                # Check if box overlaps with this region
                if bx1 < ex2 and bx2 > ex1 and by1 < ey2 and by2 > ey1:
                    ex1 = min(ex1, bx1)
                    ey1 = min(ey1, by1)
                    ex2 = max(ex2, bx2)
                    ey2 = max(ey2, by2)
        expanded.append((ex1, ey1, ex2, ey2))

    # Final merge
    result = _merge_overlapping(expanded)
    print(f"[Consolidate] {len(result)} persistent subtitle regions: {result}")
    return result


def _merge_overlapping(rects):
    """Merge overlapping rectangles"""
    if not rects:
        return []

    # Sort by y1 then x1
    rects = sorted(rects, key=lambda r: (r[1], r[0]))
    merged = [list(rects[0])]

    for (x1, y1, x2, y2) in rects[1:]:
        last = merged[-1]
        # Check overlap (with generous margin)
        margin = 20
        if x1 <= last[2] + margin and y1 <= last[3] + margin and x2 >= last[0] - margin:
            last[0] = min(last[0], x1)
            last[1] = min(last[1], y1)
            last[2] = max(last[2], x2)
            last[3] = max(last[3], y2)
        else:
            merged.append([x1, y1, x2, y2])

    return [tuple(r) for r in merged]


def blur_video_opencv(video_path: str, out_path: str, regions: list, blur_strength: int = 51):
    """OpenCVでフレームごとにぼかし適用→h264_nvencで出力"""
    if not regions:
        print("[Blur] No regions to blur, copying video")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "h264_nvenc", "-preset", "p4",
            "-c:a", "aac", "-b:a", "192k",
            out_path,
        ], check=True)
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Step 1: Pipe blurred frames to ffmpeg (video-only NVENC)
    temp_video = Path(out_path).with_suffix(".temp.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "-",
        "-c:v", "h264_nvenc", "-preset", "p4",
        "-an",  # no audio
        str(temp_video),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Apply Gaussian blur to each subtitle region
        for (x1, y1, x2, y2) in regions:
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                blurred = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 0)
                frame[y1:y2, x1:x2] = blurred

        proc.stdin.write(frame.tobytes())
        frame_count += 1
        if frame_count % 100 == 0:
            print(f"  Processed {frame_count} frames...")

    try:
        proc.stdin.close()
    except (BrokenPipeError, ValueError):
        pass
    proc.wait()
    stderr = proc.stderr.read()
    cap.release()

    if proc.returncode != 0:
        print(f"[Blur] ffmpeg stderr: {stderr.decode()[-500:]}")
        temp_video.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg video encoding failed (exit {proc.returncode})")

    print(f"[Blur] Video-only: {frame_count} frames -> {temp_video}")

    # Step 2: Merge audio from original video
    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", video_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v", "-map", "1:a?",
        "-shortest",
        out_path,
    ], capture_output=True, text=True)

    temp_video.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"[Blur] merge stderr: {result.stderr[-500:]}")
        raise RuntimeError(f"ffmpeg audio merge failed (exit {result.returncode})")

    print(f"[Blur] Done: {out_path}")


def blur_video_subtitles(
    video_path: str,
    out_path: str = None,
    sample_interval: float = 1.0,
    min_confidence: float = 0.5,
    blur_strength: int = 51,
):
    """Main function: detect subtitles and blur them"""
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if out_path is None:
        out_path = video_path.parent / f"{video_path.stem}_blurred{video_path.suffix}"
    else:
        out_path = Path(out_path).resolve()

    print(f"=== Subtitle Blur ===")
    print(f"Input:  {video_path}")
    print(f"Output: {out_path}")

    # Step 1: Detect text regions
    all_boxes, fps, w, h = detect_text_regions(
        str(video_path), sample_interval, min_confidence
    )

    # Step 2: Consolidate into persistent regions
    regions = consolidate_regions(all_boxes, w, h)

    if not regions:
        print("[Blur] No subtitle regions detected, copying as-is")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-c:v", "h264_nvenc", "-preset", "p4",
            "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ], check=True)
        return str(out_path)

    # Save detected regions as JSON for reference
    regions_json = out_path.parent / f"{video_path.stem}_blur_regions.json"
    regions_json.write_text(json.dumps({
        "video": str(video_path),
        "regions": regions,
        "sample_interval": sample_interval,
    }, indent=2))
    print(f"[Blur] Regions saved: {regions_json}")

    # Step 3: Apply blur
    blur_video_opencv(str(video_path), str(out_path), regions, blur_strength)

    return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="Blur subtitle text in video")
    parser.add_argument("input", help="Input video file path")
    parser.add_argument("--output", help="Output video file path (default: input_blurred.mp4)")
    parser.add_argument("--sample-interval", type=float, default=1.0,
                        help="Frame sampling interval in seconds (default: 1.0)")
    parser.add_argument("--min-confidence", type=float, default=0.5,
                        help="Minimum OCR confidence threshold (default: 0.5)")
    parser.add_argument("--blur-strength", type=int, default=51,
                        help="Gaussian blur kernel size (odd number, default: 51)")
    args = parser.parse_args()

    result = blur_video_subtitles(
        args.input,
        args.output,
        args.sample_interval,
        args.min_confidence,
        args.blur_strength,
    )
    print(f"\nResult: {result}")


if __name__ == "__main__":
    main()
