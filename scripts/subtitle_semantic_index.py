#!/usr/bin/env python3
"""
字幕セマンティック検索インデックス
merged_*.json からchunk化→Gemini Embedding→FAISS/JSON保存→検索

使い方:
  python3 scripts/subtitle_semantic_index.py build           # 全merged JSONをインデックス化
  python3 scripts/subtitle_semantic_index.py search "クエリ" # セマンティック検索
  python3 scripts/subtitle_semantic_index.py update          # 未登録merged JSONを追加
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
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
INDEX_DIR = DOZLE_DIR / "work" / "subtitle_index"
EMBED_JSON = INDEX_DIR / "embeddings.json"
FAISS_FILE = INDEX_DIR / "subtitle_index.faiss"
REGISTRY_FILE = DOZLE_DIR / "reports" / "semantic_index_registry.yaml"

EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072
BATCH_SIZE = 20        # Gemini APIのバッチサイズ
CHUNK_SECONDS = 30     # チャンク幅（秒）
RATE_LIMIT_SLEEP = 3.0 # バッチ間スリープ（秒）


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("ERROR: GEMINI_API_KEY not set. Run: source ~/.bashrc")
        sys.exit(1)
    return key


def get_client():
    return genai.Client(api_key=get_api_key())


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
    """work/配下の全merged_*.jsonを返す（出力ディレクトリ内のclip用も含む）"""
    work_dir = DOZLE_DIR / "work"
    return sorted(work_dir.rglob("merged_*.json"))


def chunk_merged_json(merged_path: Path, chunk_sec=CHUNK_SECONDS):
    """merged JSONから30秒チャンクのリストを返す"""
    chunks = []
    try:
        with open(merged_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  WARN: {merged_path}: {e}")
        return chunks

    if not isinstance(data, dict):
        # speaker_id等のリスト形式ファイルはスキップ
        return chunks
    words = data.get("words", [])
    meta = data.get("metadata", {})
    video_id = meta.get("video_id", merged_path.stem.replace("merged_", ""))

    if not words:
        return chunks

    # word単位で30秒チャンクに集約
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
                "source_file": str(merged_path),
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


def embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT"):
    """テキストリストのembeddingを返す (list of list[float])。429時はリトライ。"""
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
                # retryDelay秒を抽出
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


def load_embeddings():
    """既存embeddings.jsonを読み込む"""
    if not EMBED_JSON.exists():
        return []
    try:
        with open(EMBED_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_embeddings(entries):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(EMBED_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)
    print(f"  saved {len(entries)} entries → {EMBED_JSON}")


def build_faiss_index(entries):
    """entriesからFAISSインデックスを構築して保存"""
    if not entries:
        print("  WARN: no entries to index")
        return None
    embeds = np.array([e["embedding"] for e in entries], dtype=np.float32)
    faiss.normalize_L2(embeds)
    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(embeds)
    faiss.write_index(index, str(FAISS_FILE))
    print(f"  FAISS index: {len(entries)} vectors → {FAISS_FILE}")
    return index


def load_faiss_index():
    if FAISS_FILE.exists():
        return faiss.read_index(str(FAISS_FILE))
    return None


def cmd_build(args):
    """全merged JSONをインデックス化（既登録はスキップ）"""
    print("=== subtitle_semantic_index build ===")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    registry = load_registry()
    already_indexed = indexed_video_ids(registry)
    print(f"既登録動画: {len(already_indexed)}本")

    all_merged = find_all_merged_jsons()
    print(f"merged JSON総数: {len(all_merged)}本")

    # 未登録を抽出
    to_process = []
    for p in all_merged:
        meta_check = {}
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            meta_check = d.get("metadata", {})
        except Exception:
            pass
        vid = meta_check.get("video_id", p.stem.replace("merged_", ""))
        if vid not in already_indexed:
            to_process.append((vid, p))

    print(f"未登録: {len(to_process)}本 → 処理開始")

    # 既存embeddings読み込み
    existing = load_embeddings()
    print(f"既存チャンク数: {len(existing)}")

    client = get_client()
    new_entries = []

    for i, (video_id, merged_path) in enumerate(to_process):
        print(f"\n[{i+1}/{len(to_process)}] {video_id} ({merged_path.name})")
        chunks = chunk_merged_json(merged_path)
        if not chunks:
            print(f"  チャンク0件 → スキップ")
            continue

        print(f"  チャンク数: {len(chunks)}")
        texts = [c["text"] for c in chunks]
        embeds = embed_texts(client, texts)

        video_entries = []
        for chunk, emb in zip(chunks, embeds):
            entry = {
                "video_id": chunk["video_id"],
                "start_ms": chunk["start_ms"],
                "end_ms": chunk["end_ms"],
                "text": chunk["text"],
                "embedding": emb,
            }
            video_entries.append(entry)

        new_entries.extend(video_entries)

        # レジストリ更新
        registry["videos"].append({
            "video_id": video_id,
            "merged_json": str(merged_path),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "chunk_count": len(video_entries),
        })
        # 中間保存（中断対策）
        all_entries = existing + new_entries
        save_embeddings(all_entries)
        save_registry(registry)

    all_entries = existing + new_entries
    print(f"\n=== インデックス構築 ===")
    print(f"合計チャンク数: {len(all_entries)}")
    build_faiss_index(all_entries)
    save_registry(registry)
    print(f"登録動画数: {len(registry['videos'])}本")
    print("=== 完了 ===")


def cmd_update(args):
    """新規merged JSONのみ追加（build --skipと同等）"""
    cmd_build(args)


def cmd_search(args):
    """セマンティック検索"""
    query = args.query
    top_k = args.top

    entries = load_embeddings()
    if not entries:
        print("ERROR: インデックスが空です。先に build を実行してください")
        sys.exit(1)

    print(f"クエリ: {query}")
    print(f"インデックス: {len(entries)}チャンク")

    client = get_client()
    q_embs = embed_texts(client, [query], task_type="RETRIEVAL_QUERY")
    q_embed = np.array(q_embs, dtype=np.float32)

    # FAISSインデックスがあれば使う、なければ構築
    index = load_faiss_index()
    if index is None or index.ntotal != len(entries):
        print("FAISSインデックスを構築中...")
        index = build_faiss_index(entries)
        if index is None:
            sys.exit(1)

    faiss.normalize_L2(q_embed)
    distances, ids = index.search(q_embed, min(top_k, len(entries)))

    print(f"\n=== 検索結果 (Top {top_k}) ===")
    for rank, (idx, score) in enumerate(zip(ids[0], distances[0]), 1):
        if idx < 0:
            continue
        e = entries[idx]
        start_sec = e["start_ms"] / 1000
        end_sec = e["end_ms"] / 1000
        start_fmt = f"{int(start_sec//60):02d}:{start_sec%60:05.2f}"
        end_fmt = f"{int(end_sec//60):02d}:{end_sec%60:05.2f}"
        print(f"\n[{rank}] score={score:.4f} video_id={e['video_id']} {start_fmt}〜{end_fmt}")
        preview = e["text"][:200].replace("\n", " ")
        print(f"  {preview}")


def main():
    parser = argparse.ArgumentParser(description="字幕セマンティック検索インデックス")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", help="全merged JSONからインデックス構築（未登録のみ）")
    sub.add_parser("update", help="新規merged JSONを追加（buildと同等）")

    s_parser = sub.add_parser("search", help="セマンティック検索")
    s_parser.add_argument("query", help="検索クエリ")
    s_parser.add_argument("--top", type=int, default=10, help="表示件数 (default: 10)")

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
