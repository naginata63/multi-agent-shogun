#!/usr/bin/env python3
"""Gemini動画理解APIによるショートネタ提案・ハイライトスクリーニング"""

import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml


def upload_video(client, video_path: str):
    """File APIで動画をアップロードし、処理完了を待つ"""
    print(f"[upload] アップロード開始: {video_path}", flush=True)
    video_file = client.files.upload(file=video_path)
    print(f"[upload] ファイル名: {video_file.name} 状態: {video_file.state.name}", flush=True)

    while video_file.state.name == "PROCESSING":
        print("[upload] 処理中... 10秒待機", flush=True)
        time.sleep(10)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name != "ACTIVE":
        raise RuntimeError(f"ファイルが ACTIVE になりませんでした: {video_file.state.name}")

    print(f"[upload] 完了: {video_file.name}", flush=True)
    return video_file


def calc_cost(usage_metadata, model: str) -> dict:
    """usage_metadata からコスト情報を返す"""
    try:
        input_tokens = getattr(usage_metadata, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage_metadata, "candidates_token_count", 0) or 0
        # Gemini 2.0 Flash 料金（2026-03時点の仮定値）
        input_cost = input_tokens / 1_000_000 * 0.10
        output_cost = output_tokens / 1_000_000 * 0.40
        total_cost = input_cost + output_cost
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost": f"${total_cost:.4f}",
        }
    except Exception as e:
        return {"error": str(e)}


def extract_yaml_block(text: str) -> str:
    """```yaml ... ``` マーカーを除去してYAML文字列を返す"""
    # ```yaml ... ``` または ``` ... ``` を検索（closing ``` あり）
    match = re.search(r"```(?:yaml)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # closing ``` がない場合: ```yaml 以降をすべて取得
    match = re.search(r"```(?:yaml)?\s*(.*)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # コードブロックなし: candidates: 以降を取得
    match = re.search(r"(candidates:.*)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def parse_partial_yaml_candidates(yaml_text: str) -> list:
    """部分的なYAMLから完全な候補エントリを正規表現で抽出する（インデント保持）"""
    # "  - id: N" ブロックをそれぞれ抽出（次の "  - id:" またはEOSまで）
    candidate_blocks = re.findall(
        r"(  - id:\s*\d+.*?)(?=\n  - id:|\Z)",
        yaml_text,
        re.DOTALL,
    )
    candidates = []
    for block in candidate_blocks:
        # candidates: ラッパーで元のインデントを保持してパース
        test_yaml = f"candidates:\n{block}"
        try:
            parsed = yaml.safe_load(test_yaml)
            if parsed and "candidates" in parsed and parsed["candidates"]:
                candidates.append(parsed["candidates"][0])
        except Exception:
            pass
    return candidates


def cmd_short_ideas(args):
    """short-ideas: 動画からショート動画候補を提案"""
    from google import genai
    from google.genai import types as genai_types

    client = genai.Client()

    video_file = upload_video(client, args.video_path)

    model = args.model
    top_n = args.top

    prompt = f"""この動画を分析して、9:16縦型ショート動画として切り出すのに最適なシーンを{top_n}件提案してください。

要件:
- 15〜60秒の長さで切り出せるシーン
- 面白い瞬間、リアクション、サプライズ要素、オヤジギャグ、ボケツッコミを優先
- 各候補にタイムスタンプ（開始-終了）、理由、推奨タイトルを含める
- ショート動画のフック（冒頭3秒で視聴者を引き付ける要素）を明記
- バイラル性（SNSでシェアされやすさ）を5段階で評価

出力形式（YAMLのみ。説明文は不要）:
candidates:
  - id: 1
    start_time: "MM:SS"
    end_time: "MM:SS"
    duration_sec: 30
    title: "推奨タイトル"
    hook: "冒頭フックの説明"
    reason: "選出理由"
    speakers: ["話者名"]
    viral_score: 4
    category: "ギャグ/リアクション/サプライズ/感動/その他"
"""

    print(f"[generate] モデル: {model}", flush=True)
    response = client.models.generate_content(
        model=model,
        contents=[video_file, prompt],
        config=genai_types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
        ),
    )

    raw_text = response.text
    print(f"[generate] レスポンス長: {len(raw_text)} 文字", flush=True)

    # YAMLパース
    yaml_text = extract_yaml_block(raw_text)
    try:
        data = yaml.safe_load(yaml_text)
        if not isinstance(data, dict) or "candidates" not in data:
            raise ValueError("candidatesキーが見つかりません")
        candidates = data["candidates"]
    except Exception as e:
        print(f"[warn] YAMLパース失敗: {e} — 部分パースを試みる", flush=True)
        candidates = parse_partial_yaml_candidates(yaml_text)
        if candidates:
            print(f"[info] 部分パースで {len(candidates)} 件の候補を取得", flush=True)
            raw_fallback = None
        else:
            print(f"[raw]\n{raw_text[:500]}", flush=True)
            candidates = []
            raw_fallback = raw_text

    cost = calc_cost(response.usage_metadata, model)

    output = {
        "metadata": {
            "video_path": str(args.video_path),
            "model": model,
            "top": top_n,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost": cost,
        },
        "candidates": candidates,
    }
    if raw_fallback:
        output["raw_response"] = raw_fallback

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[output] 保存: {output_path}", flush=True)
    print(f"[result] 候補数: {len(candidates)}", flush=True)
    print(f"[cost] 入力: {cost.get('input_tokens', '?')} トークン, 出力: {cost.get('output_tokens', '?')} トークン, 合計: {cost.get('total_cost', '?')}", flush=True)

    if candidates:
        print("\n=== Top3 候補 ===", flush=True)
        for c in candidates[:3]:
            print(f"  [{c.get('start_time', '?')}-{c.get('end_time', '?')}] {c.get('title', '?')} (viral={c.get('viral_score', '?')})", flush=True)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Gemini動画理解APIによるショートネタ提案")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # short-ideas サブコマンド
    p_ideas = subparsers.add_parser("short-ideas", help="動画からショート動画候補を提案")
    p_ideas.add_argument("video_path", help="入力動画ファイルパス")
    p_ideas.add_argument("--output", "-o", required=True, help="出力YAMLファイルパス")
    p_ideas.add_argument("--top", "-n", type=int, default=10, help="提案数（デフォルト: 10）")
    p_ideas.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="使用モデル（デフォルト: gemini-2.0-flash）",
    )
    p_ideas.set_defaults(func=cmd_short_ideas)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
