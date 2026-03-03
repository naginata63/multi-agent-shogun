#!/usr/bin/env python3
"""
生成AI 技術トレンド日報 — レポート生成ロジック
依存: Python標準ライブラリのみ (urllib, xml.etree.ElementTree, json, datetime)

使い方:
  python3 scripts/genai_daily_fetch.py [YYYY-MM-DD] [output_path]
"""

import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import os
import html
import re


# JST timezone
JST = timezone(timedelta(hours=9))

# RSS/Atom フィード一覧 (15サイト以上)
FEEDS = [
    # === AI企業公式ブログ ===
    ("Google AI Blog",     "https://feeds.feedburner.com/blogspot/gJZg"),
    ("Microsoft AI Blog",  "https://blogs.microsoft.com/ai/feed/"),
    ("DeepMind Blog",      "https://deepmind.google/blog/rss.xml"),
    ("Amazon Science",     "https://www.amazon.science/index.rss"),
    # === テックメディア ===
    ("TechCrunch AI",      "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge",          "https://www.theverge.com/rss/index.xml"),
    ("VentureBeat AI",     "https://venturebeat.com/category/ai/feed/"),
    ("Ars Technica AI",    "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("MIT Tech Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed/"),
    # === 学術・OSS ===
    ("arXiv cs.AI",        "http://arxiv.org/rss/cs.AI"),
    ("arXiv cs.CL",        "http://arxiv.org/rss/cs.CL"),
    ("HuggingFace Blog",   "https://huggingface.co/blog/feed.xml"),
    ("Apple ML",           "https://machinelearning.apple.com/rss.xml"),
    # === 日本語サイト ===
    ("ITmedia AI+",        "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"),
    ("ITmedia NEWS",       "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml"),
    ("@IT",                "https://rss.itmedia.co.jp/rss/2.0/ait.xml"),
    ("GIGAZINE",           "https://gigazine.net/news/rss_2.0/"),
    ("Publickey",          "https://www.publickey1.jp/atom.xml"),
    ("ASCII.jp",           "https://ascii.jp/rss.xml"),
    ("CNET Japan",         "https://japan.cnet.com/rss/index.rdf"),
    ("マイナビニュース",     "https://news.mynavi.jp/rss/index.rdf"),
    ("Impress Watch",      "https://www.watch.impress.co.jp/data/rss/1.0/ipw/feed.rdf"),
    ("PC Watch",           "https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf"),
]

# 日本語フィードのソース名セット（ソート優先度判定用）
JAPANESE_SOURCES = {
    "ITmedia AI+", "ITmedia NEWS", "@IT", "GIGAZINE", "Publickey",
    "ASCII.jp", "CNET Japan", "マイナビニュース", "Impress Watch", "PC Watch",
}

# 1フィードあたり最大取得件数
MAX_ITEMS_PER_FEED = 5
# レポート全体の最大トピック数 (23フィード×5件上限=115。全フィードを網羅するため余裕を持たせる)
MAX_TOTAL_ITEMS = 120

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GenAIReportBot/1.0; +https://github.com/murakami/multi-agent-shogun)"
}

# カテゴリ分類
CATEGORY_KEYWORDS = {
    "model": ["model", "release", "launch", "gpt", "claude", "gemini", "llama",
              "mistral", "grok", "deepseek", "モデル", "発表", "リリース"],
    "paper": ["paper", "arxiv", "research", "benchmark", "evaluation", "survey",
              "論文", "研究", "ベンチマーク"],
    "api":   ["api", "pricing", "price", "token", "cost", "billing", "rate limit",
              "API", "価格", "料金", "課金"],
    "oss":   ["open source", "github", "open-source", "huggingface", "library",
              "framework", "オープンソース", "ライブラリ"],
    "news":  ["acquire", "acquisition", "partnership", "funding", "invest",
              "買収", "提携", "資金調達", "投資"],
}

CATEGORY_ICONS = {
    "model": "🤖", "paper": "📄", "api": "💰", "oss": "🛠️", "news": "📢",
}

# 生成AI関連記事のキーワードフィルタ（"AI" は別途 re.search(\bAI\b) で判定するため除外）
AI_KEYWORDS = [
    # 英語
    "LLM", "GPT", "Claude", "Gemini", "Llama", "ChatGPT",
    "machine learning", "deep learning", "neural", "transformer",
    "diffusion", "generative", "large language model", "AI agent",
    "multimodal", "foundation model", "Anthropic", "OpenAI",
    "Google DeepMind", "Meta AI", "Mistral",
    # 日本語
    "生成AI", "人工知能", "機械学習", "ディープラーニング", "大規模言語モデル",
    "チャットボット", "プロンプト", "自動生成", "AIエージェント", "言語モデル",
]

# AI専門フィード（これらのソースはキーワードフィルタをスキップし、除外パターンのみ適用）
AI_SPECIALIZED_SOURCES = {
    "ITmedia AI+", "TechCrunch AI", "MIT Tech Review AI",
    "arXiv cs.AI", "arXiv cs.CL", "HuggingFace Blog",
    "DeepMind Blog", "Google AI Blog", "Microsoft AI Blog",
    "Amazon Science", "Apple ML", "VentureBeat AI",
}

# AI無関係記事の除外パターン（タイトルにこれらが含まれる場合は除外）
NON_AI_EXCLUDE_PATTERNS = [
    "AirPods", "iPad Air", "iPad mini", "HomePod", "Apple Watch",
    "iPhone 1", "iPhone SE", "MacBook", "iMac", "Mac mini",
    "PlayStation", "Xbox", "Nintendo",
    # HW商品名（CPU/SoC型番に含まれる "AI" の誤検知対策）
    "Ryzen AI", "Snapdragon", "Core Ultra", "Qualcomm",
    # 買い物・セール記事
    "お買い得", "セール", "クーポン", "円引き", " OFF",
    # 広告
    "[Sponsored]", "[PR]", "[AD]", "Sponsored",
    # その他非AI
    "Mastodon", "VAIOバッテリー",
]


def is_ai_related(title: str, summary: str, source: str = "") -> bool:
    """タイトルと要約にAI関連キーワードが含まれるか判定"""
    # 除外パターンチェック（AI関連キーワードがあっても除外）
    for pattern in NON_AI_EXCLUDE_PATTERNS:
        if pattern.lower() in title.lower():
            return False
    # AI専門フィードはキーワードフィルタをスキップ（除外パターンのみ適用）
    if source in AI_SPECIALIZED_SOURCES:
        return True
    # "AI"（英大文字）は単語境界マッチで判定（"VAIO"→"vaio"内の"ai"誤検知を防ぐ）
    if re.search(r'\bAI\b', title + " " + summary):
        return True
    # 残りのキーワードは従来の部分文字列マッチ
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in AI_KEYWORDS)


def classify_category(title: str, summary: str) -> tuple[str, str]:
    text = (title + " " + summary).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw.lower() in text for kw in keywords):
            return cat, CATEGORY_ICONS[cat]
    return "news", "📢"  # デフォルト


def is_recent(pub_date_str: str, hours: int = 48) -> bool:
    """pubDate文字列が直近N時間以内かチェック"""
    if not pub_date_str:
        return True  # 日付不明はスルー
    try:
        # RSS形式: "Mon, 02 Mar 2026 08:00:00 +0000"
        dt = parsedate_to_datetime(pub_date_str)
        now = datetime.now(timezone.utc)
        return (now - dt.astimezone(timezone.utc)).total_seconds() < hours * 3600
    except Exception:
        pass
    try:
        # Atom / ISO 8601形式
        dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - dt.astimezone(timezone.utc)).total_seconds() < hours * 3600
    except Exception:
        return True  # パース失敗もスルー


def is_duplicate(new_title: str, seen_titles: list[str], threshold: float = 0.6) -> bool:
    new_words = set(new_title.lower().split())
    for seen in seen_titles:
        seen_words = set(seen.lower().split())
        if not new_words or not seen_words:
            continue
        overlap = len(new_words & seen_words) / max(len(new_words), len(seen_words))
        if overlap >= threshold:
            return True
    return False


def clean_html(text: str) -> str:
    """HTMLタグを除去してテキストを返す"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate(text: str, max_chars: int = 300) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def fetch_feed(name: str, url: str) -> list[dict]:
    """RSSまたはAtomフィードを取得してアイテムリストを返す"""
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"  [WARN] {name}: フィード取得失敗 — {e}", file=sys.stderr)
        return items

    # Atom フィード判定
    is_atom = root.tag.startswith("{http://www.w3.org/2005/Atom}")

    if is_atom:
        # Atom
        atom_ns = "http://www.w3.org/2005/Atom"
        for entry in root.findall(f"{{{atom_ns}}}entry")[:MAX_ITEMS_PER_FEED]:
            title_el   = entry.find(f"{{{atom_ns}}}title")
            link_el    = entry.find(f"{{{atom_ns}}}link")
            summary_el = entry.find(f"{{{atom_ns}}}summary")
            content_el = entry.find(f"{{{atom_ns}}}content")
            updated_el = entry.find(f"{{{atom_ns}}}updated")

            title   = clean_html(title_el.text if title_el is not None else "")
            link    = link_el.get("href", "") if link_el is not None else ""
            summary = clean_html(
                (content_el.text if content_el is not None else None)
                or (summary_el.text if summary_el is not None else "")
            )
            pub_date = updated_el.text if updated_el is not None else ""
            if title:
                cat, cat_icon = classify_category(title, summary)
                items.append({
                    "source": name, "url": url,
                    "title": title, "link": link, "summary": summary,
                    "pub_date": pub_date, "category": cat, "category_icon": cat_icon,
                })
    else:
        # RSS 2.0 / RSS 1.0
        channel = root.find("channel")
        if channel is None:
            # RSS 1.0 (RDF): items at root level
            rdf_ns = "http://purl.org/rss/1.0/"
            for item in root.findall(f"{{{rdf_ns}}}item")[:MAX_ITEMS_PER_FEED]:
                title_el  = item.find(f"{{{rdf_ns}}}title")
                link_el   = item.find(f"{{{rdf_ns}}}link")
                desc_el   = item.find(f"{{{rdf_ns}}}description")
                date_el   = item.find("pubDate") or item.find(f"{{{rdf_ns}}}date")
                title   = clean_html(title_el.text if title_el is not None else "")
                link    = link_el.text if link_el is not None else ""
                summary = clean_html(desc_el.text if desc_el is not None else "")
                pub_date = date_el.text if date_el is not None else ""
                if title:
                    cat, cat_icon = classify_category(title, summary)
                    items.append({
                        "source": name, "url": url,
                        "title": title, "link": link, "summary": summary,
                        "pub_date": pub_date, "category": cat, "category_icon": cat_icon,
                    })
        else:
            for item in channel.findall("item")[:MAX_ITEMS_PER_FEED]:
                title_el = item.find("title")
                link_el  = item.find("link")
                desc_el  = item.find("description")
                date_el  = item.find("pubDate")
                title   = clean_html(title_el.text if title_el is not None else "")
                link    = link_el.text if link_el is not None else ""
                summary = clean_html(desc_el.text if desc_el is not None else "")
                pub_date = date_el.text if date_el is not None else ""
                if title:
                    cat, cat_icon = classify_category(title, summary)
                    items.append({
                        "source": name, "url": url,
                        "title": title, "link": link, "summary": summary,
                        "pub_date": pub_date, "category": cat, "category_icon": cat_icon,
                    })

    print(f"  [OK] {name}: {len(items)}件取得", file=sys.stderr)
    return items


def build_report(date_str: str, all_items: list[dict]) -> str:
    now_jst = datetime.now(JST)
    time_str = now_jst.strftime("%H:%M JST")
    total = len(all_items)

    lines = [
        "# 生成AI 技術トレンド日報",
        f"**日付**: {date_str}",
        f"**生成日時**: {time_str}",
        f"**トピック数**: {total}件",
        "",
        "---",
        "",
    ]

    for item in all_items:
        title      = item["title"]
        link       = item.get("link", "")
        summary    = truncate(item.get("summary", ""), 300)
        source     = item["source"]
        cat_icon   = item.get("category_icon", "📢")

        lines.append(f"## {cat_icon} {title}")
        lines.append("")
        if summary:
            lines.append(summary)
            lines.append("")
        if link:
            lines.append(f"**ソース**: [{source}]({link})")
        else:
            lines.append(f"**ソース**: {source}")
        lines.append("")

    if total == 0:
        lines.append("※ 本日はRSSフィードから取得できるトピックがありませんでした。")

    return "\n".join(lines)


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now(JST).strftime("%Y-%m-%d")
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"[INFO] 生成AI日報生成開始 — {date_str}", file=sys.stderr)
    print(f"[INFO] フィード数: {len(FEEDS)}サイト", file=sys.stderr)

    all_items: list[dict] = []
    seen_titles: list[str] = []

    filtered_out = 0
    for name, url in FEEDS:
        items = fetch_feed(name, url)
        for item in items:
            # 日付フィルタ（直近48時間以内）
            if not is_recent(item.get("pub_date", ""), hours=48):
                continue
            # キーワードフィルタ（生成AI無関係記事を除外）
            if not is_ai_related(item["title"], item.get("summary", ""), item["source"]):
                filtered_out += 1
                continue
            # 重複排除
            if is_duplicate(item["title"], seen_titles):
                continue
            seen_titles.append(item["title"])
            all_items.append(item)
            if len(all_items) >= MAX_TOTAL_ITEMS:
                break
        if len(all_items) >= MAX_TOTAL_ITEMS:
            break

    print(f"[INFO] キーワードフィルタ: {filtered_out}件除外", file=sys.stderr)

    # 日本語ソース優先ソート（日本語記事を先頭に）
    all_items.sort(key=lambda x: 0 if x.get("source") in JAPANESE_SOURCES else 1)

    report = build_report(date_str, all_items)

    if output_path:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[INFO] レポート出力: {output_path}", file=sys.stderr)
    else:
        print(report)

    print(f"[INFO] 完了 — トピック数: {len(all_items)}", file=sys.stderr)


if __name__ == "__main__":
    main()
