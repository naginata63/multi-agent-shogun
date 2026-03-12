#!/usr/bin/env python3
"""Gemini動画理解APIによるショートネタ提案・ハイライトスクリーニング"""

import argparse
import re
import subprocess
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


def get_video_duration(video_path: str) -> float:
    """ffprobeで動画の長さ（秒）を取得する"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"[warn] ffprobeで動画長取得失敗: {e}", flush=True)
        return 0.0


def validate_distribution(candidates: list, video_duration: float, min_back_half: int = 2) -> tuple[bool, int]:
    """後半候補数を検証する。(ok, back_half_count) を返す"""
    if video_duration <= 0:
        return True, 0  # 動画長不明なら検証スキップ
    half_point = video_duration / 2
    back_count = 0
    for c in candidates:
        start_sec = parse_mmss(c.get("start_time", ""))
        if start_sec >= half_point:
            back_count += 1
    ok = back_count >= min_back_half
    return ok, back_count


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


def _build_short_ideas_prompt(top_n: int) -> str:
    return f"""この動画を分析して、9:16縦型ショート動画として切り出すのに最適なシーンを{top_n}件提案してください。

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


def _build_retry_prompt(top_n: int, back_start_mmss: str, video_duration_mmss: str, back_count: int) -> str:
    return f"""この動画を分析して、9:16縦型ショート動画として切り出すのに最適なシーンを{top_n}件提案してください。

{MEMBER_INFO}

**重要な指示（前回の候補は全て前半に集中していました。必ず後半も含めてください）**:
- 前回の回答は後半候補が{back_count}件しかなく、不十分でした
- **動画の後半（{back_start_mmss}〜{video_duration_mmss}の範囲）から最低3件の候補を必ず含めること**
- 全体の候補を前半・中盤・後半に均等に分散させること

要件:
- 各候補は15秒以上60秒以下の区間を選ぶこと。短すぎる候補（15秒未満）は不可
- 面白い瞬間、リアクション、サプライズ要素、オヤジギャグ、ボケツッコミを優先
- 各候補にタイムスタンプ（開始-終了）、理由、推奨タイトルを含める
- ショート動画のフック（冒頭3秒で視聴者を引き付ける要素）を明記
- viral_scoreは1-10の整数で、バズる可能性を評価。全候補が同じスコアにならないよう相対的に評価すること。最高スコアは1件のみ、最低スコアの候補も含めること

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


def _build_back_half_prompt(back_start_mmss: str, video_duration_mmss: str) -> str:
    return f"""この動画の後半部分（{back_start_mmss}〜{video_duration_mmss}の範囲のみ）から、
9:16縦型ショート動画として切り出すのに最適なシーンを5件提案してください。

{MEMBER_INFO}

**必ず {back_start_mmss} 以降のシーンのみを選ぶこと**

要件:
- 各候補は15秒以上60秒以下の区間を選ぶこと
- 面白い瞬間、リアクション、サプライズ要素、オヤジギャグ、ボケツッコミを優先
- 各候補にタイムスタンプ（開始-終了）、理由、推奨タイトルを含める
- ショート動画のフック（冒頭3秒で視聴者を引き付ける要素）を明記
- viral_scoreは1-10の整数で評価

出力形式（YAMLのみ）:
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


def _secs_to_mmss(secs: float) -> str:
    """秒数をMM:SS形式に変換"""
    secs = int(secs)
    return f"{secs // 60:02d}:{secs % 60:02d}"


def cmd_short_ideas(args):
    """short-ideas: 動画からショート動画候補を提案（後半分布バリデーション+リトライ付き）"""
    from google import genai
    from google.genai import types as genai_types

    client = genai.Client()

    video_file = upload_video(client, args.video_path)

    model = args.model
    top_n = args.top

    # 動画長取得（後半バリデーション用）
    video_duration = get_video_duration(args.video_path)
    half_point = video_duration / 2 if video_duration > 0 else 0
    back_start_mmss = _secs_to_mmss(half_point) if half_point > 0 else "??:??"
    video_duration_mmss = _secs_to_mmss(video_duration) if video_duration > 0 else "??:??"
    print(f"[info] 動画長: {video_duration:.1f}秒 ({video_duration_mmss}), 後半開始: {back_start_mmss}", flush=True)

    total_cost_tokens_in = 0
    total_cost_tokens_out = 0
    retry_count = 0
    candidates = []
    raw_fallback = None

    # --- 初回生成 ---
    prompt = _build_short_ideas_prompt(top_n)
    print(f"[generate] モデル: {model} (attempt 1)", flush=True)
    t0 = time.time()
    response = client.models.generate_content(
        model=model,
        contents=[video_file, prompt],
        config=genai_types.GenerateContentConfig(temperature=0.2, max_output_tokens=8192),
    )
    elapsed = time.time() - t0
    raw_text = response.text
    print(f"[generate] レスポンス長: {len(raw_text)} 文字 ({elapsed:.1f}s)", flush=True)
    cost = calc_cost(response.usage_metadata, model)
    total_cost_tokens_in += cost.get("input_tokens", 0) or 0
    total_cost_tokens_out += cost.get("output_tokens", 0) or 0

    yaml_text = extract_yaml_block(raw_text)
    candidates = parse_candidates_robust(raw_text, yaml_text)
    if not candidates:
        print(f"[warn] 全パース失敗 — raw_responseとして保存\n[raw]\n{raw_text[:500]}", flush=True)
        raw_fallback = raw_text

    # --- 分布バリデーション + リトライ（最大2回）---
    MAX_RETRIES = 2
    while candidates and video_duration > 0:
        ok, back_count = validate_distribution(candidates, video_duration, min_back_half=2)
        print(f"[validate] 後半候補数: {back_count}/{len(candidates)} (half_point={back_start_mmss}) → {'OK' if ok else 'NG'}", flush=True)
        if ok:
            break
        if retry_count >= MAX_RETRIES:
            print(f"[warn] リトライ上限({MAX_RETRIES}回)到達。後半のみ追加生成でフォールバック", flush=True)
            # フォールバック: 後半のみ5件生成 → 前半5件 + 後半5件マージ → 上位10件
            back_prompt = _build_back_half_prompt(back_start_mmss, video_duration_mmss)
            print(f"[generate] モデル: {model} (back-half fallback)", flush=True)
            t0 = time.time()
            back_response = client.models.generate_content(
                model=model,
                contents=[video_file, back_prompt],
                config=genai_types.GenerateContentConfig(temperature=0.3, max_output_tokens=4096),
            )
            elapsed = time.time() - t0
            back_raw = back_response.text
            print(f"[generate] 後半生成レスポンス長: {len(back_raw)} 文字 ({elapsed:.1f}s)", flush=True)
            back_cost = calc_cost(back_response.usage_metadata, model)
            total_cost_tokens_in += back_cost.get("input_tokens", 0) or 0
            total_cost_tokens_out += back_cost.get("output_tokens", 0) or 0

            back_yaml = extract_yaml_block(back_raw)
            back_candidates = parse_candidates_robust(back_raw, back_yaml)
            if back_candidates:
                # 前半5件 + 後半追加5件 → viral_scoreソートで上位top_n件
                front_5 = sorted(candidates, key=lambda c: c.get("viral_score", 0), reverse=True)[:5]
                back_5 = sorted(back_candidates, key=lambda c: c.get("viral_score", 0), reverse=True)[:5]
                merged = front_5 + back_5
                # IDを振り直し
                merged_sorted = sorted(merged, key=lambda c: c.get("viral_score", 0), reverse=True)[:top_n]
                for i, c in enumerate(merged_sorted, 1):
                    c["id"] = i
                candidates = merged_sorted
                print(f"[info] マージ後候補数: {len(candidates)}", flush=True)
            break

        retry_count += 1
        retry_prompt = _build_retry_prompt(top_n, back_start_mmss, video_duration_mmss, back_count)
        print(f"[generate] モデル: {model} (retry {retry_count}/{MAX_RETRIES})", flush=True)
        t0 = time.time()
        response = client.models.generate_content(
            model=model,
            contents=[video_file, retry_prompt],
            config=genai_types.GenerateContentConfig(temperature=0.3, max_output_tokens=8192),
        )
        elapsed = time.time() - t0
        raw_text = response.text
        print(f"[generate] レスポンス長: {len(raw_text)} 文字 ({elapsed:.1f}s)", flush=True)
        cost = calc_cost(response.usage_metadata, model)
        total_cost_tokens_in += cost.get("input_tokens", 0) or 0
        total_cost_tokens_out += cost.get("output_tokens", 0) or 0

        yaml_text = extract_yaml_block(raw_text)
        new_candidates = parse_candidates_robust(raw_text, yaml_text)
        if new_candidates:
            candidates = new_candidates
        else:
            print(f"[warn] リトライ{retry_count}でもパース失敗 — 前回候補を継続", flush=True)

    # 最終分布チェック（ログ用）
    if candidates and video_duration > 0:
        _, final_back_count = validate_distribution(candidates, video_duration, min_back_half=2)
        print(f"[result] 最終後半候補数: {final_back_count}/{len(candidates)}", flush=True)

    total_cost_str = f"${(total_cost_tokens_in / 1_000_000 * 0.10 + total_cost_tokens_out / 1_000_000 * 0.40):.4f}"

    output = {
        "metadata": {
            "video_path": str(args.video_path),
            "model": model,
            "top": top_n,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "video_duration_sec": round(video_duration, 1),
            "retry_count": retry_count,
            "cost": {
                "input_tokens": total_cost_tokens_in,
                "output_tokens": total_cost_tokens_out,
                "total_cost": total_cost_str,
            },
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
    print(f"[result] 候補数: {len(candidates)}, リトライ: {retry_count}回", flush=True)
    print(f"[cost] 入力: {total_cost_tokens_in} トークン, 出力: {total_cost_tokens_out} トークン, 合計: {total_cost_str}", flush=True)

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
