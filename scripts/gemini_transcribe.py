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

    if not args.video_path:
        parser.error("video_path は --validate-only なしの場合に必須です")

    # google-genai クライアント初期化
    from google import genai

    client = genai.Client()

    # 動画アップロード
    video_file = upload_video(client, args.video_path)

    # 字幕生成
    srt_text, response = generate_subtitles(client, video_file, args.model)

    # SRTバリデーション
    validated_text, stats = validate_srt(srt_text)

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
