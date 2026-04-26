# generate_manga_short.py ガチャ生成手順

正規スクリプト `generate_manga_short.py` を使った漫画パネル生成・ガチャ手順。
**⚠️ generate_odai_panels.py 使用禁止** — お題01専用ハードコード（OKワード/NGワード混入バグ）。

## 前提確認

```bash
cd /home/murakami/multi-agent-shogun
source config/vertex_api_key.env  # VERTEX_API_KEY を読み込む（~/.bashrcのGEMINI_API_KEYは期限切れ）
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py --help
```

## 基本実行

```bash
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels <panels_json_path> \
  --output <output_dir>
```

## 特定パネルのみ生成（ガチャ用）

`--test-panel N` で N 番目のパネルのみ生成（1-indexed）。

```bash
# 例: panels_railgun.json の p6b_orafu_revive_and_die（インデックス7）のみ
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels <panels_json_path> \
  --test-panel 7 \
  --output <output_dir>
```

## ガチャ3回実行パターン

各回を別ディレクトリに出力し、キャッシュを無効化して異なる画像を生成する。

```bash
# 1回目 (v1): キャッシュなし
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels <panels_json_path> \
  --test-panel <N> \
  --output <base_dir>/v1 \
  --no-cache

# 2回目 (v2): キャッシュなし
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels <panels_json_path> \
  --test-panel <N> \
  --output <base_dir>/v2 \
  --no-cache

# 3回目 (v3): キャッシュなし
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels <panels_json_path> \
  --test-panel <N> \
  --output <base_dir>/v3 \
  --no-cache
```

## ガチャ後のギャラリーHTML作成

テンプレートを使ってガチャ比較ギャラリーを作成する。

テンプレート: `projects/dozle_kirinuki/scripts/manga_poc/gacha_gallery_template.html`

```bash
# テンプレートを参照してギャラリーHTMLを作成（Write toolで直接作成）
# 各 v1/v2/v3 の PNG を並べて表示するHTML
```

## ntfy通知

**⚠️ URLのプレフィックスは必ず `/work/` を使え**（`/projects/dozle_kirinuki/work/` ではない）

```bash
bash scripts/ntfy.sh "P6bガチャ完了 http://100.66.15.93:8770/work/<relative_path>/gallery.html"
```

URL変換: `projects/dozle_kirinuki/work/X/Y.html` → `http://100.66.15.93:8770/work/X/Y.html`

## 注意事項

- デフォルト=軽量モード（GCS URI+重いロードスキップ）。`--full` は不要
- `source config/vertex_api_key.env` 必須（毎実行前）
- GCS URI方式のみ（Part.from_bytes禁止）
- ガチャ上限3回（殿の許可なく追加禁止）
- git commit不要（work/ は git-ignored）
- 全パネル生成時は `--test-panel` を省略（全パネルが生成される）
