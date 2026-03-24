#!/usr/bin/env python3
"""
3D Frame QC Script — 3d_frame_qc.py
cmd_933: 参考動画と生成動画を0.5秒おきにフレーム比較→Gemini Visionで分析→差異NG判定

Usage:
    python3 scripts/3d/3d_frame_qc.py \
        --ref <参考動画.mp4> \
        --gen <生成動画.mp4> \
        --interval 0.5 \
        --output qc_report.yaml
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

# --- Gemini ---
from google import genai
from google.genai import types

# ============================================================
# 定数・設定
# ============================================================
BATCH_SIZE = 5         # 同時送信数（順番送信、RPM対策）
RETRY_MAX = 3
RETRY_DELAY_BASE = 2   # 秒、指数バックオフ
RPM_DELAY = max(60.0 / int(os.environ.get("GEMINI_RPM_LIMIT", "15")), 0.5)

SIZE_MAP = {"close-up": 4, "medium": 3, "full-body": 2, "distant": 1}

VISION_PROMPT = """You are a quality checker for 3D Minecraft character animation shorts.
I will show you two frames: [REFERENCE] (target to match) and [GENERATED] (to evaluate).

Analyze EACH frame and return a JSON object:

{
  "reference": {
    "character_count": <int>,
    "characters": [
      {
        "position": "left" | "center" | "right",
        "size": "close-up" | "medium" | "full-body" | "distant",
        "motion_pose": "<brief description of pose/action>",
        "facing": "left" | "right" | "front" | "back"
      }
    ],
    "has_text_overlay": <bool>,
    "text_position": "top" | "center" | "bottom" | "none",
    "camera_type": "two-shot" | "close-up" | "wide" | "other",
    "background_type": "grass" | "stone" | "nether" | "sky" | "dark" | "other",
    "overall_brightness": "dark" | "normal" | "bright"
  },
  "generated": {
    "character_count": <int>,
    "characters": [
      {
        "position": "left" | "center" | "right",
        "size": "close-up" | "medium" | "full-body" | "distant",
        "motion_pose": "<brief description of pose/action>",
        "facing": "left" | "right" | "front" | "back"
      }
    ],
    "has_text_overlay": <bool>,
    "text_position": "top" | "center" | "bottom" | "none",
    "camera_type": "two-shot" | "close-up" | "wide" | "other",
    "background_type": "grass" | "stone" | "nether" | "sky" | "dark" | "other",
    "overall_brightness": "dark" | "normal" | "bright"
  }
}

Rules:
- Count only distinct Minecraft-style characters (blocky humanoids)
- "close-up" = character fills >50% of frame height
- "full-body" = full character visible, <50% of frame
- "distant" = character is very small
- If no character visible, character_count = 0
- text_overlay includes subtitles, titles, any text

CRITICAL CHECK: If character_count is 0 in the generated frame,
add "critical_issue": "no_characters_visible" to the generated object.

Return ONLY valid JSON with no markdown code blocks."""


# ============================================================
# ffprobe / ffmpeg ユーティリティ
# ============================================================

def get_video_metadata(video_path: str) -> dict:
    """ffprobeでメタデータを取得する"""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {video_path}: {result.stderr}")
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data.get("streams", []) if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in data.get("streams", []) if s["codec_type"] == "audio"), None
    )

    if video_stream is None:
        raise RuntimeError(f"No video stream found in {video_path}")

    # FPS計算
    fps_str = video_stream.get("r_frame_rate", "30/1")
    num, den = fps_str.split("/")
    fps = float(num) / float(den) if float(den) != 0 else 30.0

    # 解像度
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))

    # 尺（duration）
    duration = float(data.get("format", {}).get("duration", 0))

    return {
        "resolution": f"{width}x{height}",
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "has_audio": audio_stream is not None,
    }


def extract_frames(video_path: str, output_dir: str, interval: float, max_frames: int, verbose: bool = False) -> list:
    """ffmpegでフレームを抽出し、フレームパスのリストを返す"""
    os.makedirs(output_dir, exist_ok=True)

    # fps=1/interval → 例: interval=0.5 → fps=2
    fps_val = 1.0 / interval

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps_val:.4f}",
        "-q:v", "2",
        "-frames:v", str(max_frames),
        os.path.join(output_dir, "frame_%04d.png"),
        "-y", "-loglevel", "warning"
    ]

    if verbose:
        print(f"  [ffmpeg] {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    frames = sorted(Path(output_dir).glob("frame_*.png"))
    return [str(f) for f in frames]


# ============================================================
# 黒フレーム検出
# ============================================================

def is_black_frame(frame_path: str, threshold: int = 15, black_ratio: float = 0.95) -> bool:
    """フレームがほぼ全黒ならTrue（トランジションスキップ用）"""
    try:
        img = np.array(Image.open(frame_path).convert("RGB"))
        return (img < threshold).all(axis=2).mean() > black_ratio
    except Exception:
        return False


# ============================================================
# Gemini Vision分析
# ============================================================

def analyze_frame_pair(client, ref_path: str, gen_path: str, verbose: bool = False) -> dict:
    """2フレームを1リクエストでGemini Visionに送信し分析結果を返す"""
    for attempt in range(RETRY_MAX):
        try:
            with open(ref_path, "rb") as f:
                ref_bytes = f.read()
            with open(gen_path, "rb") as f:
                gen_bytes = f.read()

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=VISION_PROMPT),
                    types.Part.from_bytes(data=ref_bytes, mime_type="image/png"),   # [REFERENCE]
                    types.Part.from_bytes(data=gen_bytes, mime_type="image/png"),   # [GENERATED]
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            # コードブロックが含まれる場合は除去
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

            return json.loads(text)

        except Exception as e:
            err_str = str(e)
            if attempt < RETRY_MAX - 1 and any(code in err_str for code in ["429", "500", "503"]):
                wait = RETRY_DELAY_BASE * (2 ** attempt)
                if verbose:
                    print(f"  [retry] attempt {attempt+1}/{RETRY_MAX}, wait {wait}s: {e}")
                time.sleep(wait)
            else:
                raise


# ============================================================
# 比較ロジック
# ============================================================

def size_diff(ref_size: str, gen_size: str) -> int:
    return abs(SIZE_MAP.get(ref_size, 0) - SIZE_MAP.get(gen_size, 0))


def frame_score(ref_analysis: dict, gen_analysis: dict) -> list:
    """フレーム単位の問題リストを返す"""
    issues = []

    # CRITICAL: キャラ不在
    if gen_analysis.get("critical_issue") == "no_characters_visible" or gen_analysis.get("character_count", 1) == 0:
        issues.append({
            "severity": "CRITICAL",
            "type": "no_characters",
            "detail": "generated frame has 0 characters"
        })

    ref_count = ref_analysis.get("character_count", 0)
    gen_count = gen_analysis.get("character_count", 0)

    # HIGH: キャラ数不一致
    if ref_count != gen_count:
        issues.append({
            "severity": "HIGH",
            "type": "character_count_mismatch",
            "detail": f"ref={ref_count}, gen={gen_count}"
        })

    # HIGH: テロップ有無不一致
    ref_text = ref_analysis.get("has_text_overlay", False)
    gen_text = gen_analysis.get("has_text_overlay", False)
    if ref_text != gen_text:
        issues.append({
            "severity": "HIGH",
            "type": "text_overlay_mismatch",
            "detail": f"ref={ref_text}, gen={gen_text}"
        })

    # MEDIUM: カメラタイプ不一致
    ref_cam = ref_analysis.get("camera_type", "")
    gen_cam = gen_analysis.get("camera_type", "")
    if ref_cam and gen_cam and ref_cam != gen_cam:
        issues.append({
            "severity": "MEDIUM",
            "type": "camera_type_mismatch",
            "detail": f"ref={ref_cam}, gen={gen_cam}"
        })

    # WARN: キャラサイズ差（キャラ数が一致している場合のみ）
    if ref_count == gen_count:
        ref_chars = ref_analysis.get("characters", [])
        gen_chars = gen_analysis.get("characters", [])
        for i in range(min(len(ref_chars), len(gen_chars))):
            diff = size_diff(ref_chars[i].get("size", ""), gen_chars[i].get("size", ""))
            if diff >= 2:
                issues.append({
                    "severity": "WARN",
                    "type": "character_size_diff",
                    "detail": f"character {i}: ref={ref_chars[i].get('size')}({SIZE_MAP.get(ref_chars[i].get('size',''), 0)}), gen={gen_chars[i].get('size')}({SIZE_MAP.get(gen_chars[i].get('size',''), 0)}), diff={diff}"
                })

    return issues


def overall_verdict(all_frame_issues: list) -> tuple:
    """全体NG判定。('PASS'|'WARN'|'NG', reason)を返す"""
    critical_count = sum(1 for f in all_frame_issues
                         for i in f["issues"] if i["severity"] == "CRITICAL")
    high_count = sum(1 for f in all_frame_issues
                     for i in f["issues"] if i["severity"] == "HIGH")

    if critical_count > 0:
        return "NG", f"CRITICAL issues in {critical_count} frames"
    if high_count >= 3:
        return "NG", f"HIGH issues in {high_count} frames (threshold: 3 for NG)"
    if high_count > 0:
        return "WARN", f"HIGH issues in {high_count} frames (threshold: 3 for NG)"
    return "PASS", "No significant issues detected"


def make_recommendations(all_frame_issues: list, interval: float) -> list:
    recs = []
    for frame_info in all_frame_issues:
        ts = frame_info["timestamp"]
        idx = frame_info["frame_index"]
        for issue in frame_info["issues"]:
            sev = issue["severity"]
            itype = issue["type"]
            detail = issue.get("detail", "")

            if itype == "no_characters":
                recs.append(f"Frame {idx} ({ts:.1f}s): キャラが映っていない。レンダリング確認")
            elif itype == "character_count_mismatch":
                recs.append(f"Frame {idx} ({ts:.1f}s): キャラ数不一致 ({detail})。レンダリング確認")
            elif itype == "text_overlay_mismatch":
                recs.append(f"Frame {idx} ({ts:.1f}s): テロップ有無が参考と異なる ({detail})")
            elif itype == "camera_type_mismatch":
                recs.append(f"Frame {idx} ({ts:.1f}s): カメラタイプ不一致 ({detail})。camera_director.pyのプリセット確認")
            elif itype == "character_size_diff":
                recs.append(f"Frame {idx} ({ts:.1f}s): キャラサイズが参考と大きく異なる ({detail})")
    return recs


# ============================================================
# メタデータチェック
# ============================================================

def check_metadata(ref_meta: dict, gen_meta: dict) -> tuple:
    """メタデータ比較。('PASS'|'WARN'|'NG', dict)を返す"""
    checks = {
        "ref_resolution": ref_meta["resolution"],
        "gen_resolution": gen_meta["resolution"],
        "resolution_match": ref_meta["resolution"] == gen_meta["resolution"],
        "ref_duration": round(ref_meta["duration"], 2),
        "gen_duration": round(gen_meta["duration"], 2),
        "duration_diff": round(abs(ref_meta["duration"] - gen_meta["duration"]), 2),
        "gen_fps": round(gen_meta["fps"], 1),
        "gen_has_audio": gen_meta["has_audio"],
    }

    verdict = "PASS"

    if not checks["gen_has_audio"]:
        verdict = "NG"
    elif checks["duration_diff"] > 10:
        verdict = "NG"
    elif not checks["resolution_match"] or checks["duration_diff"] > 3 or not (29 <= checks["gen_fps"] <= 31):
        verdict = "WARN"

    checks["metadata_verdict"] = verdict
    return verdict, checks


# ============================================================
# メイン処理
# ============================================================

def run_qc(args):
    verbose = args.verbose

    # 引数バリデーション
    if not os.path.exists(args.ref):
        print(f"ERROR: --ref file not found: {args.ref}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.gen):
        print(f"ERROR: --gen file not found: {args.gen}", file=sys.stderr)
        sys.exit(1)
    if args.interval <= 0:
        print("ERROR: --interval must be > 0", file=sys.stderr)
        sys.exit(1)

    print(f"[3d_frame_qc] ref: {args.ref}")
    print(f"[3d_frame_qc] gen: {args.gen}")
    print(f"[3d_frame_qc] interval: {args.interval}s, max-frames: {args.max_frames}")

    # Geminiクライアント
    if not args.skip_vision:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
            sys.exit(1)
        client = genai.Client(api_key=api_key)
    else:
        client = None
        print("[3d_frame_qc] --skip-vision: Vision分析をスキップ")

    # Step 1: メタデータ取得
    print("[Step 1] メタデータ取得...")
    ref_meta = get_video_metadata(args.ref)
    gen_meta = get_video_metadata(args.gen)

    if verbose:
        print(f"  ref: {ref_meta}")
        print(f"  gen: {gen_meta}")

    for meta, label in [(ref_meta, "ref"), (gen_meta, "gen")]:
        if meta["duration"] == 0:
            print(f"ERROR: {label} video duration is 0", file=sys.stderr)
            sys.exit(1)

    meta_verdict, meta_checks = check_metadata(ref_meta, gen_meta)
    print(f"  メタデータ verdict: {meta_verdict}")

    with tempfile.TemporaryDirectory(prefix="3d_qc_") as tmpdir:
        ref_dir = os.path.join(tmpdir, "ref")
        gen_dir = os.path.join(tmpdir, "gen")

        # Step 2: フレーム抽出
        print("[Step 2] フレーム抽出...")
        ref_frames = extract_frames(args.ref, ref_dir, args.interval, args.max_frames, verbose)
        gen_frames = extract_frames(args.gen, gen_dir, args.interval, args.max_frames, verbose)
        print(f"  ref: {len(ref_frames)} frames, gen: {len(gen_frames)} frames")

        # 短い方に合わせる
        n_frames = min(len(ref_frames), len(gen_frames))
        ref_frames = ref_frames[:n_frames]
        gen_frames = gen_frames[:n_frames]

        if n_frames == 0:
            print("ERROR: No frames extracted", file=sys.stderr)
            sys.exit(1)

        # Step 3: Vision分析 + Step 4: 比較
        print(f"[Step 3] Vision分析 ({n_frames} frame pairs)...")

        all_frame_issues = []
        skipped = 0

        for i in range(n_frames):
            timestamp = round(i * args.interval, 2)
            ref_path = ref_frames[i]
            gen_path = gen_frames[i]

            # 黒フレームスキップ
            if is_black_frame(ref_path) and is_black_frame(gen_path):
                if verbose:
                    print(f"  frame {i+1}/{n_frames} ({timestamp}s): 黒フレームスキップ")
                skipped += 1
                continue

            if args.skip_vision:
                # Vision省略時は空issueでスキップ
                continue

            if verbose:
                print(f"  frame {i+1}/{n_frames} ({timestamp}s): 分析中...")

            try:
                result = analyze_frame_pair(client, ref_path, gen_path, verbose)
                ref_analysis = result.get("reference", {})
                gen_analysis = result.get("generated", {})
                issues = frame_score(ref_analysis, gen_analysis)

                if issues:
                    all_frame_issues.append({
                        "timestamp": timestamp,
                        "frame_index": i + 1,
                        "issues": issues,
                        "ref_summary": _make_summary(ref_analysis),
                        "gen_summary": _make_summary(gen_analysis),
                    })

                # RPMレート制限対策
                time.sleep(RPM_DELAY)

                # バッチ区切りで少し待機
                if (i + 1) % BATCH_SIZE == 0 and i + 1 < n_frames:
                    time.sleep(1.0)

            except Exception as e:
                print(f"  WARNING: Vision analysis failed at frame {i+1} ({timestamp}s): {e}")
                # エラーフレームはWARNとして記録
                all_frame_issues.append({
                    "timestamp": timestamp,
                    "frame_index": i + 1,
                    "issues": [{"severity": "WARN", "type": "vision_error", "detail": str(e)}],
                    "ref_summary": "analysis_failed",
                    "gen_summary": "analysis_failed",
                })

        # Step 5: NG判定
        print("[Step 5] NG判定...")

        verdict, verdict_reason = overall_verdict(all_frame_issues)

        # 全issueサマリー
        issues_summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "WARN": 0}
        for f in all_frame_issues:
            for iss in f["issues"]:
                issues_summary[iss["severity"]] = issues_summary.get(iss["severity"], 0) + 1

        recs = make_recommendations(all_frame_issues, args.interval)

        # レポート組み立て
        report = {
            "report": {
                "version": "1.0",
                "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "ref_video": str(args.ref),
                "gen_video": str(args.gen),
                "interval": args.interval,
                "metadata_check": meta_checks,
                "frame_analysis": {
                    "total_frames_compared": n_frames - skipped if not args.skip_vision else 0,
                    "frames_skipped_black": skipped,
                    "frames_with_issues": len(all_frame_issues),
                    "issues_summary": issues_summary,
                    "flagged_frames": all_frame_issues,
                },
                "verdict": verdict,
                "verdict_reason": verdict_reason,
                "recommendations": recs,
            }
        }

        # 出力
        report_yaml = yaml.dump(report, allow_unicode=True, sort_keys=False, default_flow_style=False)

        if args.output:
            out_path = args.output
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report_yaml)
            print(f"[3d_frame_qc] レポート出力: {out_path}")
        else:
            print("\n--- QC REPORT ---")
            print(report_yaml)

        print(f"\n[3d_frame_qc] 完了 | verdict: {verdict} | {verdict_reason}")
        return report


def _make_summary(analysis: dict) -> str:
    """分析結果を短いサマリー文字列にする"""
    if not analysis:
        return "no_data"
    count = analysis.get("character_count", 0)
    cam = analysis.get("camera_type", "?")
    bg = analysis.get("background_type", "?")
    return f"{count} character(s), {cam}, {bg} bg"


# ============================================================
# エントリポイント
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="3D Frame QC — 参考動画と生成動画をGemini Visionで比較してNG判定"
    )
    parser.add_argument("--ref", required=True, help="参考動画パス（本家ショートや過去の良品）")
    parser.add_argument("--gen", required=True, help="生成動画パス（QC対象）")
    parser.add_argument("--interval", type=float, default=0.5, help="フレーム抽出間隔（秒、デフォルト0.5）")
    parser.add_argument("--output", default=None, help="QCレポート出力先YAML（省略時stdout）")
    parser.add_argument("--max-frames", type=int, default=120, help="最大フレーム数（デフォルト120）")
    parser.add_argument("--skip-vision", action="store_true", help="Vision分析をスキップしffprobeのみ実施")
    parser.add_argument("--verbose", action="store_true", help="詳細ログ出力")

    args = parser.parse_args()
    run_qc(args)


if __name__ == "__main__":
    main()
