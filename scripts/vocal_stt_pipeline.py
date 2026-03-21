#!/usr/bin/env python3
"""
vocal_stt_pipeline.py — Demucs vocal STT pipeline (1コマンド完結)

MP4 → ffmpeg 10分チャンク分割 → Demucs vocals分離(順次) → ffmpeg結合
    → AssemblyAI Universal-2 (diarize有効) → word-level JSON
    → Deepgram Nova-3 → word-level JSON
    → stt_merge.py → merged JSON
    → ECAPA-TDNN声紋マッチング → 話者ラベル実名変換 (最終成果物)

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
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
STT_MERGE_SCRIPT = PROJECT_DIR / "scripts" / "stt_merge.py"

CHUNK_DURATION_SEC = 600  # 10分チャンク


def load_members_from_yaml(profiles_path: Path | None = None) -> list[str]:
    """member_profiles.yamlからメンバーキー一覧を読み込む。失敗時はデフォルト値を返す。"""
    if profiles_path is None:
        profiles_path = PROJECT_DIR / "projects" / "dozle_kirinuki" / "context" / "member_profiles.yaml"
    try:
        import yaml
        with open(profiles_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return list(data.get("members", {}).keys())
    except Exception:
        return ["dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"]


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
    音声先行抽出方式でffmpegを使い10分チャンクに分割する。
    Step1a: 音声をWAV抽出（AAC境界問題を回避）
    Step1b: WAVを正確な600秒チャンクに分割
    既存チャンクがあればスキップ。
    戻り値: チャンクパスのリスト (ソート済み)
    """
    chunks_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(chunks_dir.glob("chunk_*.wav"))
    if existing:
        print(f"[pipeline] Step1スキップ: チャンク{len(existing)}本が既存 ({chunks_dir})")
        return existing

    # Step1a: 音声をWAVとして抽出（AAC境界損失を排除）
    full_audio_path = chunks_dir / "full_audio.wav"
    if not full_audio_path.exists():
        print(f"[pipeline] Step1a: 音声WAV抽出 (48kHz PCM) ...")
        cmd_extract = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ar", "48000", "-c:a", "pcm_s16le",
            str(full_audio_path),
        ]
        result = subprocess.run(cmd_extract, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg音声抽出失敗:\n{result.stderr[-3000:]}")
        print(f"[pipeline] Step1a完了: {full_audio_path.name}")
    else:
        print(f"[pipeline] Step1aスキップ: {full_audio_path.name} が既存")

    # Step1b: WAVを正確な600秒チャンクに分割
    print(f"[pipeline] Step1b: WAVチャンク分割 ({CHUNK_DURATION_SEC}秒/チャンク) ...")
    out_pattern = str(chunks_dir / "chunk_%03d.wav")
    cmd_split = [
        "ffmpeg", "-y", "-i", str(full_audio_path),
        "-f", "segment",
        "-segment_time", str(CHUNK_DURATION_SEC),
        out_pattern,
    ]
    result = subprocess.run(cmd_split, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpegWAVチャンク分割失敗:\n{result.stderr[-3000:]}")

    chunks = sorted(chunks_dir.glob("chunk_*.wav"))
    if not chunks:
        raise RuntimeError(f"チャンクが生成されませんでした: {chunks_dir}")
    print(f"[pipeline] Step1完了: {len(chunks)}チャンク生成 (WAV形式, ドリフトゼロ)")
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

    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise KeyError("環境変数 ASSEMBLYAI_API_KEY が設定されていません。source ~/.bashrc を実行してください。")
    headers = {"authorization": api_key}

    print(f"[pipeline] Step4: AssemblyAI Universal-2 アップロード中 ({vocals_path.stat().st_size // 1024 // 1024}MB)...", flush=True)
    t0 = time.time()
    with open(vocals_path, "rb") as f:
        r = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f, timeout=300)
    r.raise_for_status()
    try:
        upload_url = r.json()["upload_url"]
    except (ValueError, KeyError) as e:
        raise RuntimeError(f"AssemblyAI アップロードレスポンス解析失敗: {e} / body={r.text[:200]}") from e
    print(f"[pipeline]   アップロード完了 ({time.time()-t0:.0f}秒): {upload_url[:60]}...")

    payload = {
        "audio_url": upload_url,
        "speech_models": ["universal-2"],
        "speaker_labels": True,
        "speakers_expected": 6,  # ドズル社メンバー6名
        # language_code removed: not compatible with speaker_labels on Universal
        # speech_model (singular) deprecated → speech_models list per AssemblyAI v2 API
    }
    r = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json=payload, timeout=30)
    if r.status_code == 400:
        print(f"[pipeline]   AssemblyAI 400エラー (speaker_labels=True): {r.text}", flush=True)
        print("[pipeline]   WARNING: speaker_labels=Falseで自動リトライ（話者分離はECAPA-TDNNで後付け）", flush=True)
        payload_no_speaker = {k: v for k, v in payload.items() if k != "speaker_labels"}
        payload_no_speaker["speaker_labels"] = False
        r = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json=payload_no_speaker, timeout=30)
    if not r.ok:
        print(f"[pipeline]   AssemblyAI エラーレスポンス: {r.status_code} {r.text}", flush=True)
    r.raise_for_status()
    try:
        job_id = r.json()["id"]
    except (ValueError, KeyError) as e:
        raise RuntimeError(f"AssemblyAI ジョブ投入レスポンス解析失敗: {e} / body={r.text[:200]}") from e
    print(f"[pipeline]   ジョブID: {job_id}")

    print("[pipeline]   ポーリング中...", flush=True)
    max_iterations = 60  # 5分上限 (5s間隔 × 60 = 300s)
    for _poll_iter in range(max_iterations):
        r = requests.get(f"https://api.assemblyai.com/v2/transcript/{job_id}", headers=headers, timeout=30)
        r.raise_for_status()
        try:
            data = r.json()
        except ValueError as e:
            raise RuntimeError(f"AssemblyAI ポーリングレスポンス解析失敗: {e} / body={r.text[:200]}") from e
        status = data["status"]
        print(f"[pipeline]   status: {status}", flush=True)
        if status == "completed":
            break
        elif status == "error":
            raise RuntimeError(f"AssemblyAI エラー: {data.get('error')}")
        time.sleep(ASSEMBLYAI_POLL_INTERVAL_SEC)
    else:
        raise RuntimeError(f"AssemblyAI ポーリングタイムアウト: {max_iterations}回 ({max_iterations * ASSEMBLYAI_POLL_INTERVAL_SEC}秒) 経過")

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

    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise KeyError("環境変数 DEEPGRAM_API_KEY が設定されていません。source ~/.bashrc を実行してください。")
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
    youtube_subs_path: Path | None = None,
) -> Path:
    """stt_merge.pyを呼び出してmerged JSONを生成する"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[pipeline] Step6: stt_merge.py実行中...", flush=True)

    cmd = [
        sys.executable, str(STT_MERGE_SCRIPT),
        "--assemblyai", str(assemblyai_path),
        "--deepgram", str(deepgram_path),
        "--output", str(output_path),
        "--report", str(report_path),
        f"--video-id={video_id}",
    ]
    if gemini_srt_path is not None:
        cmd += ["--gemini", str(gemini_srt_path)]
    else:
        print("[pipeline]   Gemini SRT未指定: 話者ラベルなしで実行")
    if youtube_subs_path is not None:
        cmd += ["--youtube-subs", str(youtube_subs_path)]
        print(f"[pipeline]   YouTube字幕: {youtube_subs_path.name}")

    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"stt_merge.py失敗 (returncode={result.returncode})")

    print(f"[pipeline] Step6完了: {output_path}")
    return output_path


def run_speaker_identification(
    merged_json_path: Path,
    vocals_full_path: Path,
    report_path: Path,
) -> None:
    """ECAPA-TDNNでAssemblyAI話者ラベル(A/B/C...)を実名(dozle/bon/...)に変換する。

    speaker_id.pyのロジック流用。声紋プロファイルは speaker_profiles/ を参照。
    """
    if not vocals_full_path.exists():
        print(f"[pipeline] Step7スキップ: vocals_full.wavが見つかりません ({vocals_full_path})")
        return

    # speaker_id.pyの定数・閾値を流用
    MEMBERS = load_members_from_yaml()
    THRESHOLD = 0.25
    MIN_SEG_SEC = 1.0   # 声紋照合に使う最小セグメント長（秒）
    GAP_MS = 500        # 同一話者の連続ワードをマージするギャップ閾値（ms）
    profile_dir = PROJECT_DIR / "projects" / "dozle_kirinuki" / "speaker_profiles"

    try:
        import torch
        import torchaudio
        import torch.nn.functional as F
        from speechbrain.inference.speaker import EncoderClassifier
    except ImportError as e:
        print(f"[pipeline] Step7スキップ: 依存ライブラリ不足 ({e})")
        return

    # merged JSON読み込み
    with open(merged_json_path, encoding="utf-8") as f:
        merged_data = json.load(f)

    words = merged_data.get("words", [])
    speaker_labels = sorted(set(w.get("speaker", "") for w in words if w.get("speaker")))
    if not speaker_labels:
        print("[pipeline] Step7スキップ: 話者ラベルなし")
        return

    print(f"[pipeline] Step7: ECAPA-TDNN声紋マッチング (話者: {speaker_labels})", flush=True)

    # ECAPA-TDNNモデルロード（speaker_id.pyのロジック流用）
    device = "cuda" if torch.cuda.is_available() else "cpu"
    savedir = str(profile_dir / "pretrained_models" / "spkrec-ecapa-voxceleb")
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=savedir,
        run_opts={"device": device},
    )
    print(f"[pipeline]   モデルロード完了 (device: {device})")

    # 声紋プロファイルロード（speaker_id.pyのロジック流用）
    embeddings = {}
    for member in MEMBERS:
        multi_path = profile_dir / f"{member}_embeddings.pt"
        single_path = profile_dir / f"{member}_embedding.pt"
        if multi_path.exists():
            embs = torch.load(str(multi_path), map_location=device)
            if embs.dim() == 1:
                embs = embs.unsqueeze(0)
            embeddings[member] = embs
            print(f"[pipeline]     {member}: _embeddings.pt ({embs.shape[0]}個)")
        elif single_path.exists():
            emb = torch.load(str(single_path), map_location=device).squeeze()
            embeddings[member] = emb.unsqueeze(0)
            print(f"[pipeline]     {member}: _embedding.pt (旧形式)")

    if not embeddings:
        print("[pipeline]   声紋プロファイルなし → Step7スキップ")
        return

    # vocals_full.wav読み込み・16kHzリサンプル
    print(f"[pipeline]   vocals_full.wav読み込み: {vocals_full_path}", flush=True)
    waveform, sr = torchaudio.load(str(vocals_full_path))
    if sr != 16000:
        waveform = torchaudio.transforms.Resample(sr, 16000)(waveform)
        sr = 16000
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    # 話者ラベルごとに声紋照合（多数決）
    from collections import Counter
    label_to_real_name = {}

    for label in speaker_labels:
        # 同ラベルのワードをソートして連続セグメントにマージ
        label_words = sorted(
            [w for w in words if w.get("speaker") == label],
            key=lambda x: x["start"]
        )
        if not label_words:
            label_to_real_name[label] = "unknown"
            continue

        # 連続ワードをセグメントにマージ（ギャップ < GAP_MS なら連結）
        segments = []
        cur_start = label_words[0]["start"]
        cur_end = label_words[0]["end"]
        for w in label_words[1:]:
            if w["start"] - cur_end <= GAP_MS:
                cur_end = w["end"]
            else:
                segments.append((cur_start, cur_end))
                cur_start = w["start"]
                cur_end = w["end"]
        segments.append((cur_start, cur_end))

        # 各セグメントでECAPA-TDNN照合（MIN_SEG_SEC以上のみ）
        votes = []
        for seg_start_ms, seg_end_ms in segments:
            seg_start = seg_start_ms / 1000.0
            seg_end = seg_end_ms / 1000.0
            if seg_end - seg_start < MIN_SEG_SEC:
                continue

            s_sample = int(seg_start * sr)
            e_sample = int(seg_end * sr)
            seg_audio = waveform[:, s_sample:e_sample]
            if seg_audio.shape[1] < int(MIN_SEG_SEC * sr):
                continue

            seg_signal = seg_audio.squeeze()
            with torch.no_grad():
                seg_emb = classifier.encode_batch(seg_signal.unsqueeze(0)).squeeze()

            # cosine similarity照合（speaker_id.pyのロジック流用）
            sims = {}
            for member, embs in embeddings.items():
                seg_exp = seg_emb.unsqueeze(0).expand(embs.shape[0], -1)
                s = F.cosine_similarity(seg_exp, embs, dim=1)
                sims[member] = s.max().item()

            best_member = max(sims, key=sims.get)
            if sims[best_member] >= THRESHOLD:
                votes.append(best_member)

        if votes:
            real_name = Counter(votes).most_common(1)[0][0]
        else:
            real_name = "unknown"

        print(f"[pipeline]   {label} → {real_name} (投票数: {len(votes)}/{len(segments)}セグメント)")
        label_to_real_name[label] = real_name

    print(f"[pipeline]   話者マッピング: {label_to_real_name}")

    # merged JSONの全ワードのspeakerフィールドを実名に置換
    for w in words:
        orig = w.get("speaker", "")
        if orig in label_to_real_name:
            w["speaker"] = label_to_real_name[orig]

    # metadata.speaker_distributionを実名で更新
    metadata = merged_data.get("metadata", {})
    old_dist = metadata.get("speaker_distribution", {})
    new_dist: dict[str, int] = {}
    for old_label, count in old_dist.items():
        real_name = label_to_real_name.get(old_label, old_label)
        new_dist[real_name] = new_dist.get(real_name, 0) + count
    metadata["speaker_distribution"] = new_dist
    merged_data["metadata"] = metadata

    # speaker_id_pctを実名変換後に再計算
    known_members_set = set(load_members_from_yaml())
    total = len(words)
    known_count = sum(1 for w in words if w.get("speaker") in known_members_set)
    metadata["speaker_id_pct"] = round(known_count / total * 100, 2) if total > 0 else 0

    with open(merged_json_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    print(f"[pipeline]   merged JSON更新完了: {merged_json_path}")

    # merge_report.yamlに話者マッピング結果を追記
    try:
        import yaml
        report_data = {}
        if report_path.exists():
            with open(report_path, encoding="utf-8") as f:
                report_data = yaml.safe_load(f) or {}
        report_data["speaker_identification"] = {
            "method": "ECAPA-TDNN",
            "threshold": THRESHOLD,
            "profiles_used": list(embeddings.keys()),
            "label_mapping": label_to_real_name,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            yaml.dump(report_data, f, allow_unicode=True, default_flow_style=False)
        print(f"[pipeline]   merge_report更新: {report_path}")
    except Exception as e:
        print(f"[pipeline]   merge_report更新失敗 (非致命的): {e}")

    print(f"[pipeline] Step7完了")


def run_direct_speaker_identification(
    merged_json_path: Path,
    vocals_full_path: Path,
    report_path: Path,
) -> None:
    """ECAPA-TDNNでワード単位の直接話者特定を行う。

    AssemblyAIの話者ラベルに依存せず、音声波形から直接各ワードの話者を特定する。
    AssemblyAIが全ワードを同一話者（speakers_detected=1）にまとめた場合のフォールバック。

    アルゴリズム:
    1. vocals_full.wavをロード
    2. merged JSONの各ワードをウィンドウ（~1s）単位にまとめる
    3. 各ウィンドウでECAPA-TDNN embeddingを計算
    4. 全声紋プロファイルとcosine類似度を比較し最高スコアの話者を割り当て
    5. merged JSON更新 + SRT再生成
    """
    if not vocals_full_path.exists():
        print(f"[pipeline] DirectSpeakerID スキップ: vocals_full.wavが見つかりません ({vocals_full_path})")
        return

    MEMBERS = load_members_from_yaml()
    THRESHOLD = 0.25
    MIN_WIN_SEC = 0.30    # ウィンドウ最小長（秒）; 未満はゼロパディング
    TARGET_WIN_MS = 1000  # ウィンドウ目標長（ms）
    MAX_WIN_MS = 2000     # ウィンドウ最大長（ms）
    MAX_GAP_MS = 500      # ウィンドウを区切る無音ギャップ閾値（ms）
    profile_dir = PROJECT_DIR / "projects" / "dozle_kirinuki" / "speaker_profiles"

    try:
        import torch
        import torchaudio
        import torch.nn.functional as F
        from speechbrain.inference.speaker import EncoderClassifier
    except ImportError as e:
        print(f"[pipeline] DirectSpeakerID スキップ: 依存ライブラリ不足 ({e})")
        return

    # merged JSON読み込み
    with open(merged_json_path, encoding="utf-8") as f:
        merged_data = json.load(f)

    words = merged_data.get("words", [])
    if not words:
        print("[pipeline] DirectSpeakerID スキップ: wordsが空")
        return

    print(f"[pipeline] Step7(Direct): ECAPA-TDNN直接話者特定 ({len(words)}ワード)", flush=True)

    # ECAPA-TDNNモデルロード
    device = "cuda" if torch.cuda.is_available() else "cpu"
    savedir = str(profile_dir / "pretrained_models" / "spkrec-ecapa-voxceleb")
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=savedir,
        run_opts={"device": device},
    )
    print(f"[pipeline]   モデルロード完了 (device: {device})")

    # 声紋プロファイルロード
    embeddings = {}
    for member in MEMBERS:
        multi_path = profile_dir / f"{member}_embeddings.pt"
        single_path = profile_dir / f"{member}_embedding.pt"
        if multi_path.exists():
            embs = torch.load(str(multi_path), map_location=device)
            if embs.dim() == 1:
                embs = embs.unsqueeze(0)
            embeddings[member] = embs
        elif single_path.exists():
            emb = torch.load(str(single_path), map_location=device).squeeze()
            embeddings[member] = emb.unsqueeze(0)

    if not embeddings:
        print("[pipeline]   声紋プロファイルなし → DirectSpeakerID スキップ")
        return
    print(f"[pipeline]   プロファイルロード: {list(embeddings.keys())}")

    # vocals_full.wav読み込み・16kHzリサンプル
    print(f"[pipeline]   vocals_full.wav読み込み中 ({vocals_full_path.stat().st_size // 1024 // 1024}MB)...", flush=True)
    waveform, sr = torchaudio.load(str(vocals_full_path))
    if sr != 16000:
        waveform = torchaudio.transforms.Resample(sr, 16000)(waveform)
        sr = 16000
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    total_samples = waveform.shape[1]
    print(f"[pipeline]   音声ロード完了: {total_samples/sr:.1f}秒")

    def extract_window(start_ms: int, end_ms: int) -> torch.Tensor | None:
        """音声ウィンドウを切り出す。短すぎる場合はゼロパディング。"""
        s = max(0, int(start_ms / 1000.0 * sr))
        e = min(total_samples, int(end_ms / 1000.0 * sr))
        min_samples = int(MIN_WIN_SEC * sr)
        seg = waveform[:, s:e]
        if seg.shape[1] < min_samples:
            # ゼロパディングで最小長を確保
            pad = torch.zeros(1, min_samples - seg.shape[1], dtype=seg.dtype)
            seg = torch.cat([seg, pad], dim=1)
        if seg.shape[1] < 10:
            return None
        return seg.squeeze(0)

    def get_speaker(audio_seg: torch.Tensor) -> str:
        """ECAPA-TDNNで話者を特定。閾値未満は'unknown'。"""
        with torch.no_grad():
            emb = classifier.encode_batch(audio_seg.unsqueeze(0)).squeeze()
        sims = {}
        for member, embs in embeddings.items():
            seg_exp = emb.unsqueeze(0).expand(embs.shape[0], -1)
            s = F.cosine_similarity(seg_exp, embs, dim=1)
            sims[member] = s.max().item()
        best = max(sims, key=sims.get)
        return best if sims[best] >= THRESHOLD else "unknown"

    # ワードをウィンドウ単位に区切って処理
    speaker_assignments = ["unknown"] * len(words)
    i = 0
    window_count = 0
    speaker_counts: dict[str, int] = {}

    while i < len(words):
        win_start = words[i]["start"]
        win_end = words[i]["end"]
        win_indices = [i]
        j = i + 1

        while j < len(words):
            gap = words[j]["start"] - words[j - 1]["end"]
            new_end = words[j]["end"]
            # ギャップ超過またはウィンドウ最大長超過で区切る
            if gap > MAX_GAP_MS:
                break
            if new_end - win_start > MAX_WIN_MS:
                # ウィンドウが既にTARGET_WIN_MSを超えていれば終了
                if win_end - win_start >= TARGET_WIN_MS:
                    break
            win_end = new_end
            win_indices.append(j)
            j += 1

        # ウィンドウ音声を切り出してECAPA-TDNN
        audio_seg = extract_window(win_start, win_end)
        if audio_seg is not None:
            speaker = get_speaker(audio_seg)
        else:
            speaker = "unknown"

        for idx in win_indices:
            speaker_assignments[idx] = speaker

        speaker_counts[speaker] = speaker_counts.get(speaker, 0) + len(win_indices)
        window_count += 1
        if window_count % 100 == 0:
            print(f"[pipeline]   処理中: {window_count}ウィンドウ完了 (word {i}/{len(words)})", flush=True)

        i = j

    print(f"[pipeline]   完了: {window_count}ウィンドウ処理")
    print(f"[pipeline]   話者分布: {speaker_counts}")

    # merged JSON更新
    for idx, w in enumerate(words):
        w["speaker"] = speaker_assignments[idx]

    # metadata.speaker_distributionを実名（speaker_counts）で更新
    metadata = merged_data.get("metadata", {})
    metadata["speaker_distribution"] = dict(speaker_counts)
    merged_data["metadata"] = metadata

    # speaker_id_pctを実名変換後に再計算
    known_members_set = set(load_members_from_yaml())
    total = len(words)
    known_count = sum(1 for w in words if w.get("speaker") in known_members_set)
    metadata["speaker_id_pct"] = round(known_count / total * 100, 2) if total > 0 else 0

    with open(merged_json_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    print(f"[pipeline]   merged JSON更新完了: {merged_json_path}")

    # SRT再生成
    srt_path = merged_json_path.parent / merged_json_path.name.replace(".json", ".srt")
    regenerate_srt_from_merged(words, srt_path)
    print(f"[pipeline]   SRT再生成完了: {srt_path}")

    # merge_report更新（古いspeaker_identificationセクションを削除してから書き込み）
    try:
        import yaml
        report_data = {}
        if report_path.exists():
            with open(report_path, encoding="utf-8") as f:
                report_data = yaml.safe_load(f) or {}
        # C003: direct方式実行時は古いspeaker_identificationを削除
        report_data.pop("speaker_identification", None)
        report_data["direct_speaker_identification"] = {
            "method": "ECAPA-TDNN-direct",
            "threshold": THRESHOLD,
            "profiles_used": list(embeddings.keys()),
            "windows_processed": window_count,
            "speaker_distribution": speaker_counts,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            yaml.dump(report_data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"[pipeline]   merge_report更新失敗 (非致命的): {e}")

    print(f"[pipeline] Step7(Direct)完了")


def regenerate_srt_from_merged(words: list[dict], srt_path: Path) -> None:
    """merged JSONのwordsリストからSRTファイルを再生成する。

    連続する同一話者のワードを1セグメントにまとめる（最大5秒、ギャップ2秒で区切り）。
    """
    MAX_SEG_MS = 5000
    MAX_GAP_MS = 2000

    def ms_to_srt_time(ms: int) -> str:
        h = ms // 3600000
        m = (ms % 3600000) // 60000
        s = (ms % 60000) // 1000
        cs = (ms % 1000) // 10
        return f"{h:02d}:{m:02d}:{s:02d},{cs:02d}0"

    segments = []
    if not words:
        srt_path.write_text("", encoding="utf-8")
        return

    seg_words = [words[0]]
    seg_start = words[0]["start"]
    seg_end = words[0]["end"]
    seg_speaker = words[0].get("speaker", "")

    def flush_segment():
        text = " ".join(w["text"] for w in seg_words if w.get("text")).strip()
        if text:
            segments.append((seg_start, seg_end, seg_speaker, text))

    for w in words[1:]:
        gap = w["start"] - seg_end
        duration = seg_end - seg_start
        speaker = w.get("speaker", "")

        if speaker != seg_speaker or gap > MAX_GAP_MS or duration >= MAX_SEG_MS:
            flush_segment()
            seg_words = [w]
            seg_start = w["start"]
            seg_end = w["end"]
            seg_speaker = speaker
        else:
            seg_words.append(w)
            seg_end = w["end"]

    flush_segment()

    lines = []
    for idx, (start, end, speaker, text) in enumerate(segments, 1):
        label = f"[{speaker}]" if speaker else "[?]"
        lines.append(str(idx))
        lines.append(f"{ms_to_srt_time(start)} --> {ms_to_srt_time(end)}")
        lines.append(f"{label}: {text}")
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Demucs vocal STT pipeline: MP4 → merged word-level JSON"
    )
    parser.add_argument("input_video", help="入力MP4ファイルパス")
    parser.add_argument("--output", "-o", required=True, help="出力merged JSONパス")
    parser.add_argument("--work-dir", required=True, help="中間成果物保存ディレクトリ")
    parser.add_argument("--cache", action="store_true", help="既存中間成果物をスキップ")
    parser.add_argument("--gemini", metavar="SRT_FILE",
                        help="Gemini SRTパス（廃止済み・互換用に残存）話者IDはECAPA-TDNNで付与")
    parser.add_argument("--direct-speaker-id", action="store_true",
                        help="AssemblyAI話者ラベルを無視してECAPA-TDNN直接話者特定を強制実行")
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
    # YouTube字幕を自動検出（work_dir内の {video_id}_subs.json または {video_id}.ja.vtt）
    youtube_subs: Path | None = None
    for subs_candidate in [
        work_dir / f"{video_id}_subs.json",
        work_dir / f"{video_id}.ja.vtt",
    ]:
        if subs_candidate.exists():
            youtube_subs = subs_candidate
            print(f"[pipeline] YouTube字幕自動検出: {subs_candidate.name}")
            break
    run_stt_merge(
        assemblyai_path=assemblyai_json,
        deepgram_path=deepgram_json,
        gemini_srt_path=gemini_srt,
        output_path=output_path,
        report_path=report_path,
        video_id=video_id,
        youtube_subs_path=youtube_subs,
    )

    # Step 7: ECAPA-TDNN声紋マッチング
    # AssemblyAI話者検出数=1または--direct-speaker-idフラグ時はdirect方式を使用
    use_direct = args.direct_speaker_id
    if not use_direct and assemblyai_json.exists():
        try:
            with open(assemblyai_json, encoding="utf-8") as f:
                aai_data = json.load(f)
            words = aai_data.get("words", [])
            speakers_from_words = len(set(w.get("speaker", "") for w in words if w.get("speaker")))
            speakers_detected = aai_data.get("speakers_detected", speakers_from_words or 2)
            if speakers_detected <= 1:
                print(f"[pipeline] AssemblyAI話者数={speakers_detected} → direct話者特定方式にフォールバック")
                use_direct = True
        except Exception:
            pass

    if use_direct:
        run_direct_speaker_identification(
            merged_json_path=output_path,
            vocals_full_path=vocals_full,
            report_path=report_path,
        )
    else:
        run_speaker_identification(
            merged_json_path=output_path,
            vocals_full_path=vocals_full,
            report_path=report_path,
        )

    elapsed = time.time() - t_start
    print(f"\n[pipeline] ===== 完了 =====")
    print(f"[pipeline] merged JSON: {output_path}")
    print(f"[pipeline] レポート:   {report_path}")
    print(f"[pipeline] 総処理時間: {elapsed:.0f}秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
