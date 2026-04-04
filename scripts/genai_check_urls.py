#!/usr/bin/env python3
"""genai_viewer内のJS/HTMLファイルからURLを抽出し、HTTP GETで死活確認する。

使い方: python3 scripts/genai_check_urls.py
出力: work/cmd_1049/url_check_results.txt
"""

import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
TARGET_FILES = [
    BASE / "genai_viewer" / "static" / "app.js",
    BASE / "genai_viewer" / "static" / "index.html",
    BASE / "dist" / "index.html",
    BASE / "dist" / "stats.html",
]
OUTPUT = BASE / "work" / "cmd_1049" / "url_check_results.txt"
TIMEOUT = 5  # 秒

URL_RE = re.compile(r'https?://[^\s"\'<>)}\]]+')


def extract_urls_from_file(path: Path) -> list[str]:
    """ファイルからURLを抽出。JSON内のURLも拾う。"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    # JSON内URL（source_url, ogp_image等）を個別に抽出
    urls: list[str] = []
    seen: set[str] = set()
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(",;")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def check_url(url: str) -> tuple[int, str]:
    """HTTP GETリクエスト送信、(status_code, note)を返す。"""
    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "GenAI-URL-Checker/1.0"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, "OK"
    except urllib.error.HTTPError as e:
        return e.code, f"HTTP Error: {e.reason}"
    except urllib.error.URLError as e:
        return 0, f"URL Error: {e.reason}"
    except Exception as e:
        return 0, str(e)


def main():
    all_urls: list[tuple[str, str]] = []  # (source_file, url)

    for fp in TARGET_FILES:
        if not fp.exists():
            continue
        urls = extract_urls_from_file(fp)
        rel = fp.relative_to(BASE)
        for u in urls:
            all_urls.append((str(rel), u))

    print(f"抽出URL数: {len(all_urls)}")

    results: list[str] = []
    results.append(f"# genai_viewer URL Check Results")
    results.append(f"Date: {datetime.now().isoformat()}")
    results.append(f"Total URLs: {len(all_urls)}")
    results.append("")

    ok_count = 0
    ng_count = 0
    err_count = 0

    for source, url in all_urls:
        status, note = check_url(url)
        if status == 200:
            ok_count += 1
            line = f"[OK] {status} {url}"
        elif status >= 400:
            ng_count += 1
            line = f"[WARN] {status} {note} — {url}"
        elif status > 0:
            ng_count += 1
            line = f"[WARN] {status} {note} — {url}"
        else:
            err_count += 1
            line = f"[ERR] {note} — {url}"
        line += f"  (from {source})"
        results.append(line)
        print(f"  {line}")

    results.append("")
    results.append(f"## Summary")
    results.append(f"- OK: {ok_count}")
    results.append(f"- WARN (non-200): {ng_count}")
    results.append(f"- ERR (connection): {err_count}")
    results.append(f"- Total: {len(all_urls)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(results), encoding="utf-8")
    print(f"\n結果保存先: {OUTPUT}")
    print(f"OK={ok_count} WARN={ng_count} ERR={err_count} / Total={len(all_urls)}")


if __name__ == "__main__":
    main()
