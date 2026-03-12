#!/usr/bin/env python3
"""Gemini動画理解APIによるショートネタ提案・ハイライトスクリーニング"""

import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ドズル社メンバー情報（プロンプト共通）
MEMBER_INFO = """このYouTubeチャンネルのメンバー:
- ドズル (dozle): チャンネル主、MC役
- ぼんじゅうる (bon): ボケ・ギャグ担当
- おんりー (qnly): ツッコミ担当
- おらふくん (orafu): 天然担当
- おおはらMEN (oo_men): リアクション担当
- ネコおじ/三木 (nekooji): ナレーター、色々な声色で出演

マイクラ内プレイヤーID → メンバー名:
- Dooozle → dozle（ドズル）
- bonj55 → bon（ぼんじゅうる）
- ORAMAINECRAF → orafu（おらふくん）
- Only_qdm → qnly（おんりー）
- ooharaMEN → oo_men（おおはらMEN）
- Neko_Oji → nekooji（ネコおじ/三木）
これらのIDがゲーム画面に表示されている場合、対応するメンバー名（キー名）に変換して出力すること。
話者名は上記の括弧内のキー名(dozle/bon/qnly/orafu/oo_men/nekooji)で出力すること。"""


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
        # Gemini 3 Flash 料金（2026-03時点の仮定値）
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


def parse_candidates_robust(raw_text: str, yaml_text: str) -> list:
    """複数の方法でcandidatesリストをパースする（BUG-1対策）"""
    # 方法1: 全体パース
    try:
        data = yaml.safe_load(yaml_text)
        if isinstance(data, dict) and "candidates" in data:
            items = data["candidates"]
            if isinstance(items, list) and len(items) > 0:
                return items
    except Exception:
        pass

    # 方法2: 生テキストから candidates: セクションを抽出して再パース
    section_match = re.search(r"(candidates:\s*\n(?:[ \t]+.*\n?)+)", raw_text, re.MULTILINE)
    if section_match:
        try:
            data = yaml.safe_load(section_match.group(1))
            if isinstance(data, dict) and "candidates" in data:
                items = data["candidates"]
                if isinstance(items, list) and len(items) > 0:
                    return items
        except Exception:
            pass

    # 方法3: 部分パース（インデントブロック単位）
    candidates = parse_partial_yaml_candidates(yaml_text)
    if candidates:
        print(f"[info] 部分パースで {len(candidates)} 件の候補を取得", flush=True)
        return candidates

    # 方法4: 生テキストから直接ブロック抽出
    candidates = parse_partial_yaml_candidates(raw_text)
    if candidates:
        print(f"[info] 生テキスト部分パースで {len(candidates)} 件の候補を取得", flush=True)
        return candidates

    return []


def extract_section_yaml(text: str, section_key: str) -> list:
    """レスポンステキストから指定セクション(highlight_candidates/short_candidates)を抽出"""
    # 行頭のsection_keyから次のトップレベルキー（行頭の\w+:）まで抽出（MULTILINEで行頭マッチ）
    match = re.search(rf"^({section_key}:.*?)(?=^\w|\Z)", text, re.DOTALL | re.MULTILINE)
    if not match:
        return []
    section_text = match.group(1).strip()
    try:
        data = yaml.safe_load(section_text)
        if isinstance(data, dict) and section_key in data:
            items = data[section_key]
            return items if isinstance(items, list) else []
        return []
    except Exception:
        return []


def cmd_screen(args):
    """screen: 動画からハイライト候補とショート候補を同時提案（統合スクリーニング）"""
    from google import genai
    from google.genai import types as genai_types

    client = genai.Client()

    video_file = upload_video(client, args.video_path)

    model = args.model

    prompt = f"""この動画を分析して、切り抜き動画用の候補を2種類提案してください。

{MEMBER_INFO}

## ハイライト候補（長尺切り抜き）
- 3〜10分の見どころシーン
- 笑い・感動・盛り上がり・企画のクライマックスを優先
- **必ず**ハイライト候補を**5件以上**含めること。0件は不可。
- ハイライト候補が見つからない場合でも、比較的盛り上がるシーンを5件選んで提案すること
- スコア（1-10の整数）で評価。全候補が同じスコアにならないよう相対評価すること

## ショート候補（バズ系縦型ショート）
- 各候補は15秒以上60秒以下の区間を選ぶこと。短すぎる候補（15秒未満）は不可
- 冒頭3秒で視聴者を引き付けるフックが必要
- オヤジギャグ・ボケツッコミ・サプライズ・リアクションを優先
- 5〜10件提案
- バイラルスコア（1-10の整数）で評価。最高スコアは1件のみ、最低スコアの候補も含めること

出力形式（YAMLのみ。説明文は不要）:
highlight_candidates:
  - start: "MM:SS"
    end: "MM:SS"
    title: "タイトル"
    reason: "選出理由"
    speakers: ["話者キー名"]
    score: 9
short_candidates:
  - start: "MM:SS"
    end: "MM:SS"
    title: "タイトル"
    hook: "冒頭フックの説明"
    reason: "選出理由"
    speakers: ["話者キー名"]
    viral_score: 9
"""

    print(f"[generate] モデル: {model}", flush=True)
    t0 = time.time()
    response = client.models.generate_content(
        model=model,
        contents=[video_file, prompt],
        config=genai_types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
        ),
    )
    elapsed = time.time() - t0

    raw_text = response.text
    print(f"[generate] レスポンス長: {len(raw_text)} 文字 ({elapsed:.1f}s)", flush=True)
    print(f"[screen] 生レスポンス（先頭2000文字）:\n{raw_text[:2000]}", flush=True)

    # YAMLブロック抽出
    yaml_text = extract_yaml_block(raw_text)

    # 全体パースを試みる
    highlight_candidates = []
    short_candidates = []
    try:
        data = yaml.safe_load(yaml_text)
        if isinstance(data, dict):
            highlight_candidates = data.get("highlight_candidates", []) or []
            short_candidates = data.get("short_candidates", []) or []
    except Exception as e:
        print(f"[warn] YAMLパース失敗: {e} — セクション別パースを試みる", flush=True)
        highlight_candidates = extract_section_yaml(raw_text, "highlight_candidates")
        short_candidates = extract_section_yaml(raw_text, "short_candidates")

    # BUG-S1: HL候補0件のフォールバック（extract_yaml_blockのpartial match対策）
    # extract_yaml_blockの3番目フォールバック "candidates:" が "highlight_candidates:" を部分マッチして
    # "highlight_" プレフィックスを切り落とす場合があるため、HL=0件ならセクション別パースで再試行
    if not highlight_candidates:
        hl = extract_section_yaml(raw_text, "highlight_candidates")
        if hl:
            print(f"[info] セクション別パースでHL {len(hl)} 件を回収（partial match対策）", flush=True)
            highlight_candidates = hl
        else:
            print("[warn] HL候補が0件です。プロンプトの指示が無視された可能性があります。", flush=True)
    if not short_candidates:
        sc = extract_section_yaml(raw_text, "short_candidates")
        if sc:
            print(f"[info] セクション別パースでSH {len(sc)} 件を回収", flush=True)
            short_candidates = sc

    # BUG-S2: SH候補15秒未満・60秒超を自動除外
    def parse_mmss(ts: str) -> float:
        """'MM:SS' または 'H:MM:SS' 形式を秒数に変換"""
        try:
            parts = str(ts).strip().split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except Exception:
            pass
        return -1

    valid_shorts = []
    for candidate in short_candidates:
        start_sec = parse_mmss(candidate.get("start", ""))
        end_sec = parse_mmss(candidate.get("end", ""))
        if start_sec < 0 or end_sec < 0:
            print(f"[warn] SH候補 '{candidate.get('title', '')}' のタイムスタンプ解析失敗 (start={candidate.get('start')}, end={candidate.get('end')}) — 除外", flush=True)
            continue
        duration = end_sec - start_sec
        if duration < 15:
            print(f"[warn] SH候補 '{candidate.get('title', '')}' は{duration:.0f}秒で15秒未満のため除外", flush=True)
            continue
        if duration > 60:
            print(f"[warn] SH候補 '{candidate.get('title', '')}' は{duration:.0f}秒で60秒超のため除外", flush=True)
            continue
        valid_shorts.append(candidate)
    excluded_shorts = len(short_candidates) - len(valid_shorts)
    if excluded_shorts > 0:
        print(f"[info] SH候補 {excluded_shorts}件を尺バリデーションで除外 ({len(valid_shorts)}件残)", flush=True)
    short_candidates = valid_shorts

    cost = calc_cost(response.usage_metadata, model)

    # video_id をパスから抽出（ファイル名の拡張子除去）
    video_path = Path(args.video_path)
    video_id = video_path.stem

    output = {
        "video_id": video_id,
        "metadata": {
            "video_path": str(args.video_path),
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": round(elapsed, 1),
            "cost": cost,
        },
        "highlight_candidates": highlight_candidates,
        "short_candidates": short_candidates,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[output] 保存: {output_path}", flush=True)
    print(f"[result] ハイライト候補: {len(highlight_candidates)}件, ショート候補: {len(short_candidates)}件", flush=True)
    print(f"[cost] 入力: {cost.get('input_tokens', '?')} トークン, 出力: {cost.get('output_tokens', '?')} トークン, 合計: {cost.get('total_cost', '?')}", flush=True)

    if highlight_candidates:
        print("\n=== ハイライト Top3 ===", flush=True)
        for c in highlight_candidates[:3]:
            print(f"  [{c.get('start', '?')}-{c.get('end', '?')}] {c.get('title', '?')} (score={c.get('score', '?')})", flush=True)

    if short_candidates:
        print("\n=== ショート Top3 ===", flush=True)
        for c in short_candidates[:3]:
            print(f"  [{c.get('start', '?')}-{c.get('end', '?')}] {c.get('title', '?')} (viral={c.get('viral_score', '?')})", flush=True)

    return 0


def cmd_short_ideas(args):
    """short-ideas: 動画からショート動画候補を提案"""
    from google import genai
    from google.genai import types as genai_types

    client = genai.Client()

    video_file = upload_video(client, args.video_path)

    model = args.model
    top_n = args.top

    prompt = f"""この動画を分析して、9:16縦型ショート動画として切り出すのに最適なシーンを{top_n}件提案してください。

{MEMBER_INFO}

要件:
- 各候補は15秒以上60秒以下の区間を選ぶこと。短すぎる候補（15秒未満）は不可
- 面白い瞬間、リアクション、サプライズ要素、オヤジギャグ、ボケツッコミを優先
- 各候補にタイムスタンプ（開始-終了）、理由、推奨タイトルを含める
- ショート動画のフック（冒頭3秒で視聴者を引き付ける要素）を明記
- viral_scoreは1-10の整数で、バズる可能性を評価。全候補が同じスコアにならないよう相対的に評価すること。最高スコアは1件のみ、最低スコアの候補も含めること
- **動画の前半・中盤・後半から均等に候補を選べ。前半に偏らないこと**
- **動画の後半（全体の後半60%以降）にも必ず3件以上の候補を含めること**

出力形式（YAMLのみ。説明文は不要）:
candidates:
  - id: 1
    start_time: "MM:SS"
    end_time: "MM:SS"
    duration_sec: 30
    title: "推奨タイトル"
    hook: "冒頭フックの説明"
    reason: "選出理由"
    speakers: ["話者キー名"]
    viral_score: 8
    category: "ギャグ/リアクション/サプライズ/感動/その他"
"""

    print(f"[generate] モデル: {model}", flush=True)
    t0 = time.time()
    response = client.models.generate_content(
        model=model,
        contents=[video_file, prompt],
        config=genai_types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
        ),
    )
    elapsed = time.time() - t0

    raw_text = response.text
    print(f"[generate] レスポンス長: {len(raw_text)} 文字 ({elapsed:.1f}s)", flush=True)

    # YAMLパース（BUG-1対策: 複数フォールバック）
    yaml_text = extract_yaml_block(raw_text)
    candidates = parse_candidates_robust(raw_text, yaml_text)

    raw_fallback = None
    if not candidates:
        print(f"[warn] 全パース失敗 — raw_responseとして保存\n[raw]\n{raw_text[:500]}", flush=True)
        raw_fallback = raw_text

    cost = calc_cost(response.usage_metadata, model)

    output = {
        "metadata": {
            "video_path": str(args.video_path),
            "model": model,
            "top": top_n,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": round(elapsed, 1),
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
        default="gemini-3-flash-preview",
        help="使用モデル（デフォルト: gemini-3-flash-preview）",
    )
    p_ideas.set_defaults(func=cmd_short_ideas)

    # screen サブコマンド
    p_screen = subparsers.add_parser("screen", help="ハイライト候補とショート候補を同時提案（統合スクリーニング）")
    p_screen.add_argument("video_path", help="入力動画ファイルパス")
    p_screen.add_argument("--output", "-o", required=True, help="出力YAMLファイルパス")
    p_screen.add_argument(
        "--model",
        default="gemini-3-flash-preview",
        help="使用モデル（デフォルト: gemini-3-flash-preview）",
    )
    p_screen.set_defaults(func=cmd_screen)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
