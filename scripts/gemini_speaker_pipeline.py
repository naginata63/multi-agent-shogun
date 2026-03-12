#!/usr/bin/env python3
"""
gemini_speaker_pipeline.py — Gemini Flash Lite + Speaker ID 統合パイプライン

MP4投入→最終SRT（テキスト+秒TS+正確な話者ラベル）を1コマンドで生成する。

Design:
  Step1: gemini_transcribe.py → SRT（テキスト+秒TS+仮話者）  [API, GPU不要]
  Step2: ffmpegで音声抽出（Step1と並列実行）                   [CPU]
  Step3: speaker_id_srt_based.py → 正確な話者ラベル           [GPU, ECAPA-TDNN]
  Step4: 最終SRT = Geminiテキスト + Gemini秒TS + Speaker ID話者ラベル

Usage:
    # 基本
    python3 scripts/gemini_speaker_pipeline.py video.mp4 --output output.srt

    # 既存Gemini SRTを再利用（Step1スキップ）
    python3 scripts/gemini_speaker_pipeline.py video.mp4 --output output.srt \\
        --gemini-srt work/gemini_video.srt

    # モデル指定
    python3 scripts/gemini_speaker_pipeline.py video.mp4 --output output.srt \\
        --model gemini-3.1-flash-lite-preview
"""

import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DOZLE_PROJECT = PROJECT_DIR / "projects" / "dozle_kirinuki"
SPEAKER_PROFILES = DOZLE_PROJECT / "speaker_profiles"
GEMINI_TRANSCRIBE = PROJECT_DIR / "scripts" / "gemini_transcribe.py"
SPEAKER_ID_SRT = DOZLE_PROJECT / "scripts" / "speaker_id_srt_based.py"

DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"


def extract_audio(video_path: Path, audio_path: Path) -> Path:
    """MP4から音声をWAV(16kHz mono)で抽出する"""
    print(f"[pipeline] Step2: 音声抽出 {video_path.name} → {audio_path.name}", flush=True)
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg音声抽出失敗:\n{result.stderr[-2000:]}")
    print(f"[pipeline] Step2完了: {audio_path}", flush=True)
    return audio_path


def run_gemini_transcribe(video_path: Path, srt_path: Path, model: str) -> Path:
    """Step1: gemini_transcribe.pyでGemini SRTを生成する"""
    print(f"[pipeline] Step1: Gemini字幕生成 (model={model})", flush=True)
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(GEMINI_TRANSCRIBE),
        str(video_path),
        "--output", str(srt_path),
        "--model", model,
    ]
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gemini_transcribe.py失敗 (returncode={result.returncode})")

    if not srt_path.exists():
        raise RuntimeError(f"SRTファイルが生成されませんでした: {srt_path}")

    entry_count = count_srt_entries(srt_path)
    print(f"[pipeline] Step1完了: {srt_path} ({entry_count}エントリ)", flush=True)
    return srt_path


def run_speaker_id(
    audio_path: Path,
    srt_path: Path,
    output_path: Path,
    json_path: Path,
    profile_dir: Path,
    threshold: float = 0.25,
) -> Path:
    """Step3+4: speaker_id_srt_based.pyで話者ラベルを付与し最終SRTを生成する"""
    print(f"[pipeline] Step3: Speaker ID照合 (profiles={profile_dir})", flush=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # dozle_kirinuki venvのPythonを優先使用（speechbrain/torchaudio含む）
    venv_python = DOZLE_PROJECT / "venv" / "bin" / "python3"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    cmd = [
        python_cmd, str(SPEAKER_ID_SRT),
        "--audio", str(audio_path),
        "--srt", str(srt_path),
        "--profiles", str(profile_dir),
        "--output", str(output_path),
        "--json", str(json_path),
        "--threshold", str(threshold),
    ]
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"speaker_id_srt_based.py失敗 (returncode={result.returncode})")

    if not output_path.exists():
        raise RuntimeError(f"Speaker ID SRTが生成されませんでした: {output_path}")

    entry_count = count_srt_entries(output_path)
    print(f"[pipeline] Step3完了: {output_path} ({entry_count}エントリ)", flush=True)
    return output_path


def clean_gemini_labels(srt_path: Path) -> None:
    """
    Speaker ID SRT出力のGemini仮話者ラベルを除去する。

    speaker_id_srt_based.pyは `[speaker] {text}` 形式でラベルを付与するが、
    Geminiテキストが `[speaker]: テキスト` を含む場合、二重になる。
    例: `[dozle] [dozle]: テキスト` → `[dozle]: テキスト`
    """
    import re
    text = srt_path.read_text(encoding="utf-8")
    blocks = text.strip().split("\n\n")
    cleaned = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            cleaned.append(block)
            continue
        # テキスト行（3行目以降）を結合して処理
        text_lines = lines[2:]
        text_content = "\n".join(text_lines)
        # パターン: [speaker_id_label] [gemini_label]: テキスト
        # → [speaker_id_label]: テキスト
        fixed = re.sub(r"^(\[[^\]]+\]) \[[^\]]+\]: ", r"\1: ", text_content, flags=re.MULTILINE)
        lines[2:] = fixed.split("\n")
        cleaned.append("\n".join(lines))
    srt_path.write_text("\n\n".join(cleaned) + "\n", encoding="utf-8")


def count_srt_entries(srt_path: Path) -> int:
    """SRTのエントリ数を返す"""
    text = srt_path.read_text(encoding="utf-8")
    return len([b for b in text.strip().split("\n\n") if b.strip()])


def show_sample_entries(srt_path: Path, n: int = 3):
    """SRTの先頭Nエントリを表示する"""
    text = srt_path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    print(f"\n[pipeline] 先頭{min(n, len(blocks))}エントリ:", flush=True)
    for block in blocks[:n]:
        print(f"  {block}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Gemini Flash Lite + Speaker ID 統合パイプライン: MP4 → SRT"
    )
    parser.add_argument("video_path", help="入力動画ファイルパス（MP4）")
    parser.add_argument("--output", "-o", required=True, help="最終SRT出力パス")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Geminiモデル（デフォルト: {DEFAULT_MODEL}）",
    )
    parser.add_argument(
        "--profile-dir",
        default=str(SPEAKER_PROFILES),
        help=f"声紋プロファイルディレクトリ（デフォルト: {SPEAKER_PROFILES}）",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.25,
        help="Speaker ID類似度閾値（デフォルト: 0.25）",
    )
    parser.add_argument(
        "--gemini-srt",
        metavar="SRT_FILE",
        help="既存Gemini SRTを使用（Step1をスキップ）",
    )
    parser.add_argument(
        "--wx-cache",
        metavar="JSON_FILE",
        help="WhisperXキャッシュJSONパス（将来拡張用）",
    )
    args = parser.parse_args()

    video_path = Path(args.video_path).resolve()
    output_path = Path(args.output).resolve()
    profile_dir = Path(args.profile_dir).resolve()

    # 入力チェック
    if not video_path.exists():
        print(f"[pipeline] エラー: 動画ファイルが見つかりません: {video_path}", flush=True)
        return 1
    if not profile_dir.exists():
        print(f"[pipeline] エラー: 声紋プロファイルディレクトリが見つかりません: {profile_dir}", flush=True)
        return 1

    # 作業ディレクトリ設定
    video_stem = video_path.stem
    work_dir = PROJECT_DIR / "work" / f"pipeline_{video_stem}"
    work_dir.mkdir(parents=True, exist_ok=True)

    gemini_srt_path = work_dir / f"gemini_{video_stem}.srt"
    audio_path = work_dir / f"audio_{video_stem}.wav"
    speaker_json_path = work_dir / f"speaker_id_{video_stem}.json"

    start_time = time.time()
    print(f"[pipeline] ===== 開始: {video_path.name} =====", flush=True)
    print(f"[pipeline] 作業ディレクトリ: {work_dir}", flush=True)

    # Step1: Gemini字幕生成 / Step2: 音声抽出（並列実行）
    if args.gemini_srt:
        gemini_srt_path = Path(args.gemini_srt).resolve()
        print(f"[pipeline] Step1スキップ（既存SRT使用）: {gemini_srt_path}", flush=True)
        # 音声抽出のみ実行
        if not audio_path.exists():
            extract_audio(video_path, audio_path)
    else:
        print("[pipeline] Step1+Step2を並列実行中...", flush=True)
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_gemini = executor.submit(
                run_gemini_transcribe, video_path, gemini_srt_path, args.model
            )
            future_audio = executor.submit(extract_audio, video_path, audio_path)

            # 両方完了を待ち、例外があれば再発生
            for future in as_completed([future_gemini, future_audio]):
                future.result()

    # Step3+4: Speaker IDで話者ラベル付与 → 最終SRT生成
    run_speaker_id(
        audio_path=audio_path,
        srt_path=gemini_srt_path,
        output_path=output_path,
        json_path=speaker_json_path,
        profile_dir=profile_dir,
        threshold=args.threshold,
    )

    # Step4後処理: Gemini仮話者ラベルを除去（二重ラベル解消）
    print("[pipeline] Step4: Gemini仮話者ラベル除去", flush=True)
    clean_gemini_labels(output_path)

    # 結果表示
    if output_path.exists():
        entry_count = count_srt_entries(output_path)
        elapsed = time.time() - start_time
        print(f"\n[pipeline] ===== 完了 =====", flush=True)
        print(f"[pipeline] 最終SRT:    {output_path}", flush=True)
        print(f"[pipeline] エントリ数: {entry_count}", flush=True)
        print(f"[pipeline] 処理時間:   {elapsed:.1f}秒", flush=True)
        show_sample_entries(output_path)
        return 0
    else:
        print("[pipeline] エラー: 最終SRTが生成されませんでした", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
