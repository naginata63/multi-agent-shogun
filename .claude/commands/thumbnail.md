---
name: thumbnail
description: |
  ドズル社切り抜き動画のサムネイルをmake_thumbnail_auto.pyで自動生成する。
  selected.json/SRTからシーン情報抽出→Geminiテキスト生成→キャラ立ち絵(Embedding 2)表情マッチング→PIL合成→viability QCまで一貫して担当。
  「サムネイル生成」「thumbnail」「サムネ自動生成」「make_thumbnail_auto」「/thumbnail」で起動。
  Do NOT use for: 表情差分画像の新規生成（それは/expression-genを使え）。Do NOT use for: 動画素材準備（それは/video-pipelineを使え）。
argument-hint: "[video_id] [work_dir] [--chars <key1,key2>]"
allowed-tools: Bash, Read
---

# /thumbnail — サムネイル生成スキル

## North Star

selected.jsonとSRTから動画の「見せ場」を抽出し、キャラ立ち絵・テキスト・背景フレームを合成した
1920×1080のサムネイル案（A/B/C 3レイアウト）を生成し、viabilityスコアで最優秀案を提示すること。

## 前提知識

### スクリプトパス（プロジェクトルート相対）

| スクリプト | パス |
|-----------|------|
| サムネ自動生成（推奨） | `projects/dozle_kirinuki/scripts/make_thumbnail_auto.py` |
| サムネ手動生成（参考） | `projects/dozle_kirinuki/scripts/make_highlight_thumbnail.py` |
| メンバープロファイル | `projects/dozle_kirinuki/context/member_profiles.yaml` |
| 表情インデックス | `projects/dozle_kirinuki/context/expression_index.json` |
| 立ち絵（バストアップ） | `projects/dozle_kirinuki/assets/dozle_jp/character/selected/bust/` |
| ロゴ | `projects/dozle_kirinuki/branding/channel_logo.png` |
| フォント | `projects/dozle_kirinuki/assets/fonts/RanobePopB.otf` |

### make_thumbnail_auto.py 処理フロー

| STEP | 処理 | 備考 |
|------|------|------|
| 1 | コンテキスト収集 | selected.json / SRT / merged.json 読み込み |
| 2 | 背景フレーム選定 | ffmpeg + Gemini Vision 自動選定（`--bg-frame`で手動指定可） |
| 3 | サムネテキスト生成 | Gemini Textで煽り文（`--main-text`で手動指定可） |
| 4 | キャラ選定 | ルールベース（`--chars`で手動指定可） |
| 5 | 表情マッチング | Gemini Embedding 2でテキスト→表情スコア（`--main-expr`で手動指定可） |
| 6 | Embeddingスコアリング | viabilityスコア算出 |
| 7 | PIL合成 | A/B/C 3レイアウト生成（1920×1080） |
| 8 | メタデータ出力 | `thumbnail_meta.json` |

### 必須引数

| 引数 | 説明 |
|------|------|
| `--video-id` | YouTube動画ID（例: `Ccc2eq0LUAg`） |
| `--work-dir` | workディレクトリ（例: `projects/dozle_kirinuki/work/20260314_動画タイトル`） |
| `--output-dir` | 出力ディレクトリ |

### 主要オプション

| オプション | 説明 |
|-----------|------|
| `--srt <path>` | SRTファイルパス（話者抽出・テキスト生成に使用） |
| `--chars <key1,key2>` | キャラキーをカンマ区切り（例: `dozle,qnly,oo_men,orafu`） |
| `--main-char <key>` | メインキャラキー（2人モード） |
| `--sub-char <key>` | サブキャラキー（2人モード） |
| `--main-expr <expr>` | メイン表情を手動指定（例: `smile_r2`） |
| `--sub-expr <expr>` | サブ表情を手動指定（例: `surprise_r3`） |
| `--bg-frame <path>` | 背景フレーム手動指定（STEP 2スキップ） |
| `--main-text <text>` | メインテキスト手動指定（STEP 3スキップ） |
| `--text-mode suggest` | テキスト5案候補モード（殿が選ぶ） |
| `--use-image-embedding` | テキストラベルの代わりにバスト画像Embeddingでマッチング |
| `--no-effects` | 集中線・吹き出しエフェクトを無効化 |

### キャラクターキー一覧

| キー | 名前 |
|------|------|
| dozle | ドズル |
| bon | ぼんじゅうる |
| qnly | おんりー |
| orafu | おらふくん |
| oo_men | おおはらMEN |

※ `nekooji` は `--chars` での自動選定不可。ネコおじをサムネに含めたい場合は `--bg-frame` + PIL手動合成を使用。

### work/ ディレクトリ規則

```
projects/dozle_kirinuki/work/{YYYYMMDD_動画タイトル}/
  input/
    {video_id}.mp4           # 360p動画（背景フレーム抽出に使用）
    selected.json            # HL/SH選定結果
  output/
    {cmd_id}/
      merged.srt / merged.json   # SRTマージ済み
      thumbnail/
        thumbnail_A.png      # レイアウトA案
        thumbnail_B.png      # レイアウトB案
        thumbnail_C.png      # レイアウトC案
        thumbnail_meta.json  # メタデータ + viabilityスコア
```

**注意**: プロジェクトルート直下の `work/` 禁止。必ず `projects/dozle_kirinuki/work/` 配下。

## 実行手順

### Step 1: 前提ファイル確認

```bash
cd /home/murakami/multi-agent-shogun

# 360p動画（背景フレーム抽出に必要）
ls projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/input/{video_id}.mp4

# SRT（話者情報・テキスト生成に使用）
ls projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/merged.srt

# selected.json（場所はcmd_idによって異なる。家老のタスクYAMLで指定されたパスを使え）
# 例: output/{cmd_id}/selected.json または input/selected.json
ls <家老指定のselected.jsonパス>
```

### Step 2: 出力ディレクトリ作成

```bash
mkdir -p projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/thumbnail
```

### Step 3: サムネイル自動生成（推奨: テキスト5案モード）

まず5案候補を生成して殿に選ばせる（テキスト自動選定の場合）:

```bash
source ~/.bashrc && source projects/dozle_kirinuki/venv/bin/activate

python3 projects/dozle_kirinuki/scripts/make_thumbnail_auto.py \
  --video-id "{video_id}" \
  --work-dir "projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>" \
  --output-dir "projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/thumbnail" \
  --srt "projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/merged.srt" \
  --text-mode suggest \
  --chars "dozle,qnly"
```

### Step 4: テキスト確定後、本生成

殿がテキストを選んだら `--main-text` / `--sub-text` で確定:

```bash
python3 projects/dozle_kirinuki/scripts/make_thumbnail_auto.py \
  --video-id "{video_id}" \
  --work-dir "projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>" \
  --output-dir "projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/thumbnail" \
  --srt "projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/merged.srt" \
  --main-text "殿が選んだメインテキスト" \
  --sub-text "殿が選んだサブテキスト" \
  --chars "dozle,qnly"
```

### Step 5: Gemini Vision QC

生成された3案をGemini Visionで検証:
- サムネとして視覚的に成立しているか
- テキストが読みやすいか（コントラスト・フォントサイズ）
- キャラ立ち絵が自然に配置されているか
- viabilityスコアが最も高い案を確認

```bash
cat projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/thumbnail/thumbnail_meta.json
# viability_score が最高の案を特定
```

### Step 6: 比較画像を殿に提示

**必ず3案（A/B/C）の比較画像を殿に見せて選ばせること**（数値だけで決めない）。
殿が選んだ案をYouTubeサムネイルとして設定する。

```bash
python3 projects/dozle_kirinuki/scripts/youtube_uploader.py thumbnail \
  "<video_id>" \
  "projects/dozle_kirinuki/work/<YYYYMMDD_タイトル>/output/{cmd_id}/thumbnail/thumbnail_<A|B|C>.png"
```

## 重要ルール

1. **AIがサムネを独断で選ぶな** — 必ず3案提示→殿が選ぶ。viabilityスコアは参考値
2. **レイアウト変更は比較画像で確認** — 数値だけで報告するな
3. **テキストモードはsuggestから始める** — auto一発決定は殿の意図と外れることが多い
4. **背景フレーム自動選定が失敗したら手動指定** — `--bg-frame`で任意フレームを指定
5. **2MB超過は自動JPEG変換** — スクリプト内で処理済み（確認のみ）

## 報告フォーマット

```
## thumbnail 完了報告
- 動画ID: {video_id}
- 生成案: A案 / B案 / C案 (3レイアウト)
- viabilityスコア: A={X.XXXX}, B={X.XXXX}, C={X.XXXX}
- 推奨案: {案} (viability最高)
- テキスト: メイン「{text}」/ サブ「{text}」
- 出力パス: work/.../thumbnail/
- 殿確認待ち: どの案をYouTubeに設定するか選択ください
```
