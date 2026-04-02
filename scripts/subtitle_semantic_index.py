#!/usr/bin/env python3
"""
字幕セマンティック検索インデックス（BigQuery版）
merged_*.json からchunk化→Gemini Embedding→BigQuery保存→検索

使い方:
  source config/vertex_api_key.env
  python3 scripts/subtitle_semantic_index.py build           # 全merged JSONをインデックス化してBQにアップロード
  python3 scripts/subtitle_semantic_index.py search "クエリ" # BigQueryセマンティック検索
  python3 scripts/subtitle_semantic_index.py update          # 未登録merged JSONを追加

移行について:
  - ローカルFAISSインデックス廃止（ローカルにベクトルを保持しない）
  - 検索時はBigQuery VECTOR_SEARCH() APIを呼び出すのみ
  - 一回限りの移行: scripts/bq_subtitle_migrate.py を参照
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("ERROR: google-genai not installed")
    sys.exit(1)

# ===== 設定 =====
BASE_DIR = Path(__file__).parent.parent
DOZLE_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
REGISTRY_FILE = DOZLE_DIR / "reports" / "semantic_index_registry.yaml"

EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072
BATCH_SIZE = 20
CHUNK_SECONDS = 30
RATE_LIMIT_SLEEP = 3.0

GCP_PROJECT = "dozlesha-mainichi-kirinuki"
BQ_DATASET = "dozle_subtitle_semantic"
BQ_TABLE = "subtitle_chunks"
BQ_LOCATION = "asia-northeast1"
FULL_TABLE_ID = f"`{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`"


# ===== 認証・API =====

def get_api_key(explicit_key=None):
    key = explicit_key or os.environ.get("VERTEX_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("ERROR: VERTEX_API_KEY not set. Run: source config/vertex_api_key.env")
        sys.exit(1)
    return key


def get_embedding_client(api_key=None):
    return genai.Client(api_key=get_api_key(api_key))


def bq_query(sql: str, timeout_ms: int = 60000) -> list[dict]:
    """bq CLIを使ってBigQueryクエリを実行し、結果をdictリストで返す"""
    import subprocess
    # SQLを標準入力でbq queryに渡す（CLI引数制限を回避）
    try:
        result = subprocess.run(
            [
                "bq", "query",
                "--use_legacy_sql=false",
                "--format=json",
                f"--project_id={GCP_PROJECT}",
                f"--location={BQ_LOCATION}",
            ],
            input=sql,
            capture_output=True,
            text=True,
            timeout=timeout_ms // 1000 + 30,
        )
        if result.returncode != 0:
            print(f"ERROR: bq query failed: {result.stderr[:500]}")
            sys.exit(1)
        # bq query --format=json returns a JSON array
        output = result.stdout.strip()
        if not output or output == "[]":
            return []
        rows = json.loads(output)
        if not isinstance(rows, list):
            return []
        return rows
    except subprocess.TimeoutExpired:
        print(f"ERROR: bq query timeout ({timeout_ms}ms)")
        sys.exit(1)


def bq_check_table() -> bool:
    """BigQueryテーブルが存在するか確認"""
    try:
        rows = bq_query(f"SELECT COUNT(*) as cnt FROM {FULL_TABLE_ID}", timeout_ms=30000)
        if rows:
            # bq CLI --format=json returns {"cnt": "45602"} (string values)
            cnt_val = rows[0].get("cnt", "0")
            return int(cnt_val) > 0
        return False
    except Exception:
        return False


# ===== Embedding =====

def embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT"):
    """テキストリストのembeddingを返す (list of list[float])"""
    import re as _re
    all_embeds = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"    batch {batch_num}/{total_batches} ({len(batch)} items)...", end=" ", flush=True)
        max_retry = 5
        for attempt in range(max_retry):
            try:
                response = client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=batch,
                    config=genai_types.EmbedContentConfig(
                        task_type=task_type,
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
                m = _re.search(r"retry[Dd]elay.*?(\d+)s", err_str)
                wait = int(m.group(1)) + 5 if m else 65
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f"429 (wait {wait}s, attempt {attempt+1}/{max_retry})...", end=" ", flush=True)
                    time.sleep(wait)
                else:
                    print(f"ERROR: {err_str[:100]}", flush=True)
                    for _ in batch:
                        all_embeds.append([0.0] * EMBED_DIM)
                    break
        else:
            print(f"GIVE UP after {max_retry} retries", flush=True)
            for _ in batch:
                all_embeds.append([0.0] * EMBED_DIM)
    return all_embeds


# ===== チャンク化 =====

def load_registry():
    if not REGISTRY_FILE.exists():
        return {"videos": []}
    try:
        with open(REGISTRY_FILE) as f:
            data = yaml.safe_load(f) or {}
        if "videos" not in data:
            data["videos"] = []
        return data
    except Exception as e:
        print(f"WARN: registry load failed: {e}")
        return {"videos": []}


def save_registry(registry):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)


def indexed_video_ids(registry):
    return {v["video_id"] for v in registry.get("videos", [])}


def find_all_merged_jsons():
    work_dir = DOZLE_DIR / "work"
    return sorted(work_dir.rglob("merged_*.json"))


def chunk_merged_json(merged_path: Path, chunk_sec=CHUNK_SECONDS):
    chunks = []
    try:
        with open(merged_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  WARN: {merged_path}: {e}")
        return chunks

    if not isinstance(data, dict):
        return chunks
    words = data.get("words", [])
    meta = data.get("metadata", {})
    video_id = meta.get("video_id", merged_path.stem.replace("merged_", ""))

    if not words:
        return chunks

    chunk_ms = chunk_sec * 1000
    window_start_ms = words[0].get("start", 0)
    window_texts = []

    def flush(ws_ms, we_ms, texts):
        if texts:
            chunks.append({
                "video_id": video_id,
                "start_ms": int(ws_ms),
                "end_ms": int(we_ms),
                "text": "".join(texts),
            })

    for w in words:
        start_ms = w.get("start", 0)
        text = w.get("text", "")
        if start_ms - window_start_ms >= chunk_ms:
            flush(window_start_ms, start_ms, window_texts)
            window_start_ms = start_ms
            window_texts = [text]
        else:
            window_texts.append(text)

    flush(window_start_ms, window_start_ms + chunk_ms, window_texts)
    return chunks


# ===== BigQuery アップロード =====

def bq_insert_rows(rows: list[dict]):
    """bq insert CLIを使ってBigQueryにrowsを挿入する"""
    import subprocess
    jsonl_data = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    result = subprocess.run(
        ["bq", "insert",
         f"--project_id={GCP_PROJECT}",
         f"{BQ_DATASET}.{BQ_TABLE}"],
        input=jsonl_data,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"  INSERT ERROR: {result.stderr[:300]}")
    else:
        print(f"  INSERT OK: {len(rows)} rows")


# ===== コマンド =====

def cmd_build(args):
    """全merged JSONをインデックス化してBigQueryにアップロード"""
    api_key = getattr(args, "api_key", None)
    chunk_id_offset = getattr(args, "chunk_id_offset", 0)

    print("=== subtitle_semantic_index build (BigQuery) ===")

    registry = load_registry()
    already_indexed = indexed_video_ids(registry)
    print(f"既登録動画: {len(already_indexed)}本")

    all_merged = find_all_merged_jsons()
    print(f"merged JSON総数: {len(all_merged)}本")

    to_process = []
    for p in all_merged:
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            vid = d.get("metadata", {}).get("video_id", p.stem.replace("merged_", ""))
        except Exception:
            vid = p.stem.replace("merged_", "")
        if vid not in already_indexed:
            to_process.append((vid, p))

    print(f"未登録: {len(to_process)}本 → 処理開始")
    if not to_process:
        print("新規動画なし。終了。")
        return

    client = get_embedding_client(api_key)
    global_chunk_id = chunk_id_offset

    for i, (video_id, merged_path) in enumerate(to_process):
        print(f"\n[{i+1}/{len(to_process)}] {video_id} ({merged_path.name})")
        chunks = chunk_merged_json(merged_path)
        if not chunks:
            print(f"  チャンク0件 → スキップ")
            continue

        print(f"  チャンク数: {len(chunks)}")
        texts = [c["text"] for c in chunks]
        embeds = embed_texts(client, texts)

        rows = []
        for j, (chunk, emb) in enumerate(zip(chunks, embeds)):
            rows.append({
                "chunk_id": global_chunk_id + j,
                "video_id": chunk["video_id"],
                "start_ms": chunk["start_ms"],
                "end_ms": chunk["end_ms"],
                "text": chunk["text"],
                "embedding": emb,
            })

        # BigQueryにINSERT
        bq_insert_rows(rows)
        global_chunk_id += len(rows)

        # レジストリ更新
        registry["videos"].append({
            "video_id": video_id,
            "merged_json": str(merged_path),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "chunk_count": len(rows),
        })
        save_registry(registry)
        print(f"  BigQuery INSERT完了: {len(rows)} チャンク")

    print(f"\n=== ビルド完了 ===")
    print(f"処理動画数: {len(to_process)}本")
    print(f"合計チャンク数: {global_chunk_id - chunk_id_offset}")
    print(f"登録動画数: {len(registry['videos'])}本")


def cmd_search(args):
    """BigQueryセマンティック検索"""
    query = args.query
    top_k = args.top
    api_key = getattr(args, "api_key", None)

    print(f"クエリ: {query}")

    # テーブル存在確認
    if not bq_check_table():
        print(f"ERROR: BigQueryテーブルが空またはアクセス不可: {FULL_TABLE_ID}")
        print("  先に bq_subtitle_migrate.py を実行してデータをアップロードしてください")
        sys.exit(1)

    # クエリをembedding化
    client = get_embedding_client(api_key)
    print("クエリのembedding生成中...")
    q_embeds = embed_texts(client, [query], task_type="RETRIEVAL_QUERY")
    q_vec = q_embeds[0]

    # BigQuery VECTOR_SEARCH SQLを構築
    vec_str = ", ".join(str(x) for x in q_vec)
    sql = f"""
SELECT
  base.video_id,
  base.start_ms,
  base.end_ms,
  base.text,
  distance
FROM
  VECTOR_SEARCH(
    TABLE {FULL_TABLE_ID},
    'embedding',
    (SELECT [{vec_str}] AS embedding),
    top_k => {top_k},
    distance_type => 'COSINE'
  )
ORDER BY distance ASC
"""

    print("BigQuery VECTOR_SEARCH実行中...")
    t0 = time.time()
    rows = bq_query(sql, timeout_ms=60000)
    elapsed = time.time() - t0
    print(f"検索完了: {elapsed:.2f}秒")

    print(f"\n=== 検索結果 (Top {top_k}) ===")
    for rank, row in enumerate(rows, 1):
        video_id = row.get("video_id", "?")
        start_ms = int(row.get("start_ms", 0) or 0)
        end_ms = int(row.get("end_ms", 0) or 0)
        text = row.get("text", "") or ""
        distance = float(row.get("distance", 0) or 0)
        score = 1.0 - distance  # cosine distance → similarity

        start_sec = start_ms / 1000
        end_sec = end_ms / 1000
        start_fmt = f"{int(start_sec//60):02d}:{start_sec%60:05.2f}"
        end_fmt = f"{int(end_sec//60):02d}:{end_sec%60:05.2f}"

        print(f"\n[{rank}] score={score:.4f} video_id={video_id} {start_fmt}〜{end_fmt}")
        preview = text[:200].replace("\n", " ")
        print(f"  {preview}")


def cmd_update(args):
    """新規merged JSONのみ追加（buildと同等）"""
    cmd_build(args)


def main():
    parser = argparse.ArgumentParser(description="字幕セマンティック検索インデックス（BigQuery版）")
    sub = parser.add_subparsers(dest="command")

    b_parser = sub.add_parser("build", help="全merged JSONからインデックス構築→BigQueryアップロード（未登録のみ）")
    b_parser.add_argument("--api-key", dest="api_key", default=None)
    b_parser.add_argument("--chunk-id-offset", dest="chunk_id_offset", type=int, default=0)

    u_parser = sub.add_parser("update", help="新規merged JSONを追加（buildと同等）")
    u_parser.add_argument("--api-key", dest="api_key", default=None)
    u_parser.add_argument("--chunk-id-offset", dest="chunk_id_offset", type=int, default=0)

    s_parser = sub.add_parser("search", help="セマンティック検索（BigQuery VECTOR_SEARCH）")
    s_parser.add_argument("query", help="検索クエリ")
    s_parser.add_argument("--top", type=int, default=10, help="表示件数 (default: 10)")
    s_parser.add_argument("--api-key", dest="api_key", default=None)

    args = parser.parse_args()

    if args.command in ("build", None):
        cmd_build(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "search":
        cmd_search(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
