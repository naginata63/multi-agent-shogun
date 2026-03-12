#!/usr/bin/env python3
"""
cmd_helper.py — cmdナレッジ支援ツール

サブコマンド:
  similar  "テキスト"   — 類似cmdをshogun_to_karoから検索
  dedup    "テキスト"   — 同内容ナレッジがcontext/memoryに既存か確認
  rag      "テキスト"   — 過去cmd・スクリプト・ナレッジ・コメントを統合検索
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SEMANTIC_SEARCH = str(BASE_DIR / "scripts" / "semantic_search.py")

DEDUP_THRESHOLD = 0.85  # config/settings.yamlがあれば上書き可
try:
    import yaml
    settings_path = BASE_DIR / "config" / "settings.yaml"
    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as _f:
            _settings = yaml.safe_load(_f) or {}
        DEDUP_THRESHOLD = _settings.get("dedup_threshold", DEDUP_THRESHOLD)
except Exception:
    pass


def run_semantic_search(query: str, source: str, top: int) -> list:
    """semantic_search.pyをsubprocessで呼んでJSONを返す"""
    cmd = (
        f"source ~/.bashrc && python3 {SEMANTIC_SEARCH} query "
        f"{json.dumps(query)} --source {source} --top {top} --json"
    )
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(f"ERROR: semantic_search タイムアウト (source={source})")
        return []
    except Exception as e:
        print(f"ERROR: {e}")
        return []

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            print(f"WARN: semantic_search stderr: {stderr[:200]}")
        return []

    # stdout から JSON部分を抽出（embeddings進捗ログが混在している場合あり）
    stdout = result.stdout.strip()
    # JSON配列を探す
    start = stdout.find("[")
    end = stdout.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        return json.loads(stdout[start:end + 1])
    except json.JSONDecodeError as e:
        print(f"WARN: JSON parse error: {e}")
        return []


def cmd_similar(args):
    """類似cmd検索"""
    text = args.text
    top = getattr(args, "top", 5)

    print(f"類似cmd検索: {text!r}")
    results = run_semantic_search(text, "shogun_to_karo", top)

    if not results:
        print("  (結果なし、またはインデックス未構築)")
        return

    print(f"\n類似cmd Top{len(results)}:")
    for i, r in enumerate(results, 1):
        chunk_id = r.get("chunk_id", "")
        # chunk_id から cmd_id を抽出: "shogun_to_karo::cmd_575" → "cmd_575"
        cmd_id = chunk_id.split("::")[-1] if "::" in chunk_id else chunk_id
        score = r.get("score", 0.0)
        text_preview = r.get("text", "")[:80].replace("\n", " ")
        print(f"  {i}. {cmd_id:15s} (score: {score:.2f}) {text_preview}")


def cmd_dedup(args):
    """重複ナレッジ検出"""
    text = args.text
    threshold = getattr(args, "threshold", DEDUP_THRESHOLD)

    print(f"重複チェック: {text!r} (閾値: {threshold})")

    hits = []
    for source in ("context", "memory"):
        results = run_semantic_search(text, source, 10)
        for r in results:
            if r.get("score", 0.0) >= threshold:
                r["_source_label"] = source
                hits.append(r)

    if not hits:
        print("  重複なし（閾値以上のナレッジが見つかりませんでした）")
        return

    # スコア降順ソート
    hits.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    print(f"\n⚠️  類似ナレッジ検出 ({len(hits)}件):")
    for i, r in enumerate(hits, 1):
        score = r.get("score", 0.0)
        chunk_id = r.get("chunk_id", "")
        file_path = r.get("file", "")
        src = r.get("_source_label", r.get("source", ""))
        text_preview = r.get("text", "")[:100].replace("\n", " ")
        print(f"  {i}. (score: {score:.2f}) [{src}] {chunk_id}")
        print(f"       file: {file_path}")
        print(f"       → 重複の可能性あり。既存ナレッジを更新すべき？")
        print(f"       preview: {text_preview}...")
        print()


def cmd_rag(args):
    """RAG参考資料統合表示"""
    text = args.text
    top = getattr(args, "top", 5)
    output_json = getattr(args, "json", False)

    sources = [
        ("shogun_to_karo", "過去の類似cmd"),
        ("scripts", "関連スクリプト"),
        ("context", "関連ナレッジ"),
        ("comments", "関連コメント"),
    ]

    all_results = {}
    for source, label in sources:
        results = run_semantic_search(text, source, top)
        all_results[source] = (label, results)

    if output_json:
        output = {}
        for source, (label, results) in all_results.items():
            output[source] = {
                "label": label,
                "results": results[:top],
            }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"\n=== RAG参考資料 ===")
    print(f"クエリ: {text!r}\n")

    for source, (label, results) in all_results.items():
        print(f"【{label}】")
        if not results:
            print("  (結果なし、またはインデックス未構築)")
        else:
            for i, r in enumerate(results[:top], 1):
                chunk_id = r.get("chunk_id", "")
                score = r.get("score", 0.0)
                text_preview = r.get("text", "")[:80].replace("\n", " ")
                file_path = r.get("file", "")

                if source == "shogun_to_karo":
                    display = chunk_id.split("::")[-1] if "::" in chunk_id else chunk_id
                    print(f"  {i}. {display:15s} (score: {score:.2f}) {text_preview}")
                elif source == "scripts":
                    parts = chunk_id.split("::")
                    display = parts[1] if len(parts) > 1 else chunk_id
                    print(f"  {i}. {display} (score: {score:.2f}) — {text_preview}")
                else:
                    fname = Path(file_path).name if file_path else chunk_id
                    print(f"  {i}. {fname} (score: {score:.2f}) — {text_preview}")
        print()


def main():
    parser = argparse.ArgumentParser(description="cmd_helper — cmdナレッジ支援ツール")
    sub = parser.add_subparsers(dest="command")

    # similar
    sim = sub.add_parser("similar", help="類似cmdをshogun_to_karoから検索")
    sim.add_argument("text", help="検索テキスト")
    sim.add_argument("--top", type=int, default=5, help="表示件数 (default: 5)")

    # dedup
    dup = sub.add_parser("dedup", help="context/memoryに同内容ナレッジが既存か確認")
    dup.add_argument("text", help="確認テキスト")
    dup.add_argument("--threshold", type=float, default=DEDUP_THRESHOLD,
                     help=f"類似度閾値 (default: {DEDUP_THRESHOLD})")

    # rag
    rag = sub.add_parser("rag", help="過去cmd・スクリプト・ナレッジ・コメントを統合検索")
    rag.add_argument("text", help="検索テキスト（cmdテーマ）")
    rag.add_argument("--top", type=int, default=5, help="各ソースの表示件数 (default: 5)")
    rag.add_argument("--json", action="store_true", help="JSON形式で出力")

    args = parser.parse_args()

    if args.command == "similar":
        cmd_similar(args)
    elif args.command == "dedup":
        cmd_dedup(args)
    elif args.command == "rag":
        cmd_rag(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
