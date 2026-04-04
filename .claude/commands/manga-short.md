---
name: manga-short
description: |
  ドズル社漫画ショート動画の制作ワークフローを実行する。
  panels JSONからPNG生成→音声結合→縦型動画→YouTube非公開アップロード→説明欄設定まで一貫して担当。
  「漫画ショート制作」「manga-short」「パネルPNG生成」「ショート動画アップ」「/manga-short」で起動。
  Do NOT use for: ハイライト動画制作（それはmain.py highlight modeを使え）。Do NOT use for: panels JSON自体の内容編集（panels JSONはGeminiが生成する）。
argument-hint: "[panels_json_path] [output_dir] [--skip-gen]"
allowed-tools: Bash, Read
---

# /manga-short — 漫画ショート制作スキル

## North Star

panels JSONから縦型ショート動画を生成し、YouTubeに非公開アップロードするまでを最短で完了させること。

## 前提知識

### スクリプトパス（プロジェクトルート相対）

| スクリプト | パス |
|-----------|------|
| PNG生成 | `projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py` |
| YouTubeアップロード | `projects/dozle_kirinuki/scripts/youtube_uploader.py` |
| メンバープロファイル | `projects/dozle_kirinuki/context/member_profiles.yaml` |

### panels JSON フォーマット

```json
{
  "meta": {
    "scene": "シーン説明",
    "video_id": "XXXXXXXXXXX",
    "short_title": "タイトル",
    "estimated_duration_sec": 94
  },
  "panels": [
    {
      "id": "panel_01",
      "title": "パネルタイトル",
      "speaker": "dozle",
      "line": "セリフ",
      "characters": ["dozle", "bon"],
      "start_sec": 3.6,
      "duration_sec": 5.0,
      "scene_desc": "場面説明（Geminiへの画像生成プロンプト用）",
      "situation": "状況説明"
    }
  ]
}
```

キャラクターキー: `dozle` / `bon` / `qnly` / `orafu` / `oo_men` / `nekooji`

### work/ ディレクトリ規則

`projects/dozle_kirinuki/work/{YYYYMMDD_動画タイトル}/output/{cmd_XXX}/`

**注意**: プロジェクトルート直下の `work/` 禁止。必ず `projects/dozle_kirinuki/work/` 配下。

## 実行手順

### Step 1: panels JSON 確認

```bash
cat <panels_json_path>
```

確認項目:
- パネル枚数・合計秒数（`estimated_duration_sec`）
- 出演キャラクター（`characters`配列のキー）
- clip音声ファイルが存在するか確認

```bash
ls <work_dir>/output/<cmd_id>/
# clip_{shN}.mp4 が存在すること
```

### Step 2: PNG生成

```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc && source projects/dozle_kirinuki/venv/bin/activate

python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels "<panels_json_path>" \
  --output "<output_dir>"
```

オプション:
- `--skip-gen` : PNG生成をスキップ（生成済みPNGを流用してfailした動画を再組み立て時に使用）
- `--panels` : panels JSONパス（必須）
- `--output` : 出力ディレクトリ（デフォルト: work/20260315_manga_short_proto/）

生成物確認:
```bash
ls <output_dir>/panel_*.png | wc -l  # panels枚数と一致すること
```

### Step 3: 動画組み立て（PNG + 音声 → 縦型MP4）

generate_manga_short.pyが内部で実行するが、ffmpeg使用時は**必ずh264_nvenc（GPU）**:

```bash
# スクリプト内でffmpegを呼ぶ場合の確認
# -c:v h264_nvenc -preset p4 を使用すること
# -c:v libx264 は絶対禁止（CPUエンコード: 数十分かかる）
```

出力動画確認:
```bash
ffprobe -v quiet -print_format json -show_format <output_dir>/*.mp4 | grep duration
# estimated_duration_sec と±3秒以内であること
```

### Step 4: YouTube 非公開アップロード

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
source ~/.bashrc && source venv/bin/activate

python3 scripts/youtube_uploader.py upload \
  "<output_video_path>" \
  --title "<タイトル【ドズル社/マイクラ/切り抜き】>" \
  --description "仮説明" \
  --privacy private
```

アップロード完了後、video_idをメモする（次ステップで必要）。

### Step 5: 説明欄設定

```bash
python3 scripts/youtube_uploader.py update_description \
  "<video_id>" \
  --description "$(cat <<'EODESC'
概要説明文（複数行可）
EODESC
)"
```

または事前にファイルに書いて渡す:
```bash
python3 scripts/youtube_uploader.py update_description \
  "<video_id>" \
  --description-file "<description_file.txt>"
```

### Step 6: サムネイル設定（オプション）

```bash
python3 scripts/youtube_uploader.py thumbnail \
  "<video_id>" \
  "<thumbnail_path>"
```

## ネコおじ出演確認ルール

panels JSONに `"nekooji"` が含まれるかチェック:

```bash
grep -c "nekooji" <panels_json_path>
```

- **0件**: スキップ。報告に「nekooji出演なし」と明記
- **1件以上**: 全パネルPNG再生成必要（`--skip-gen` 不可）

## 重要ルール

1. **ffmpegはh264_nvenc必須** — libx264禁止。RTX 4060 Ti搭載、NVENCは常に利用可能
2. **panels JSONは変更するな** — 読み取り専用。内容編集が必要な場合はKaroに報告
3. **アップロードはprivate** — `--privacy private`。公開判断は殿が行う
4. **Geminiプロンプト設計**: `skills/gemini-image-prompt/SKILL.md` 参照。situationや性格情報はsystem_instructionに入れよ（contentsに入れると画像内に文字として描画される）
4. **旧動画削除は慎重に** — 新URLを確認してから削除。競合状態に注意（他足軽が同じ動画を操作中かもしれない）
5. **動画編集スクリプトは1つずつ実行** — 同時並列実行禁止

## 報告フォーマット

```
## manga-short 完了報告
- panels: <N>枚 / <X>秒
- PNG生成: 完了 (panel_01.png 〜 panel_N.png)
- 動画: <output_path> (<X>秒)
- YouTube URL: https://youtu.be/<video_id>  (private)
- video_id: <video_id>
```
