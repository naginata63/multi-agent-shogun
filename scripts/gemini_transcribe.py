#!/usr/bin/env python3
"""Gemini動画理解APIによる字幕生成PoC"""

import argparse
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
        "- タイムスタンプは HH:MM:SS,mmm 形式\n"
        "- 話者が変わったら新しいエントリにする\n"
        "- 可能なら話者名を [speaker_name]: 形式で先頭に付ける\n"
        "- ゲーム実況動画なので、ゲーム内SE/BGMは無視し発話のみ\n"
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
    parser.add_argument("video_path", help="入力動画ファイルパス")
    parser.add_argument("--output", "-o", required=True, help="出力SRTファイルパス")
    parser.add_argument(
        "--model", default="gemini-3-flash-preview", help="使用モデル（デフォルト: gemini-3-flash-preview）"
    )
    parser.add_argument("--compare", help="比較対象のWhisperX SRTファイルパス")
    args = parser.parse_args()

    # google-genai クライアント初期化
    from google import genai

    client = genai.Client()

    # 動画アップロード
    video_file = upload_video(client, args.video_path)

    # 字幕生成
    srt_text, response = generate_subtitles(client, video_file, args.model)

    # SRT保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(srt_text, encoding="utf-8")
    print(f"[output] SRT保存: {output_path}", flush=True)

    # エントリ数表示
    entries = parse_srt(srt_text)
    print(f"[result] SRTエントリ数: {len(entries)}", flush=True)

    # コスト計測
    cost_info = calc_cost(response.usage_metadata, args.model)
    print(f"[cost]\n{cost_info}", flush=True)

    # 比較レポート
    if args.compare:
        report = compare_srt(srt_text, args.compare)
        print(f"\n{report}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
