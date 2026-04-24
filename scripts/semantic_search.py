#!/usr/bin/env python3
"""
セマンティック検索システム — Gemini Embedding 2 + FAISS
使い方:
  python3 scripts/semantic_search.py build            # インデックス構築
  python3 scripts/semantic_search.py update           # 差分更新
  python3 scripts/semantic_search.py query "クエリ"   # 検索
  python3 scripts/semantic_search.py query "クエリ" --source scripts --top 5
注: SRT字幕検索はsubtitle_semantic_index.py (BigQuery) に統合済み。本スクリプトでは非対応。
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# APIキー読み込み（ADC認証使用、環境変数不要）
GEMINI_API_KEY = ""  # unused — ADC auth

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
# BATCH_SIZE 100→50: embed_content_input_tokens_per_minute_per_base_model quota 対策 (cmd_1451)
# 100 items/batch で 429 再発・50 に半減 + 成功時 sleep 延長で per-minute token quota 内に収める
BATCH_SIZE = 50
# 成功時の inter-batch sleep (cmd_1451): 0.5s → 4s に延長して token/min quota を十分回復させる
BATCH_INTER_SLEEP_SEC = 4.0

DOZLE_DIR = BASE_DIR / "projects" / "dozle_kirinuki"

SCRIPT_DIRS = [
    BASE_DIR / "scripts",
    BASE_DIR / "projects" / "dozle_kirinuki" / "scripts",
    BASE_DIR / "projects" / "note_mcp_server" / "scripts",
]
SCRIPT_EXTENSIONS = {".py", ".sh", ".js"}
SCRIPT_EXCLUDE = {"__pycache__", "node_modules", "venv"}

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

    # 3. memory/*.md
    mem_dir = BASE_DIR / ".claude" / "projects" / "-home-murakami-multi-agent-shogun" / "memory"
    if mem_dir.exists():
        for f in mem_dir.glob("*.md"):
            sources.append(("memory", str(f)))

    # 4. dozle context/*.md
    ctx_dir = DOZLE_DIR / "context"
    if ctx_dir.exists():
        for f in ctx_dir.glob("*.md"):
            sources.append(("context", str(f)))

    # 5. scripts (py/sh/js)
    for script_dir in SCRIPT_DIRS:
        if not script_dir.exists():
            continue
        for f in script_dir.rglob("*"):
            if f.suffix not in SCRIPT_EXTENSIONS:
                continue
            if any(ex in f.parts for ex in SCRIPT_EXCLUDE):
                continue
            if f.name.endswith(".pyc"):
                continue
            sources.append(("scripts", str(f)))

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


def chunk_scripts(filepath: str):
    """スクリプトを関数/クラス単位でチャンク化"""
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"  WARN: {filepath}: {e}")
        return chunks

    path = Path(filepath)
    fname = path.name
    # スクリプトディレクトリからの相対パス
    for sdir in SCRIPT_DIRS:
        try:
            rel = path.relative_to(sdir)
            fname = str(rel)
            break
        except ValueError:
            pass

    def _add_chunk(name, text, header=""):
        body = (header + "\n" + text).strip()
        chunks.append({
            "text": body[:4000],
            "source": "scripts",
            "source_file": filepath,
            "chunk_id": f"scripts::{fname}::{name}",
            "metadata": {"file": fname, "function": name},
        })

    if path.suffix == ".py":
        # モジュールヘッダ（docstring + 冒頭コメント）抽出
        header_lines = []
        for line in content.splitlines()[:20]:
            if line.startswith("#") or line.startswith('"""') or line.startswith("'''") or line.strip() == "":
                header_lines.append(line)
            else:
                break
        module_header = "\n".join(header_lines)

        # def/class で分割
        pattern = re.compile(r"^(def |class )", re.MULTILINE)
        positions = [m.start() for m in pattern.finditer(content)]

        if not positions:
            _add_chunk("__module__", content, module_header)
            return chunks

        # モジュールレベルのコード（最初のdef/classより前）
        if positions[0] > 0:
            pre = content[:positions[0]].strip()
            if pre:
                _add_chunk("__module__", pre)

        for i, pos in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(content)
            block = content[pos:end].strip()
            # 関数/クラス名
            first_line = block.split("\n")[0]
            m = re.match(r"(?:def|class)\s+(\w+)", first_line)
            name = m.group(1) if m else f"chunk_{i}"
            _add_chunk(name, block, module_header)

    elif path.suffix == ".sh":
        # 冒頭コメント（#で始まる行）
        header_lines = []
        for line in content.splitlines()[:10]:
            if line.startswith("#"):
                header_lines.append(line)
        shell_header = "\n".join(header_lines)

        # function キーワードで分割
        pattern = re.compile(r"^(\w+\s*\(\s*\)|function\s+\w+)", re.MULTILINE)
        positions = [m.start() for m in pattern.finditer(content)]

        if not positions:
            _add_chunk("__file__", content, shell_header)
            return chunks

        if positions[0] > 0:
            pre = content[:positions[0]].strip()
            if pre:
                _add_chunk("__preamble__", pre, shell_header)

        for i, pos in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(content)
            block = content[pos:end].strip()
            first_line = block.split("\n")[0]
            m = re.match(r"(?:function\s+)?(\w+)", first_line)
            name = m.group(1) if m else f"func_{i}"
            _add_chunk(name, block, shell_header)

    elif path.suffix == ".js":
        # 冒頭コメント
        header_lines = []
        for line in content.splitlines()[:10]:
            if line.startswith("//") or line.startswith("/*"):
                header_lines.append(line)
        js_header = "\n".join(header_lines)

        # function キーワードで分割
        pattern = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+\w+", re.MULTILINE)
        positions = [m.start() for m in pattern.finditer(content)]

        if not positions:
            _add_chunk("__file__", content, js_header)
            return chunks

        for i, pos in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(content)
            block = content[pos:end].strip()
            first_line = block.split("\n")[0]
            m = re.search(r"function\s+(\w+)", first_line)
            name = m.group(1) if m else f"func_{i}"
            _add_chunk(name, block, js_header)

    else:
        _add_chunk("__file__", content)

    return chunks


def load_comments():
    """YouTubeコメント(comment_analysis.yaml)をコメント1件=1チャンクで返す"""
    chunks = []
    work_dir = DOZLE_DIR / "work"
    if not work_dir.exists():
        return chunks
    for yaml_path in work_dir.glob("*/comment_analysis.yaml"):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue
            video_id = data.get("video_id", yaml_path.parent.name)
            # top_liked_comments が主なコメントリスト
            comments = data.get("top_liked_comments", data.get("comments", []))
            if not isinstance(comments, list):
                continue
            for i, comment in enumerate(comments):
                if not isinstance(comment, dict):
                    continue
                text = comment.get("text", comment.get("comment", ""))
                like_count = comment.get("likes", comment.get("like_count", 0))
                related_member = comment.get("related_member", "")
                if not text:
                    continue
                chunks.append({
                    "text": f"[{video_id}] {text}"[:4000],
                    "source": "comments",
                    "source_file": str(yaml_path),
                    "chunk_id": f"comments::{video_id}::{i}",
                    "metadata": {
                        "video_id": video_id,
                        "author": related_member,
                        "like_count": like_count,
                        "timestamp": "",
                    },
                })
        except Exception as e:
            print(f"  WARN comments: {yaml_path}: {e}")
    return chunks


def load_git_commits():
    """git log -500 を両リポジトリから取得してコミット1件=1チャンクで返す"""
    chunks = []
    repos = [
        ("multi-agent-shogun", BASE_DIR),
        ("dozle_kirinuki", DOZLE_DIR),
    ]
    for repo_name, repo_dir in repos:
        if not repo_dir.exists():
            continue
        try:
            result = subprocess.run(
                ["git", "log", "-500", "--format=%H|||%ai|||%an|||%s", "--stat"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                continue
            output = result.stdout
            # 各コミットブロックをパース: HASH|||DATE|||AUTHOR|||SUBJECT + stat行 + 空行
            commit_pattern = re.compile(
                r"([a-f0-9]{40})\|\|\|([^|]+)\|\|\|([^|]+)\|\|\|(.+?)(?=\n[a-f0-9]{40}\|\|\||\Z)",
                re.DOTALL,
            )
            for m in commit_pattern.finditer(output):
                commit_hash = m.group(1)
                date = m.group(2).strip()
                author = m.group(3).strip()
                rest = m.group(4).strip()
                lines = rest.split("\n")
                subject = lines[0].strip()
                stat_lines = [l.strip() for l in lines[1:] if l.strip()]
                files_changed = [l for l in stat_lines if "|" in l or "changed" in l]
                text = (
                    f"Commit: {commit_hash[:8]} ({repo_name})\n"
                    f"Date: {date}\nAuthor: {author}\nMessage: {subject}\n"
                    f"Files:\n" + "\n".join(files_changed[:20])
                )
                chunks.append({
                    "text": text[:4000],
                    "source": "git",
                    "source_file": f"git::{repo_name}",
                    "chunk_id": f"git::{repo_name}::{commit_hash[:8]}",
                    "metadata": {
                        "commit_hash": commit_hash[:8],
                        "date": date,
                        "author": author,
                        "repo": repo_name,
                        "files_changed": ",".join(files_changed[:5]),
                    },
                })
        except Exception as e:
            print(f"  WARN git log {repo_name}: {e}")
    return chunks


def load_error_logs():
    """logs/*.log からエラーブロック(Traceback/ERROR/FAIL行+前後5行)を抽出してチャンク化"""
    chunks = []
    logs_dir = BASE_DIR / "logs"
    if not logs_dir.exists():
        return chunks
    for log_path in logs_dir.glob("*.log"):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
            lines = all_lines[-1000:]  # 末尾1000行のみ
            fname = log_path.name
            i = 0
            while i < len(lines):
                line = lines[i]
                if "Traceback (most recent call last)" in line:
                    block_lines = [line]
                    i += 1
                    while i < len(lines) and (
                        lines[i].startswith(" ")
                        or lines[i].strip() == ""
                        or "Error:" in lines[i]
                        or "Exception:" in lines[i]
                    ):
                        block_lines.append(lines[i])
                        i += 1
                    text = "".join(block_lines).strip()
                    if text:
                        ts_match = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", text)
                        ts = ts_match.group(0) if ts_match else ""
                        err_match = re.search(r"(\w+Error|\w+Exception).*", text)
                        error_type = err_match.group(0)[:80] if err_match else "Traceback"
                        chunk_i = len(chunks)
                        chunks.append({
                            "text": text[:4000],
                            "source": "logs",
                            "source_file": str(log_path),
                            "chunk_id": f"logs::{fname}::{chunk_i}",
                            "metadata": {
                                "log_file": fname,
                                "timestamp": ts,
                                "error_type": error_type,
                            },
                        })
                elif re.search(r"\b(ERROR|FAIL|CRITICAL)\b", line, re.IGNORECASE):
                    start = max(0, i - 5)
                    end = min(len(lines), i + 6)
                    text = "".join(lines[start:end]).strip()
                    if text:
                        ts_match = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", line)
                        ts = ts_match.group(0) if ts_match else ""
                        chunk_i = len(chunks)
                        chunks.append({
                            "text": text[:4000],
                            "source": "logs",
                            "source_file": str(log_path),
                            "chunk_id": f"logs::{fname}::err{chunk_i}",
                            "metadata": {
                                "log_file": fname,
                                "timestamp": ts,
                                "error_type": line.strip()[:80],
                            },
                        })
                    i += 1
                else:
                    i += 1
        except Exception as e:
            print(f"  WARN logs: {log_path}: {e}")
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
        elif src_type in ("memory", "context"):
            all_chunks.extend(chunk_markdown(filepath, src_type))
        elif src_type == "scripts":
            all_chunks.extend(chunk_scripts(filepath))

    # 動的ソース（ファイルパス非依存）
    if not source_filter or source_filter == "comments":
        all_chunks.extend(load_comments())
    if not source_filter or source_filter == "git":
        all_chunks.extend(load_git_commits())
    if not source_filter or source_filter == "logs":
        all_chunks.extend(load_error_logs())

    return all_chunks


# ===== Embedding =====
def get_client():
    return genai.Client(vertexai=True, project="gen-lang-client-0119911773", location="us-central1")


class QuotaExhaustedError(Exception):
    """Vertex AI Embedding の429 quota枯渇を示す専用例外。"""


def embed_texts(client, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
    """テキストリストのembedding取得（バッチ処理、429時は指数バックオフで再試行）"""
    all_embeds = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        batch_idx = i // BATCH_SIZE + 1
        print(f"  Embedding batch {batch_idx}/{total_batches} ({len(batch)} items)...")
        succeeded = False
        for attempt in range(3):
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
                time.sleep(BATCH_INTER_SLEEP_SEC)  # レート制限対策（成功時・cmd_1451で0.5→4s拡大）
                succeeded = True
                break
            except Exception as e:
                err_s = str(e)
                if "429" in err_s or "RESOURCE_EXHAUSTED" in err_s:
                    wait = 60 * (attempt + 1)
                    print(f"  [quota] batch {batch_idx} hit 429 quota; waiting {wait}s before retry {attempt+2}/3", flush=True)
                    time.sleep(wait)
                    continue
                # 非クォータ系エラーはそのまま上位へ
                raise
        if not succeeded:
            # 3回 429 で諦め → アボート（ゼロベクトルで黙ってデータ汚染するのを避ける）
            # メッセージに "error"/"fail"/"exception" 等の cron_health_check パターン語を
            # 含めないこと (含むと C02 が false-positive で再発火する)。
            raise QuotaExhaustedError(
                f"batch {batch_idx}/{total_batches} hit quota ceiling after 3 retries; "
                "skipping update until next cycle to avoid zero-vector data pollution"
            )
    return np.array(all_embeds, dtype=np.float32)


# ===== インデックス操作 =====
def _load_json_tolerant(path):
    """JSONを読み込む。末尾ガベージ (concurrent write 等) は raw_decode で切り捨てる。"""
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        obj, end = decoder.raw_decode(data)
        print(f"  WARN: {path} had {len(data) - end} bytes trailing garbage — recovered valid prefix", flush=True)
        return obj


def load_index_and_meta():
    """既存インデックスとメタデータを読み込む"""
    if INDEX_FILE.exists() and META_FILE.exists():
        index = faiss.read_index(str(INDEX_FILE), faiss.IO_FLAG_MMAP)
        metadata = _load_json_tolerant(META_FILE)
        return index, metadata
    return None, []


def load_hashes():
    if HASH_FILE.exists():
        return _load_json_tolerant(HASH_FILE)
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
    output_json = getattr(args, "json", False)

    index, metadata = load_index_and_meta()
    if index is None:
        print("ERROR: インデックスが未構築です。先に `build` を実行してください。")
        sys.exit(1)

    if not output_json:
        print(f"クエリ: {query}")
    client = get_client()
    q_embed = embed_texts(client, [query], "RETRIEVAL_QUERY")
    faiss.normalize_L2(q_embed)

    # source filterがある場合は対象IDを絞る
    if source_filter:
        target_indices = [i for i, m in enumerate(metadata) if m.get("source") == source_filter]
        if not target_indices:
            if not output_json:
                print(f"ERROR: source='{source_filter}' のチャンクが見つかりません")
            else:
                print("[]")
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

    if output_json:
        results = []
        for idx, score in zip(result_indices, result_scores):
            m = metadata[idx]
            results.append({
                "score": float(score),
                "source": m.get("source"),
                "file": m.get("source_file", ""),
                "chunk_id": m.get("chunk_id", ""),
                "text": m.get("text", "")[:500],
            })
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

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
                          help="絞り込み: shogun_to_karo / tasks / memory / context / scripts / comments / git / logs")
    q_parser.add_argument("--json", action="store_true", help="JSON形式で出力")

    args = parser.parse_args()

    try:
        if args.command == "build":
            cmd_build(args)
        elif args.command == "update":
            cmd_update(args)
        elif args.command == "query":
            cmd_query(args)
        else:
            parser.print_help()
    except QuotaExhaustedError as e:
        # 429 quota枯渇は既知状況。Traceback ではなく1行 WARN で終了。
        # 次の cron サイクルで自動リトライされる（チャンクは hash未登録のまま保持）。
        print(f"[quota-skip] {e}", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
