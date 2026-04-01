#!/usr/bin/env python3
"""
CDP方式 Gemini UI 画像生成スクリプト (リファレンス画像添付 + 縦型9:16対応版)
cmd_1057のPoC成果物をベースに改修。

改修内容:
  - ファイル添付ボタン操作 (Playwrightでinput[type="file"]にsetInputFiles)
  - プロンプトに縦型指定 (9:16, 768×1376) を追加
  - P1/P3の2枚を生成してwork/cmd_1074/に保存

使い方:
  python3 cdp_gemini_with_ref.py --panel p1
  python3 cdp_gemini_with_ref.py --panel p3
  python3 cdp_gemini_with_ref.py --panel both
"""

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import argparse
from datetime import datetime
from pathlib import Path

from Crypto.Cipher import AES
from playwright.async_api import async_playwright

# ============================================================
# 設定
# ============================================================
CHROME_PROFILE_DIR = Path("/home/murakami/.config/google-chrome/Default")
TEMP_PROFILE_DIR = Path("/tmp/chrome_cdp_gemini_session")  # cmd_1057/cmd_1065と同じプロファイルを再利用
COOKIE_CACHE = Path("/tmp/google_cookies_cache.json")
COOKIE_CACHE_TTL = 4 * 3600  # 4時間
DISPLAY_ENV = ":0"

GEMINI_URL = "https://gemini.google.com/app"
BROWSER_TIMEOUT = 30_000   # ms
GENERATION_TIMEOUT = 200   # seconds (リファレンス添付で少し長め)

OUTPUT_DIR = Path("work/cmd_1074")

# ============================================================
# パネル定義
# ============================================================
REF_BASE = Path("projects/dozle_kirinuki/assets/dozle_jp/character/selected")

PANELS = {
    "p1": {
        "panel_id": "panel_01_nanitsukttenno",
        "title": "P1: ぼん「何作ってんの？」",
        "prompt": (
            "Minecraft 3D render style. Blocky voxel characters in snowy Minecraft world. "
            "A large ice structure (pachinko machine) looms in background. "
            "MEN (blocky pink/magenta Minecraft character with square head, goggles on head) is building. "
            "Bon (blocky character, black skull-print shirt, black hair) looks on from above with puzzled expression. "
            "Speech bubble (Japanese text in it): 「何作ってんの？」 "
            "Speed lines radiating from the massive ice structure. "
            "Thick black panel border. Manga panel composition. "
            "IMPORTANT: Generate in 9:16 portrait orientation, 768×1376 pixels. "
            "縦型9:16フォーマット、768×1376ピクセルで生成してください。"
        ),
        "ref_images": [
            REF_BASE / "bon_skeptical_r1_rgba.png",
            REF_BASE / "oo_men_smug_r1_rgba.png",
        ],
        "output_name": "cdp_ref_p1_nanitsukttenno.jpg",
    },
    "p3": {
        "panel_id": "panel_02_seikainai_pachinko",
        "title": "P3: MEN「正解がないパチンコっす」",
        "prompt": (
            "Minecraft 3D render style. "
            "MEN (blocky pink/magenta Minecraft character with square head, goggles) "
            "looks up at camera with smug confident expression, explaining the pachinko machine. "
            "Ice block interior visible. Bon reaction visible off-panel or background (looking shocked/stunned). "
            "Speech bubble (Japanese text in it): 「正解がないパチンコっす」 with emphasis marks. "
            "Thick black panel border. Manga panel composition. "
            "IMPORTANT: Generate in 9:16 portrait orientation, 768×1376 pixels. "
            "縦型9:16フォーマット、768×1376ピクセルで生成してください。"
        ),
        "ref_images": [
            REF_BASE / "oo_men_smug_r2_rgba.png",
            REF_BASE / "bon_surprise_r1_rgba.png",
        ],
        "output_name": "cdp_ref_p3_seikainai.jpg",
    },
}


# ============================================================
# Cookie復号 (cmd_1057 PoC実装そのまま)
# ============================================================

def _try_decrypt_test(key: bytes) -> bool:
    try:
        cookie_src = CHROME_PROFILE_DIR / "Cookies"
        cookie_tmp = Path("/tmp/chrome_cookies_keytest.db")
        shutil.copy2(cookie_src, cookie_tmp)
        derived = hashlib.pbkdf2_hmac("sha1", key, b"saltysalt", iterations=1, dklen=16)
        conn = sqlite3.connect(cookie_tmp)
        cursor = conn.cursor()
        cursor.execute("SELECT encrypted_value FROM cookies WHERE encrypted_value != '' LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        count = 0
        for (enc,) in rows:
            if enc[:3] in (b"v10", b"v11"):
                iv = b" " * 16
                cipher = AES.new(derived, AES.MODE_CBC, iv)
                dec = cipher.decrypt(enc[3:])[32:]
                pad = dec[-1] if dec else 0
                if 0 < pad <= 16:
                    try:
                        dec[:-pad].decode("utf-8")
                        count += 1
                    except UnicodeDecodeError:
                        pass
        return count >= 2
    except Exception:
        return False


def _get_chrome_key() -> bytes:
    candidates = []
    try:
        import secretstorage
        bus = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(bus)
        for item in collection.get_all_items():
            if item.get_label() == "Chrome Safe Storage":
                candidates.append(("keyring-secretstorage", item.get_secret()))
    except Exception:
        pass
    candidates.append(("peanuts", b"peanuts"))
    for name, key in candidates:
        if _try_decrypt_test(key):
            print(f"[cookies] 有効なキー: {name}")
            return key
    print("[cookies] 警告: キー検出失敗。peanuts を使用")
    return b"peanuts"


def _decrypt_cookie_value(encrypted: bytes, derived_key: bytes) -> str:
    if not encrypted or encrypted[:3] not in (b"v10", b"v11"):
        return encrypted.decode("utf-8", errors="replace") if encrypted else ""
    payload = encrypted[3:]
    iv = b" " * 16
    cipher = AES.new(derived_key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(payload)
    decrypted = decrypted[32:]
    pad_len = decrypted[-1] if decrypted else 0
    if 0 < pad_len <= 16:
        decrypted = decrypted[:-pad_len]
    try:
        return decrypted.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def load_cookies(force_refresh: bool = False) -> list:
    if not force_refresh and COOKIE_CACHE.exists():
        age = datetime.now().timestamp() - COOKIE_CACHE.stat().st_mtime
        if age < COOKIE_CACHE_TTL:
            print(f"[cookies] キャッシュ使用 ({age:.0f}s前に更新)")
            return json.loads(COOKIE_CACHE.read_text())

    print("[cookies] Chrome プロファイルから読み込み中...")
    chrome_key = _get_chrome_key()
    derived_key = hashlib.pbkdf2_hmac("sha1", chrome_key, b"saltysalt", iterations=1, dklen=16)

    cookie_src = CHROME_PROFILE_DIR / "Cookies"
    cookie_tmp = Path("/tmp/chrome_cookies_read.db")
    shutil.copy2(cookie_src, cookie_tmp)

    conn = sqlite3.connect(cookie_tmp)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly, samesite
        FROM cookies
        WHERE host_key LIKE '%google.com%' OR host_key LIKE '%gemini%'
    """)
    rows = cursor.fetchall()
    conn.close()

    samesite_map = {0: "None", 1: "Strict", 2: "Lax"}
    cookies = []
    for row in rows:
        val = _decrypt_cookie_value(row["encrypted_value"], derived_key)
        if val:
            cookies.append({
                "name": row["name"],
                "value": val,
                "domain": row["host_key"],
                "path": row["path"],
                "secure": bool(row["is_secure"]),
                "httpOnly": bool(row["is_httponly"]),
                "sameSite": samesite_map.get(row["samesite"], "None"),
            })

    print(f"[cookies] {len(cookies)}/{len(rows)} 件復号完了")
    COOKIE_CACHE.write_text(json.dumps(cookies, ensure_ascii=False))
    return cookies


# ============================================================
# リファレンス画像添付ヘルパー
# ============================================================

async def attach_reference_images(page, ref_images: list) -> bool:
    """Gemini UIにリファレンス画像を添付する。

    複数の方法を試みる:
    1. ファイル添付ボタンをクリックして input[type="file"] を探す
    2. input[type="file"] を直接 setInputFiles で操作（非表示でも動作）

    Returns:
        True: 添付成功, False: 失敗
    """
    # 存在するリファレンスファイルだけ使用
    valid_refs = []
    for ref in ref_images:
        ref_path = Path(ref)
        if ref_path.exists():
            valid_refs.append(str(ref_path.absolute()))
            print(f"[ref] リファレンス画像: {ref_path.name}")
        else:
            print(f"[ref] 警告: {ref} が見つからない、スキップ")

    if not valid_refs:
        print("[ref] 警告: 有効なリファレンス画像なし。プロンプトのみで生成")
        return False

    # 方法1: ファイル添付ボタンを探してクリック
    # Gemini UI のファイル添付ボタン候補セレクタ
    attach_btn_selectors = [
        'button[aria-label*="添付"]',
        'button[aria-label*="attach"]',
        'button[aria-label*="upload"]',
        'button[aria-label*="Upload"]',
        'button[data-mat-icon-name*="attach"]',
        '[aria-label*="ファイルを追加"]',
        '[aria-label*="Add image"]',
        '[aria-label*="Add file"]',
        'mat-icon[fonticon="attach_file"]',
        '.add-image-button',
        'button[jsname*="upload"]',
    ]

    for sel in attach_btn_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2000):
                print(f"[ref] 添付ボタン発見: {sel}")
                await btn.click()
                await page.wait_for_timeout(500)
                break
        except Exception:
            continue

    # 方法2: input[type="file"] に直接 setInputFiles
    file_input_selectors = [
        'input[type="file"]',
        'input[accept*="image"]',
        'input[accept*="image/"]',
    ]

    for sel in file_input_selectors:
        try:
            file_inputs = page.locator(sel)
            count = await file_inputs.count()
            if count > 0:
                print(f"[ref] file input 発見 ({count}個): {sel}")
                # 最初のinputに添付
                await file_inputs.first.set_input_files(valid_refs)
                await page.wait_for_timeout(2000)

                # 添付確認: サムネイルまたはファイル名が表示されるか
                thumbs = await page.locator('img[alt*="uploaded"], .upload-thumbnail, [data-testid*="attachment"]').count()
                print(f"[ref] 添付サムネイル確認: {thumbs}個")
                print(f"[ref] {len(valid_refs)}枚の画像を添付完了")
                return True
        except Exception as e:
            print(f"[ref] {sel} での添付失敗: {e}")
            continue

    print("[ref] ファイル添付に失敗。プロンプトのみで生成を続行")
    return False


# ============================================================
# Gemini UI 操作 (リファレンス画像添付対応版)
# ============================================================

async def generate_image_with_ref(panel_key: str) -> dict:
    """リファレンス画像添付 + 縦型指定でGemini UIから画像を生成する。"""
    panel = PANELS[panel_key]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cookies = load_cookies()
    os.environ["DISPLAY"] = DISPLAY_ENV

    captured_image_urls = []
    result = {
        "status": "started",
        "panel_key": panel_key,
        "panel_id": panel["panel_id"],
        "images": [],
        "ref_attached": False,
        "error": None,
        "prompt": panel["prompt"],
    }

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(TEMP_PROFILE_DIR),
            channel="chrome",
            headless=True,
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--password-store=basic",
                "--disable-blink-features=AutomationControlled",
            ],
            timeout=BROWSER_TIMEOUT,
        )

        # 生成画像URLを監視
        async def on_response(resp):
            ct = resp.headers.get("content-type", "")
            url = resp.url
            if (
                "image/" in ct
                and resp.status == 200
                and "rd-gg-dl" in url
            ):
                captured_image_urls.append(url)
                print(f"[capture] 生成画像URL: {url[:80]}...")

        ctx.on("response", on_response)
        await ctx.add_cookies(cookies)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        try:
            await page.goto(GEMINI_URL, timeout=BROWSER_TIMEOUT, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            url = page.url
            if "accounts.google.com" in url or "signin" in url.lower():
                result["status"] = "not_logged_in"
                result["error"] = "Cookie期限切れ。--update-cookiesで更新が必要"
                return result

            print("[gemini] ログイン確認OK")

            # リファレンス画像添付（プロンプト入力前）
            ref_ok = await attach_reference_images(page, panel["ref_images"])
            result["ref_attached"] = ref_ok

            # プロンプト入力
            input_el = page.locator('[role="textbox"]').first
            if not await input_el.is_visible(timeout=5000):
                result["status"] = "input_not_found"
                result["error"] = "入力フィールドが見つからない"
                return result

            await input_el.click()
            await page.keyboard.press("Control+a")
            await page.wait_for_timeout(200)
            await page.keyboard.type(panel["prompt"], delay=20)
            await page.wait_for_timeout(500)
            print(f"[gemini] プロンプト入力完了 (縦型指定含む)")

            # スクリーンショット保存（送信前確認用）
            snap_path = OUTPUT_DIR / f"snap_before_submit_{panel_key}.png"
            await page.screenshot(path=str(snap_path))
            print(f"[snap] 送信前スナップ: {snap_path}")

            # 送信
            await page.keyboard.press("Enter")
            print("[gemini] 送信完了")

            await page.wait_for_timeout(2000)

            # 生成待ち
            print(f"[gemini] 画像生成待ち（最大{GENERATION_TIMEOUT}秒）...")
            deadline = GENERATION_TIMEOUT

            for elapsed in range(0, deadline, 5):
                await page.wait_for_timeout(5000)

                if captured_image_urls:
                    break

                imgs = await page.evaluate("""
                    () => {
                        function getAllImgs(root) {
                            let imgs = Array.from(root.querySelectorAll('img'));
                            root.querySelectorAll('*').forEach(el => {
                                if (el.shadowRoot) imgs = imgs.concat(getAllImgs(el.shadowRoot));
                            });
                            return imgs;
                        }
                        return getAllImgs(document).map(img => ({
                            src: img.src,
                            w: img.naturalWidth,
                            h: img.naturalHeight,
                        }));
                    }
                """)
                candidates = [
                    img for img in imgs
                    if img["w"] > 200 and img["h"] > 200
                    and "rd-gg-dl" in img["src"]
                ]
                if candidates:
                    for c in candidates:
                        captured_image_urls.append(c["src"])
                    break

                if elapsed % 30 == 0:
                    print(f"[gemini] 待機中... {elapsed}秒")

            # 生成後スナップ
            snap_after = OUTPUT_DIR / f"snap_after_gen_{panel_key}.png"
            await page.screenshot(path=str(snap_after))
            print(f"[snap] 生成後スナップ: {snap_after}")

            if not captured_image_urls:
                result["status"] = "timeout"
                result["error"] = f"{GENERATION_TIMEOUT}秒以内に画像が生成されなかった"
                return result

            # 画像ダウンロード（最初の1枚）
            url = captured_image_urls[0]
            try:
                img_data = await page.evaluate(f"""
                    async () => {{
                        const r = await fetch('{url}', {{
                            credentials: 'include',
                            headers: {{'Referer': 'https://gemini.google.com/'}}
                        }});
                        if (!r.ok) return {{error: r.status}};
                        const buf = await r.arrayBuffer();
                        return {{data: Array.from(new Uint8Array(buf))}};
                    }}
                """)
                if "error" in img_data:
                    result["status"] = "download_failed"
                    result["error"] = f"HTTP {img_data['error']}"
                    return result

                img_bytes = bytes(img_data["data"])
                out_path = OUTPUT_DIR / panel["output_name"]
                out_path.write_bytes(img_bytes)
                result["images"].append(str(out_path))
                print(f"[download] 保存: {out_path} ({len(img_bytes):,} bytes)")

                # 画像サイズ確認
                try:
                    from PIL import Image
                    img = Image.open(out_path)
                    w, h = img.size
                    result["width"] = w
                    result["height"] = h
                    orientation = "縦型" if h > w else "横型"
                    aspect = f"{w}:{h}"
                    print(f"[size] {w}×{h}px ({orientation}, {aspect})")
                    result["orientation"] = orientation
                except ImportError:
                    # PIL未インストールの場合はスキップ
                    pass
            except Exception as e:
                result["status"] = "download_failed"
                result["error"] = str(e)
                return result

            result["status"] = "success"

        except Exception as e:
            import traceback
            result["status"] = "error"
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            print(f"[error] {e}")

        finally:
            await ctx.close()

    return result


# ============================================================
# エントリポイント
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="CDP方式 Gemini UI 画像生成 (リファレンス画像+縦型対応)")
    parser.add_argument("--panel", choices=["p1", "p3", "both"], default="both",
                        help="生成するパネル (p1/p3/both)")
    parser.add_argument("--update-cookies", action="store_true", help="Cookieキャッシュ更新")
    args = parser.parse_args()

    if args.update_cookies:
        load_cookies(force_refresh=True)
        print("Cookie更新完了")
        return

    panels_to_run = ["p1", "p3"] if args.panel == "both" else [args.panel]
    all_results = {}

    for panel_key in panels_to_run:
        print(f"\n{'='*60}")
        print(f"パネル生成開始: {PANELS[panel_key]['title']}")
        print(f"{'='*60}")

        result = asyncio.run(generate_image_with_ref(panel_key))
        all_results[panel_key] = result

        print(f"\n結果: {result['status']}")
        if result["images"]:
            for img in result["images"]:
                print(f"  画像: {img}")
        if result.get("ref_attached"):
            print(f"  リファレンス添付: 成功")
        else:
            print(f"  リファレンス添付: 失敗（プロンプトのみ）")
        if result.get("error"):
            print(f"  エラー: {result['error']}")

    # 結果ログ保存
    log_path = OUTPUT_DIR / "result_log_v2.json"
    for r in all_results.values():
        r["timestamp"] = datetime.now().isoformat()
    log_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2))
    print(f"\n[log] 結果ログ: {log_path}")

    success_count = sum(1 for r in all_results.values() if r["status"] == "success")
    print(f"\n{'='*60}")
    print(f"完了: {success_count}/{len(panels_to_run)} 枚成功")
    print(f"{'='*60}")

    sys.exit(0 if success_count == len(panels_to_run) else 1)


if __name__ == "__main__":
    main()
