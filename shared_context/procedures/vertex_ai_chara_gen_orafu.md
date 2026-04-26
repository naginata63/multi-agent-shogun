# Vertex AI キャラクター立ち絵生成手順 (おらふくん未来人版)

## 目的
`scripts/gen_naginata_chara.py` を改修してGCS URI方式に対応させ、おらふくん未来人版立ち絵5枚を生成する。

## 前提
- `source /home/murakami/multi-agent-shogun/config/vertex_api_key.env` 必須（実行前に毎回）
- GCS URI方式のみ (`Part.from_bytes` 禁止)
- gsutil が使えること: `which gsutil`
- GCS bucket: `gs://shogun-manga-refs/ref_images/`
- 出力先: `projects/dozle_kirinuki/work/orafu_futuristic/`

## Step 1: gen_naginata_chara.py の改修

以下の変更を加えよ（既存スクリプトの拡張）:

### 1-a: import追加
```python
import subprocess
import argparse
```

### 1-b: upload_to_gcs 関数追加（main()の前に挿入）
```python
GCS_BUCKET = "gs://shogun-manga-refs/ref_images/"

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
```

### 1-c: generate_image 関数の Part.from_bytes → Part.from_uri に置換
```python
# 変更前
parts = [
    types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg"),
    types.Part.from_text(text=...),
]

# 変更後（ref_gcs_uri を引数に追加）
parts = [
    types.Part.from_uri(file_uri=ref_gcs_uri, mime_type="image/png"),
    types.Part.from_text(text=...),
]
```

generate_image のシグネチャ: `def generate_image(client, ref_gcs_uri, prompt, aspect_ratio, out_path):`

### 1-d: main() にモード分岐追加
argparse で `--mode orafu` オプションを追加し、おらふくんモード時は以下を使用:

```python
ORAFU_REF = Path("projects/dozle_kirinuki/assets/dozle_jp/character/oraf-kun.png")
ORAFU_OUT_DIR = Path("projects/dozle_kirinuki/work/orafu_futuristic")
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
```

main()のおらふくんモード生成ループ:
```python
if mode == "orafu":
    ORAFU_OUT_DIR.mkdir(parents=True, exist_ok=True)
    gcs_uri = upload_to_gcs(ORAFU_REF)
    if not gcs_uri:
        print("ERROR: GCSアップロード失敗"); sys.exit(1)
    for i in range(1, 6):  # 5枚
        out = ORAFU_OUT_DIR / f"orafu_futuristic_{i:02d}.png"
        print(f"\n[Orafu {i}/5]")
        generate_image(client, gcs_uri, ORAFU_PROMPT, "3:4", out)
        if i < 5: time.sleep(3)
```

## Step 2: 実行
```bash
cd /home/murakami/multi-agent-shogun
source config/vertex_api_key.env
python scripts/gen_naginata_chara.py --mode orafu
```

## Step 3: 成果物確認
```bash
ls -la projects/dozle_kirinuki/work/orafu_futuristic/
file projects/dozle_kirinuki/work/orafu_futuristic/*.png
```
5枚全て存在し、各ファイルが0バイトでないことを確認。

## Step 4: git commit
```bash
git add scripts/gen_naginata_chara.py
git add projects/dozle_kirinuki/work/orafu_futuristic/
git commit -m "feat(cmd_1370): おらふくん未来人版立ち絵5枚生成"
```
