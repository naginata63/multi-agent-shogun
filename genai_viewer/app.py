#!/usr/bin/env python3
"""生成AIレポートビューア — stdlib版 (Flask不要)"""
import json
import re
import urllib.parse
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STATIC_DIR = Path(__file__).parent / "static"
REPORTS_DIR = Path(__file__).parent.parent / "reports" / "genai_daily"
FEEDBACK_FILE = Path(__file__).parent.parent / "queue" / "genai_feedback.yaml"
OGP_CACHE_FILE = REPORTS_DIR / ".ogp_cache.json"
PORT = 8580

CATEGORY_MAP = {
    "🤖": "model",
    "📄": "paper",
    "💰": "api",
    "🛠️": "oss",
    "📢": "news",
}


def _load_ogp_cache() -> dict:
    if OGP_CACHE_FILE.exists():
        try:
            return json.loads(OGP_CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _enrich_topics_with_ogp(topics: list) -> list:
    """キャッシュからOGP画像URLを付与する（取得はしない）。"""
    cache = _load_ogp_cache()
    for topic in topics:
        url = topic.get("source_url", "")
        topic["ogp_image"] = cache.get(url) if url and url != "#" else None
    return topics


def _get_category(emoji: str) -> tuple:
    """絵文字からカテゴリ文字列とアイコンを返す。"""
    for icon, category in CATEGORY_MAP.items():
        if emoji.startswith(icon):
            return category, icon
    return "other", emoji[:2] if emoji else ""


def _parse_report(md_text: str) -> list:
    """Markdownテキストからトピックリストを返す。"""
    topics = []
    lines = md_text.splitlines()

    current_title = None
    current_icon = ""
    current_category = ""
    current_score = 0
    summary_lines = []
    in_topic = False

    source_pattern = re.compile(
        r'\*\*ソース\*\*:\s*\[([^\]]+)\]\(([^)]+)\)'
    )

    def flush_topic():
        nonlocal summary_lines, current_score
        if current_title is None:
            return
        source_name = ""
        source_url = ""
        cleaned = []
        for line in summary_lines:
            m = source_pattern.search(line)
            if m:
                source_name = m.group(1)
                source_url = m.group(2)
            else:
                cleaned.append(line)
        summary = "\n".join(cleaned).strip()
        topics.append({
            "title": current_title,
            "category": current_category,
            "category_icon": current_icon,
            "score": current_score,
            "summary": summary,
            "source_name": source_name,
            "source_url": source_url,
        })

    for line in lines:
        if line.startswith("## "):
            if in_topic:
                flush_topic()

            heading = line[3:].strip()
            category, icon = _get_category(heading)
            # スコア ★★★★☆ を heading から抽出（絵文字除去前に行う）
            # 星の数を numeric score に変換: ★☆☆☆☆=1,★★=2,★★★=3,★★★★=4,★★★★★=5
            score = 0
            star_m = re.search(r'(★[★☆]{4})\s*', heading)
            if star_m:
                stars = star_m.group(1)
                score = stars.count('★') * 20  # 1→20, 2→40, 3→60, 4→80, 5→100
                heading = heading[:star_m.start()] + heading[star_m.end():]
            # 先頭の絵文字ブロックを除去
            title = re.sub(r'^[^\w\d\u3000-\u9FFF\uF900-\uFAFF]+', '', heading)

            current_title = title.strip()
            current_icon = icon
            current_category = category
            current_score = score
            summary_lines = []
            in_topic = True

        elif line.strip() == "---":
            if in_topic:
                flush_topic()
                in_topic = False
                current_title = None
                summary_lines = []

        elif in_topic:
            summary_lines.append(line)

    if in_topic and current_title:
        flush_topic()

    return topics


def _list_dates() -> list:
    """日付降順でレポートファイル名（拡張子なし）を返す。テスト・ハイフン含むファイルは除外。"""
    if not REPORTS_DIR.exists():
        return []
    dates = []
    for f in REPORTS_DIR.glob("*.md"):
        stem = f.stem
        if "test" in stem or stem.count("-") != 2:
            continue
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', stem):
            dates.append(stem)
    return sorted(dates, reverse=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self.send_json({"error": "not found"}, 404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

        elif path.startswith("/static/"):
            rel = path[len("/static/"):]
            ext = rel.rsplit(".", 1)[-1]
            ctype = {"js": "application/javascript", "css": "text/css"}.get(ext, "application/octet-stream")
            self.send_file(STATIC_DIR / rel, ctype)

        elif path == "/api/dates":
            self.send_json({"dates": _list_dates()})

        elif path.startswith("/api/report/"):
            date = path[len("/api/report/"):]
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                self.send_json({"error": "invalid date"}, 400)
                return
            md_path = REPORTS_DIR / f"{date}.md"
            if not md_path.exists():
                self.send_json({"error": "not found"}, 404)
                return
            md_text = md_path.read_text(encoding="utf-8")
            topics = _parse_report(md_text)
            # スコアが付いている場合はスコア降順でソート
            if any(t["score"] > 0 for t in topics):
                topics = sorted(topics, key=lambda t: t["score"], reverse=True)
            topics = _enrich_topics_with_ogp(topics)
            self.send_json({"date": date, "markdown": md_text, "topics": topics})

        elif path == "/api/search":
            qs = urllib.parse.parse_qs(parsed.query)
            q = (qs.get("q", [""])[0]).lower()
            cat = qs.get("category", [""])[0]
            results = []
            for date in _list_dates():
                md_path = REPORTS_DIR / f"{date}.md"
                if not md_path.exists():
                    continue
                try:
                    md_text = md_path.read_text(encoding="utf-8")
                except OSError:
                    continue
                for topic in _parse_report(md_text):
                    if cat and topic["category"] != cat:
                        continue
                    if q and q not in topic["title"].lower() and q not in topic["summary"].lower():
                        continue
                    results.append({"date": date, "topic": topic})
                    if len(results) >= 50:
                        self.send_json({"results": results})
                        return
            self.send_json({"results": results})

        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/feedback":
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_json({"error": "invalid JSON"}, 400)
                return

            article_title = body.get("article_title", "")
            date = body.get("date", "")
            reaction = body.get("reaction", "")

            if reaction not in ("up", "down", "none"):
                self.send_json({"error": "reaction must be 'up', 'down', or 'none'"}, 400)
                return
            if not article_title or not date:
                self.send_json({"error": "article_title and date are required"}, 400)
                return
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                self.send_json({"error": "date must be YYYY-MM-DD"}, 400)
                return

            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            entry = (
                f"- title: {json.dumps(article_title, ensure_ascii=False)}\n"
                f"  date: \"{date}\"\n"
                f"  reaction: \"{reaction}\"\n"
                f"  timestamp: \"{timestamp}\"\n"
            )

            FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
            with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
                f.write(entry)

            self.send_json({"status": "ok", "timestamp": timestamp})
        else:
            self.send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[GenAI Viewer] http://0.0.0.0:{PORT}")
    server.serve_forever()
