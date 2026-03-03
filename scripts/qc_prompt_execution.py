#!/usr/bin/env python3
"""
qc_prompt_execution.py — ココナラプロンプト 実行QCパイプライン
Gemini API (gemini-2.0-flash) でプロンプトを実投入し、LLM-as-Judgeで品質採点する。

使用方法:
    python3 scripts/qc_prompt_execution.py <category_dir> <output_yaml>

例:
    python3 scripts/qc_prompt_execution.py \\
        reports/coconala_prompts/individual/01_sales \\
        reports/coconala_prompts/execution_qc/01_sales_results.yaml
"""

import sys
import os
import re
import json
import time
from datetime import datetime
from pathlib import Path

# --- 依存パッケージチェック ---
try:
    import google.generativeai as genai
except ImportError:
    print(
        "ERROR: google-generativeai パッケージが未インストールです。",
        file=sys.stderr,
    )
    print("インストール方法:", file=sys.stderr)
    print("    pip install google-generativeai", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が未インストールです。", file=sys.stderr)
    print("インストール方法:", file=sys.stderr)
    print("    pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- プレースホルダ置換用ダミー値 ---
PLACEHOLDER_VALUES = {
    # 会社・人物
    "会社名": "株式会社サンプル",
    "自社名": "株式会社テクノソリューション",
    "社名": "株式会社サンプル",
    "担当者名": "山田太郎",
    "担当者": "営業部 山田太郎",
    "名前": "山田太郎",
    "自分の名前": "山田太郎",
    # 商品・サービス
    "商品名": "AIアシスタントPro",
    "サービス名": "業務自動化SaaS",
    "サービス名・概要（例：中小企業向けの請求書自動化SaaS）": "中小企業向け業務自動化SaaS",
    "製品名": "スマートオフィスツール",
    # 業種・業界
    "業種": "IT・テクノロジー",
    "業界": "製造業",
    # 送付先情報
    "送付先企業名": "株式会社テスト商事",
    "役職・名前 / 不明なら「ご担当者様」": "営業部長 田中様",
    "役職・名前": "営業部長 田中様",
    # 課題・問題
    "課題": "業務効率化の遅れ",
    "想定している相手の課題": "請求書処理に月40時間以上かかっている",
    "例：請求書処理に月40時間以上かかっている": "請求書処理に月40時間以上かかっている",
    # 数値・量
    "数値": "30%",
    "金額": "100,000円",
    "期間": "3ヶ月",
    "件数": "50件",
    # その他汎用
    "内容": "業務効率化に関する重要なご提案",
    "詳細": "詳細については別途ご案内いたします",
    "URL": "https://example.com",
    # 業種（例...）パターン
    "業種（例：製造業、IT企業など）": "IT・テクノロジー",
}


def replace_placeholders(prompt: str) -> str:
    """{{key}} パターンをダミー値で置換。未知のキーはフォールバック値を返す。"""

    def replace_match(m):
        key = m.group(1).strip()
        # 完全一致
        if key in PLACEHOLDER_VALUES:
            return PLACEHOLDER_VALUES[key]
        # 部分マッチ（例: "例：..."を含むキー）
        for k, v in PLACEHOLDER_VALUES.items():
            if k in key or key in k:
                return v
        # マッチなし → 汎用フォールバック
        return f"[サンプル: {key}]"

    return re.sub(r"\{\{([^}]+)\}\}", replace_match, prompt)


def extract_prompt(text: str) -> str | None:
    """
    マークダウンテキストから ### プロンプト セクションのコードブロックを抽出する。
    出力例セクション（### 出力例 以降）は無視。
    """
    # ### 出力例 以降を切り捨て
    output_example_match = re.search(r"^###\s*出力例", text, re.MULTILINE)
    if output_example_match:
        text = text[: output_example_match.start()]

    # ### プロンプト セクションを探す
    prompt_section_match = re.search(r"^###\s*プロンプト", text, re.MULTILINE)
    if not prompt_section_match:
        return None

    after_header = text[prompt_section_match.end():]

    # 最初のコードブロック (``` ... ```) を抽出
    code_block_match = re.search(r"```[^\n]*\n(.*?)```", after_header, re.DOTALL)
    if not code_block_match:
        return None

    return code_block_match.group(1).strip()


def run_prompt(api_key: str, prompt_text: str, model_name: str = "gemini-2.0-flash") -> str:
    """Gemini APIでプロンプトを実行し、生成テキストを返す。"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt_text)
    return response.text


def score_output(api_key: str, original_prompt: str, output: str) -> dict:
    """LLM-as-Judge: Geminiで出力品質を採点し、スコア辞書を返す。"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    judge_prompt = f"""以下のプロンプトとその出力を評価してください。
各基準を1〜5点で採点し、JSON形式で返してください。

## 元のプロンプト
{original_prompt[:500]}

## 生成された出力
{output[:1000]}

## 採点基準
- instruction_compliance: 指示通りの構造・フォーマットで出力されたか（1=全く従っていない、5=完全に従っている）
- content_quality: 具体的で実用的な内容か（1=薄い・汎用的すぎ、5=具体的で実用的）
- placeholder_response: 埋め込み値が出力に自然に反映されているか（1=無視・不自然、5=自然に活用）
- practicality: そのまま業務に使えるレベルか（1=使えない、5=すぐ使える）

必ずJSON形式のみで返してください（説明不要）:
{{"instruction_compliance": N, "content_quality": N, "placeholder_response": N, "practicality": N, "issues": ["問題点があれば記述"]}}"""

    response = model.generate_content(judge_prompt)
    text = response.text.strip()

    # ```json...``` ブロックのケア
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON解析失敗: {e}. フォールバック採点を使用。", file=sys.stderr)
        return {
            "instruction_compliance": 3,
            "content_quality": 3,
            "placeholder_response": 3,
            "practicality": 3,
            "issues": [f"judge_json_parse_error: {str(e)}"],
        }


def process_category(api_key: str, category_dir: str, output_path: str):
    """カテゴリ内のすべての.mdファイルを処理し、結果をYAMLに出力する。"""
    category_path = Path(category_dir)
    category_name = category_path.name
    md_files = sorted(category_path.glob("*.md"))

    if not md_files:
        print(f"ERROR: {category_dir} に.mdファイルが見つかりません。", file=sys.stderr)
        sys.exit(1)

    print(f"カテゴリ: {category_name}", file=sys.stderr)
    print(f"対象ファイル数: {len(md_files)}", file=sys.stderr)
    print(f"開始時刻: {datetime.now().isoformat()}", file=sys.stderr)
    print("---", file=sys.stderr)

    results = []
    counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}

    for i, md_file in enumerate(md_files):
        print(f"[{i + 1}/{len(md_files)}] {md_file.name}", file=sys.stderr)
        text = md_file.read_text(encoding="utf-8")

        # フロントマターからid・titleを抽出
        id_match = re.search(r'^id:\s*"([^"]+)"', text, re.MULTILINE)
        title_match = re.search(r'^title:\s*"([^"]+)"', text, re.MULTILINE)
        item_id = id_match.group(1) if id_match else md_file.stem
        title = title_match.group(1) if title_match else md_file.stem

        # プロンプト本文抽出
        prompt_raw = extract_prompt(text)
        if not prompt_raw:
            print(f"  [WARN] プロンプト抽出失敗: {md_file.name}", file=sys.stderr)
            counts["skip"] += 1
            results.append({
                "id": item_id,
                "title": title,
                "scores": {},
                "total": 0,
                "grade": "skip",
                "issues": ["prompt_extraction_failed"],
            })
            continue

        prompt_filled = replace_placeholders(prompt_raw)

        # Gemini実行（レート制限: 15RPM → 4秒/リクエスト）
        try:
            print(f"  実行中...", file=sys.stderr)
            time.sleep(4)
            output = run_prompt(api_key, prompt_filled)
        except Exception as e:
            print(f"  [ERROR] Gemini実行失敗: {e}", file=sys.stderr)
            counts["skip"] += 1
            results.append({
                "id": item_id,
                "title": title,
                "scores": {},
                "total": 0,
                "grade": "skip",
                "issues": [f"api_error: {str(e)}"],
            })
            continue

        # 採点
        try:
            time.sleep(4)
            scores = score_output(api_key, prompt_raw, output)
        except Exception as e:
            print(f"  [ERROR] 採点失敗: {e}. フォールバック使用。", file=sys.stderr)
            scores = {
                "instruction_compliance": 3,
                "content_quality": 3,
                "placeholder_response": 3,
                "practicality": 3,
                "issues": [f"score_api_error: {str(e)}"],
            }

        total = sum(
            scores.get(k, 0)
            for k in ["instruction_compliance", "content_quality", "placeholder_response", "practicality"]
        )
        grade = "pass" if total >= 16 else ("warn" if total >= 12 else "fail")
        counts[grade] += 1

        result_entry = {
            "id": item_id,
            "title": title,
            "scores": {
                "instruction_compliance": scores.get("instruction_compliance", 0),
                "content_quality": scores.get("content_quality", 0),
                "placeholder_response": scores.get("placeholder_response", 0),
                "practicality": scores.get("practicality", 0),
            },
            "total": total,
            "grade": grade,
            "issues": scores.get("issues", []),
        }
        results.append(result_entry)
        print(f"  score={total}/20 grade={grade}", file=sys.stderr)

    # 出力YAML生成
    output_data = {
        "category": category_name,
        "tested_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "model": "gemini-2.0-flash",
        "summary": {
            "total": len(md_files),
            "pass": counts["pass"],
            "warn": counts["warn"],
            "fail": counts["fail"],
            "skip": counts["skip"],
        },
        "results": results,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print("---", file=sys.stderr)
    print(f"完了: {output_path}", file=sys.stderr)
    print(
        f"結果: pass={counts['pass']} warn={counts['warn']} fail={counts['fail']} skip={counts['skip']}",
        file=sys.stderr,
    )

    return output_data


def main():
    # GEMINI_API_KEY チェック
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY 環境変数が設定されていません。", file=sys.stderr)
        print("設定方法:", file=sys.stderr)
        print("    export GEMINI_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)

    # CLI引数チェック
    if len(sys.argv) != 3:
        print(f"使用方法: python3 {sys.argv[0]} <category_dir> <output_yaml>", file=sys.stderr)
        print("例:", file=sys.stderr)
        print(
            f"    python3 {sys.argv[0]} "
            "reports/coconala_prompts/individual/01_sales "
            "reports/coconala_prompts/execution_qc/01_sales_results.yaml",
            file=sys.stderr,
        )
        sys.exit(1)

    category_dir = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(category_dir).is_dir():
        print(f"ERROR: ディレクトリが存在しません: {category_dir}", file=sys.stderr)
        sys.exit(1)

    process_category(api_key, category_dir, output_path)


if __name__ == "__main__":
    main()
