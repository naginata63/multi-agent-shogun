#!/usr/bin/env python3
"""
CDP方式 Gemini UI 画像生成スクリプト (Clipboard貼り付け方式 リファレンス画像添付)
subtask_1074c: connect_over_cdp + Clipboard APIでリファレンス画像を添付。

使い方:
  python3 cdp_gemini_with_ref.py --panel p1
  python3 cdp_gemini_with_ref.py --panel p3
  python3 cdp_gemini_with_ref.py --panel both
"""

import asyncio
import base64
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

# ============================================================
# 設定
# ============================================================
CDP_ENDPOINT = "http://localhost:9222"

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
        # --- system_context: メタ情報（UIに入力しない。参考記録のみ）---
        # SKILL.md ルール: キャラ性格・situation・禁止ルール → system_instruction扱い
        "system_context": {
            "situation": "MENが氷で巨大パチンコを作っている。ぼんが上から見て不思議がる。",
            "character_rules": {
                "bon": "黒髪、丸いサングラス。サングラスは外さない。表情は口元中心。",
                "oo_men": "ピンク肌の丸っこい体型。ゴーグル（サングラスではない）。",
            },
            "prohibitions": [
                "YouTubeロゴ禁止", "指定外キャラ描画禁止",
                "サングラス/ゴーグルを外す描写禁止",
            ],
            "face_maintenance": "リファレンス画像の顔立ちを80%維持",
        },
        # --- scene_desc: 純粋な視覚描写のみ（UIに入力する）---
        # SKILL.md ルール: contents = 視覚描写 + セリフ + スタイル
        # expression_design_v5: bon skeptical r2 = サングラスを少しずらして覗く
        "scene_desc": (
            "Japanese manga style color illustration in Minecraft 3D voxel art. "
            "Snowy Minecraft landscape. A massive ice structure resembling a pachinko machine "
            "rises from the ground, towering overhead. "
            "One character with round sunglasses and black hair stands on higher ground, "
            "head tilted, sunglasses slightly lowered to peer down with a questioning look. "
            "Another smaller round character with goggles on their head is at the base, "
            "actively placing ice blocks with focused determination. "
            "Speech bubble: 「何作ってんの？」 "
            "Speed lines radiating from the towering ice structure. "
            "Thick black panel border. Portrait 9:16 composition."
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
        "system_context": {
            "situation": "MENが完成したパチンコを自慢げに解説。ぼんは驚き呆れている。",
            "character_rules": {
                "bon": "黒髪、丸いサングラス。驚きはワンテンポ遅れ。",
                "oo_men": "ピンク肌の丸っこい体型。ゴーグル。ドヤ顔は胸を張る。",
            },
            "prohibitions": [
                "YouTubeロゴ禁止", "指定外キャラ描画禁止",
                "サングラス/ゴーグルを外す描写禁止",
            ],
            "face_maintenance": "リファレンス画像の顔立ちを80%維持",
        },
        # expression_design_v5: oo_men smug r2 = 胸を張る / bon surprise r2 = ワンテンポ遅れ
        "scene_desc": (
            "Japanese manga style color illustration in Minecraft 3D voxel art. "
            "Interior of a large ice block structure. "
            "A small round character with goggles on their head stands confidently, "
            "chest puffed out, grinning broadly while gesturing toward the pachinko machine. "
            "In the background, a character with round sunglasses and black hair "
            "stands frozen with eyes wide and mouth open in delayed shock. "
            "Speech bubble with emphasis marks: 「正解がないパチンコっす！」 "
            "Thick black panel border. Portrait 9:16 composition."
        ),
        "ref_images": [
            REF_BASE / "oo_men_smug_r2_rgba.png",
            REF_BASE / "bon_surprise_r1_rgba.png",
        ],
        "output_name": "cdp_ref_p3_seikainai.jpg",
    },
}


# ============================================================
# リファレンス画像添付ヘルパー (FileChooser + Clipboard方式)
# ============================================================

async def attach_reference_images(page, ref_images: list) -> bool:
    """Gemini UIにリファレンス画像を添付する。

    方法1: expect_file_chooser()でアップロードボタンクリックからファイル選択
    方法2: Clipboard API + Ctrl+V (フォールバック)

    Returns:
        True: 添付成功, False: 失敗
    """
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

    # 方法1: expect_file_chooser（最も確実なPlaywrightネイティブ方式）
    ok = await _attach_via_file_chooser(page, valid_refs)
    if ok:
        return True

    # 方法2: Clipboard API + Ctrl+V (フォールバック)
    print("[ref] FileChooser失敗、Clipboard方式にフォールバック")
    ok = await _attach_via_clipboard(page, valid_refs)
    return ok


async def _attach_via_file_chooser(page, file_paths: list) -> bool:
    """CDP: Page.setInterceptFileChooserDialog → メニューボタン→メニュー内アップロード項目→ファイルチューザー傍受。

    手順:
    1. CDPでPage.setInterceptFileChooserDialogを有効化
    2. アップロードメニューボタン（アイコン）をクリック
    3. メニュー内の「ファイルをアップロード」をクリック
    4. ファイルチューザーを傍受してset_files
    """
    # Step 1: CDP file chooser interception有効化
    try:
        cdp = await page.context.new_cdp_session(page)
        await cdp.send('Page.setInterceptFileChooserDialog', {'enabled': True})
        print("[filechooser] CDP file chooser interception有効化")
    except Exception as e:
        print(f"[filechooser] CDP interception有効化失敗: {e}")
        return False

    # Step 2: アップロードメニューボタンをクリック
    menu_btn_selectors = [
        'button[aria-label*="ファイルをアップロード"]',
        'button.upload-card-button',
        'button[aria-label*="Upload"]',
        'button[aria-label*="アップロード"]',
    ]

    menu_opened = False
    for sel in menu_btn_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=3000):
                print(f"[filechooser] メニューボタン発見: {sel}")
                await btn.click()
                await page.wait_for_timeout(1000)
                menu_opened = True
                break
        except Exception:
            continue

    if not menu_opened:
        print("[filechooser] メニューボタンが見つからない")
        return False

    # Step 3: メニュー内の「ファイルをアップロード」をクリック + ファイルチューザー傍受
    try:
        upload_option = page.get_by_text("ファイルをアップロード", exact=False).first
        async with page.expect_file_chooser(timeout=10000) as fc_info:
            await upload_option.click()
        file_chooser = await fc_info.value
        print(f"[filechooser] ファイルチューザー傍受成功! multiple={file_chooser.is_multiple()}")

        # Step 4: ファイル設定
        await file_chooser.set_files(file_paths)
        await page.wait_for_timeout(3000)
        print(f"[filechooser] {len(file_paths)}ファイル設定完了")

        # 添付確認
        thumbs = await _count_attached_thumbnails(page)
        print(f"[filechooser] 添付サムネイル数: {thumbs}")
        return True

    except Exception as e:
        print(f"[filechooser] ファイルチューザー取得失敗: {e}")
        return False


async def _attach_via_clipboard(page, file_paths: list) -> bool:
    """Clipboard APIで画像を書き込み、Ctrl+Vで貼り付け。"""
    # clipboard権限付与
    try:
        ctx = page.context
        await ctx.grant_permissions(
            ["clipboard-read", "clipboard-write"],
            origin="https://gemini.google.com"
        )
        print("[clipboard] 権限付与成功")
    except Exception as e:
        print(f"[clipboard] 権限付与失敗: {e}")

    any_ok = False
    for fp in file_paths:
        img_path = Path(fp)
        if not img_path.exists():
            continue

        img_bytes = img_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode("ascii")
        mime_type = "image/png" if img_path.suffix == ".png" else "image/jpeg"

        print(f"[clipboard] 書き込み: {img_path.name} ({len(img_bytes):,} bytes)")

        try:
            result = await page.evaluate("""async (params) => {
                try {
                    const byteStr = atob(params.b64);
                    const ab = new ArrayBuffer(byteStr.length);
                    const ia = new Uint8Array(ab);
                    for (let i = 0; i < byteStr.length; i++) {
                        ia[i] = byteStr.charCodeAt(i);
                    }
                    const blob = new Blob([ab], {type: params.mime});
                    const item = new ClipboardItem({[params.mime]: blob});
                    await navigator.clipboard.write([item]);
                    return {ok: true};
                } catch (e) {
                    return {ok: false, error: e.message};
                }
            }""", {"b64": img_b64, "mime": mime_type})

            if result.get("ok"):
                print("[clipboard] 書き込み成功")
                # テキストボックスにフォーカスして貼り付け
                textbox = page.locator('[role="textbox"]').first
                await textbox.click()
                await page.wait_for_timeout(300)
                await page.keyboard.press("Control+v")
                await page.wait_for_timeout(2000)
                any_ok = True
            else:
                print(f"[clipboard] 書き込み失敗: {result.get('error')}")
        except Exception as e:
            print(f"[clipboard] エラー: {e}")

    if any_ok:
        thumbs = await _count_attached_thumbnails(page)
        print(f"[clipboard] 添付サムネイル数: {thumbs}")

    return any_ok


async def _count_attached_thumbnails(page) -> int:
    """Gemini UI上の添付画像要素を数える。"""
    return await page.evaluate("""() => {
        let total = 0;
        const selectors = [
            'img[alt*="uploaded"]',
            'img[alt*="Uploaded"]',
            '[data-testid*="attachment"]',
            '[data-testid*="image"]',
            '.upload-thumbnail',
            '.uploaded-image',
        ];
        for (const sel of selectors) {
            total += document.querySelectorAll(sel).length;
        }
        const editor = document.querySelector('[role="textbox"]');
        if (editor) {
            total += editor.querySelectorAll('img').length;
        }
        return total;
    }""")


# ============================================================
# Gemini UI 操作 (リファレンス画像添付対応版)
# ============================================================

async def generate_image_with_ref(panel_key: str) -> dict:
    """connect_over_cdpで殿のChromeに接続し、リファレンス画像添付+縦型指定で画像生成。"""
    panel = PANELS[panel_key]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    captured_image_urls = []
    result = {
        "status": "started",
        "panel_key": panel_key,
        "panel_id": panel["panel_id"],
        "images": [],
        "ref_attached": False,
        "error": None,
        "scene_desc": panel["scene_desc"],
        "system_context": panel.get("system_context", {}),
    }

    async with async_playwright() as p:
        print(f"[cdp] connect_over_cdp({CDP_ENDPOINT}) ...")
        browser = await p.chromium.connect_over_cdp(CDP_ENDPOINT)
        print(f"[cdp] 接続成功: {browser.version}")

        # 既存のコンテキストのページを使用
        contexts = browser.contexts
        if contexts:
            ctx = contexts[0]
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        else:
            ctx = await browser.new_context()
            page = await ctx.new_page()

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

        page.on("response", on_response)

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

            # フィールドを確実にクリア→keyboard.typeで入力
            # (insertTextはGemini UIのchange detectionをバイパスするためNG)
            await input_el.click()
            await page.keyboard.press("Home")
            await page.keyboard.down("Shift")
            await page.keyboard.press("End")
            await page.keyboard.up("Shift")
            await page.keyboard.press("Backspace")
            await page.wait_for_timeout(200)
            await page.keyboard.type(panel["scene_desc"], delay=15)
            await page.wait_for_timeout(500)

            # 入力内容確認
            typed_text = await input_el.evaluate("el => el.textContent")
            print(f"[gemini] 入力テキスト長: {len(typed_text)}文字")
            if len(typed_text) < 10:
                print(f"[gemini] 警告: テキストが短い: '{typed_text[:50]}'")
            else:
                print(f"[gemini] scene_desc入力完了（SKILL.md準拠・視覚描写のみ）")

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
            # ブラウザは閉じない（殿のChrome）。切断のみ。
            # about:blank遷移やbrowser.close()は殿のブラウザに影響するので実行しない
            pass
            # disconnectのみ（コンテキストから離脱）

    return result


# ============================================================
# エントリポイント
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="CDP方式 Gemini UI 画像生成 (リファレンス画像+縦型対応)")
    parser.add_argument("--panel", choices=["p1", "p3", "both"], default="both",
                        help="生成するパネル (p1/p3/both)")
    args = parser.parse_args()

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
