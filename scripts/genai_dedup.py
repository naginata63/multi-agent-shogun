#!/usr/bin/env python3
"""
genai_dedup.py — 3段階重複排除スクリプト

レポートのトピックをURL一致→タイトル単語一致→Embedding類似度の3段階でチェックし、
直近7日分のキャッシュと比較して重複を除去する。

Usage:
  python3 scripts/genai_dedup.py [YYYY-MM-DD]
  source ~/.bashrc && GEMINI_API_KEY=<key> python3 scripts/genai_dedup.py
"""

import json
import math
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "genai_daily"
CACHE_FILE = REPORTS_DIR / ".dedup_cache.json"
CACHE_DAYS = 7

GEMINI_API_KEY = os.environ.get("VERTEX_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
EMBED_MODEL = "gemini-embedding-2-preview"
SIMILARITY_THRESHOLD = 0.85
TITLE_OVERLAP_THRESHOLD = 0.6


def log(msg: str):
    print(f"[dedup] {msg}", flush=True)


# ===== キャッシュ操作 =====

def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"WARN: キャッシュ読み込み失敗: {e}")
        return {}


def save_cache(cache: dict):
    """7日以内のエントリのみ保持して保存"""
    cutoff = (datetime.now() - timedelta(days=CACHE_DAYS)).strftime("%Y-%m-%d")
    cache_trimmed = {k: v for k, v in cache.items() if k >= cutoff}
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache_trimmed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_cache_entries(cache: dict, exclude_date: str) -> list[dict]:
    """指定日を除くキャッシュエントリを全件返す"""
    entries = []
    for date, items in cache.items():
        if date == exclude_date:
            continue
        for item in items:
            entries.append({**item, "_date": date})
    return entries


# ===== 類似度計算 =====

def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def is_title_overlap(title1: str, title2: str) -> bool:
    """タイトル単語一致チェック（既存is_duplicate()相当）"""
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())
    if not words1 or not words2:
        return False
    overlap = len(words1 & words2) / max(len(words1), len(words2))
    return overlap >= TITLE_OVERLAP_THRESHOLD


# ===== Embedding取得 =====

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Gemini APIでembeddingを取得。失敗時は空リストで代替"""
    if not texts:
        return []
    if not GEMINI_API_KEY:
        log("WARN: GEMINI_API_KEY未設定。Embeddingチェックをスキップ")
        return [[] for _ in texts]

    try:
        from google import genai
    except ImportError:
        log("WARN: google-genai未インストール。Embeddingチェックをスキップ")
        return [[] for _ in texts]

    client = genai.Client(api_key=GEMINI_API_KEY)
    results = []
    for i, text in enumerate(texts):
        try:
            response = client.models.embed_content(
                model=EMBED_MODEL,
                contents=text,
            )
            results.append(list(response.embeddings[0].values))
        except Exception as e:
            log(f"WARN: Embedding取得失敗 [{i}]: {e}")
            results.append([])
    return results


# ===== マークダウンパース =====

def parse_report(content: str) -> tuple[str, list[dict]]:
    """
    レポートをヘッダー部分とトピックリストに分割。

    Returns:
        header: # 生成AI ... の冒頭ブロック
        topics: [{title, url, summary, raw_block}, ...]
    """
    # ## で始まる行の前後で分割
    blocks = re.split(r'\n(?=## )', '\n' + content)

    header = ""
    topics = []

    for block in blocks:
        if not block.strip():
            continue
        if block.lstrip().startswith('## '):
            block = block.lstrip('\n')
            title_line = block.split('\n')[0]
            # アイコン・星評価を除去してタイトルを抽出
            title_clean = re.sub(r'^##\s+', '', title_line)
            title_clean = re.sub(r'[★☆]{1,5}\s*', '', title_clean).strip()

            # URL抽出: **ソース**: [xxx](URL)
            url_match = re.search(r'\*\*ソース\*\*.*?\]\((https?://[^\)]+)\)', block)
            url = url_match.group(1) if url_match else ""

            # 要約（タイトル行の次の行から **ソース** 行まで）
            lines = block.split('\n')[1:]
            summary_lines = []
            for line in lines:
                if line.startswith('**ソース**') or line.strip() == '---':
                    break
                if line.strip():
                    summary_lines.append(line.strip())
            summary = ' '.join(summary_lines)[:200]

            topics.append({
                "title": title_clean,
                "url": url,
                "summary": summary,
                "raw_block": block,
            })
        else:
            header += block

    return header.strip(), topics


def rebuild_report(header: str, topics: list[dict]) -> str:
    """ヘッダーと残存トピックからレポートを再構築。トピック数も更新"""
    # トピック数を更新
    new_header = re.sub(
        r'\*\*トピック数\*\*:.*',
        f'**トピック数**: {len(topics)}件',
        header,
    )

    parts = [new_header.strip()]
    for topic in topics:
        block = topic["raw_block"].rstrip()
        # --- 区切りがなければ追加
        if not block.endswith('---'):
            block += '\n\n---'
        parts.append(block)

    return '\n\n'.join(parts) + '\n'


# ===== 重複チェック =====

def check_duplicate(
    topic: dict,
    cache_entries: list[dict],
    topic_embeddings: dict[str, list[float]],
) -> tuple[bool, str]:
    """
    3段階重複チェック。
    Returns: (is_duplicate, reason_string)
    """
    # Stage 1: URL完全一致
    if topic["url"]:
        for entry in cache_entries:
            if entry.get("url") and entry["url"] == topic["url"]:
                return True, f"URL一致({entry['_date']}): {entry['url'][:60]}"

    # Stage 2: タイトル単語一致
    for entry in cache_entries:
        if entry.get("title") and is_title_overlap(topic["title"], entry["title"]):
            return True, f"タイトル類似({entry['_date']}): {entry['title'][:40]}"

    # Stage 3: Embedding類似度
    topic_emb = topic_embeddings.get(topic["title"], [])
    if topic_emb:
        for entry in cache_entries:
            entry_emb = entry.get("embedding", [])
            if entry_emb:
                sim = cosine_similarity(topic_emb, entry_emb)
                if sim >= SIMILARITY_THRESHOLD:
                    return True, f"Embedding類似(sim={sim:.3f}, {entry['_date']}): {entry['title'][:40]}"

    return False, ""


# ===== メイン =====

def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    report_file = REPORTS_DIR / f"{date_str}.md"

    if not report_file.exists():
        log(f"ERROR: レポートが存在しません: {report_file}")
        sys.exit(1)

    log(f"=== genai重複排除開始 date={date_str} ===")

    # レポート読み込み・パース
    content = report_file.read_text(encoding="utf-8")
    header, topics = parse_report(content)
    log(f"トピック数: {len(topics)}件")

    if not topics:
        log("トピックなし、スキップ")
        return

    # キャッシュ読み込み
    cache = load_cache()
    cache_entries = get_cache_entries(cache, exclude_date=date_str)
    log(f"キャッシュ: {len(cache_entries)}件エントリ（{len(cache)}日分）")

    if not cache_entries:
        log("比較対象キャッシュなし。Embeddingのみ取得してキャッシュ保存")

    # Embedding取得（全トピック）
    log(f"Embedding取得中（{len(topics)}件）...")
    embed_texts = [f"{t['title']} {t['summary'][:100]}" for t in topics]
    embeddings_list = get_embeddings(embed_texts)
    topic_embeddings = {
        t["title"]: emb
        for t, emb in zip(topics, embeddings_list)
    }

    # 重複チェック
    remaining = []
    removed = []
    for topic in topics:
        is_dup, reason = check_duplicate(topic, cache_entries, topic_embeddings)
        if is_dup:
            log(f"  [除去] {topic['title'][:50]} — {reason}")
            removed.append(topic)
        else:
            remaining.append(topic)

    log(f"重複: {len(removed)}件除去 / {len(remaining)}件残存")

    # レポート更新（重複があった場合のみ書き換え）
    if removed:
        new_content = rebuild_report(header, remaining)
        report_file.write_text(new_content, encoding="utf-8")
        log(f"レポート更新完了: {report_file}")
    else:
        log("重複なし、レポート更新スキップ")

    # 今日のトピックをキャッシュに保存（除去分も含む — 将来の重複防止のため）
    today_entries = []
    for topic in topics:
        today_entries.append({
            "title": topic["title"],
            "url": topic["url"],
            "summary_short": topic["summary"][:100],
            "embedding": topic_embeddings.get(topic["title"], []),
        })

    cache[date_str] = today_entries
    save_cache(cache)
    log(f"キャッシュ保存完了: {len(today_entries)}件 → {CACHE_FILE}")
    log("=== 完了 ===")


if __name__ == "__main__":
    main()
