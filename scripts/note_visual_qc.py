#!/usr/bin/env python3
"""note記事 視覚QCスクリプト — Gemini Vision 3分割拡大スクショ自動検証

使い方:
    python3 note_visual_qc.py --url "https://editor.note.com/notes/XXX/edit/"

前提:
    - Chrome起動: google-chrome --remote-debugging-port=9222
    - gcloud ADC認証済み
"""

import argparse
import os
import sys
import tempfile
import yaml
from datetime import datetime
from pathlib import Path

from google import genai
from playwright.sync_api import sync_playwright

# --- Config ---
CDP_URL = "http://localhost:9222"
PROJECT = "gen-lang-client-0119911773"
LOCATION = "global"
MODEL = "gemini-2.5-flash"
VIEWPORT_WIDTH = 800
SECTION_HEIGHT = 1200
REPORT_DIR = Path("/home/murakami/multi-agent-shogun/queue/reports")

QC_PROMPT = """このnote記事エディタのスクリーンショットを厳しくQCせよ。
以下の問題がないか確認:
(1) Markdown記法の生テキスト残り（#, ##, ###, **, --, <!-- -->, ---等）
(2) HTMLコメントが本文に表示（<!-- --> が見える）
(3) タイトルが二重表示（記事タイトル欄と本文両方に同じテキスト）
(4) 見出しがプレーンテキストになっている（H2/H3ブロックでなく生テキスト）
(5) 画像が欠落または不正な位置に配置
(6) テキストや画像の表示崩れ

問題があれば具体的に指摘せよ。問題がなければ「PASS」と答えよ。"""


def take_screenshots(page) -> list[dict]:
    """ページを3分割でスクショ撮影し、[(path, label), ...]を返す。"""
    total_h = page.evaluate("document.body.scrollHeight")
    screenshots = []

    sections = [
        ("top", 0, min(SECTION_HEIGHT, total_h // 3)),
        ("middle", total_h // 3, SECTION_HEIGHT),
        ("bottom", total_h * 2 // 3, min(SECTION_HEIGHT, total_h - total_h * 2 // 3)),
    ]

    for label, y_offset, height in sections:
        if height <= 0:
            continue
        clip = {"x": 0, "y": y_offset, "width": VIEWPORT_WIDTH, "height": height}
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        page.screenshot(path=tmp.name, clip=clip)
        screenshots.append({"path": tmp.name, "label": label, "y": y_offset, "h": height})
        print(f"  screenshot: {label} y={y_offset} h={height}")

    return screenshots


def analyze_section(client, image_path: str, label: str) -> dict:
    """Gemini 2.5 Flashで1セクションを分析。"""
    from google.genai import types

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    types.Part.from_text(text=QC_PROMPT),
                ],
            ),
        ],
    )

    text = response.text.strip()
    # Gemini may include analysis before the PASS/FAIL verdict
    last_lines = text.split("\n")[-3:]  # check last 3 lines
    passed = any("PASS" in line.upper() and "FAIL" not in line.upper() for line in last_lines) or text.upper().startswith("PASS")
    return {"section": label, "result": "PASS" if passed else "FAIL", "detail": text}


def main():
    parser = argparse.ArgumentParser(description="note記事 視覚QC")
    parser.add_argument("--url", required=True, help="note記事エディタURL")
    parser.add_argument("--cdp", default=CDP_URL, help=f"CDP endpoint (default: {CDP_URL})")
    args = parser.parse_args()

    # Gemini client (Vertex AI ADC)
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    print(f"Gemini client ready: {MODEL}")

    # Playwright → Chrome CDP
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(args.cdp)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page() if not browser.contexts else context.pages[0]

        print(f"Navigating: {args.url}")
        page.goto(args.url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Set viewport for consistent screenshots
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": 900})

        print("Taking 3-section screenshots...")
        screenshots = take_screenshots(page)

        print("Analyzing with Gemini...")
        for ss in screenshots:
            r = analyze_section(client, ss["path"], ss["label"])
            results.append(r)
            print(f"  {r['section']}: {r['result']}")
            # Cleanup temp file
            os.unlink(ss["path"])

    # Overall verdict
    overall = "PASS" if all(r["result"] == "PASS" for r in results) else "FAIL"
    print(f"\n=== Overall: {overall} ===")

    # Report YAML
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"visual_qc_{ts}.yaml"

    report = {
        "url": args.url,
        "timestamp": ts,
        "overall": overall,
        "sections": results,
    }
    with open(report_path, "w") as f:
        yaml.dump(report, f, allow_unicode=True, default_flow_style=False)
    print(f"Report: {report_path}")

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
