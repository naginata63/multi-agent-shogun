#!/usr/bin/env python3
"""
vocal_stt_pipeline.py — Demucs vocal STT pipeline (1コマンド完結)

MP4 → ffmpeg 10分チャンク分割 → Demucs vocals分離(順次) → ffmpeg結合
    → AssemblyAI Universal-2 (diarize有効) → word-level JSON
    → Deepgram Nova-3 → word-level JSON
    → stt_merge.py → merged JSON (最終成果物)

Usage:
    python3 scripts/vocal_stt_pipeline.py INPUT_VIDEO.mp4 \\
        --output work/pipeline_VIDEOID/merged.json \\
        --work-dir work/pipeline_VIDEOID/ \\
        --cache \\
        [--gemini GEMINI_SRT_PATH]

鉄則:
  - Demucs一発投入禁止: 必ず600秒チャンク→順次Demucs→concat
  - 中間成果物は /tmp 禁止 (work-dir配下)
  - APIキー未設定時は即エラー停止
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
STT_MERGE_SCRIPT = PROJECT_DIR / "scripts" / "stt_merge.py"

CHUNK_DURATION_SEC = 600  # 10分チャンク
DEMUCS_TIMEOUT_SEC = 600  # 1チャンクあたり最大10分
ASSEMBLYAI_POLL_INTERVAL_SEC = 10


def check_api_keys():
    """APIキー未設定チェック（冒頭で実施）"""
    missing = []
    if not os.environ.get("ASSEMBLYAI_API_KEY"):
        missing.append("ASSEMBLYAI_API_KEY")
    if not os.environ.get("DEEPGRAM_API_KEY"):
        missing.append("DEEPGRAM_API_KEY")
    if missing:
        print(f"[pipeline] ERROR: 以下のAPIキーが未設定です: {', '.join(missing)}")
        print("[pipeline] source ~/.bashrc を実行してからやり直してください。")
        sys.exit(1)


def split_into_chunks(video_path: Path, chunks_dir: Path) -> list[Path]:
    """
    ffmpegで10分チャンクに分割する。
    既存チャンクがあればスキップ。
    戻り値: チャンクパスのリスト (ソート済み)
    """
    chunks_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(chunks_dir.glob("chunk_*.mp4"))
    if existing:
        print(f"[pipeline] Step1スキップ: チャンク{len(existing)}本が既存 ({chunks_dir})")
        return existing

    print(f"[pipeline] Step1: ffmpegでチャンク分割 (600秒/チャンク) ...")
    out_pattern = str(chunks_dir / "chunk_%03d.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-c", "copy",
        "-f", "segment",
        "-segment_time", str(CHUNK_DURATION_SEC),
        "-reset_timestamps", "1",
        out_pattern,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpegチャンク分割失敗:\n{result.stderr[-3000:]}")

    chunks = sorted(chunks_dir.glob("chunk_*.mp4"))
    if not chunks:
        raise RuntimeError(f"チャンクが生成されませんでした: {chunks_dir}")
    print(f"[pipeline] Step1完了: {len(chunks)}チャンク生成")
    return chunks


def run_demucs_on_chunk(chunk_path: Path, demucs_out_dir: Path) -> Path:
    """
    1チャンクにDemucsを実行してvocals.wavを返す。
    既存成果物があればスキップ。
    Demucs出力: {demucs_out_dir}/htdemucs/{chunk_stem}/vocals.wav
    """
    chunk_stem = chunk_path.stem
    vocals_path = demucs_out_dir / "htdemucs" / chunk_stem / "vocals.wav"

    if vocals_path.exists():
        print(f"[pipeline]   Demucsスキップ (既存): {vocals_path.name}")
        return vocals_path

    demucs_out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[pipeline]   Demucs実行中: {chunk_path.name} ...", flush=True)
    t0 = time.time()
    cmd = [
        sys.executable, "-m", "demucs",
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "--out", str(demucs_out_dir),
        str(chunk_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEMUCS_TIMEOUT_SEC)
    elapsed = time.time() - t0
    if result.returncode != 0:
        raise RuntimeError(
            f"Demucs失敗 ({chunk_path.name}): returncode={result.returncode}\n"
            f"stderr: {result.stderr[-2000:]}"
        )
    if not vocals_path.exists():
        # Demucs出力ディレクトリ名を確認 (稀に名前が変わる場合の保護)
        htdemucs_dir = demucs_out_dir / "htdemucs"
        dirs = list(htdemucs_dir.iterdir()) if htdemucs_dir.exists() else []
        raise RuntimeError(
            f"vocals.wav が見つかりません: {vocals_path}\n"
            f"htdemucs配下: {dirs}"
        )
    print(f"[pipeline]   Demucs完了: {vocals_path.name} ({elapsed:.0f}秒)", flush=True)
    return vocals_path


def concat_vocals(vocals_paths: list[Path], output_path: Path) -> Path:
    """複数vocals.wavをffmpegで連結してvocals_full.wavを生成する"""
    if output_path.exists():
        print(f"[pipeline] Step3スキップ (既存): {output_path.name}")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[pipeline] Step3: vocals.wav連結 ({len(vocals_paths)}本) ...")

    # ffmpeg concat demuxerのリストファイルを作成
    concat_list = output_path.parent / "concat_list.txt"
    with open(concat_list, "w") as f:
        for p in vocals_paths:
            f.write(f"file '{p.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg concat失敗:\n{result.stderr[-2000:]}")

    print(f"[pipeline] Step3完了: {output_path}")
    return output_path


def run_assemblyai(vocals_path: Path, output_path: Path) -> Path:
    """AssemblyAI Universal-2でSTT (speaker_labels有効) → word-level JSON保存"""
    import requests

    if output_path.exists():
        print(f"[pipeline] Step4スキップ (既存): {output_path.name}")
        return output_path

    api_key = os.environ["ASSEMBLYAI_API_KEY"]
    headers = {"authorization": api_key}

    print(f"[pipeline] Step4: AssemblyAI Universal-2 アップロード中 ({vocals_path.stat().st_size // 1024 // 1024}MB)...", flush=True)
    t0 = time.time()
    with open(vocals_path, "rb") as f:
        r = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f, timeout=300)
    r.raise_for_status()
    upload_url = r.json()["upload_url"]
    print(f"[pipeline]   アップロード完了 ({time.time()-t0:.0f}秒): {upload_url[:60]}...")

    payload = {
        "audio_url": upload_url,
        "speech_models": ["universal-2"],
        "speaker_labels": True,
        # language_code removed: not compatible with speaker_labels on Universal
        # speech_model (singular) deprecated → speech_models list per AssemblyAI v2 API
    }
    r = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json=payload, timeout=30)
    if not r.ok:
        print(f"[pipeline]   AssemblyAI エラーレスポンス: {r.status_code} {r.text}", flush=True)
    r.raise_for_status()
    job_id = r.json()["id"]
    print(f"[pipeline]   ジョブID: {job_id}")

    print("[pipeline]   ポーリング中...", flush=True)
    while True:
        r = requests.get(f"https://api.assemblyai.com/v2/transcript/{job_id}", headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        status = data["status"]
        print(f"[pipeline]   status: {status}", flush=True)
        if status == "completed":
            break
        elif status == "error":
            raise RuntimeError(f"AssemblyAI エラー: {data.get('error')}")
        time.sleep(ASSEMBLYAI_POLL_INTERVAL_SEC)

    elapsed = time.time() - t0
    print(f"[pipeline] Step4完了: {elapsed:.0f}秒")

    # word-level JSONを保存
    words = []
    for w in data.get("words", []):
        words.append({
            "text": w.get("text", ""),
            "start": w.get("start", 0),  # ms
            "end": w.get("end", 0),
            "confidence": w.get("confidence", 0.0),
            "speaker": w.get("speaker", ""),
        })

    utterances = []
    for u in data.get("utterances", []):
        utterances.append({
            "speaker": u.get("speaker", ""),
            "text": u.get("text", ""),
            "start": u.get("start", 0),
            "end": u.get("end", 0),
        })

    output_data = {
        "service": "assemblyai_universal_vocals",
        "total_words": len(words),
        "speakers_detected": len(set(w["speaker"] for w in words if w["speaker"])),
        "processing_time_sec": round(elapsed, 1),
        "job_id": job_id,
        "words": words,
        "utterances": utterances,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"[pipeline]   AssemblyAI保存: {output_path} ({len(words)}words)")
    return output_path


def run_deepgram(vocals_path: Path, output_path: Path) -> Path:
    """Deepgram Nova-3でSTT → word-level JSON保存"""
    import requests

    if output_path.exists():
        print(f"[pipeline] Step5スキップ (既存): {output_path.name}")
        return output_path

    api_key = os.environ["DEEPGRAM_API_KEY"]
    print(f"[pipeline] Step5: Deepgram Nova-3 投入中...", flush=True)
    t0 = time.time()

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/wav",
    }
    params = {
        "model": "nova-3",
        "language": "ja",
        "punctuate": "true",
        "words": "true",
        "utterances": "false",
        "smart_format": "true",
    }
    with open(vocals_path, "rb") as f:
        r = requests.post(
            "https://api.deepgram.com/v1/listen",
            headers=headers,
            params=params,
            data=f,
            timeout=600,
        )
    r.raise_for_status()
    elapsed = time.time() - t0
    print(f"[pipeline] Step5完了: {elapsed:.0f}秒")

    data = r.json()
    words = []
    channels = data.get("results", {}).get("channels", [])
    if channels:
        alts = channels[0].get("alternatives", [])
        if alts:
            for w in alts[0].get("words", []):
                words.append({
                    "text": w.get("word", ""),
                    "start": int(w.get("start", 0) * 1000),  # 秒→ms変換
                    "end": int(w.get("end", 0) * 1000),
                    "confidence": w.get("confidence", 0.0),
                    "speaker": w.get("speaker", ""),
                })

    output_data = {
        "service": "deepgram_nova3_vocals",
        "total_words": len(words),
        "processing_time_sec": round(elapsed, 1),
        "words": words,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"[pipeline]   Deepgram保存: {output_path} ({len(words)}words)")
    return output_path


def run_stt_merge(
    assemblyai_path: Path,
    deepgram_path: Path,
    gemini_srt_path: Path | None,
    output_path: Path,
    report_path: Path,
    video_id: str,
) -> Path:
    """stt_merge.pyを呼び出してmerged JSONを生成する"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[pipeline] Step6: stt_merge.py実行中...", flush=True)

    # gemini SRTが未指定の場合は空のSRTファイルを一時作成
    temp_srt = None
    if gemini_srt_path is None:
        tmp = tempfile.NamedTemporaryFile(
            suffix=".srt", mode="w", encoding="utf-8", delete=False
        )
        tmp.write("")  # 空SRT = 話者ラベルなし
        tmp.close()
        gemini_srt_path = Path(tmp.name)
        temp_srt = gemini_srt_path
        print("[pipeline]   Gemini SRT未指定: 話者ラベルなしで実行")

    try:
        cmd = [
            sys.executable, str(STT_MERGE_SCRIPT),
            "--assemblyai", str(assemblyai_path),
            "--deepgram", str(deepgram_path),
            "--gemini", str(gemini_srt_path),
            "--output", str(output_path),
            "--report", str(report_path),
            "--video-id", video_id,
        ]
        result = subprocess.run(cmd, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"stt_merge.py失敗 (returncode={result.returncode})")
    finally:
        if temp_srt and temp_srt.exists():
            temp_srt.unlink()

    print(f"[pipeline] Step6完了: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Demucs vocal STT pipeline: MP4 → merged word-level JSON"
    )
    parser.add_argument("input_video", help="入力MP4ファイルパス")
    parser.add_argument("--output", "-o", required=True, help="出力merged JSONパス")
    parser.add_argument("--work-dir", required=True, help="中間成果物保存ディレクトリ")
    parser.add_argument("--cache", action="store_true", help="既存中間成果物をスキップ")
    parser.add_argument("--gemini", metavar="SRT_FILE", help="Gemini SRTパス (話者ラベル付与用、省略可)")
    args = parser.parse_args()

    # APIキーチェック（最初に実施）
    check_api_keys()

    video_path = Path(os.path.abspath(args.input_video))
    output_path = Path(os.path.abspath(args.output))
    work_dir = Path(os.path.abspath(args.work_dir))
    gemini_srt = Path(os.path.abspath(args.gemini)) if args.gemini else None

    if not video_path.exists():
        print(f"[pipeline] ERROR: 動画ファイルが見つかりません: {video_path}")
        sys.exit(1)
    if gemini_srt and not gemini_srt.exists():
        print(f"[pipeline] ERROR: Gemini SRTが見つかりません: {gemini_srt}")
        sys.exit(1)

    video_id = video_path.stem
    work_dir.mkdir(parents=True, exist_ok=True)

    # 各成果物パスを定義
    chunks_dir = work_dir / "demucs_chunks"
    demucs_out_dir = work_dir / "demucs_output"
    vocals_full = work_dir / "vocals_full.wav"
    assemblyai_json = work_dir / "assemblyai_vocals.json"
    deepgram_json = work_dir / "deepgram_vocals.json"
    report_path = work_dir / f"merge_report_{video_id}.yaml"

    t_start = time.time()
    print(f"[pipeline] ===== Demucs Vocal STT Pipeline =====")
    print(f"[pipeline] 入力: {video_path}")
    print(f"[pipeline] 出力: {output_path}")
    print(f"[pipeline] 作業DIR: {work_dir}")
    print(f"[pipeline] キャッシュ: {'有効' if args.cache else '無効'}")

    # キャッシュ無効時は既存成果物を無視して全ステップを実行
    if not args.cache:
        # キャッシュ無効でも既存ファイルはffmpegの-yオプションで上書きされる
        # stt_merge出力だけはチェック不要（毎回上書き）
        pass

    # Step 1: ffmpegチャンク分割
    # キャッシュ無効時は既存チャンクを削除して再実行
    if not args.cache and chunks_dir.exists():
        import shutil
        shutil.rmtree(chunks_dir)
    chunks = split_into_chunks(video_path, chunks_dir)

    # Step 2: 各チャンクをDemucs処理（順次）
    if not args.cache and demucs_out_dir.exists():
        import shutil
        shutil.rmtree(demucs_out_dir)

    # キャッシュ有効でvocals_full.wavが既にあればStep2+3をスキップ
    if args.cache and vocals_full.exists():
        print(f"[pipeline] Step2+3スキップ (--cache, 既存): {vocals_full.name}")
    else:
        print(f"[pipeline] Step2: Demucs処理 ({len(chunks)}チャンク順次実行)")
        vocals_list = []
        for i, chunk in enumerate(chunks):
            print(f"[pipeline]   チャンク {i+1}/{len(chunks)}: {chunk.name}", flush=True)
            vocals_wav = run_demucs_on_chunk(chunk, demucs_out_dir)
            vocals_list.append(vocals_wav)

        # Step 3: vocals.wav連結
        concat_vocals(vocals_list, vocals_full)

    # Step 4: AssemblyAI STT
    # キャッシュ有効でassemblyai_vocals.jsonが既にあればスキップ
    if args.cache and assemblyai_json.exists():
        print(f"[pipeline] Step4スキップ (--cache, 既存): {assemblyai_json.name}")
    else:
        if not args.cache and assemblyai_json.exists():
            assemblyai_json.unlink()
        run_assemblyai(vocals_full, assemblyai_json)

    # Step 5: Deepgram STT
    if args.cache and deepgram_json.exists():
        print(f"[pipeline] Step5スキップ (--cache, 既存): {deepgram_json.name}")
    else:
        if not args.cache and deepgram_json.exists():
            deepgram_json.unlink()
        run_deepgram(vocals_full, deepgram_json)

    # Step 6: stt_merge.py
    run_stt_merge(
        assemblyai_path=assemblyai_json,
        deepgram_path=deepgram_json,
        gemini_srt_path=gemini_srt,
        output_path=output_path,
        report_path=report_path,
        video_id=video_id,
    )

    elapsed = time.time() - t_start
    print(f"\n[pipeline] ===== 完了 =====")
    print(f"[pipeline] merged JSON: {output_path}")
    print(f"[pipeline] レポート:   {report_path}")
    print(f"[pipeline] 総処理時間: {elapsed:.0f}秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
