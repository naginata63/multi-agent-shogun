---
name: highlight
description: |
  ドズル社ハイライト動画（長尺切り抜き）の制作ワークフローを実行する。
  selected.json確認→1080p DL→main.py highlight mode→サムネイル生成→YouTubeアップ→概要欄チャプター設定まで一貫して担当。
  「ハイライト制作」「highlight」「HL動画」「長尺切り抜き」「/highlight」で起動。
  Do NOT use for: ショート動画制作（それは/manga-shortを使え）。Do NOT use for: 素材取得・STTマージ（それは/video-pipelineを使え）。
argument-hint: "[work_dir] [cmd_id]"
allowed-tools: Bash, Read
---

# /highlight — ハイライト動画制作スキル

## North Star

selected.jsonで指定されたシーンから、1080p高画質ハイライト動画を生成し、YouTubeに非公開アップロードするまでを最短で完了させること。

## 前提知識

### スクリプトパス（プロジェクトルート相対）

| スクリプト | パス |
|-----------|------|
| メインパイプライン | `projects/dozle_kirinuki/scripts/main.py` |
| ハイライトパイプライン | `projects/dozle_kirinuki/scripts/highlight_pipeline.py` |
| サムネイル生成 | `projects/dozle_kirinuki/scripts/make_highlight_thumbnail.py` |
| YouTubeアップロード | `projects/dozle_kirinuki/scripts/youtube_uploader.py` |

### selected.json v2 フォーマット

```json
{
  "video_id": "XXXXXXXXXXX",
  "title": "ハイライトタイトル",
  "description": "概要欄テキスト",
  "main_speaker": "dozle",
  "scenes": [
    {
      "id": 1,
      "start": 120.5,
      "end": 180.0,
      "title": "シーンタイトル",
      "telop": "テロップテキスト",
      "speaker": "dozle"
    }
  ]
}
```

`main_speaker`にはメンバーキー（`dozle` / `bon` / `qnly` / `orafu` / `oo_men` / `nekooji`）を指定。

### work/ ディレクトリ規則

```
projects/dozle_kirinuki/work/{YYYYMMDD_動画タイトル}/
  input/
    {video_id}.mp4          # 360p動画（素材取得済み）
    {video_id}_1080p.mp4    # 1080p動画（本スキルでDL）
    {video_id}_subs.json    # YouTube字幕
  output/
    {cmd_id}/
      highlight_*.mp4       # 生成されたハイライト動画
      thumbnail.png         # サムネイル
      selected.json         # 使用したselected.json
```

**注意**: プロジェクトルート直下の `work/` 禁止。必ず `projects/dozle_kirinuki/work/` 配下。

## 実行手順

### Step 1: 前提確認

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
source ~/.bashrc && source venv/bin/activate
```

selected.jsonを確認:
```bash
cat work/<YYYYMMDD_タイトル>/output/<cmd_id>/selected.json
```

確認項目:
- `scenes`配列の件数・各シーンの`start`/`end`
- `main_speaker`（立ち絵・字幕色に影響）
- `title`（YouTube動画タイトルに使用）

360p素材の存在確認:
```bash
ls work/<YYYYMMDD_タイトル>/input/{video_id}.mp4
```

### Step 2: 1080p動画DL

**ハイライト動画は1080pで生成。** 360pは音声解析・字幕生成専用。

```bash
python3 scripts/downloader.py "https://www.youtube.com/watch?v={video_id}" \
  --output-dir work/<YYYYMMDD_タイトル>/input/ \
  --quality 1080p
```

DL完了確認:
```bash
ls -lh work/<YYYYMMDD_タイトル>/input/{video_id}_1080p.mp4
ffprobe -v quiet -print_format json -show_format work/.../{video_id}_1080p.mp4 | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'duration: {float(d[\"format\"][\"duration\"]):.1f}s')"
```

### Step 3: ハイライト動画生成

```bash
python3 scripts/main.py \
  "https://www.youtube.com/watch?v={video_id}" \
  --mode highlight \
  --selected work/<YYYYMMDD_タイトル>/output/<cmd_id>/selected.json \
  --work-dir work/<YYYYMMDD_タイトル>/ \
  --output-dir work/<YYYYMMDD_タイトル>/output/<cmd_id>/
```

**ffmpegエンコードルール（厳守）**:

| 用途 | コーデック | 禁止 |
|------|-----------|------|
| H.264エンコード | `-c:v h264_nvenc -preset p4` | `-c:v libx264` |
| コピー（無変換） | `-c:v copy` | — |
| 音声 | `-c:a aac -b:a 192k` | — |

RTX 4060 Ti搭載。NVENCは常に利用可能。libx264を使うと32分動画で3時間半かかる。

処理完了確認:
```bash
ls -lh work/<YYYYMMDD_タイトル>/output/<cmd_id>/highlight_*.mp4
ffprobe -v quiet -print_format json -show_format work/.../highlight_*.mp4 | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'duration: {float(d[\"format\"][\"duration\"]):.1f}s')"
```

### Step 4: サムネイル生成

```bash
python3 scripts/make_highlight_thumbnail.py \
  --video work/<YYYYMMDD_タイトル>/input/{video_id}_1080p.mp4 \
  --selected work/<YYYYMMDD_タイトル>/output/<cmd_id>/selected.json \
  --output work/<YYYYMMDD_タイトル>/output/<cmd_id>/thumbnail.png
```

サムネイル確認:
```bash
ls -lh work/<YYYYMMDD_タイトル>/output/<cmd_id>/thumbnail.png
# 2MB以下であること（YouTube制限）
```

2MB超えの場合:
```bash
python3 scripts/compress_thumbnail.py \
  work/<YYYYMMDD_タイトル>/output/<cmd_id>/thumbnail.png
```

### Step 5: YouTube 非公開アップロード

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki

python3 scripts/youtube_uploader.py upload \
  "work/<YYYYMMDD_タイトル>/output/<cmd_id>/highlight_*.mp4" \
  --title "<selected.jsonのtitle>" \
  --description "仮説明（後で更新）" \
  --privacy private
```

アップロード完了後、video_idをメモする。

### Step 6: 概要欄・チャプター設定

チャプターはselected.jsonのscenesから自動生成:

```python
# チャプター形式:
# 0:00 オープニング
# 0:30 シーン1タイトル
# 2:15 シーン2タイトル
# ...
```

`scripts/add_chapters.py` または手動でselected.jsonから生成:
```bash
python3 scripts/add_chapters.py \
  --selected work/.../selected.json \
  --video-id <youtube_video_id>
```

または手動で概要欄更新:
```bash
python3 scripts/youtube_uploader.py update_description \
  "<video_id>" \
  --description "$(cat <<'EODESC'
${selected.jsonのdescription}

━━ チャプター ━━
0:00 オープニング
0:30 シーン1タイトル
...

#ドズル社 #マイクラ #切り抜き
EODESC
)"
```

### Step 7: サムネイル設定

```bash
python3 scripts/youtube_uploader.py thumbnail \
  "<video_id>" \
  "work/<YYYYMMDD_タイトル>/output/<cmd_id>/thumbnail.png"
```

## 重要ルール

1. **ffmpegはh264_nvenc必須** — libx264禁止。RTX 4060 Ti搭載、NVENCは常に利用可能
2. **アップロードはprivate** — `--privacy private`。公開判断は殿が行う
3. **エンドロールを含めない** — selected.jsonにエンドロールシーンを入れるな
4. **シーン選定は殿が行う** — AIがシーンを勝手に選ばない。selected.jsonは家老から渡される
5. **動画編集スクリプトは1つずつ実行** — 同時並列実行禁止

## 中間成果物保存ルール

1080p DLは時間がかかる。2回目以降は既存ファイルを再利用:
```bash
if [ -f "work/.../input/{video_id}_1080p.mp4" ]; then
  echo "[skip] 1080p DL済み"
else
  python3 scripts/downloader.py ... --quality 1080p
fi
```

## 報告フォーマット

```
## highlight 完了報告
- video_id（元動画）: {video_id}
- scenes: {N}シーン / 合計{X}秒
- 動画: work/.../output/{cmd_id}/highlight_*.mp4 ({X}秒)
- サムネイル: work/.../output/{cmd_id}/thumbnail.png
- YouTube URL: https://youtu.be/{youtube_video_id}  (private)
- チャプター設定: 完了 / 未完了
```
