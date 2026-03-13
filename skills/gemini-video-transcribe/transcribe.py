#!/usr/bin/env python3
"""
gemini_video_transcribe — Gemini APIによる動画字幕生成ラッパー

動画ファイルをGemini APIに投入してSRT字幕を一発生成する。
内部でgemini_speaker_pipeline.py（話者分離あり）またはgemini_transcribe.py（なし）を呼び出す。

Usage:
    # 基本（話者分離あり: Gemini + ECAPA-TDNN Speaker ID）
    python3 skills/gemini-video-transcribe/transcribe.py video.mp4 -o output.srt

    # 話者分離なし（GPU不要、高速）
    python3 skills/gemini-video-transcribe/transcribe.py video.mp4 -o output.srt --no-speaker-diarize

    # モデル指定
    python3 skills/gemini-video-transcribe/transcribe.py video.mp4 -o output.srt \\
        --model gemini-3-flash-preview

    # コスト確認のみ（実行しない）
    python3 skills/gemini-video-transcribe/transcribe.py video.mp4 -o output.srt --dry-run

    # 既存Gemini SRTを再利用（API再呼出しをスキップ、Speaker IDのみ再実行）
    python3 skills/gemini-video-transcribe/transcribe.py video.mp4 -o output.srt \\
        --gemini-srt work/pipeline_xxx/gemini_xxx.srt
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent

# モデル別コスト目安（45分動画あたり、2026-03時点）
# Flash Lite: $0.05 / Flash: $0.20 / Pro: $0.61
COST_PER_45MIN = {
    "gemini-3.1-flash-lite-preview": 0.05,
    "gemini-3-flash-preview": 0.20,
    "gemini-3.0-pro-preview": 0.61,
    "gemini-3-pro-preview": 0.61,
    "gemini-3-flash-lite-preview": 0.05,
}

DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"

HALLUCINATION_RULES = """
【ハルシネーション防止ルール（厳守）】:
- 同一テキストを3回以上連続で出力しないこと。同じ発話が実際に繰り返されている場合でも、3回目以降は省略してよい
- 動画の実際の尺を超えるタイムスタンプを絶対に生成しないこと
- 動画全体を最初から最後まで網羅すること。冒頭だけ書いて途中で止めたり、中間を飛ばしたりしないこと
- 5分ごとに内容が進行していることを自己確認すること（0〜5分、5〜10分、10〜15分...）
- テキストが単調になっていると感じたら、一度立ち止まって動画の該当箇所を再確認すること
"""


def get_video_duration(video_path: Path) -> float:
    """ffprobeで動画の尺（秒）を取得する。失敗時は0.0を返す"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0


def show_cost_estimate(duration_sec: float, selected_model: str) -> None:
    """コスト目安を表示する"""
    REF_SEC = 45 * 60  # 45分 = 2700秒
    print("=" * 60)
    print("【コスト目安】")
    print(f"  動画尺:   {duration_sec / 60:.1f}分 ({duration_sec:.0f}秒)")
    print(f"  モデル:   {selected_model}")
    print()
    print("  モデル別コスト比較（45分動画基準）:")
    for model, cost_45min in sorted(COST_PER_45MIN.items(), key=lambda x: x[1]):
        if duration_sec > 0:
            estimated = cost_45min * (duration_sec / REF_SEC)
            note = f"${cost_45min:.2f}/45min → 今回: ${estimated:.3f}"
        else:
            note = f"${cost_45min:.2f}/45min"
        marker = " ← 選択中" if model == selected_model else ""
        print(f"    {model}: {note}{marker}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Gemini APIによる動画字幕生成スキル: MP4 → SRT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HALLUCINATION_RULES,
    )
    parser.add_argument("video_path", help="入力動画ファイルパス（MP4）")
    parser.add_argument("--output", "-o", required=True, help="出力SRTファイルパス")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Geminiモデル（デフォルト: {DEFAULT_MODEL}）\n"
             "  Flash Lite: $0.05/45min（推奨）\n"
             "  Flash:      $0.20/45min\n"
             "  Pro:        $0.61/45min",
    )
    parser.add_argument(
        "--no-speaker-diarize",
        action="store_true",
        help="話者分離をスキップ（GPU不要、高速。Geminiの仮話者ラベルのみ）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="コスト確認のみ（実行しない）",
    )
    parser.add_argument(
        "--gemini-srt",
        metavar="SRT_FILE",
        help="既存Gemini SRTを再利用してGemini APIをスキップ（Speaker IDのみ再実行）",
    )
    parser.add_argument(
        "--profile-dir",
        metavar="DIR",
        help="声紋プロファイルディレクトリ（話者分離ありの場合のみ使用）",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.25,
        help="Speaker ID類似度閾値（デフォルト: 0.25）",
    )
    args = parser.parse_args()

    video_path = Path(args.video_path).resolve()
    output_path = Path(args.output).resolve()

    # 入力チェック
    if not video_path.exists():
        print(f"[transcribe] エラー: 動画ファイルが見つかりません: {video_path}", flush=True)
        return 1

    # コスト見積もり表示
    duration_sec = get_video_duration(video_path)
    show_cost_estimate(duration_sec, args.model)

    if args.dry_run:
        print("[dry-run] コスト確認のみ。--dry-run を外して実行してください。", flush=True)
        return 0

    # 実行モード分岐
    if args.no_speaker_diarize:
        # 話者分離なし: gemini_transcribe.py のみ
        print("[transcribe] モード: 話者分離なし（Gemini字幕のみ、GPU不要）", flush=True)
        cmd = [
            sys.executable,
            str(PROJECT_DIR / "scripts" / "gemini_transcribe.py"),
            str(video_path),
            "--output", str(output_path),
            "--model", args.model,
        ]
    else:
        # 話者分離あり: gemini_speaker_pipeline.py（Gemini + ECAPA-TDNN Speaker ID）
        print("[transcribe] モード: 話者分離あり（Gemini + Speaker ID, GPU推奨）", flush=True)
        cmd = [
            sys.executable,
            str(PROJECT_DIR / "scripts" / "gemini_speaker_pipeline.py"),
            str(video_path),
            "--output", str(output_path),
            "--model", args.model,
            "--threshold", str(args.threshold),
        ]
        if args.gemini_srt:
            cmd += ["--gemini-srt", args.gemini_srt]
        if args.profile_dir:
            cmd += ["--profile-dir", args.profile_dir]

    print(f"[transcribe] 実行: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
