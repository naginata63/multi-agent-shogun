#!/usr/bin/env python3
"""Gemini動画理解APIによる字幕生成PoC"""

import argparse
import re
import sys
import time
from pathlib import Path


def upload_video(client, video_path: str):
    """File APIで動画をアップロードし、処理完了を待つ"""
    print(f"[upload] アップロード開始: {video_path}", flush=True)
    video_file = client.files.upload(file=video_path)
    print(f"[upload] ファイル名: {video_file.name} 状態: {video_file.state.name}", flush=True)

    # 処理完了を待機（PROCESSING → ACTIVE）
    while video_file.state.name == "PROCESSING":
        print("[upload] 処理中... 10秒待機", flush=True)
        time.sleep(10)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name != "ACTIVE":
        raise RuntimeError(f"ファイルが ACTIVE になりませんでした: {video_file.state.name}")

    print(f"[upload] 完了: {video_file.name}", flush=True)
    return video_file


def generate_subtitles(client, video_file, model: str) -> tuple[str, object]:
    """generateContent で SRT 字幕を生成する"""
    print(f"[generate] モデル: {model}", flush=True)

    prompt = (
        "この動画の全発話をSRT形式の字幕として書き起こしてください。\n"
        "要件:\n"
        "- SRT形式（番号、タイムスタンプ、テキスト）\n"
        "- タイムスタンプは HH:MM:SS,mmm 形式で、ミリ秒も含めてできるだけ正確に\n"
        "- 話者が変わったら新しいエントリにする\n"
        "- 可能なら話者名を [speaker_name]: 形式で先頭に付ける\n"
        "- ゲーム実況動画なので、ゲーム内SE/BGMは無視し発話のみ\n"
        "- ナレーション（ネコおじ/三木俊英）がいる場合は [ナレーション]: として区別\n"
        "- 動画の最後がエンドカード（チャンネル登録画面等）の場合、そこでの架空の発話は含めない\n"
        "- 日本語で出力\n"
        "- SRTテキストのみを出力し、説明文は不要"
    )

    from google.genai import types as genai_types

    response = client.models.generate_content(
        model=model,
        contents=[video_file, prompt],
        config=genai_types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=65536,
        ),
    )

    srt_text = response.text
    return srt_text, response


# SRTタイムスタンプの正規表現（HH:MM:SS,mmm）
_TS_RE = re.compile(r"^(\d{1,2}):(\d{2}):(\d{2}),(\d{3})$")


def _ts_to_seconds(ts: str) -> float | None:
    """'HH:MM:SS,mmm' を秒数に変換。パース失敗時はNone"""
    m = _TS_RE.match(ts.strip())
    if not m:
        return None
    h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return h * 3600 + mi * 60 + s + ms / 1000.0


def _fix_timestamp(ts: str) -> str | None:
    """不正なタイムスタンプを修正を試みる。修正不能ならNone"""
    ts = ts.strip()
    # カンマ多重（例: 00:10,04,000 や 00:10:04,00,0 など）
    # カンマを全て除去して最後の3桁をmsとして再構築
    if ts.count(",") > 1:
        parts = ts.replace(",", ":")
        segs = parts.split(":")
        # 末尾3桁をms候補として使う
        if len(segs) >= 4:
            ms_candidate = segs[-1].zfill(3)[:3]
            time_segs = segs[:-1]
            if len(time_segs) >= 3:
                h, mi, s = time_segs[-3], time_segs[-2], time_segs[-1]
                fixed = f"{h.zfill(2)}:{mi.zfill(2)}:{s.zfill(2)},{ms_candidate}"
                if _TS_RE.match(fixed):
                    return fixed
    return None


def validate_srt(srt_text: str) -> tuple[str, dict]:
    """
    SRTテキストをバリデーションし、修正済みSRTと統計を返す。

    Returns:
        (validated_srt_text, stats)
        stats keys: total, kept, fixed_ts, removed_invalid, removed_start_gt_end, removed_overlap
    """
    stats = {
        "total": 0,
        "kept": 0,
        "fixed_ts": 0,
        "removed_invalid": 0,
        "removed_start_gt_end": 0,
        "removed_overlap": 0,
    }

    blocks = srt_text.strip().split("\n\n")
    valid_entries = []
    prev_end_sec = -1.0

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # インデックス行
        try:
            int(lines[0].strip())
        except ValueError:
            continue

        stats["total"] += 1

        # タイムスタンプ行: "HH:MM:SS,mmm --> HH:MM:SS,mmm"
        ts_line = lines[1].strip()
        ts_parts = ts_line.split("-->")
        if len(ts_parts) != 2:
            print(f"[validate] 無効なタイムスタンプ行（除外）: {ts_line!r}", flush=True)
            stats["removed_invalid"] += 1
            continue

        start_raw, end_raw = ts_parts[0].strip(), ts_parts[1].strip()

        # start の修正
        start_sec = _ts_to_seconds(start_raw)
        if start_sec is None:
            fixed = _fix_timestamp(start_raw)
            if fixed:
                print(f"[validate] start修正: {start_raw!r} → {fixed!r}", flush=True)
                start_raw = fixed
                start_sec = _ts_to_seconds(fixed)
                stats["fixed_ts"] += 1
            else:
                print(f"[validate] start修正不能（除外）: {start_raw!r}", flush=True)
                stats["removed_invalid"] += 1
                continue

        # end の修正
        end_sec = _ts_to_seconds(end_raw)
        if end_sec is None:
            fixed = _fix_timestamp(end_raw)
            if fixed:
                print(f"[validate] end修正: {end_raw!r} → {fixed!r}", flush=True)
                end_raw = fixed
                end_sec = _ts_to_seconds(fixed)
                stats["fixed_ts"] += 1
            else:
                print(f"[validate] end修正不能（除外）: {end_raw!r}", flush=True)
                stats["removed_invalid"] += 1
                continue

        # start > end チェック
        if start_sec >= end_sec:
            print(f"[validate] start>=end（除外）: {start_raw} --> {end_raw}", flush=True)
            stats["removed_start_gt_end"] += 1
            continue

        # タイムスタンプ重複チェック（前エントリのendと逆転）
        if start_sec < prev_end_sec - 0.001:
            # prev_end >= current_end の場合、前エントリのendが不正（大きすぎる）
            # 例: 前エントリのendが誤った修正でジャンプした場合
            # → 元のタイムスタンプを維持し、prev_endをcurrent_endにリセット
            if prev_end_sec >= end_sec:
                print(
                    f"[validate] prev_end({prev_end_sec:.3f}) >= current_end({end_sec:.3f}): "
                    f"前エントリのend不正とみなし元TS維持（{start_raw} --> {end_raw}）",
                    flush=True,
                )
                prev_end_sec = end_sec
                # fall through: このエントリを元のTSで追加
            else:
                print(
                    f"[validate] 重複検出（start={start_sec:.3f} < prev_end={prev_end_sec:.3f}）: "
                    f"{start_raw} → startをprev_endに補正",
                    flush=True,
                )
                # startを前エントリのendに合わせる
                prev_end_s = prev_end_sec
                h = int(prev_end_s // 3600)
                mi = int((prev_end_s % 3600) // 60)
                s = int(prev_end_s % 60)
                ms = int(round((prev_end_s % 1) * 1000))
                start_raw = f"{h:02d}:{mi:02d}:{s:02d},{ms:03d}"
                start_sec = prev_end_sec
                stats["fixed_ts"] += 1
                # 補正後もstart >= endなら除外
                if start_sec >= end_sec:
                    stats["removed_overlap"] += 1
                    continue

        text = "\n".join(lines[2:]).strip()
        valid_entries.append(
            {
                "start_raw": start_raw,
                "end_raw": end_raw,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "text": text,
            }
        )
        prev_end_sec = end_sec
        stats["kept"] += 1

    # SRT再構築（連番振り直し）
    out_lines = []
    for i, e in enumerate(valid_entries, 1):
        out_lines.append(str(i))
        out_lines.append(f"{e['start_raw']} --> {e['end_raw']}")
        out_lines.append(e["text"])
        out_lines.append("")

    validated_text = "\n".join(out_lines).strip() + "\n"

    print(
        f"[validate] 結果: 合計={stats['total']}, 保持={stats['kept']}, "
        f"TS修正={stats['fixed_ts']}, 無効除外={stats['removed_invalid']}, "
        f"start>end除外={stats['removed_start_gt_end']}, 重複除外={stats['removed_overlap']}",
        flush=True,
    )

    return validated_text, stats


def trim_end_hallucination(srt_text: str, trim_seconds: float) -> str:
    """
    動画末尾N秒のエントリのうち、テキストが極端に短い or 繰り返しのものを除外する。
    trim_seconds=0 の場合は何もしない。
    """
    if trim_seconds <= 0:
        return srt_text

    blocks = srt_text.strip().split("\n\n")
    if not blocks:
        return srt_text

    # 最後のエントリのend時刻を取得
    last_end_sec = 0.0
    for block in reversed(blocks):
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        ts_parts = lines[1].split("-->")
        if len(ts_parts) == 2:
            end_sec = _ts_to_seconds(ts_parts[1].strip())
            if end_sec is not None:
                last_end_sec = end_sec
                break

    cutoff = last_end_sec - trim_seconds
    if cutoff <= 0:
        return srt_text

    filtered = []
    removed = 0
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            filtered.append(block)
            continue
        ts_parts = lines[1].split("-->")
        if len(ts_parts) != 2:
            filtered.append(block)
            continue
        start_sec = _ts_to_seconds(ts_parts[0].strip())
        if start_sec is None or start_sec < cutoff:
            filtered.append(block)
            continue
        # 末尾区間のエントリ: テキスト検査
        text = "\n".join(lines[2:]).strip()
        chars = len(text.replace(" ", "").replace("\n", ""))
        if chars <= 5:
            print(f"[trim_end] 短テキスト除外（{chars}文字）: {text!r}", flush=True)
            removed += 1
            continue
        # 繰り返し検出（テキストの文字種が極端に少ない: 例「・・・」「んー」「ー」）
        unique_chars = len(set(text))
        if unique_chars <= 2 and chars >= 3:
            print(f"[trim_end] 繰り返しテキスト除外（ユニーク{unique_chars}文字）: {text!r}", flush=True)
            removed += 1
            continue
        filtered.append(block)

    if removed:
        print(f"[trim_end] 末尾{trim_seconds}秒から{removed}エントリ除外", flush=True)

    # 再構築
    out_lines = []
    idx = 1
    for block in filtered:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        try:
            int(lines[0].strip())
        except ValueError:
            continue
        out_lines.append(str(idx))
        out_lines.extend(lines[1:])
        out_lines.append("")
        idx += 1

    return "\n".join(out_lines).strip() + "\n"


def entries_to_srt(entries: list[dict]) -> str:
    """SRTエントリリストをSRTテキストに変換する（連番振り直し）"""
    out_lines = []
    for i, e in enumerate(entries, 1):
        out_lines.append(str(i))
        out_lines.append(e["timestamp"])
        out_lines.append(e["text"])
        out_lines.append("")
    return "\n".join(out_lines).strip() + "\n"


def align_with_whisperx(srt_entries: list[dict], audio_path: str, device: str | None = None) -> list[dict]:
    """
    WhisperX自身のtranscription+alignmentでms精度タイムスタンプを取得し、
    Geminiエントリのテキストと類似度マッチングでタイムスタンプを転写する。

    Phase A: Word-levelプール構築
    Phase B: Word-levelマッチング（find_longest_match）
    Phase C: N:1 按分マッチング（WhisperXセグメント単位で複数Geminiエントリに按分）
    Phase D: 最終フォールバック（Gemini元値維持）
    """
    try:
        import whisperx
    except ImportError:
        raise ImportError(
            "whisperxが見つかりません。dozle_kirinukiのvenvを有効化してください:\n"
            "  source projects/dozle_kirinuki/venv/bin/activate"
        )
    import torch
    from difflib import SequenceMatcher

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[align] WhisperXタイムスタンプ転写方式開始 (device={device})", flush=True)
    print(f"[align] 対象エントリ数: {len(srt_entries)}", flush=True)

    import numpy as np

    # 全音声をロード（numpy float32 array @ 16kHz）
    audio_full = whisperx.load_audio(audio_path)
    sample_rate = 16000
    total_dur = len(audio_full) / sample_rate
    print(f"[align] 総時間: {total_dur:.1f}秒", flush=True)

    # WhisperXモデルロード
    print("[align] WhisperXモデルロード中...", flush=True)
    wx_model = whisperx.load_model("large-v2", device, language="ja", compute_type="int8_float16")
    align_model, metadata = whisperx.load_align_model(language_code="ja", device=device)
    print("[align] モデルロード完了", flush=True)

    # VRAM節約のためチャンク分割処理（CHUNK_SEC秒単位）
    CHUNK_SEC = 300.0  # 5分チャンク
    chunk_starts = list(np.arange(0, total_dur, CHUNK_SEC))

    # WhisperXセグメントを全チャンクから収集（絶対時刻）
    wx_all_segments: list[dict] = []
    # Phase A: word-levelプール（絶対時刻）
    wx_all_words: list[dict] = []

    for chunk_i, chunk_start in enumerate(chunk_starts):
        chunk_end = chunk_start + CHUNK_SEC
        buf = 1.0
        audio_start = max(0, int((chunk_start - buf) * sample_rate))
        audio_end = min(len(audio_full), int((chunk_end + buf) * sample_rate))
        audio_chunk = audio_full[audio_start:audio_end]
        offset = audio_start / sample_rate

        try:
            # WhisperX自身のtranscription（forced alignmentではなく自前転写）
            result = wx_model.transcribe(audio_chunk, batch_size=4)
            # 転写結果に対してalignment（ms精度）
            align_result = whisperx.align(result["segments"], align_model, metadata, audio_chunk, device)

            for seg in align_result["segments"]:
                words = seg.get("words", [])
                # word-levelの実値を優先してセグメントのstart/endを決定
                start_val = None
                for w in words:
                    w_start = w.get("start")
                    if w_start is not None:
                        start_val = w_start
                        break
                if start_val is None:
                    start_val = seg.get("start")

                end_val = None
                for w in reversed(words):
                    w_end = w.get("end")
                    if w_end is not None:
                        end_val = w_end
                        break
                if end_val is None:
                    end_val = seg.get("end")

                if start_val is not None and end_val is not None:
                    wx_all_segments.append({
                        "start": start_val + offset,
                        "end": end_val + offset,
                        "text": seg.get("text", "").strip(),
                    })

                # Phase A: word-levelプールに追加
                for w in words:
                    if w.get("start") is not None and w.get("end") is not None:
                        wx_all_words.append({
                            "word": w.get("word", ""),
                            "start": w["start"] + offset,
                            "end": w["end"] + offset,
                        })
        except Exception as e:
            print(f"[align] チャンク{chunk_i} transcriptionエラー: {e}", flush=True)

        print(f"[align] チャンク{chunk_i+1}/{len(chunk_starts)} 完了", flush=True)

    print(f"[align] WhisperXセグメント数: {len(wx_all_segments)}", flush=True)
    print(f"[align] WhisperX word数: {len(wx_all_words)}", flush=True)

    if not wx_all_segments:
        print("[align] 警告: WhisperXセグメントが空。元のエントリを返します。", flush=True)
        return srt_entries

    def _sec_to_srt_ts(s: float) -> str:
        h = int(s // 3600)
        mi = int((s % 3600) // 60)
        sec = int(s % 60)
        ms = int(round((s % 1) * 1000))
        if ms >= 1000:
            ms = 999
        return f"{h:02d}:{mi:02d}:{sec:02d},{ms:03d}"

    MATCH_THRESHOLD = 0.3

    wx_sorted = sorted(wx_all_segments, key=lambda s: s["start"])
    updated_entries = list(srt_entries)  # コピー
    phase_b_count = 0
    phase_c_count = 0

    # Phase B対象外（タイムスタンプ解析不能等）のエントリはPhase D直行
    fallback_set: set[int] = set()  # Phase B失敗インデックス

    # Phase B: Word-levelマッチング
    use_word_level = len(wx_all_words) > 50
    wx_concat = ""
    char_to_word_idx: list[int] = []  # 文字位置 → wx_all_words index

    if use_word_level:
        print(f"[align] Phase B: Word-levelマッチング開始 (words={len(wx_all_words)})", flush=True)
        for wi, w in enumerate(wx_all_words):
            word_text = w["word"]
            for _ in word_text:
                char_to_word_idx.append(wi)
            wx_concat += word_text
        print(f"[align] wx_concat長: {len(wx_concat)}文字", flush=True)
    else:
        print("[align] Phase B: word数不足のためスキップ", flush=True)

    # Phase B: monotonic制約 — 前のマッチ末尾より後ろからのみ探索
    search_start_char = 0

    for entry_idx, entry in enumerate(srt_entries):
        ts_parts = entry["timestamp"].split(" --> ")
        if len(ts_parts) != 2:
            fallback_set.add(entry_idx)
            continue

        gemini_start = _ts_to_seconds(ts_parts[0].strip())
        if gemini_start is None:
            fallback_set.add(entry_idx)
            continue

        # 話者ラベルを除去したテキストで比較
        gemini_text = entry["text"]
        if "]: " in gemini_text:
            gemini_text = gemini_text.split("]: ", 1)[-1]
        gemini_text = gemini_text.strip()

        matched = False

        if use_word_level and gemini_text:
            sm = SequenceMatcher(None, gemini_text, wx_concat, autojunk=False)
            # alo=search_start_char: 前エントリのマッチ末尾より後ろのみ探索（monotonic保証）
            match = sm.find_longest_match(0, len(gemini_text), search_start_char, len(wx_concat))
            if match.size > 0 and match.size / len(gemini_text) >= MATCH_THRESHOLD:
                b_char = match.b
                b_char_end = match.b + match.size - 1
                if b_char < len(char_to_word_idx) and b_char_end < len(char_to_word_idx):
                    first_word_idx = char_to_word_idx[b_char]
                    last_word_idx = char_to_word_idx[b_char_end]
                    wx_start = wx_all_words[first_word_idx]["start"]
                    wx_end = wx_all_words[last_word_idx]["end"]
                    if wx_end > wx_start:
                        new_ts = f"{_sec_to_srt_ts(wx_start)} --> {_sec_to_srt_ts(wx_end)}"
                        updated_entries[entry_idx] = {
                            "index": entry["index"],
                            "timestamp": new_ts,
                            "text": entry["text"],
                        }
                        phase_b_count += 1
                        matched = True
                        # monotonic更新: 次のエントリはここより後ろを探索
                        search_start_char = b_char_end + 1

        if not matched:
            fallback_set.add(entry_idx)

    print(f"[align] Phase B完了: {phase_b_count}/{len(srt_entries)}件マッチ", flush=True)

    # Phase C: N:1 按分マッチング
    # fallback_setのエントリのstart時刻を取得
    fallback_starts: dict[int, float | None] = {}
    for fidx in fallback_set:
        entry = srt_entries[fidx]
        ts_parts = entry["timestamp"].split(" --> ")
        if len(ts_parts) == 2:
            gs = _ts_to_seconds(ts_parts[0].strip())
            fallback_starts[fidx] = gs
        else:
            fallback_starts[fidx] = None

    if fallback_set:
        print(f"[align] Phase C: N:1按分マッチング開始 ({len(fallback_set)}件対象)", flush=True)

        PHASE_C_WINDOW = 30.0
        resolved_in_c: set[int] = set()
        # Phase C全体でmonotonic保証: 前のエントリのendより前には割り当てない
        phase_c_prev_end = 0.0

        for seg in wx_sorted:
            wx_seg_start = seg["start"]
            wx_seg_end = seg["end"]

            # このWXセグメントの時間範囲に重なる未解決Geminiエントリを収集
            # entry_idxでソートしてmonotonic保証
            matched_fidxs = sorted(
                [
                    fidx for fidx in fallback_set
                    if fidx not in resolved_in_c
                    and fallback_starts.get(fidx) is not None
                    and wx_seg_start - PHASE_C_WINDOW <= fallback_starts[fidx] <= wx_seg_end + PHASE_C_WINDOW
                ]
            )

            if not matched_fidxs:
                continue

            # 連結テキストとWXセグメントの類似度確認
            gemini_texts_for_c = []
            for fidx in matched_fidxs:
                gt = srt_entries[fidx]["text"]
                if "]: " in gt:
                    gt = gt.split("]: ", 1)[-1]
                gemini_texts_for_c.append(gt.strip())

            combined_gemini = "".join(gemini_texts_for_c)
            ratio = SequenceMatcher(None, combined_gemini, seg["text"]).ratio()

            if ratio < 0.3:
                continue

            # 按分: WXセグメントのstart〜endを文字数比で分割
            total_chars = sum(len(t) for t in gemini_texts_for_c)
            if total_chars == 0:
                continue

            cursor = max(wx_seg_start, phase_c_prev_end)
            for i, fidx in enumerate(matched_fidxs):
                entry = srt_entries[fidx]
                char_share = len(gemini_texts_for_c[i]) / total_chars
                entry_start = cursor
                entry_end = cursor + (wx_seg_end - wx_seg_start) * char_share
                # monotonic保証: endがstartより小さい場合は最小間隔で補正
                if entry_end <= entry_start:
                    entry_end = entry_start + 0.1
                cursor = entry_end

                new_ts = f"{_sec_to_srt_ts(entry_start)} --> {_sec_to_srt_ts(entry_end)}"
                updated_entries[fidx] = {
                    "index": entry["index"],
                    "timestamp": new_ts,
                    "text": entry["text"],
                }
                phase_c_count += 1
                resolved_in_c.add(fidx)
                phase_c_prev_end = entry_end

        print(f"[align] Phase C完了: {phase_c_count}件按分", flush=True)

    # Phase D: 残りはGemini元値維持（updated_entriesにすでに元値が入っているので何もしない）
    phase_d_count = len(fallback_set) - phase_c_count

    print(
        f"[align] タイムスタンプ転写完了: Phase B={phase_b_count}, "
        f"Phase C={phase_c_count}, Phase D(フォールバック)={phase_d_count}",
        flush=True,
    )
    total = len(srt_entries)
    if total > 0:
        fallback_rate = phase_d_count / total * 100
        print(f"[align] フォールバック率: {fallback_rate:.1f}% ({phase_d_count}/{total})", flush=True)

    # 最終バリデーション: 全エントリの時系列順を保証（monotonic後処理）
    # start-vs-start で比較（SRTのstart順が必須）
    violations = 0
    prev_start_final = 0.0
    prev_end_final = 0.0
    for i in range(len(updated_entries)):
        ts_str = updated_entries[i]["timestamp"]
        ts_parts = ts_str.split(" --> ")
        if len(ts_parts) != 2:
            continue
        entry_start = _ts_to_seconds(ts_parts[0].strip())
        entry_end = _ts_to_seconds(ts_parts[1].strip())
        if entry_start is None or entry_end is None:
            continue
        if entry_start < prev_start_final - 1.0:
            # 前エントリのstartより1秒以上逆行 → monotonic補正
            entry_start = max(prev_start_final, prev_end_final)
            entry_end = max(entry_end, entry_start + 0.1)
            updated_entries[i]["timestamp"] = (
                f"{_sec_to_srt_ts(entry_start)} --> {_sec_to_srt_ts(entry_end)}"
            )
            violations += 1
        prev_start_final = entry_start
        prev_end_final = max(prev_end_final, entry_end)
    if violations > 0:
        print(f"[align] Monotonic補正: {violations}件の逆行を修正", flush=True)
    else:
        print("[align] Monotonic検証: 逆行なし ✅", flush=True)

    # サンプル比較（先頭3件）
    for i in range(min(3, len(srt_entries), len(updated_entries))):
        before = srt_entries[i]["timestamp"].split(" --> ")[0]
        after = updated_entries[i]["timestamp"].split(" --> ")[0]
        print(f"[align] サンプル{i+1}: {before} → {after}", flush=True)

    return updated_entries


def identify_speakers_ecapa(
    srt_entries: list[dict],
    audio_path: str,
    profile_dir: str,
    threshold: float = 0.25,
    device: str | None = None,
) -> list[dict]:
    """
    ECAPA-TDNN声紋照合でSRTエントリの話者ラベルを上書きする。
    profile_dir: {member}_embeddings.pt ファイルが置かれたディレクトリ。
    """
    import torch
    import torch.nn.functional as F

    try:
        import torchaudio
    except ImportError:
        raise ImportError("torchaudioが見つかりません。pip install torchaudio")
    try:
        from speechbrain.inference.speaker import EncoderClassifier
    except ImportError:
        raise ImportError(
            "speechbrainが見つかりません。dozle_kirinukiのvenvを有効化してください:\n"
            "  source projects/dozle_kirinuki/venv/bin/activate"
        )

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    profile_path = Path(profile_dir)
    if not profile_path.exists():
        raise FileNotFoundError(f"プロファイルディレクトリが見つかりません: {profile_dir}")

    # プロファイルembedding読み込み（_embeddings.pt優先、なければ_embedding.pt）
    members = {}
    for pt_file in sorted(profile_path.glob("*_embeddings.pt")):
        member_name = pt_file.stem.replace("_embeddings", "")
        emb = torch.load(str(pt_file), weights_only=True)
        if emb.dim() == 2:
            emb = emb.mean(dim=0)  # [N, 192] → [192] 平均
        members[member_name] = emb.to(device)
    if not members:
        for pt_file in sorted(profile_path.glob("*_embedding.pt")):
            member_name = pt_file.stem.replace("_embedding", "")
            emb = torch.load(str(pt_file), weights_only=True)
            members[member_name] = emb.squeeze().to(device)

    if not members:
        print(f"[speaker-profile] 警告: {profile_dir} にembeddingファイルが見つかりません", flush=True)
        return srt_entries

    print(f"[speaker-profile] プロファイルロード: {list(members.keys())}", flush=True)

    # ECAPA-TDNNモデルロード
    savedir = str(profile_path / "pretrained_models" / "spkrec-ecapa-voxceleb")
    print(f"[speaker-profile] ECAPAモデルロード中 (savedir={savedir})...", flush=True)
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=savedir,
        run_opts={"device": str(device)},
    )
    print(f"[speaker-profile] ECAPAモデルロード完了 (device={device})", flush=True)

    # 音声ロード（16kHz mono）
    waveform, sr = torchaudio.load(audio_path)
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        waveform = resampler(waveform)
        sr = 16000
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    MIN_SAMPLES = 8000  # 0.5秒以上（16kHz）

    updated_entries = []
    matched = 0
    unknown_count = 0
    skip_count = 0

    for entry in srt_entries:
        ts_parts = entry["timestamp"].split(" --> ")
        if len(ts_parts) != 2:
            updated_entries.append(entry)
            skip_count += 1
            continue

        start_sec = _ts_to_seconds(ts_parts[0].strip())
        end_sec = _ts_to_seconds(ts_parts[1].strip())

        if start_sec is None or end_sec is None or (end_sec - start_sec) < 0.5:
            updated_entries.append(entry)
            skip_count += 1
            continue

        # 音声セグメント抽出
        start_sample = int(start_sec * sr)
        end_sample = min(int(end_sec * sr), waveform.shape[1])
        seg_audio = waveform[:, start_sample:end_sample]

        if seg_audio.shape[1] < MIN_SAMPLES:
            updated_entries.append(entry)
            skip_count += 1
            continue

        # ECAPA embedding計算
        seg_signal = seg_audio.squeeze()
        seg_embedding = classifier.encode_batch(seg_signal.unsqueeze(0)).squeeze().to(device)

        # コサイン類似度で照合
        similarities = {}
        for member_name, ref_emb in members.items():
            sim = F.cosine_similarity(
                seg_embedding.unsqueeze(0), ref_emb.unsqueeze(0)
            ).item()
            similarities[member_name] = sim

        best_member = max(similarities, key=similarities.get)
        best_sim = similarities[best_member]
        assigned = best_member if best_sim >= threshold else "unknown"

        if assigned == "unknown":
            unknown_count += 1
            updated_entries.append(entry)
        else:
            matched += 1
            text = entry["text"]
            # 話者ラベルを上書き（既存ラベルがある場合は置換）
            if "]: " in text:
                new_text = f"[{assigned}]: " + text.split("]: ", 1)[1]
            else:
                new_text = f"[{assigned}]: " + text
            updated_entries.append(
                {"index": entry["index"], "timestamp": entry["timestamp"], "text": new_text}
            )

    print(
        f"[speaker-profile] 照合完了: 一致={matched}, unknown={unknown_count}, スキップ={skip_count}",
        flush=True,
    )

    # サンプル表示（先頭3件）
    for i in range(min(3, len(srt_entries), len(updated_entries))):
        before = srt_entries[i]["text"][:60]
        after = updated_entries[i]["text"][:60]
        if before != after:
            print(f"[speaker-profile] 更新{i+1}: {before!r} → {after!r}", flush=True)

    return updated_entries


def parse_srt(srt_text: str) -> list[dict]:
    """SRTテキストをエントリリストに変換する"""
    entries = []
    blocks = srt_text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        try:
            idx = int(lines[0].strip())
            timestamp = lines[1].strip()
            text = "\n".join(lines[2:]).strip()
            entries.append({"index": idx, "timestamp": timestamp, "text": text})
        except (ValueError, IndexError):
            continue
    return entries


def srt_timestamp_to_seconds(ts: str) -> float:
    """'HH:MM:SS,mmm' を秒数に変換"""
    try:
        ts = ts.split(" --> ")[0].strip()
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0
    except Exception:
        return 0.0


def compare_srt(gemini_srt: str, whisperx_path: str) -> str:
    """WhisperX SRT と Gemini SRT を比較してレポートを返す"""
    gemini_entries = parse_srt(gemini_srt)

    whisperx_text = Path(whisperx_path).read_text(encoding="utf-8")
    whisperx_entries = parse_srt(whisperx_text)

    lines = [
        "=== WhisperX vs Gemini 比較レポート ===",
        f"エントリ数: WhisperX={len(whisperx_entries)}, Gemini={len(gemini_entries)}",
    ]

    # タイムスタンプのずれ計算（エントリ数が少ない方に合わせる）
    n = min(len(whisperx_entries), len(gemini_entries))
    if n > 0:
        diffs = []
        for i in range(n):
            wx_start = srt_timestamp_to_seconds(whisperx_entries[i]["timestamp"])
            gm_start = srt_timestamp_to_seconds(gemini_entries[i]["timestamp"])
            diffs.append(abs(wx_start - gm_start))
        avg_diff = sum(diffs) / len(diffs)
        max_diff = max(diffs)
        lines.append(f"タイムスタンプのずれ（先頭{n}エントリ）: 平均={avg_diff:.2f}s, 最大={max_diff:.2f}s")

    # テキスト類似度（共通語数/全語数）
    gemini_words = set(" ".join(e["text"] for e in gemini_entries).split())
    whisperx_words = set(" ".join(e["text"] for e in whisperx_entries).split())
    if gemini_words or whisperx_words:
        common = len(gemini_words & whisperx_words)
        total = len(gemini_words | whisperx_words)
        similarity = common / total if total > 0 else 0.0
        lines.append(f"テキスト類似度（Jaccard）: {similarity:.3f} ({common}/{total} 単語共通)")

    # 先頭5エントリのサンプル
    lines.append("\n--- Gemini先頭5エントリ ---")
    for e in gemini_entries[:5]:
        lines.append(f"  [{e['timestamp']}] {e['text'][:80]}")

    lines.append("\n--- WhisperX先頭5エントリ ---")
    for e in whisperx_entries[:5]:
        lines.append(f"  [{e['timestamp']}] {e['text'][:80]}")

    return "\n".join(lines)


def calc_cost(usage_metadata, model: str) -> str:
    """usage_metadata からコストを計算する"""
    try:
        input_tokens = getattr(usage_metadata, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage_metadata, "candidates_token_count", 0) or 0

        # Gemini 3 Flash 料金（2026-03時点の仮定値）
        # $0.10/1M input tokens, $0.40/1M output tokens
        input_cost = input_tokens / 1_000_000 * 0.10
        output_cost = output_tokens / 1_000_000 * 0.40
        total_cost = input_cost + output_cost

        return (
            f"入力トークン: {input_tokens:,}\n"
            f"出力トークン: {output_tokens:,}\n"
            f"コスト: ${total_cost:.4f} (入力: ${input_cost:.4f}, 出力: ${output_cost:.4f})"
        )
    except Exception as e:
        return f"コスト計算エラー: {e}"


def main():
    parser = argparse.ArgumentParser(description="Gemini動画理解APIによる字幕生成PoC")
    parser.add_argument("video_path", nargs="?", help="入力動画ファイルパス（--validate-only時は省略可）")
    parser.add_argument("--output", "-o", required=True, help="出力SRTファイルパス")
    parser.add_argument(
        "--model", default="gemini-3-flash-preview", help="使用モデル（デフォルト: gemini-3-flash-preview）"
    )
    parser.add_argument("--compare", help="比較対象のWhisperX SRTファイルパス")
    parser.add_argument(
        "--trim-end",
        type=float,
        default=0,
        metavar="SECONDS",
        help="末尾N秒の短い/繰り返しエントリを除外（デフォルト: 0=無効）",
    )
    parser.add_argument(
        "--validate-only",
        metavar="SRT_FILE",
        help="既存SRTファイルのバリデーションのみ実施（動画アップロード不要）",
    )
    parser.add_argument(
        "--input-srt",
        metavar="SRT_FILE",
        help="既存SRTファイルを入力として使用（Gemini APIをスキップ）",
    )
    parser.add_argument(
        "--align",
        action="store_true",
        help="WhisperXでタイムスタンプをミリ秒精度にアライン",
    )
    parser.add_argument(
        "--speaker-profile",
        metavar="PROFILE_DIR",
        help="ECAPA-TDNN声紋照合用プロファイルディレクトリ（{member}_embeddings.pt格納先）",
    )
    args = parser.parse_args()

    # --validate-only モード
    if args.validate_only:
        srt_text = Path(args.validate_only).read_text(encoding="utf-8")
        print(f"[validate-only] 入力: {args.validate_only}", flush=True)

        validated_text, stats = validate_srt(srt_text)

        if args.trim_end > 0:
            validated_text = trim_end_hallucination(validated_text, args.trim_end)

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(validated_text, encoding="utf-8")
        print(f"[output] バリデーション済みSRT保存: {output_path}", flush=True)

        entries = parse_srt(validated_text)
        print(f"[result] バリデーション後SRTエントリ数: {len(entries)}", flush=True)
        return 0

    # --input-srt モード: 既存SRTを使用してGemini APIをスキップ
    if args.input_srt:
        srt_text = Path(args.input_srt).read_text(encoding="utf-8")
        print(f"[input-srt] 入力SRT読み込み: {args.input_srt}", flush=True)
        validated_text, stats = validate_srt(srt_text)

        # 後処理: --align
        if args.align:
            if not args.video_path:
                parser.error("--align には video_path が必要です")
            entries = parse_srt(validated_text)
            entries = align_with_whisperx(entries, args.video_path)
            validated_text = entries_to_srt(entries)

        # 後処理: --speaker-profile
        if args.speaker_profile:
            if not args.video_path:
                parser.error("--speaker-profile には video_path が必要です")
            entries = parse_srt(validated_text)
            entries = identify_speakers_ecapa(entries, args.video_path, args.speaker_profile)
            validated_text = entries_to_srt(entries)

        if args.trim_end > 0:
            validated_text = trim_end_hallucination(validated_text, args.trim_end)

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(validated_text, encoding="utf-8")
        print(f"[output] SRT保存: {output_path}", flush=True)

        entries = parse_srt(validated_text)
        print(f"[result] SRTエントリ数: {len(entries)}", flush=True)

        if args.compare:
            report = compare_srt(validated_text, args.compare)
            print(f"\n{report}", flush=True)

        return 0

    if not args.video_path:
        parser.error("video_path は --validate-only / --input-srt なしの場合に必須です")

    # google-genai クライアント初期化
    from google import genai

    client = genai.Client()

    # 動画アップロード
    video_file = upload_video(client, args.video_path)

    # 字幕生成
    srt_text, response = generate_subtitles(client, video_file, args.model)

    # SRTバリデーション
    validated_text, stats = validate_srt(srt_text)

    # 後処理: --align
    if args.align:
        entries = parse_srt(validated_text)
        entries = align_with_whisperx(entries, args.video_path)
        validated_text = entries_to_srt(entries)

    # 後処理: --speaker-profile
    if args.speaker_profile:
        entries = parse_srt(validated_text)
        entries = identify_speakers_ecapa(entries, args.video_path, args.speaker_profile)
        validated_text = entries_to_srt(entries)

    # 末尾ハルシネーション対策
    if args.trim_end > 0:
        validated_text = trim_end_hallucination(validated_text, args.trim_end)

    # SRT保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(validated_text, encoding="utf-8")
    print(f"[output] SRT保存: {output_path}", flush=True)

    # エントリ数表示
    entries = parse_srt(validated_text)
    print(f"[result] SRTエントリ数: {len(entries)} (バリデーション修正件数: {stats['fixed_ts']})", flush=True)

    # コスト計測
    cost_info = calc_cost(response.usage_metadata, args.model)
    print(f"[cost]\n{cost_info}", flush=True)

    # 比較レポート
    if args.compare:
        report = compare_srt(validated_text, args.compare)
        print(f"\n{report}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
