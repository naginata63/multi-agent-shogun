#!/usr/bin/env python3
"""
sasuu スタブPDF再取得+md変換スクリプト (cmd_1069)

38本のスタブPDFをPlaywright+殿のChromeセッションで再取得→md変換。
usage: python3 scripts/sasuu_stub_refetch.py [--dry-run] [--start NUM] [--only NUM]
"""
import argparse
import re
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF
from playwright.sync_api import sync_playwright

CHROME_PROFILE = str(Path.home() / ".cache" / "ms-playwright" / "note-profile")
PDF_DIR = Path(__file__).parent.parent / "work" / "cmd_1039" / "pdfs"
MD_DIR = Path(__file__).parent.parent / "work" / "cmd_1039" / "articles"

STUB_NUMS = [
    29, 31, 33, 35, 38, 41, 44, 45, 46, 47, 48, 49,
    51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 63, 64,
    65, 66, 67, 69, 70, 71, 73, 75, 76, 77, 79, 80, 81, 82
]

PAYWALL_PATTERNS = [
    "ここから先は", "この続きをみるには", "有料部分", "購入", "定期購読",
    "続きをみる", "この記事は有料"
]


def extract_url_from_md(num: int) -> tuple[str | None, Path | None]:
    matches = list(MD_DIR.glob(f"{num:03d}_*.md"))
    if not matches:
        return None, None
    md_path = matches[0]
    content = md_path.read_text(encoding="utf-8")
    url_match = re.search(r"\*\*URL\*\*:\s*(https?://\S+)", content)
    if url_match:
        return url_match.group(1), md_path
    return None, md_path


def fetch_pdf_playwright(page, url: str, pdf_path: Path) -> bool:
    """Playwrightでnote記事をPDF化して保存"""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # コンテンツ全体の読み込みを待つ
        page.wait_for_timeout(4000)
        # 記事本文が表示されるまで待つ
        try:
            page.wait_for_selector("article, .note-body, .o-noteContentText", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        # ページ全体をPDFに出力
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
        )
        pdf_path.write_bytes(pdf_bytes)
        return True
    except Exception as e:
        print(f"  ERROR fetch_pdf: {e}")
        return False


def pdf_to_md(pdf_path: Path, md_path: Path) -> tuple[int, int]:
    """PDFをmd変換して上書き保存。(chars, pages)を返す"""
    doc = fitz.open(str(pdf_path))
    pages = doc.page_count
    lines = []
    # md冒頭のURLヘッダを保持
    if md_path.exists():
        old_content = md_path.read_text(encoding="utf-8")
        header_match = re.match(r"(#.*?\n\n\*\*URL\*\*:.*?\n\n---\n\n)", old_content, re.DOTALL)
        if header_match:
            lines.append(header_match.group(1).rstrip())
            lines.append("")
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            lines.append(f"<!-- page {i+1} -->")
            lines.append(text.strip())
    doc.close()
    content = "\n\n".join(lines)
    md_path.write_text(content, encoding="utf-8")
    return len(content), pages


def check_paywall(md_path: Path) -> list[str]:
    """ペイウォール文言をチェック。見つかったキーワードのリストを返す"""
    content = md_path.read_text(encoding="utf-8")
    found = [p for p in PAYWALL_PATTERNS if p in content]
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="URL確認のみ、取得しない")
    parser.add_argument("--start", type=int, default=0, help="この番号以降のみ処理")
    parser.add_argument("--only", type=int, default=0, help="この番号のみ処理")
    args = parser.parse_args()

    target_nums = STUB_NUMS
    if args.only:
        target_nums = [args.only]
    elif args.start:
        target_nums = [n for n in STUB_NUMS if n >= args.start]

    print(f"=== sasuu スタブPDF再取得 ({len(target_nums)}本) ===")

    # URLを事前収集
    targets = []
    for num in target_nums:
        url, md_path = extract_url_from_md(num)
        pdf_matches = list(PDF_DIR.glob(f"{num:03d}_*.pdf"))
        pdf_path = pdf_matches[0] if pdf_matches else PDF_DIR / f"{num:03d}_.pdf"
        targets.append((num, url, md_path, pdf_path))
        if args.dry_run:
            print(f"  {num:03d}: {url or 'NO URL'}")

    if args.dry_run:
        print("dry-run完了。取得しない。")
        return

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE,
            headless=True,
        )
        page = browser.pages[0] if browser.pages else browser.new_page()

        for i, (num, url, md_path, pdf_path) in enumerate(targets):
            print(f"\n[{i+1}/{len(targets)}] {num:03d}: {url}")
            if not url:
                print(f"  SKIP: URLなし")
                results.append({"num": num, "status": "skip", "reason": "no_url"})
                continue

            # PDF取得
            ok = fetch_pdf_playwright(page, url, pdf_path)
            if not ok:
                results.append({"num": num, "status": "error", "reason": "fetch_failed"})
                continue

            # 取得後のPDF文字数確認
            doc = fitz.open(str(pdf_path))
            raw_text = "".join(p.get_text("text") for p in doc)
            pdf_chars = len(raw_text)
            pdf_pages = doc.page_count
            doc.close()
            print(f"  PDF: {pdf_pages}p, {pdf_chars} chars")

            if pdf_chars < 200:
                print(f"  WARNING: スタブ疑い (chars={pdf_chars})")
                results.append({"num": num, "status": "stub", "chars": pdf_chars, "pages": pdf_pages})
                continue

            # md変換
            if md_path:
                md_chars, md_pages = pdf_to_md(pdf_path, md_path)
                print(f"  MD: {md_chars} chars")

                # ペイウォールチェック
                paywall = check_paywall(md_path)
                if paywall:
                    print(f"  WARNING: ペイウォール文言検出: {paywall}")
                    results.append({
                        "num": num, "status": "paywall",
                        "pdf_chars": pdf_chars, "md_chars": md_chars,
                        "paywall_keywords": paywall
                    })
                else:
                    print(f"  OK")
                    results.append({
                        "num": num, "status": "ok",
                        "pdf_chars": pdf_chars, "md_chars": md_chars,
                        "pages": pdf_pages
                    })
            else:
                print(f"  WARNING: mdファイルなし")
                results.append({"num": num, "status": "no_md", "pdf_chars": pdf_chars})

        browser.close()

    # サマリー
    print("\n=== サマリー ===")
    ok = [r for r in results if r["status"] == "ok"]
    ng = [r for r in results if r["status"] != "ok"]
    print(f"成功: {len(ok)}/{len(results)}")
    for r in ok:
        print(f"  ✓ {r['num']:03d}: pdf={r['pdf_chars']}, md={r['md_chars']}")
    if ng:
        print(f"NG ({len(ng)}本):")
        for r in ng:
            print(f"  ✗ {r['num']:03d}: {r['status']} - {r.get('reason', r.get('paywall_keywords', ''))}")

    return len(ng) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
