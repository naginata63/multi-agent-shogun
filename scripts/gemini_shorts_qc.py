#!/usr/bin/env python3
"""gemini_shorts_qc.py — Gemini画像理解APIによるショート動画QCスクリプト

使用法:
  python3 scripts/gemini_shorts_qc.py <shorts_video_path> [--output-yaml <path>]

コスト目標: $0.02/本以下 (gemini-2.5-flash使用)
"""

import argparse
import json  # LOW-L2: トップレベルに移動（元は関数内でimport）
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

MODEL = "gemini-2.5-flash"

QC_PROMPT = """これはYouTube Shortsの縦型動画（1080x1920）のフレームです。
以下のQCチェック項目を評価してください。

【QCチェック項目】
1. **テキスト可読性**: フックテキスト・サブフックテキストが読めるか（フォントサイズ・色・コントラスト）
2. **レイアウトバランス**: キャラクター立ち絵の位置・余白が適切か
3. **立ち絵の切れ**: キャラクターが画面端で切れていないか
4. **黒帯・余白**: 不自然な黒帯や余白が目立っていないか
5. **視覚的インパクト**: 全体的に視聴者の目を引く構成になっているか

【出力形式】（必ずこの形式で回答すること）
VERDICT: PASS または FAIL
SCORE: 1-10（10が最高）
ISSUES:
- 問題点1（なければ「なし」）
- 問題点2
SUGGESTIONS:
- 改善提案1（なければ「なし」）
- 改善提案2

各フレーム（冒頭・中盤・終盤）を総合的に判断してください。
1つでも重大な問題があればFAIL、軽微な問題のみであればPASSとしてください。"""


def extract_frames(video_path: str, output_dir: str) -> list[str]:
    """ffmpegで冒頭・中盤・終盤の3フレームを抽出する"""
    # 動画の長さを取得
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", video_path
        ],
        capture_output=True, text=True, check=True
    )
    probe = json.loads(result.stdout)
    duration = None
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            duration = float(stream.get("duration", 0))
            break
    if duration is None or duration <= 0:  # MEDIUM-M1: 0.0(falsy)の誤捕捉を防ぐ
        # フォールバック: format から取得
        result2 = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
            capture_output=True, text=True, check=True
        )
        fmt = json.loads(result2.stdout)
        duration = float(fmt.get("format", {}).get("duration", 10))
    if duration <= 0:
        raise ValueError(f"動画の長さが取得できません: {video_path}")

    timestamps = [
        min(1.0, duration * 0.05),           # 冒頭（5%地点 or 1秒）
        duration * 0.5,                        # 中盤（50%）
        max(duration - 1.0, duration * 0.95), # 終盤（95%地点）
    ]

    frame_paths = []
    for i, ts in enumerate(timestamps):
        out_path = os.path.join(output_dir, f"frame_{i:02d}.jpg")
        # 2段階シーク: キーフレーム精度→フレーム精度 (cmd_901)
        _ts_pre = max(0.0, ts - 30.0)
        _ts_fine = ts - _ts_pre
        subprocess.run(
            [
                "ffmpeg", "-y", "-ss", str(_ts_pre),
                "-i", video_path,
                "-ss", str(_ts_fine),
                "-vframes", "1",
                "-q:v", "3",
                out_path
            ],
            capture_output=True, check=True
        )
        frame_paths.append(out_path)
        print(f"[frame] ts={ts:.1f}s → {out_path}", flush=True)

    if not frame_paths:  # LOW-L4: フレーム抽出失敗時のガード
        raise RuntimeError(f"フレーム抽出に失敗しました: {video_path}")

    return frame_paths


def calc_cost(usage_metadata) -> dict:
    """usage_metadata からコスト情報を返す"""
    try:
        input_tokens = getattr(usage_metadata, "prompt_token_count", None) or 0  # LOW-L3: Noneセーフ
        output_tokens = getattr(usage_metadata, "candidates_token_count", None) or 0
        # MEDIUM-M2: gemini-2.5-flash 料金（2026-03時点）
        # 入力: $0.15/1M tokens、出力: $0.60/1M tokens（画像は別途加算されるが概算）
        input_cost = input_tokens / 1_000_000 * 0.15
        output_cost = output_tokens / 1_000_000 * 0.60
        total_cost = input_cost + output_cost
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost_usd": round(total_cost, 5),
        }
    except Exception:
        return {"input_tokens": 0, "output_tokens": 0, "total_cost_usd": 0.0}


def parse_qc_response(text: str) -> dict:
    """QC応答テキストをパースしてdict返す"""
    result = {
        "verdict": "UNKNOWN",
        "score": None,
        "issues": [],
        "suggestions": [],
        "raw": text,
    }

    lines = text.strip().split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if line.startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip().upper()
            result["verdict"] = "PASS" if "PASS" in verdict else "FAIL"
        elif line.startswith("SCORE:"):
            try:
                # LOW-L3: "8/10" "8 (優良)" など複数フォーマットに対応
                score_raw = line.split(":", 1)[1].strip().split("/")[0].split()[0]
                result["score"] = int(score_raw)
            except (ValueError, IndexError):
                pass
        elif line.startswith("ISSUES:"):
            current_section = "issues"
        elif line.startswith("SUGGESTIONS:"):
            current_section = "suggestions"
        elif line.startswith("- ") and current_section:
            content = line[2:].strip()
            if content and content != "なし":
                result[current_section].append(content)

    return result


def run_qc(video_path: str, output_yaml: str | None = None) -> dict:
    """メインQC処理"""
    from google import genai
    from google.genai import types as genai_types

    client = genai.Client()

    video_path = os.path.abspath(video_path)
    print(f"[qc] 対象: {video_path}", flush=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        # フレーム抽出
        print("[qc] フレーム抽出中...", flush=True)
        frame_paths = extract_frames(video_path, tmpdir)

        # 画像をAPIに投入
        print(f"[qc] Gemini API呼び出し (model={MODEL})...", flush=True)
        parts = []
        labels = ["冒頭", "中盤", "終盤"]
        for i, fp in enumerate(frame_paths):
            with open(fp, "rb") as f:
                img_bytes = f.read()
            parts.append(genai_types.Part.from_text(text=f"【フレーム{i+1}: {labels[i]}】"))
            parts.append(genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

        parts.append(genai_types.Part.from_text(text=QC_PROMPT))

        response = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=genai_types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )

    response_text = response.text
    print(f"\n[qc] Gemini応答:\n{response_text}\n", flush=True)

    # パース
    qc_result = parse_qc_response(response_text)

    # コスト計算
    cost_info = calc_cost(response.usage_metadata)
    qc_result["cost"] = cost_info

    print(f"[qc] 判定: {qc_result['verdict']}  スコア: {qc_result['score']}/10", flush=True)
    print(f"[qc] コスト: ${cost_info['total_cost_usd']:.5f} "
          f"(in={cost_info['input_tokens']}, out={cost_info['output_tokens']})", flush=True)

    # YAML出力
    if output_yaml:
        out_data = {
            "timestamp": datetime.now().isoformat(),
            "video_path": video_path,
            "model": MODEL,
            "verdict": qc_result["verdict"],
            "score": qc_result["score"],
            "issues": qc_result["issues"],
            "suggestions": qc_result["suggestions"],
            "cost_usd": cost_info["total_cost_usd"],
            "input_tokens": cost_info["input_tokens"],
            "output_tokens": cost_info["output_tokens"],
            "raw_response": response_text,
        }
        out_path = Path(output_yaml)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(out_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"[qc] YAML出力: {output_yaml}", flush=True)

    return qc_result


def main():
    parser = argparse.ArgumentParser(description="Gemini APIによるショート動画QC")
    parser.add_argument("video_path", help="ショート動画ファイルパス")
    parser.add_argument("--output-yaml", help="QC結果YAMLの出力先", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.video_path):
        print(f"[error] ファイルが見つかりません: {args.video_path}", file=sys.stderr)
        sys.exit(1)

    result = run_qc(args.video_path, args.output_yaml)

    # 終了コード: PASS=0, FAIL/UNKNOWN=1
    verdict = result.get("verdict", "UNKNOWN")
    if verdict == "PASS":
        print("\n✅ QC PASS", flush=True)
        sys.exit(0)
    else:
        print(f"\n❌ QC {verdict}", flush=True)
        if result.get("issues"):
            print("Issues:", flush=True)
            for issue in result["issues"]:
                print(f"  - {issue}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
