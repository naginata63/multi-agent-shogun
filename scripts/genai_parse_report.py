#!/usr/bin/env python3
"""
genai_parse_report.py — genai日報MDを解析してtopics JSONを出力
Usage: python3 scripts/genai_parse_report.py YYYY-MM-DD
出力: JSON配列をstdout
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "genai_daily"
OGP_CACHE_FILE = REPORTS_DIR / ".ogp_cache.json"


def fetch_ogp_image(url: str) -> str | None:
    """URLからOGP画像URLを取得。失敗時はNone。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read(524288).decode("utf-8", errors="ignore")
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
        return m.group(1) if m else None
    except Exception:
        return None

# ## 🤖 ★★★☆☆ タイトル  or  ## 📝 ［★★★☆☆ 個人ブログ］タイトル
SECTION_RE = re.compile(
    r'^## ([\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF🤖📢🛠️💰📄\U0001F300-\U0001F9FF]+)\s+(?:［([\★☆]+)\s+[^］]+］|([\★☆]+))\s*(.+)$'
)
SOURCE_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def count_stars(stars_str: str) -> int:
    return stars_str.count('★')


def extract_first_url(source_line: str) -> str:
    """ソース行から最初の有効なURLを取得。"""
    for m in SOURCE_RE.finditer(source_line):
        url = m.group(2)
        if url.startswith('http'):
            return url
    return ''


def parse_report(date_str: str) -> list:
    md_path = REPORTS_DIR / f"{date_str}.md"
    if not md_path.exists():
        print(f"[parse_report] ERROR: {md_path} が見つかりません", file=sys.stderr)
        return []

    # OGPキャッシュ読み込み
    ogp_cache = {}
    if OGP_CACHE_FILE.exists():
        try:
            ogp_cache = json.loads(OGP_CACHE_FILE.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            pass

    text = md_path.read_text(encoding='utf-8')
    lines = text.splitlines()

    topics = []
    current = None
    body_lines = []
    cache_updated = False

    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            # 前のトピックを確定
            if current is not None:
                current['summary'] = ' '.join(body_lines).strip()
                topics.append(current)

            category = m.group(1).strip()
            stars_str = m.group(2) or m.group(3)  # group(2)=bracket form, group(3)=normal form
            title = m.group(4).strip()
            current = {
                'title': title,
                'category': category,
                'score': count_stars(stars_str),
                'summary': '',
                'url': '',
                'ogp_image': None,
            }
            body_lines = []
            continue

        if current is None:
            continue

        # ソース行
        if line.strip().startswith('**ソース**:'):
            url = extract_first_url(line)
            if url:
                current['url'] = url
                ogp = ogp_cache.get(url)
                if ogp is None and url not in ogp_cache:
                    ogp = fetch_ogp_image(url)
                    ogp_cache[url] = ogp
                    cache_updated = True
                current['ogp_image'] = ogp
            continue

        # 区切り線
        if line.strip() == '---':
            continue

        # 空行はスキップ（bodyは非空行のみ）
        if line.strip():
            body_lines.append(line.strip())

    # 最後のトピック
    if current is not None:
        current['summary'] = ' '.join(body_lines).strip()
        topics.append(current)

    # キャッシュ更新
    if cache_updated:
        try:
            OGP_CACHE_FILE.write_text(
                json.dumps(ogp_cache, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    return topics


if __name__ == '__main__':
    date_str = sys.argv[1] if len(sys.argv) > 1 else __import__('datetime').date.today().isoformat()
    topics = parse_report(date_str)
    print(json.dumps(topics, ensure_ascii=False, indent=2))
