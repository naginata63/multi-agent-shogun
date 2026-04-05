#!/usr/bin/env python3
"""
script_semantic_index.py — スクリプトインデックスのBigQueryセマンティック検索

script_index.mdをパースして各スクリプトエントリをチャンク化→Gemini Embedding→BigQuery保存。
検索時はVECTOR_SEARCHで最も関連性の高いスクリプトを返す。

使い方:
  source config/vertex_api_key.env
  python3 scripts/script_semantic_index.py build     # インデックス構築
  python3 scripts/script_semantic_index.py search "字幕マージ"  # 検索
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("ERROR: google-genai not installed")
    sys.exit(1)

# ===== 設定 =====
BASE_DIR = Path(__file__).parent.parent
SCRIPT_INDEX = BASE_DIR / "projects" / "dozle_kirinuki" / "context" / "script_index.md"

EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072
BATCH_SIZE = 20
RATE_LIMIT_SLEEP = 3.0

GCP_PROJECT = "gen-lang-client-0119911773"
BQ_DATASET = "dozle_subtitle_semantic"
BQ_TABLE = "script_index"
BQ_LOCATION = "asia-northeast1"
FULL_TABLE_ID = f"`{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`"


def get_client():
    """Vertex AI ADC認証でGeminiクライアントを取得"""
    return genai.Client(vertexai=True, project="gen-lang-client-0119911773", location="global")


def parse_script_index(index_path: Path) -> list[dict]:
    """script_index.mdをパースして各スクリプトエントリをリストで返す"""
    content = index_path.read_text(encoding="utf-8")
    entries = []
    current_category = ""

    # ### script_name.py パターンでスクリプトエントリを検出
    blocks = re.split(r"(?=^### \S+\.(?:py|sh)\s*$)", content, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # カテゴリ見出し（## A. インフラ等）の検出
        cat_match = re.search(r"^## [A-J]\.\s+(.+)", block, re.MULTILINE)
        if cat_match:
            current_category = cat_match.group(1).strip()

        # スクリプトエントリの検出
        name_match = re.match(r"^### (\S+\.(?:py|sh))\s*$", block, re.MULTILINE)
        if not name_match:
            continue

        name = name_match.group(1)
        purpose = ""
        location = ""
        args = ""
        deps = ""
        example = ""

        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("- **用途**:"):
                purpose = line.replace("- **用途**:", "").strip()
            elif line.startswith("- **場所**:"):
                location = line.replace("- **場所**:", "").strip()
            elif line.startswith("- **引数**:"):
                args = line.replace("- **引数**:", "").strip()
            elif line.startswith("- **依存**:"):
                deps = line.replace("- **依存**:", "").strip()
            elif line.startswith("- **実行例**:"):
                example = line.replace("- **実行例**:", "").strip()

        # チャンク用テキスト構築
        text = f"{name}: {purpose}\n場所: {location}\n引数: {args}\n依存: {deps}\n実行例: {example}"
        entries.append({
            "script_name": name,
            "category": current_category,
            "purpose": purpose,
            "location": location,
            "text": text,
        })

    return entries


def embed_texts(client, texts: list[str]) -> list[list[float]]:
    """テキストリストのembeddingを返す"""
    all_embeds = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  batch {batch_num}/{total_batches} ({len(batch)} items)...", end=" ", flush=True)
        max_retry = 3
        for attempt in range(max_retry):
            try:
                response = client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=batch,
                    config=genai_types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=EMBED_DIM,
                    ),
                )
                for emb in response.embeddings:
                    all_embeds.append(list(emb.values))
                print("OK", flush=True)
                time.sleep(RATE_LIMIT_SLEEP)
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait = 65
                    print(f"429 (wait {wait}s)...", end=" ", flush=True)
                    time.sleep(wait)
                else:
                    print(f"ERROR: {err_str[:100]}", flush=True)
                    for _ in batch:
                        all_embeds.append([0.0] * EMBED_DIM)
                    break
        else:
            for _ in batch:
                all_embeds.append([0.0] * EMBED_DIM)
    return all_embeds


def bq_run(sql: str, timeout_sec: int = 60) -> str:
    """bq CLIでクエリ実行"""
    result = subprocess.run(
        ["bq", "query", "--use_legacy_sql=false", "--format=json",
         f"--project_id={GCP_PROJECT}", f"--location={BQ_LOCATION}"],
        input=sql, capture_output=True, text=True, timeout=timeout_sec + 30,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def cmd_build(args):
    """script_index.mdからインデックス構築→BQアップロード"""
    if not SCRIPT_INDEX.exists():
        print(f"ERROR: {SCRIPT_INDEX} not found")
        sys.exit(1)

    print("=== script_semantic_index build ===")
    entries = parse_script_index(SCRIPT_INDEX)
    print(f"パース完了: {len(entries)}エントリ")

    if not entries:
        print("ERROR: エントリが0件")
        sys.exit(1)

    # Embedding生成
    client = get_client()
    texts = [e["text"] for e in entries]
    print("Embedding生成中...")
    embeds = embed_texts(client, texts)

    # BQテーブル作成（存在しなければ）
    print("BigQueryテーブル確認...")
    schema_sql = f"""
    CREATE TABLE IF NOT EXISTS {FULL_TABLE_ID} (
        chunk_id INTEGER,
        script_name STRING,
        category STRING,
        purpose STRING,
        location STRING,
        text STRING,
        embedding ARRAY<FLOAT64>
    )
    """
    out, err, rc = bq_run(schema_sql)
    if rc != 0 and "Already Exists" not in err:
        print(f"ERROR: テーブル作成失敗: {err[:300]}")
        sys.exit(1)

    # 既存データ削除（全面入れ替え）
    print("既存データ削除...")
    bq_run(f"DELETE FROM {FULL_TABLE_ID} WHERE TRUE")

    # JSONL作成→bq load
    jsonl_path = BASE_DIR / "work" / "script_index_chunks.jsonl"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for i, (entry, emb) in enumerate(zip(entries, embeds)):
            row = {
                "chunk_id": i,
                "script_name": entry["script_name"],
                "category": entry["category"],
                "purpose": entry["purpose"],
                "location": entry["location"],
                "text": entry["text"],
                "embedding": emb,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"JSONL作成: {jsonl_path} ({len(entries)}行)")

    # bq load
    schema_file = BASE_DIR / "work" / "script_index_schema.json"
    schema = [
        {"name": "chunk_id", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "script_name", "type": "STRING", "mode": "REQUIRED"},
        {"name": "category", "type": "STRING", "mode": "NULLABLE"},
        {"name": "purpose", "type": "STRING", "mode": "NULLABLE"},
        {"name": "location", "type": "STRING", "mode": "NULLABLE"},
        {"name": "text", "type": "STRING", "mode": "NULLABLE"},
        {"name": "embedding", "type": "FLOAT64", "mode": "REPEATED"},
    ]
    with open(schema_file, "w") as f:
        json.dump(schema, f, indent=2)

    print("BigQueryアップロード...")
    result = subprocess.run(
        ["bq", "load", "--source_format=NEWLINE_DELIMITED_JSON",
         "--replace",
         f"{GCP_PROJECT}:{BQ_DATASET}.{BQ_TABLE}",
         str(jsonl_path), str(schema_file)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"ERROR: bq load失敗: {result.stderr[:300]}")
        sys.exit(1)

    print(f"=== 完了: {len(entries)}スクリプト登録 ===")


def cmd_search(args):
    """セマンティック検索"""
    query = args.query
    top_k = args.top
    print(f"クエリ: {query}")

    # クエリembedding
    client = get_client()
    print("クエリembedding生成中...")
    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=[query],
        config=genai_types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBED_DIM,
        ),
    )
    q_vec = list(response.embeddings[0].values)
    vec_str = ", ".join(str(x) for x in q_vec)

    sql = f"""
    SELECT base.script_name, base.category, base.purpose, base.location, distance
    FROM VECTOR_SEARCH(
        TABLE {FULL_TABLE_ID}, 'embedding',
        (SELECT [{vec_str}] AS embedding),
        top_k => {top_k}, distance_type => 'COSINE'
    )
    ORDER BY distance ASC
    """

    print("BigQuery VECTOR_SEARCH実行中...")
    t0 = time.time()
    out, err, rc = bq_run(sql, timeout_sec=60)
    elapsed = time.time() - t0

    if rc != 0:
        print(f"ERROR: 検索失敗: {err[:300]}")
        sys.exit(1)

    rows = json.loads(out) if out and out != "[]" else []
    print(f"検索完了: {elapsed:.2f}秒")
    print(f"\n=== 検索結果 (Top {top_k}) ===")

    for rank, row in enumerate(rows, 1):
        name = row.get("script_name", "?")
        cat = row.get("category", "?")
        purpose = row.get("purpose", "")
        location = row.get("location", "")
        dist = float(row.get("distance", 0))
        score = 1.0 - dist
        print(f"\n[{rank}] score={score:.4f} {name} ({cat})")
        print(f"  用途: {purpose}")
        print(f"  場所: {location}")


def main():
    parser = argparse.ArgumentParser(description="スクリプトセマンティック検索インデックス")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", help="インデックス構築")
    s = sub.add_parser("search", help="検索")
    s.add_argument("query", help="検索クエリ")
    s.add_argument("--top", type=int, default=5, help="表示件数 (default: 5)")

    args = parser.parse_args()
    if args.command == "build":
        cmd_build(args)
    elif args.command == "search":
        cmd_search(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
