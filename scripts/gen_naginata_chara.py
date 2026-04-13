#!/usr/bin/env python3
"""
なぎなたキャラクターのアイコン+立ち絵をGemini APIで生成するスクリプト。
Vertex AI ADC認証使用。
"""
import sys
import time
import io
import subprocess
import argparse
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

MODEL_ID = "gemini-3.1-flash-image-preview"

REF_IMAGE = Path("screenshots/ntfy/x5NmlBWxMjnI_2026_04_02__20_31_43_.jpg")
OUT_DIR = Path("work/cmd_1091")

# キャラ説明
CHAR_DESC = """白髪ショートヘア、緑の瞳の冒険者キャラクター「なぎなた」。
特徴: 赤いマフラー/スカーフ、青いマント/ローブ、茶色のブーツ。
冒険者風装備で、明るく前向きな性格のオリジナルアニメキャラクター。"""

ICON_PROMPTS = [
    "このキャラクターの特徴を参考にしたオリジナルアニメ風キャラクター「なぎなた」の顔〜上半身アップのアイコン画像。明るく笑顔の表情。白または薄い色のシンプルな背景。note記事のプロフィール画像用。アニメ・ライトノベル風の画風。©SQUARE ENIXの要素は使わないこと。",
    "このキャラクターの特徴を参考にしたオリジナルアニメ風キャラクター「なぎなた」の顔〜上半身アップのアイコン画像。真剣な表情で前を向いている。白または薄い色のシンプルな背景。note記事のプロフィール画像用。アニメ・ライトノベル風の画風。©SQUARE ENIXの要素は使わないこと。",
    "このキャラクターの特徴を参考にしたオリジナルアニメ風キャラクター「なぎなた」の顔〜上半身アップのアイコン画像。ちょっと照れたような微笑みの表情。白または薄い色のシンプルな背景。note記事のプロフィール画像用。アニメ・ライトノベル風の画風。©SQUARE ENIXの要素は使わないこと。",
]

TACHIE_PROMPTS = [
    "このキャラクターの特徴を参考にしたオリジナルアニメ風キャラクター「なぎなた」の立ち絵（全身〜膝上）。右手を腰に当てて自信満々のポーズ。白または薄い色のシンプルな背景。アニメ・ライトノベル風の画風。note記事の吹き出し横に配置する用途。©SQUARE ENIXの要素は使わないこと。",
    "このキャラクターの特徴を参考にしたオリジナルアニメ風キャラクター「なぎなた」の立ち絵（全身〜膝上）。左手であごに手を当てて考え事をするポーズ。白または薄い色のシンプルな背景。アニメ・ライトノベル風の画風。note記事の吹き出し横に配置する用途。©SQUARE ENIXの要素は使わないこと。",
    "このキャラクターの特徴を参考にしたオリジナルアニメ風キャラクター「なぎなた」の立ち絵（全身〜膝上）。両手を広げて明るく笑って挨拶するポーズ。白または薄い色のシンプルな背景。アニメ・ライトノベル風の画風。note記事の吹き出し横に配置する用途。©SQUARE ENIXの要素は使わないこと。",
]

GCS_BUCKET = "gs://shogun-manga-refs/ref_images/"

ORAFU_REF = Path("projects/dozle_kirinuki/assets/dozle_jp/character/oraf-kun.png")
ORAFU_OUT_DIR = Path("projects/dozle_kirinuki/work/orafu_futuristic")
ORAFU_V2_REF = Path("projects/dozle_kirinuki/work/orafu_futuristic/orafu_futuristic_01.png")
ORAFU_V2_OUT_DIR = Path("projects/dozle_kirinuki/work/orafu_futuristic/v2")
ORAFU_PROMPT = """全身のアニメ風キャラクターイラスト、透過背景、リファレンス画像と同じ画風を維持。

キャラクター: 銀白色のショートヘア、青い瞳、色白の少年。明るく元気な雰囲気。

衣装（未来人バージョン）:
- ダークティール色のフラットキャップ。帽子の上に細い黒のアンテナが2本、先端に小さな球体
- オーバーイヤー型ヘッドホン（ティール/シアン色）。耳あて部分に雪だるまロゴ
- 片目（左目）の前にスカウター型スクリーン。半透明のシアン色ホログラフィックディスプレイ、ドラゴンボールのスカウターのような形
- メタリックなティールグレーのジャケット、少しオーバーサイズ、裏地は黒
- 首元に赤いスカーフ/マフラー
- ウエストにゴールドのベルトバックル
- ダークネイビーのスキニーパンツ、サイドに白いライン
- 白いスニーカー
- 頭の上にマスコットなし（雪だるまはヘッドホンのロゴに統合）

ポーズ: 自信のある立ちポーズ、両手は自然に下ろしている
品質: 高精細、クリーンな線画、アニメイラスト風、全身が見える構図"""

ORAFU_V2_PROMPT = """全身のアニメ風キャラクターイラスト、透過背景、リファレンス画像と同じ画風を維持。

キャラクター: 銀白色のショートヘア、青い瞳、色白の少年。明るく元気な雰囲気。

衣装（未来人バージョン・スカウターなし版）:
- ダークティール色のフラットキャップ。帽子の上に細い黒のアンテナが2本、先端に小さな球体
- オーバーイヤー型ヘッドホン（ティール/シアン色）。耳あて部分に雪だるまロゴ
- 顔の前にスクリーン・バイザー・ゴーグル等を一切描画しないこと。顔は完全に見える状態にすること
- メタリックなティールグレーのジャケット、少しオーバーサイズ、裏地は黒
- 首元に赤いスカーフ/マフラー
- ウエストにゴールドのベルトバックル
- ダークネイビーのスキニーパンツ、サイドに白いライン
- 白いスニーカー
- 頭の上にマスコットなし（雪だるまはヘッドホンのロゴに統合）

ポーズ: 自信のある立ちポーズ、両手は自然に下ろしている
品質: 高精細、クリーンな線画、アニメイラスト風、全身が見える構図"""

ORAFU_V3_REF = Path("projects/dozle_kirinuki/work/orafu_futuristic/orafu_futuristic_01.png")
ORAFU_V3_OUT_DIR = Path("projects/dozle_kirinuki/work/orafu_futuristic/v3")
ORAFU_V3_PROMPT = """全身のアニメ風キャラクターイラスト、透過背景、リファレンス画像と同じ画風・衣装・ポーズを維持。

キャラクター: 銀白色ショートヘア、青い瞳、色白の少年。

衣装（未来人バージョン・スカウターフレーム残し・ホログラムオフ）:
- ダークティール色のフラットキャップ+黒アンテナ2本
- オーバーイヤー型ヘッドホン（ティール/シアン色）。耳あて部分に雪だるまロゴ
- 左目前にスカウターフレーム・アーム・レンズ枠あり（電源オフ状態・光るホログラム表示は一切なし・透明レンズのみ）
- メタリックなティールグレーのジャケット、少しオーバーサイズ、裏地は黒
- 首元に赤いスカーフ/マフラー
- ウエストにゴールドのベルトバックル
- ダークネイビーのスキニーパンツ、サイドに白いライン
- 白いスニーカー

ポーズ: 自信ある立ちポーズ
品質: 高精細アニメイラスト"""

ORAFU_V4_REF = Path("projects/dozle_kirinuki/work/orafu_futuristic/v3/orafu_futuristic_v3_01.png")
ORAFU_V4_REF_V1 = Path("projects/dozle_kirinuki/work/orafu_futuristic/orafu_futuristic_01.png")
ORAFU_V4_OUT_DIR = Path("projects/dozle_kirinuki/work/orafu_futuristic/v4")
ORAFU_V4_PROMPT = """全身のアニメ風キャラクターイラスト、透過背景、リファレンス画像と同じ画風・衣装・ポーズを維持。
銀白色ショートヘア・青い瞳・色白少年。
衣装: フラットキャップ+黒アンテナ2本、ティールヘッドホン（雪だるまロゴ）、左目前にスカウター装置（レンズが青白く発光・シアン/ライトブルーの光）。ただし顔の前にホログラムスクリーン（浮遊する半透明ディスプレイ）は投影されていない。光っているのはレンズそのものだけ。
ティールグレージャケット、赤スカーフ、ゴールドベルト、ダークネイビーパンツ（白ライン）、白スニーカー。自信ある立ちポーズ。高精細アニメイラスト。"""

ORAFU_V5_REF = Path("projects/dozle_kirinuki/work/orafu_futuristic/orafu_futuristic_01.png")
ORAFU_V5_OUT_DIR = Path("projects/dozle_kirinuki/work/orafu_futuristic/v5")
ORAFU_V5_PROMPT = """全身のアニメ風キャラクターイラスト、透過背景、リファレンス画像と同じ画風・衣装を維持。銀白色ショートヘア・青い瞳・色白少年。v1衣装そのまま（フラットキャップ+黒アンテナ2本、ティールヘッドホン雪だるまロゴ、スカウター型シアンホログラム、ティールグレージャケット、赤スカーフ、ゴールドベルト、ダークネイビーパンツ白ライン、白スニーカー）。武器: 右手にSF風ハンドガン（ティール/シアン色ボディ+グレースライド、コンパクト、未来的ブロック状デザイン、銃口は下向きまたは横向き）。ポーズ: 自信のある立ちポーズ、右手にSFハンドガン・左手は自然に下ろす。高精細アニメイラスト。"""


def upload_to_gcs(local_path: Path) -> str | None:
    """ローカルファイルをGCSにアップしGCS URIを返す。"""
    gcs_dest = GCS_BUCKET + local_path.name
    result = subprocess.run(
        ["gsutil", "cp", str(local_path), gcs_dest],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode == 0:
        print(f"  [GCS] アップロード完了: {local_path.name} → {gcs_dest}")
        return gcs_dest
    else:
        print(f"  [GCS] ERROR: {result.stderr[:200]}")
        return None


def generate_image(client, ref_bytes=None, ref_gcs_uri=None, ref_gcs_uris=None, prompt="", aspect_ratio="3:4", out_path=None, char_desc=None):
    """Gemini APIで画像を1枚生成して保存。GCS URI（単数/複数）またはバイトデータのいずれかを使用。"""
    if ref_gcs_uris:
        # 複数GCS URI対応
        parts = []
        for uri in ref_gcs_uris:
            parts.append(types.Part.from_uri(file_uri=uri, mime_type="image/png"))
        parts.append(types.Part.from_text(text=prompt))
    elif ref_gcs_uri:
        parts = [
            types.Part.from_uri(file_uri=ref_gcs_uri, mime_type="image/png"),
            types.Part.from_text(text=prompt),
        ]
    else:
        parts = [
            types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg"),
            types.Part.from_text(text=f"{prompt}\n\nキャラクターの外見特徴:\n{char_desc or CHAR_DESC}"),
        ]

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        temperature=0.8,
    )

    start = time.time()
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=parts,
            config=config,
        )
        elapsed = time.time() - start
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img = Image.open(io.BytesIO(part.inline_data.data))
                out_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(out_path, "PNG")
                size_kb = out_path.stat().st_size / 1024
                print(f"  Saved: {out_path} ({img.size[0]}x{img.size[1]}, {size_kb:.0f}KB, {elapsed:.1f}s)")
                return True
            elif part.text:
                print(f"  Text: {part.text[:100]}")
        print(f"  WARNING: No image in response ({elapsed:.1f}s)")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR: {e} ({elapsed:.1f}s)")
        return False


def main():
    parser = argparse.ArgumentParser(description="Gemini APIでキャラクター画像生成")
    parser.add_argument("--mode", choices=["naginata", "orafu", "orafu_v2", "orafu_v3", "orafu_v4", "orafu_v5"], default="naginata",
                        help="生成モード (default: naginata)")
    args = parser.parse_args()
    mode = args.mode

    client = genai.Client(vertexai=True, project="gen-lang-client-0119911773", location="global")

    if mode == "orafu":
        # おらふくん未来人版モード
        if not ORAFU_REF.exists():
            print(f"ERROR: Reference image not found: {ORAFU_REF}")
            sys.exit(1)

        ORAFU_OUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Reference image: {ORAFU_REF}")
        gcs_uri = upload_to_gcs(ORAFU_REF)
        if not gcs_uri:
            print("ERROR: GCSアップロード失敗")
            sys.exit(1)

        print(f"\n=== おらふくん未来人版立ち絵生成（5枚）===")
        results = []
        for i in range(1, 6):
            out = ORAFU_OUT_DIR / f"orafu_futuristic_{i:02d}.png"
            print(f"\n[Orafu {i}/5]")
            ok = generate_image(client, ref_gcs_uri=gcs_uri, prompt=ORAFU_PROMPT, aspect_ratio="3:4", out_path=out)
            results.append(ok)
            if i < 5:
                time.sleep(3)

        ok_count = sum(results)
        print(f"\n=== 結果 ===")
        print(f"おらふくん未来人版: {ok_count}/5")
        if ok_count == 0:
            print("ERROR: 全ての生成に失敗しました")
            sys.exit(1)
        return

    if mode == "orafu_v2":
        # おらふくん未来人版v2（スカウターなし版）
        if not ORAFU_V2_REF.exists():
            print(f"ERROR: Reference image not found: {ORAFU_V2_REF}")
            sys.exit(1)

        ORAFU_V2_OUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Reference image: {ORAFU_V2_REF}")
        gcs_uri = upload_to_gcs(ORAFU_V2_REF)
        if not gcs_uri:
            print("ERROR: GCSアップロード失敗")
            sys.exit(1)

        print(f"\n=== おらふくん未来人版v2（スカウターなし版）立ち絵生成（5枚）===")
        results = []
        for i in range(1, 6):
            out = ORAFU_V2_OUT_DIR / f"orafu_futuristic_v2_{i:02d}.png"
            print(f"\n[Orafu V2 {i}/5]")
            ok = generate_image(client, ref_gcs_uri=gcs_uri, prompt=ORAFU_V2_PROMPT, aspect_ratio="3:4", out_path=out)
            results.append(ok)
            if i < 5:
                time.sleep(3)

        ok_count = sum(results)
        print(f"\n=== 結果 ===")
        print(f"おらふくん未来人版v2: {ok_count}/5")
        if ok_count == 0:
            print("ERROR: 全ての生成に失敗しました")
            sys.exit(1)
        return

    if mode == "orafu_v3":
        # おらふくん未来人版v3（スカウターフレーム残し・ホログラムオフ）
        if not ORAFU_V3_REF.exists():
            print(f"ERROR: Reference image not found: {ORAFU_V3_REF}")
            sys.exit(1)

        ORAFU_V3_OUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Reference image: {ORAFU_V3_REF}")
        gcs_uri = upload_to_gcs(ORAFU_V3_REF)
        if not gcs_uri:
            print("ERROR: GCSアップロード失敗")
            sys.exit(1)

        out = ORAFU_V3_OUT_DIR / "orafu_futuristic_v3_01.png"
        print(f"\n=== おらふくん未来人版v3（スカウターフレーム残し・ホログラムオフ）1枚生成 ===")
        ok = generate_image(client, ref_gcs_uri=gcs_uri, prompt=ORAFU_V3_PROMPT, aspect_ratio="3:4", out_path=out)
        if not ok:
            print("ERROR: v3生成に失敗しました")
            sys.exit(1)
        print(f"\n=== 結果: v3生成 {'成功' if ok else '失敗'} ===")
        return

    if mode == "orafu_v4":
        # おらふくん未来人版v4（スカウターレンズ青白発光・ホログラムなし）
        if not ORAFU_V4_REF.exists():
            print(f"ERROR: Reference image not found: {ORAFU_V4_REF}")
            sys.exit(1)

        ORAFU_V4_OUT_DIR.mkdir(parents=True, exist_ok=True)

        # v3（メインリファレンス）をGCSアップロード
        print(f"Primary reference (v3): {ORAFU_V4_REF}")
        gcs_uri_v3 = upload_to_gcs(ORAFU_V4_REF)
        if not gcs_uri_v3:
            print("ERROR: v3 GCSアップロード失敗")
            sys.exit(1)

        # v1（補助リファレンス）をGCSアップロード
        if ORAFU_V4_REF_V1.exists():
            print(f"Secondary reference (v1): {ORAFU_V4_REF_V1}")
            gcs_uri_v1 = upload_to_gcs(ORAFU_V4_REF_V1)
            if not gcs_uri_v1:
                print("WARNING: v1 GCSアップロード失敗、v3のみで続行")
                gcs_uris = [gcs_uri_v3]
            else:
                gcs_uris = [gcs_uri_v3, gcs_uri_v1]
        else:
            print("WARNING: v1 reference not found, using v3 only")
            gcs_uris = [gcs_uri_v3]

        out = ORAFU_V4_OUT_DIR / "orafu_futuristic_v4_01.png"
        print(f"\n=== おらふくん未来人版v4（スカウターレンズ青白発光・ホログラムなし）1枚生成 ===")
        ok = generate_image(client, ref_gcs_uris=gcs_uris, prompt=ORAFU_V4_PROMPT, aspect_ratio="3:4", out_path=out)
        if not ok:
            print("ERROR: v4生成に失敗しました")
            sys.exit(1)
        print(f"\n=== 結果: v4生成 {'成功' if ok else '失敗'} ===")
        return

    if mode == "orafu_v5":
        # おらふくん未来人版v5（v1ベース+SFハンドガン持ち）
        if not ORAFU_V5_REF.exists():
            print(f"ERROR: Reference image not found: {ORAFU_V5_REF}")
            sys.exit(1)

        ORAFU_V5_OUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Reference image: {ORAFU_V5_REF}")
        gcs_uri = upload_to_gcs(ORAFU_V5_REF)
        if not gcs_uri:
            print("ERROR: GCSアップロード失敗")
            sys.exit(1)

        out = ORAFU_V5_OUT_DIR / "orafu_futuristic_v5_01.png"
        print(f"\n=== おらふくん未来人版v5（v1ベース+SFハンドガン持ち）1枚生成 ===")
        ok = generate_image(client, ref_gcs_uri=gcs_uri, prompt=ORAFU_V5_PROMPT, aspect_ratio="3:4", out_path=out)
        if not ok:
            print("ERROR: v5生成に失敗しました")
            sys.exit(1)
        print(f"\n=== 結果: v5生成 {'成功' if ok else '失敗'} ===")
        return

    # 既存のなぎなたモード
    if not REF_IMAGE.exists():
        print(f"ERROR: Reference image not found: {REF_IMAGE}")
        sys.exit(1)

    ref_bytes = REF_IMAGE.read_bytes()
    print(f"Reference image: {REF_IMAGE} ({len(ref_bytes)/1024:.0f}KB)")

    # アイコン生成（1:1）
    print("\n=== アイコン生成（1:1）===")
    icon_results = []
    for i, prompt in enumerate(ICON_PROMPTS, 1):
        print(f"\n[Icon {i}/3]")
        out = OUT_DIR / "icon" / f"icon{i}.png"
        ok = generate_image(client, ref_bytes=ref_bytes, prompt=prompt, aspect_ratio="1:1", out_path=out)
        icon_results.append(ok)
        if i < 3:
            time.sleep(2)

    # 立ち絵生成（3:4）
    print("\n=== 立ち絵生成（3:4）===")
    tachie_results = []
    for i, prompt in enumerate(TACHIE_PROMPTS, 1):
        print(f"\n[Tachie {i}/3]")
        out = OUT_DIR / "tachie" / f"tachie{i}.png"
        ok = generate_image(client, ref_bytes=ref_bytes, prompt=prompt, aspect_ratio="3:4", out_path=out)
        tachie_results.append(ok)
        if i < 3:
            time.sleep(2)

    # 結果
    icon_ok = sum(icon_results)
    tachie_ok = sum(tachie_results)
    print(f"\n=== 結果 ===")
    print(f"アイコン: {icon_ok}/3")
    print(f"立ち絵: {tachie_ok}/3")
    print(f"合計: {icon_ok + tachie_ok}/6")

    if icon_ok + tachie_ok == 0:
        print("ERROR: 全ての生成に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
