#!/usr/bin/env python3
"""
YouTube Studio 関連動画自動設定スクリプト (cmd_1077)
Playwright CDP方式でYouTube Studioに接続し、ショート動画の「関連動画」を設定する。

cmd_1074の知見: Cookie injectionはDBSC (Device Bound Session Credentials)で失敗する。
そのため、既存ChromeインスタンスのCDP経由で接続する方式を推奨。

使い方:
  # Chromeをデバッグポート付きで起動（初回のみ）
  google-chrome --remote-debugging-port=9222 &

  # 単発設定
  python3 scripts/yt_set_related_video.py --short SHORT_ID --related PARENT_ID

  # バッチ設定
  python3 scripts/yt_set_related_video.py --batch related_videos.yaml

  # ヘッドフル（デバッグ用）
  python3 scripts/yt_set_related_video.py --short SHORT_ID --related PARENT_ID --headed

  # Chrome起動ヘルパー（既存Chromeを終了→デバッグポート付きで再起動）
  python3 scripts/yt_set_related_video.py --launch-chrome
"""

import argparse
import asyncio
import json
import os
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from playwright.async_api import async_playwright, BrowserContext, Page

# ============================================================
# 設定（セレクタはDOM変更に備えて先頭で定義）
# ============================================================
CDP_ENDPOINT = os.environ.get("CDP_ENDPOINT", "http://localhost:9222")
DISPLAY_ENV = os.environ.get("DISPLAY", ":0")
STUDIO_BASE = "https://studio.youtube.com/video"
PAGE_TIMEOUT = 30_000  # ms
ACTION_DELAY = 2.0  # seconds (ToS対策: 操作間の最小ウェイト)
SAVE_WAIT = 5.0  # seconds (保存後の待機)

# YouTube Studio セレクタ（頻繁に変更されるため定数管理）
# 2026-04-03: CDP接続方式でShort編集ページの関連動画ダイアログ構造に更新
SELECTORS = {
    # 関連動画ドロップダウントリガー（Short編集ページのみ表示）
    "related_trigger": [
        'ytcp-text-dropdown-trigger#linked-video-editor-link',
    ],
    # 関連動画ダイアログ内の検索入力（自チャンネル動画検索）
    "search_yours": [
        '#search-yours',
        'input[placeholder*="自分の動画を検索"]',
        'input[placeholder*="Search your videos"]',
    ],
    # 関連動画ダイアログ内の検索入力（他チャンネル動画検索）
    "search_any": [
        '#search-any',
        'input[placeholder*="他のチャンネル"]',
        'input[placeholder*="other channel"]',
    ],
    # 動画選択カード
    "video_card": [
        'ytcp-entity-card.card',
    ],
    # ダイアログ
    "picker_dialog": [
        '#inner-dialog',
    ],
    # 保存ボタン
    "save_button": [
        '#save-button',
        'button[aria-label*="保存"]',
        'button[aria-label*="Save"]',
    ],
}

# バッチYAMLフォーマット例
BATCH_YAML_TEMPLATE = """
# related_videos.yaml
videos:
  - short_id: "SHORT_VIDEO_ID"
    related_id: "PARENT_VIDEO_ID"
  - short_id: "SHORT_VIDEO_ID_2"
    related_id: "PARENT_VIDEO_ID_2"
"""


# ============================================================
# Chrome起動ヘルパー
# ============================================================
async def launch_chrome_with_debug_port() -> None:
    """既存Chromeを終了し、--remote-debugging-port付きで再起動する。"""
    print("[chrome] 既存Chromeプロセスを終了中...")
    subprocess.run(["pkill", "-f", "google-chrome"], capture_output=True)
    await asyncio.sleep(2)

    print("[chrome] デバッグポート付きでChrome起動中...")
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY_ENV

    proc = subprocess.Popen(
        [
            "google-chrome",
            f"--remote-debugging-port=9222",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # デバッグポートが利用可能になるまで待機
    for i in range(30):
        await asyncio.sleep(1)
        try:
            import urllib.request
            with urllib.request.urlopen(f"{CDP_ENDPOINT}/json/version") as resp:
                if resp.status == 200:
                    print(f"[chrome] 起動完了 (PID: {proc.pid})")
                    print(f"[chrome] デバッグポート: {CDP_ENDPOINT}")
                    return
        except Exception:
            pass

    print("[chrome] 警告: 30秒以内にデバッグポートが応答しませんでした")
    print("[chrome] Chromeが起動していることを確認してください")


# ============================================================
# セレクタヘルパー
# ============================================================
async def find_element(page: Page, selector_key: str, timeout: int = 5000) -> Page | None:
    """セレクタリストから最初に見つかった要素を返す。"""
    selectors = SELECTORS.get(selector_key, [])
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=timeout):
                return el
        except Exception:
            continue
    return None


async def scroll_to_element(page: Page, selector_key: str, max_scrolls: int = 10) -> bool:
    """要素が見えるまでスクロールする。"""
    for _ in range(max_scrolls):
        el = await find_element(page, selector_key, timeout=500)
        if el:
            return True
        await page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(0.5)
    return False


# ============================================================
# メインロジック
# ============================================================
async def set_related_video(
    page: Page,
    short_id: str,
    related_id: str,
    related_title: str | None = None,
) -> dict:
    """1件のショート動画に Related video を設定する。

    YouTube Studio Short編集ページの関連動画はドロップダウン形式:
    1. #linked-video-editor-link をクリック → ダイアログ表示
    2. #search-yours で動画を検索（タイトルで検索）
    3. ytcp-entity-card をクリックして選択
    4. 保存ボタンで確定
    """
    result = {
        "short_id": short_id,
        "related_id": related_id,
        "status": "started",
        "error": None,
    }

    snap_dir = Path("work/cmd_1077")
    snap_dir.mkdir(parents=True, exist_ok=True)

    # 1. Short編集ページを開く
    edit_url = f"{STUDIO_BASE}/{short_id}/edit"
    print(f"[nav] {edit_url}")

    try:
        await page.goto(edit_url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
    except Exception as e:
        result["status"] = "navigation_error"
        result["error"] = str(e)
        return result

    await asyncio.sleep(ACTION_DELAY)

    # ログインチェック
    if "accounts.google.com" in page.url or "signin" in page.url.lower():
        result["status"] = "not_logged_in"
        result["error"] = "YouTube Studioにログインしていません。Chromeでログインしてください。"
        return result

    # 2. 関連動画トリガーを探す（スクロールが必要な場合あり）
    print("[search] 関連動画トリガーを探しています...")
    trigger = None
    for _ in range(15):
        try:
            t = page.locator("ytcp-text-dropdown-trigger#linked-video-editor-link")
            if await t.count() > 0 and await t.first.is_visible(timeout=2000):
                trigger = t.first
                break
        except Exception:
            pass
        await page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(0.5)

    if not trigger:
        snap_path = snap_dir / f"snap_no_related_{short_id}.png"
        await page.screenshot(path=str(snap_path))
        result["status"] = "section_not_found"
        result["error"] = (
            f"関連動画トリガーが見つかりません。Short以外の動画の可能性。"
            f"スクリーンショット: {snap_path}"
        )
        return result

    print("[found] 関連動画トリガー発見")

    # 3. トリガーをクリックしてダイアログを開く
    await trigger.click()
    await asyncio.sleep(ACTION_DELAY)

    # 4. 検索入力で関連動画を検索
    # related_titleが指定されていればタイトル検索、なければrelated_idをそのまま使用
    search_query = related_title if related_title else related_id

    print(f"[search] 検索クエリ: {search_query}")

    # 自チャンネルの動画を検索
    search_input = page.locator("#search-yours")
    if await search_input.count() > 0:
        await search_input.click()
        await asyncio.sleep(0.3)
        await search_input.fill("")
        await search_input.type(search_query, delay=30)
        await asyncio.sleep(ACTION_DELAY)
    else:
        snap_path = snap_dir / f"snap_no_search_{short_id}.png"
        await page.screenshot(path=str(snap_path))
        result["status"] = "search_input_not_found"
        result["error"] = f"検索入力が見つかりません。スクリーンショット: {snap_path}"
        return result

    # 5. 検索結果から動画を選択
    print("[select] 動画カードを探しています...")
    cards = page.locator("#inner-dialog ytcp-entity-card.card")
    card_count = await cards.count()
    print(f"[select] カード数: {card_count}")

    if card_count == 0:
        snap_path = snap_dir / f"snap_no_cards_{short_id}.png"
        await page.screenshot(path=str(snap_path))
        result["status"] = "no_results"
        result["error"] = f"検索結果に動画が見つかりません。スクリーンショット: {snap_path}"
        return result

    # 最初のカードをクリック（検索で絞り込まれている前提）
    await cards.first.click()
    await asyncio.sleep(ACTION_DELAY)

    print("[select] 動画選択完了")

    # 6. 保存ボタンをクリック
    save_btn = await find_element(page, "save_button")
    if save_btn:
        print("[save] 保存中...")
        await save_btn.click()
        await asyncio.sleep(SAVE_WAIT)
        print("[save] 保存完了")
    else:
        print("[save] 保存ボタンが見つかりません。自動保存の可能性あり。")
        await asyncio.sleep(3)

    # 7. 結果確認
    snap_path = snap_dir / f"snap_after_save_{short_id}.png"
    await page.screenshot(path=str(snap_path))

    result["status"] = "success"
    result["screenshot"] = str(snap_path)
    return result


async def run_with_cdp(
    short_id: str | None,
    related_id: str | None,
    related_title: str | None,
    batch_file: str | None,
    headed: bool = False,
    cdp_endpoint: str = CDP_ENDPOINT,
) -> list[dict]:
    """CDP接続でYouTube Studioを操作する。"""
    tasks = []

    # タスクリスト構築
    if batch_file:
        if yaml is None:
            print("[error] PyYAMLが必要です: pip install pyyaml")
            sys.exit(1)
        with open(batch_file) as f:
            data = yaml.safe_load(f)
        for item in data.get("videos", []):
            rt = item.get("related_title", item["related_id"])
            tasks.append((item["short_id"], item["related_id"], rt))
    elif short_id and related_id:
        rt = related_title if related_title else related_id
        tasks.append((short_id, related_id, rt))
    else:
        print("[error] --short/--related または --batch を指定してください")
        sys.exit(1)

    all_results = []

    async with async_playwright() as p:
        # CDP接続
        print(f"[cdp] 接続先: {cdp_endpoint}")
        try:
            browser = await p.chromium.connect_over_cdp(cdp_endpoint)
        except Exception as e:
            print(f"[error] CDP接続失敗: {e}")
            print()
            print("Chromeをデバッグポート付きで起動してください:")
            print("  google-chrome --remote-debugging-port=9222 &")
            print()
            print("または本スクリプトの --launch-chrome オプションを使用してください。")
            sys.exit(1)

        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = await browser.new_context()

        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()

        # 各タスクを実行
        for i, (sid, rid, rtitle) in enumerate(tasks):
            print(f"\n{'='*60}")
            print(f"[{i+1}/{len(tasks)}] short={sid} related={rid} title={rtitle}")
            print(f"{'='*60}")

            result = await set_related_video(page, sid, rid, rtitle)
            all_results.append(result)

            status = result["status"]
            if status == "not_logged_in":
                print(f"[error] ログインが必要です。以降のタスクを中止します。")
                break
            elif status in ("section_not_found", "search_input_not_found", "no_results"):
                print(f"[error] DOM構造の問題。以降のタスクを中止します。")
                break

            # ToS対策: 1件ごとにウェイト
            if i < len(tasks) - 1:
                print(f"[wait] {ACTION_DELAY}秒待機...")
                await asyncio.sleep(ACTION_DELAY)

    return all_results


async def run_with_cookie_fallback(
    short_id: str | None,
    related_id: str | None,
    batch_file: str | None,
    headed: bool = False,
) -> list[dict]:
    """Cookie injection方式（DBSCで失敗する可能性が高いフォールバック）。"""
    print("[warn] Cookie injection方式はDBSCで失敗する可能性が高いです (cmd_1074実績)")
    print("[warn] --cdp-endpoint または --launch-chrome を推奨します")
    print()

    # cmd_1074のCookie復号ロジックを再利用
    try:
        from Crypto.Cipher import AES
    except ImportError:
        print("[error] pycryptodomeが必要です: pip install pycryptodome")
        sys.exit(1)

    import hashlib
    import shutil
    import sqlite3
    from datetime import datetime

    CHROME_PROFILE = Path.home() / ".config" / "google-chrome" / "Default"
    TEMP_PROFILE = Path("/tmp/chrome_yt_studio_session")

    def decrypt_cookies():
        cookie_src = CHROME_PROFILE / "Cookies"
        cookie_tmp = Path("/tmp/chrome_cookies_yt.db")
        shutil.copy2(cookie_src, cookie_tmp)

        key = b"peanuts"
        try:
            import secretstorage
            bus = secretstorage.dbus_init()
            collection = secretstorage.get_default_collection(bus)
            for item in collection.get_all_items():
                if item.get_label() == "Chrome Safe Storage":
                    key = item.get_secret()
                    break
        except Exception:
            pass

        derived = hashlib.pbkdf2_hmac("sha1", key, b"saltysalt", iterations=1, dklen=16)

        conn = sqlite3.connect(cookie_tmp)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly, samesite
            FROM cookies
            WHERE host_key LIKE '%youtube%' OR host_key LIKE '%google.com%'
        """)
        rows = cursor.fetchall()
        conn.close()

        cookies = []
        for row in rows:
            enc = row["encrypted_value"]
            if not enc or enc[:3] not in (b"v10", b"v11"):
                continue
            payload = enc[3:]
            iv = b" " * 16
            cipher = AES.new(derived, AES.MODE_CBC, iv)
            dec = cipher.decrypt(payload)[32:]
            pad_len = dec[-1] if dec else 0
            if 0 < pad_len <= 16:
                dec = dec[:-pad_len]
            try:
                val = dec.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if val:
                samesite_map = {0: "None", 1: "Strict", 2: "Lax"}
                cookies.append({
                    "name": row["name"],
                    "value": val,
                    "domain": row["host_key"],
                    "path": row["path"],
                    "secure": bool(row["is_secure"]),
                    "httpOnly": bool(row["is_httponly"]),
                    "sameSite": samesite_map.get(row["samesite"], "None"),
                })
        return cookies

    # タスクリスト構築
    tasks = []
    if batch_file:
        if yaml is None:
            print("[error] PyYAMLが必要です: pip install pyyaml")
            sys.exit(1)
        with open(batch_file) as f:
            data = yaml.safe_load(f)
        for item in data.get("videos", []):
            tasks.append((item["short_id"], item["related_id"]))
    elif short_id and related_id:
        tasks.append((short_id, related_id))
    else:
        print("[error] --short/--related または --batch を指定してください")
        sys.exit(1)

    all_results = []

    async with async_playwright() as p:
        # Cookie復号
        print("[cookies] Chrome Cookieを読み込み中...")
        cookies = decrypt_cookies()
        print(f"[cookies] {len(cookies)}件復号完了")

        # 一時プロファイル準備
        TEMP_PROFILE.mkdir(parents=True, exist_ok=True)

        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(TEMP_PROFILE),
            channel="chrome",
            headless=not headed,
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--password-store=basic",
                "--disable-blink-features=AutomationControlled",
            ],
            timeout=PAGE_TIMEOUT,
        )

        await ctx.add_cookies(cookies)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        # ログイン確認
        await page.goto("https://studio.youtube.com", timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        if "accounts.google.com" in page.url or "signin" in page.url.lower():
            snap_path = Path("work/cmd_1077") / "snap_cookie_auth_fail.png"
            snap_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(snap_path))
            print(f"[error] Cookie認証失敗（DBSCの可能性）。スクリーンショット: {snap_path}")
            print("[error] --cdp-endpoint または --launch-chrome を使用してください")
            await ctx.close()
            return [{"status": "auth_failed", "error": "Cookie認証失敗 (DBSC)", "screenshot": str(snap_path)}]

        print("[auth] ログイン確認OK")

        # 各タスクを実行
        for i, (sid, rid) in enumerate(tasks):
            print(f"\n[{i+1}/{len(tasks)}] short={sid} related={rid}")
            result = await set_related_video(page, sid, rid)
            all_results.append(result)

            if result["status"] in ("not_logged_in", "section_not_found", "input_not_found"):
                break

            if i < len(tasks) - 1:
                await asyncio.sleep(ACTION_DELAY)

        await ctx.close()

    return all_results


# ============================================================
# エントリポイント
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="YouTube Studio 関連動画自動設定 (cmd_1077)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
使用例:
  # Chrome起動（初回のみ）
  %(prog)s --launch-chrome

  # 単発設定
  %(prog)s --short SHORT_ID --related PARENT_ID

  # バッチ設定
  %(prog)s --batch related_videos.yaml

  # デバッグモード
  %(prog)s --short SHORT_ID --related PARENT_ID --headed

バッチYAMLフォーマット:
{BATCH_YAML_TEMPLATE}
        """,
    )
    parser.add_argument("--short", help="ショート動画ID")
    parser.add_argument("--related", help="関連（元）動画ID または動画タイトル（検索用）")
    parser.add_argument("--related-title", help="関連動画のタイトル（検索用）。省略時は--relatedをそのまま使用")
    parser.add_argument("--batch", help="バッチ設定YAMLファイル")
    parser.add_argument("--headed", action="store_true", help="ヘッドフルモード（ブラウザ表示）")
    parser.add_argument("--cdp-endpoint", default=CDP_ENDPOINT, help=f"CDP接続先 (default: {CDP_ENDPOINT})")
    parser.add_argument("--cookie-fallback", action="store_true", help="Cookie injection方式を使用（DBSCで失敗する可能性あり）")
    parser.add_argument("--launch-chrome", action="store_true", help="デバッグポート付きChrome起動")
    args = parser.parse_args()

    os.environ["DISPLAY"] = DISPLAY_ENV
    Path("work/cmd_1077").mkdir(parents=True, exist_ok=True)

    if args.launch_chrome:
        asyncio.run(launch_chrome_with_debug_port())
        return

    if not args.short and not args.batch and not args.related:
        parser.error("--short/--related または --batch、または --launch-chrome を指定してください")

    if args.batch is None and (not args.short or not args.related):
        parser.error("--short と --related はセットで指定してください")

    if args.cookie_fallback:
        results = asyncio.run(run_with_cookie_fallback(
            short_id=args.short,
            related_id=args.related,
            batch_file=args.batch,
            headed=args.headed,
        ))
    else:
        results = asyncio.run(run_with_cdp(
            short_id=args.short,
            related_id=args.related,
            related_title=args.related_title,
            batch_file=args.batch,
            headed=args.headed,
            cdp_endpoint=args.cdp_endpoint,
        ))

    # 結果サマリ
    print(f"\n{'='*60}")
    print("結果サマリ")
    print(f"{'='*60}")

    success = sum(1 for r in results if r["status"] == "success")
    for r in results:
        status_mark = "OK" if r["status"] == "success" else "NG"
        sid = r.get("short_id", "?")
        print(f"  [{status_mark}] {sid}: {r['status']}")
        if r.get("error"):
            print(f"        エラー: {r['error']}")
        if r.get("screenshot"):
            print(f"        スクリーンショット: {r['screenshot']}")

    print(f"\n完了: {success}/{len(results)} 件成功")

    # 結果をJSON保存
    result_path = Path("work/cmd_1077") / "results.json"
    result_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"結果ファイル: {result_path}")

    sys.exit(0 if success == len(results) else 1)


if __name__ == "__main__":
    main()
