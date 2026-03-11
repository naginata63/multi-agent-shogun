#!/usr/bin/env python3
"""
セマンティック検索システム — Gemini Embedding 2 + FAISS
使い方:
  python3 scripts/semantic_search.py build            # インデックス構築
  python3 scripts/semantic_search.py update           # 差分更新
  python3 scripts/semantic_search.py query "クエリ"   # 検索
  python3 scripts/semantic_search.py query "クエリ" --source srt --top 5
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

# GEMINI_API_KEY読み込み（~/.bashrcから設定済み前提）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

import faiss
import numpy as np
import yaml

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("ERROR: google-genai not installed. Run: pip install google-genai")
    sys.exit(1)

# ===== 設定 =====
BASE_DIR = Path(__file__).parent.parent
INDEX_DIR = BASE_DIR / "data" / "semantic_index"
INDEX_FILE = INDEX_DIR / "index.faiss"
META_FILE = INDEX_DIR / "metadata.json"
HASH_FILE = INDEX_DIR / "chunk_hashes.json"

EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072
BATCH_SIZE = 100

DOZLE_DIR = BASE_DIR / "projects" / "dozle_kirinuki"

# ===== ソース定義 =====
def get_data_sources():
    sources = []

    # 1. shogun_to_karo.yaml (cmd単位)
    skf = BASE_DIR / "queue" / "shogun_to_karo.yaml"
    if skf.exists():
        sources.append(("shogun_to_karo", str(skf)))

    # 2. tasks/*.yaml (task単位)
    tasks_dir = BASE_DIR / "queue" / "tasks"
    if tasks_dir.exists():
        for f in tasks_dir.glob("*.yaml"):
            sources.append(("tasks", str(f)))

    # 3. SRT files
    work_dir = DOZLE_DIR / "work"
    if work_dir.exists():
        for srt in work_dir.rglob("fine_grained_with_speakers.srt"):
            sources.append(("srt", str(srt)))

    # 4. memory/*.md
    mem_dir = BASE_DIR / ".claude" / "projects" / "-home-murakami-multi-agent-shogun" / "memory"
    if mem_dir.exists():
        for f in mem_dir.glob("*.md"):
            sources.append(("memory", str(f)))

    # 5. dozle context/*.md
    ctx_dir = DOZLE_DIR / "context"
    if ctx_dir.exists():
        for f in ctx_dir.glob("*.md"):
            sources.append(("context", str(f)))

    return sources


# ===== チャンク分割 =====
def chunk_shogun_to_karo(filepath: str):
    """cmd単位でチャンク化。YAMLパースエラー時はrawテキストフォールバック"""
    chunks = []

    def _add_cmd(cmd_id, text):
        chunks.append({
            "text": text[:4000],
            "source": "shogun_to_karo",
            "source_file": filepath,
            "chunk_id": f"shogun_to_karo::{cmd_id}",
            "metadata": {"cmd_id": str(cmd_id)},
        })

    # YAMLパース試行
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data:
            cmds = data.get("commands", data.get("cmd_history", []))
            if isinstance(cmds, list):
                for cmd in cmds:
                    if isinstance(cmd, dict):
                        cmd_id = cmd.get("cmd_id", cmd.get("id", "unknown"))
                        text = yaml.dump(cmd, allow_unicode=True, default_flow_style=False)
                        _add_cmd(cmd_id, text)
                if chunks:
                    return chunks
    except Exception:
        pass  # フォールバックへ

    # フォールバック: rawテキストをcmd/id区切りで分割
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # "- id: cmd_XXX" または "- cmd_id: cmd_XXX" パターンで分割
        pattern = re.compile(r"(?=^- (?:id|cmd_id): (cmd_\w+))", re.MULTILINE)
        parts = pattern.split(content)
        # split returns: [before, cmd_id, block, cmd_id, block, ...]
        i = 1
        while i + 1 < len(parts):
            cmd_id = parts[i]
            block = parts[i + 1]
            _add_cmd(cmd_id, f"- id: {cmd_id}\n{block}")
            i += 2
        if chunks:
            return chunks
        # さらにフォールバック: ファイル全体を1チャンクに
        _add_cmd("all", content[:4000])
    except Exception as e:
        print(f"  WARN raw fallback: {filepath}: {e}")

    return chunks


def chunk_tasks_yaml(filepath: str):
    """task単位でチャンク化"""
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return chunks
        tasks = data.get("tasks", [])
        if isinstance(tasks, list):
            for task in tasks:
                if isinstance(task, dict):
                    task_id = task.get("task_id", task.get("id", "unknown"))
                    text = yaml.dump(task, allow_unicode=True, default_flow_style=False)
                    chunks.append({
                        "text": text[:4000],
                        "source": "tasks",
                        "source_file": filepath,
                        "chunk_id": f"tasks::{task_id}",
                        "metadata": {"task_id": str(task_id), "file": Path(filepath).name},
                    })
    except Exception as e:
        print(f"  WARN: {filepath}: {e}")
    return chunks


def chunk_srt(filepath: str, window_seconds=30):
    """30秒単位でSRTをチャンク化"""
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # SRTパース
        pattern = re.compile(
            r"(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n(.*?)(?=\n\n|\Z)",
            re.DOTALL,
        )
        entries = []
        for m in pattern.finditer(content):
            start_str = m.group(2).replace(",", ".")
            parts = start_str.split(":")
            start_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            text = m.group(4).strip().replace("\n", " ")
            entries.append((start_sec, text))

        if not entries:
            return chunks

        # 30秒ウィンドウでグループ化
        fname = Path(filepath).parent.parent.name  # work/XXX
        window_start = entries[0][0]
        window_texts = []

        def flush_window(ws, we, texts):
            if texts:
                chunks.append({
                    "text": " ".join(texts),
                    "source": "srt",
                    "source_file": filepath,
                    "chunk_id": f"srt::{fname}::{int(ws)}-{int(we)}",
                    "metadata": {
                        "video": fname,
                        "start_sec": ws,
                        "end_sec": we,
                    },
                })

        for sec, text in entries:
            if sec - window_start >= window_seconds:
                flush_window(window_start, sec, window_texts)
                window_start = sec
                window_texts = [text]
            else:
                window_texts.append(text)

        flush_window(window_start, window_start + window_seconds, window_texts)

    except Exception as e:
        print(f"  WARN: {filepath}: {e}")
    return chunks


def chunk_markdown(filepath: str, source_type: str):
    """##見出し単位でMarkdownをチャンク化"""
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # ## 見出しで分割
        sections = re.split(r"(?=^#{1,3} )", content, flags=re.MULTILINE)
        fname = Path(filepath).stem

        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            # タイトル抽出
            first_line = section.split("\n")[0].strip("# ").strip()
            chunks.append({
                "text": section[:4000],
                "source": source_type,
                "source_file": filepath,
                "chunk_id": f"{source_type}::{fname}::{i}::{first_line[:40]}",
                "metadata": {"file": fname, "section": first_line[:80]},
            })
    except Exception as e:
        print(f"  WARN: {filepath}: {e}")
    return chunks


def collect_chunks(source_filter: Optional[str] = None):
    """全チャンクを収集"""
    all_chunks = []
    sources = get_data_sources()

    for src_type, filepath in sources:
        if source_filter and src_type != source_filter:
            continue
        if not Path(filepath).exists():
            continue

        if src_type == "shogun_to_karo":
            all_chunks.extend(chunk_shogun_to_karo(filepath))
        elif src_type == "tasks":
            all_chunks.extend(chunk_tasks_yaml(filepath))
        elif src_type == "srt":
            all_chunks.extend(chunk_srt(filepath))
        elif src_type in ("memory", "context"):
            all_chunks.extend(chunk_markdown(filepath, src_type))

    return all_chunks


# ===== Embedding =====
def get_client():
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set. Run: source ~/.bashrc")
        sys.exit(1)
    return genai.Client(api_key=GEMINI_API_KEY)


def embed_texts(client, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
    """テキストリストのembedding取得（バッチ処理）"""
    all_embeds = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        print(f"  Embedding batch {i//BATCH_SIZE + 1}/{(len(texts) + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} items)...")
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
                all_embeds.append(emb.values)
            time.sleep(0.5)  # レート制限対策
        except Exception as e:
            print(f"  ERROR embedding batch: {e}")
            # ゼロベクトルで代替
            for _ in batch:
                all_embeds.append([0.0] * EMBED_DIM)
    return np.array(all_embeds, dtype=np.float32)


# ===== インデックス操作 =====
def load_index_and_meta():
    """既存インデックスとメタデータを読み込む"""
    if INDEX_FILE.exists() and META_FILE.exists():
        index = faiss.read_index(str(INDEX_FILE))
        with open(META_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return index, metadata
    return None, []


def load_hashes():
    if HASH_FILE.exists():
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_hashes(hashes: dict):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


def chunk_hash(chunk: dict) -> str:
    return hashlib.md5(chunk["text"].encode("utf-8")).hexdigest()


def cmd_build(args):
    """インデックスをフルビルド"""
    print("=== インデックス構築開始 ===")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    print("チャンク収集中...")
    chunks = collect_chunks()
    print(f"  {len(chunks)} チャンク収集完了")

    if not chunks:
        print("ERROR: チャンクが0件です")
        sys.exit(1)

    client = get_client()
    texts = [c["text"] for c in chunks]
    embeds = embed_texts(client, texts, "RETRIEVAL_DOCUMENT")

    print("FAISSインデックス構築中...")
    index = faiss.IndexFlatIP(EMBED_DIM)  # 内積（正規化後=コサイン類似度）
    # L2正規化
    faiss.normalize_L2(embeds)
    index.add(embeds)

    faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    hashes = {c["chunk_id"]: chunk_hash(c) for c in chunks}
    save_hashes(hashes)

    print(f"=== 完了: {len(chunks)} チャンク → {INDEX_FILE} ===")


def cmd_update(args):
    """差分更新"""
    print("=== インデックス差分更新 ===")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    existing_index, existing_meta = load_index_and_meta()
    existing_hashes = load_hashes()
    existing_ids = {m["chunk_id"] for m in existing_meta} if existing_meta else set()

    print("チャンク収集中...")
    new_chunks = collect_chunks()
    print(f"  {len(new_chunks)} チャンク収集完了")

    # 新規・変更チャンクを特定
    to_add = []
    for c in new_chunks:
        cid = c["chunk_id"]
        h = chunk_hash(c)
        if cid not in existing_ids or existing_hashes.get(cid) != h:
            to_add.append(c)

    print(f"  新規/変更: {len(to_add)} チャンク")

    if not to_add:
        print("更新不要")
        return

    client = get_client()
    texts = [c["text"] for c in to_add]
    embeds = embed_texts(client, texts, "RETRIEVAL_DOCUMENT")
    faiss.normalize_L2(embeds)

    if existing_index is None:
        index = faiss.IndexFlatIP(EMBED_DIM)
        all_meta = []
    else:
        index = existing_index
        all_meta = existing_meta

    index.add(embeds)
    all_meta.extend(to_add)

    faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)

    # ハッシュ更新
    for c in to_add:
        existing_hashes[c["chunk_id"]] = chunk_hash(c)
    save_hashes(existing_hashes)

    print(f"=== 完了: {len(to_add)} チャンク追加 → 合計 {len(all_meta)} チャンク ===")


def cmd_query(args):
    """検索"""
    query = args.query
    top_k = args.top
    source_filter = args.source

    index, metadata = load_index_and_meta()
    if index is None:
        print("ERROR: インデックスが未構築です。先に `build` を実行してください。")
        sys.exit(1)

    print(f"クエリ: {query}")
    client = get_client()
    q_embed = embed_texts(client, [query], "RETRIEVAL_QUERY")
    faiss.normalize_L2(q_embed)

    # source filterがある場合は対象IDを絞る
    if source_filter:
        target_indices = [i for i, m in enumerate(metadata) if m.get("source") == source_filter]
        if not target_indices:
            print(f"ERROR: source='{source_filter}' のチャンクが見つかりません")
            sys.exit(1)
        # サブインデックス構築
        sub_embeds = np.zeros((len(target_indices), EMBED_DIM), dtype=np.float32)
        for new_i, orig_i in enumerate(target_indices):
            vec = index.reconstruct(orig_i)
            sub_embeds[new_i] = vec
        sub_index = faiss.IndexFlatIP(EMBED_DIM)
        sub_index.add(sub_embeds)
        distances, sub_ids = sub_index.search(q_embed, min(top_k, len(target_indices)))
        result_indices = [target_indices[si] for si in sub_ids[0] if si >= 0]
        result_scores = distances[0]
    else:
        distances, ids = index.search(q_embed, top_k)
        result_indices = [i for i in ids[0] if i >= 0]
        result_scores = distances[0]

    print(f"\n=== 検索結果 (top {len(result_indices)}) ===")
    for rank, (idx, score) in enumerate(zip(result_indices, result_scores), 1):
        m = metadata[idx]
        print(f"\n[{rank}] score={score:.4f} source={m.get('source')} chunk_id={m.get('chunk_id')}")
        print(f"  file: {m.get('source_file', '')}")
        if m.get("metadata"):
            for k, v in m["metadata"].items():
                print(f"  {k}: {v}")
        # テキストの先頭200文字
        text_preview = m.get("text", "")[:200].replace("\n", " ")
        print(f"  preview: {text_preview}...")


def main():
    parser = argparse.ArgumentParser(description="Gemini Embedding 2 + FAISS セマンティック検索")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", help="インデックスをフルビルド")
    sub.add_parser("update", help="差分更新")

    q_parser = sub.add_parser("query", help="検索")
    q_parser.add_argument("query", help="検索クエリ")
    q_parser.add_argument("--top", type=int, default=10, help="表示件数 (default: 10)")
    q_parser.add_argument("--source", type=str, default=None,
                          help="絞り込み: shogun_to_karo / tasks / srt / memory / context")

    args = parser.parse_args()

    if args.command == "build":
        cmd_build(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "query":
        cmd_query(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
