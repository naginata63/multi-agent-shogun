#!/usr/bin/env python3
"""OGP画像URL事前取得スクリプト。

reports/genai_daily/YYYY-MM-DD.md からソースURLを抽出し、
各URLのOGP画像URLを取得して .ogp_cache.json に保存する。

Usage:
    python3 scripts/genai_ogp_prefetch.py [YYYY-MM-DD]
    引数なしなら今日の日付を使用。
"""
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).parent.parent / "reports" / "genai_daily"
OGP_CACHE_FILE = REPORTS_DIR / ".ogp_cache.json"

SOURCE_PATTERN = re.compile(r'\*\*ソース\*\*:\s*\[([^\]]+)\]\(([^)]+)\)')


def load_cache() -> dict:
    if OGP_CACHE_FILE.exists():
        try:
            return json.loads(OGP_CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_cache(cache: dict):
    try:
        OGP_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        OGP_CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        print(f"[OGP] キャッシュ保存失敗: {e}", flush=True)


def extract_urls_from_md(md_path: Path) -> list:
    """MDファイルからソースURLリストを抽出。"""
    urls = []
    try:
        text = md_path.read_text(encoding="utf-8")
        for m in SOURCE_PATTERN.finditer(text):
            url = m.group(2)
            if url and url != "#" and url.startswith("http"):
                urls.append(url)
    except OSError as e:
        print(f"[OGP] MDファイル読み取り失敗: {e}", flush=True)
    return urls


def fetch_ogp_image(url: str) -> str | None:
    """URLからOGP画像URLを取得。失敗時はNone。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read(262144).decode("utf-8", errors="ignore")
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
        return m.group(1) if m else None
    except Exception as e:
        print(f"[OGP] SKIP: {url[:60]} -> {e}", flush=True)
        return None


def main():
    if len(sys.argv) >= 2:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    md_path = REPORTS_DIR / f"{date_str}.md"
    if not md_path.exists():
        print(f"[OGP] レポートが存在しません: {md_path}", flush=True)
        sys.exit(0)

    urls = extract_urls_from_md(md_path)
    print(f"[OGP] {date_str}: {len(urls)}件のURLを処理します", flush=True)

    cache = load_cache()
    updated = 0
    for url in urls:
        if url in cache:
            print(f"[OGP] キャッシュ済み: {url[:60]}", flush=True)
            continue
        img_url = fetch_ogp_image(url)
        cache[url] = img_url
        updated += 1
        status = "取得" if img_url else "なし"
        print(f"[OGP] {status}: {url[:60]}", flush=True)

    if updated > 0:
        save_cache(cache)
        print(f"[OGP] キャッシュ更新: {updated}件追加 -> {OGP_CACHE_FILE}", flush=True)
    else:
        print("[OGP] 新規URLなし、キャッシュ更新不要", flush=True)


if __name__ == "__main__":
    main()
