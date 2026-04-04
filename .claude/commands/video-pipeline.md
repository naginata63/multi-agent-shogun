---
name: video-pipeline
description: |
  ドズル社切り抜き動画の素材パイプラインを実行する。YouTube動画DL→Demucsボーカル分離→文字起こし→話者ID→SRTマージ→軍師5回集合知（HL+SH候補選定）まで一貫して担当。
  「動画素材パイプライン」「video-pipeline」「DLから文字起こし」「HL候補選定」「軍師集合知」「/video-pipeline」で起動。
  Do NOT use for: 漫画ショート動画生成（それは/manga-shortを使え）。Do NOT use for: 動画エンコード・thumbnail作成（それはmain.pyを使え）。
argument-hint: "[youtube_url or video_id]"
allowed-tools: Bash, Read
---

# /video-pipeline — 動画素材パイプラインスキル

## North Star

YouTube動画を取得してから軍師5回集合知でHL+SH候補を選定するまでの全ステップを、中断なく効率的に完了させること。

## スクリプトパス（プロジェクトルート相対）

| スクリプト | パス |
|-----------|------|
| ダウンローダー | `projects/dozle_kirinuki/scripts/downloader.py` |
| 自動素材収集（WhisperX一括） | `projects/dozle_kirinuki/scripts/auto_fetch.py` |
| メインパイプライン | `projects/dozle_kirinuki/scripts/main.py` |
| YouTubeアップロード | `projects/dozle_kirinuki/scripts/youtube_uploader.py` |

## work/ ディレクトリ規則

```
projects/dozle_kirinuki/work/{YYYYMMDD_動画タイトル}/
  input/
    {video_id}.mp4          # 360p動画
    {video_id}_1080p.mp4    # 1080p動画（動画生成時にDL）
    {video_id}_subs.json    # YouTube字幕
    {video_id}_chat.json    # ライブチャット
    {video_id}_comments.json # コメント
  output/
    {cmd_id}/
      vocals.wav            # Demucs分離済みボーカル
      {video_id}_assemblyai.srt
      {video_id}_deepgram.srt
      merged.srt / merged.json
      gunshi_round_{N}.yaml # 軍師5回集合知結果
```

**注意**: プロジェクトルート直下の `work/` 禁止。必ず `projects/dozle_kirinuki/work/` 配下。

## 実行手順

### Phase 1: 動画DL（360p）

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
source ~/.bashrc && source venv/bin/activate

python3 scripts/downloader.py "<YouTube_URL>" \
  --output-dir work/<YYYYMMDD_タイトル>/input/
```

DL対象:
- 360p動画（`{video_id}.mp4`）— 音声解析・字幕生成用
- YouTube字幕 (`{video_id}_subs.json`)
- ライブチャット (`{video_id}_chat.json`)
- コメント (`{video_id}_comments.json`)

**注意**: 1080pは動画生成時に別途DL。最初は360pのみ。

確認:
```bash
ls work/<YYYYMMDD_タイトル>/input/
# {video_id}.mp4, {video_id}_subs.json 等が存在すること
ffprobe -v quiet -print_format json -show_format work/.../{video_id}.mp4 | grep duration
```

### Phase 2: Demucsボーカル分離（10分チャンク分割必須）

**絶対ルール**: 一発投入禁止。10分（600秒）チャンクに分割して実行。
理由: 一発投入で3回クラッシュした実績あり（2026-03-12）。

```bash
# 動画の長さを確認
DURATION=$(ffprobe -v quiet -print_format json -show_format \
  work/<YYYYMMDD_タイトル>/input/{video_id}.mp4 | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(float(d['format']['duration']))")

# 音声抽出
ffmpeg -i work/.../input/{video_id}.mp4 \
  -vn -ac 1 -ar 22050 work/.../output/{cmd_id}/audio_raw.wav

# 10分チャンクに分割
CHUNK=600  # 600秒 = 10分
for i in $(seq 0 $(($(python3 -c "import math; print(math.ceil($DURATION/$CHUNK))") - 1))); do
  START=$((i * CHUNK))
  ffmpeg -i work/.../output/{cmd_id}/audio_raw.wav \
    -ss $START -t $CHUNK \
    work/.../output/{cmd_id}/chunk_$(printf "%03d" $i).wav
done

# 各チャンクにDemucs適用
for chunk in work/.../output/{cmd_id}/chunk_*.wav; do
  source ~/.bashrc && python3 -m demucs --two-stems=vocals \
    -o work/.../output/{cmd_id}/demucs_out/ "$chunk"
done

# チャンクのvocalsを結合
ffmpeg -f concat -safe 0 \
  -i <(for f in work/.../output/{cmd_id}/demucs_out/htdemucs/*/vocals.wav; do echo "file '$f'"; done) \
  work/.../output/{cmd_id}/vocals.wav
```

タイムアウト目安: チャンク1本 = 約10分。30分動画 = 3チャンク = 約30分。

### Phase 3-5: 文字起こし＋話者ID＋STTマージ（auto_fetch.py 一括実行）

Phase 3〜5 は `auto_fetch.py` が一括で実行する（WhisperX + Speaker ID）。

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
source ~/.bashrc && source venv/bin/activate

python3 scripts/auto_fetch.py --video-id {video_id}
```

処理内容:
- WhisperX で文字起こし（10分チャンク分割自動実行）
- Speaker ID（ECAPA-TDNN）付与
- 辞書後処理・チャット密度分析・コメント分析

出力先: `work/auto_fetch/{video_id}/fine_grained_with_speakers.srt`

**注意**: 出力ディレクトリは `work/auto_fetch/{video_id}/` 固定（`cmd_id` 配下ではない）。
軍師5回集合知に渡す際は、このSRTパスを指定すること。

### Phase 6: 軍師5回集合知（HL+SH候補選定）

**目的**: 軍師を5回/clearリセットして独立した視点でHL+SH候補を選定、集約する。

**鉄則**:
- **/clearの制御権は家老**。軍師が自分でclearしない
- **本数制限なし** — 面白いシーンだけを選ぶ。数合わせ禁止
- **毎ラウンド必ず家老に報告してから次へ**

**入力ファイル（軍師に渡す）**:
- `merged.srt` または `merged.json` — 話者付き文字起こし
- `{video_id}_chat.json` — ライブチャット
- `{video_id}_comments.json` — コメント

**ナレッジ4文書（毎ラウンド必読）**:
- `context/member_profiles.yaml` — メンバー情報
- `context/highlight_command_template.md` — HL制作テンプレート
- `context/shorts_command_template.md` — SH制作テンプレート
- `memory/gunshi_5round_protocol.md` — 集合知プロトコル

**家老がタスクYAMLに書くべき内容**:
```yaml
task_id: subtask_XXX_gunshi_round_N
assigned_to: gunshi
description: |
  軍師5回集合知 ラウンドN/5
  入力: work/.../output/{cmd_id}/merged.srt
       work/.../input/{video_id}_chat.json
       work/.../input/{video_id}_comments.json
  結果を gunshi_round_N.yaml に保存して家老にinbox_write報告せよ。
  本数制限なし。面白いシーンのみ選べ。
```

**5ラウンド完了後の集約**:
1. 軍師が全5回のYAMLを集約
2. 同一シーン（前後30秒以内）を統合
3. 出現頻度でランク付け
4. 最終候補リスト → 家老に報告
5. 家老 → dashboardに反映 → 将軍が確認

## 中間成果物保存ルール

**重い処理の出力は必ずファイルに保存すること**:
- Demucs出力: `vocals.wav`（チャンク結合済み）
- AssemblyAI/Deepgram SRT: 各エンジン出力をファイルに保存
- merged.srt / merged.json: マージ済みを保存
- 軍師各ラウンド: `gunshi_round_{N}.yaml`

命名規則: `{処理名}_{video_id}_{タイムスタンプ}.{拡張子}`

## キャッシュ再利用

既存ファイルがある場合はスキップ:
```bash
# Phase 1スキップ例
if [ -f "work/.../input/{video_id}.mp4" ]; then
  echo "[skip] 動画DL済み"
else
  python3 scripts/downloader.py ...
fi
```

## ffmpeg エンコードルール

| 用途 | コーデック | 禁止 |
|------|-----------|------|
| H.264エンコード | `-c:v h264_nvenc -preset p4` | `-c:v libx264` |
| コピー（無変換） | `-c:v copy` | — |
| 音声 | `-c:a aac -b:a 192k` | — |

## 報告フォーマット

```
## video-pipeline 完了報告
### Phase完了状況
- [x] Phase 1: 動画DL (360p, {X}秒)
- [x] Phase 2: Demucs ({N}チャンク, vocals.wav)
- [x] Phase 3-5: auto_fetch.py 一括 (WhisperX + Speaker ID → fine_grained_with_speakers.srt {N}行)
- [ ] Phase 6: 軍師5回集合知 → 家老に引き継ぎ

### 成果物
- 360p動画: work/.../input/{video_id}.mp4
- SRT (話者付き): work/auto_fetch/{video_id}/fine_grained_with_speakers.srt
```
