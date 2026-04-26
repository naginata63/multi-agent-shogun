# STTパイプライン手順（DL→Demucs→STT→話者ID→SRTマージ）

## パラメータ
- `${VIDEO_ID}` — YouTube動画ID
- `${VIDEO_URL}` — YouTube URL
- `${WORK_DIR}` — 作業ディレクトリ（projects/dozle_kirinuki/work/YYYYMMDD_タイトル/）

## 前提
- AssemblyAI APIキーが設定済み
- Demucsインストール済み
- pyannote（話者分離）のtorchaudioが動作すること

## 手順

### Step0: 区間プレビュー確認（長尺動画の場合は必須）

**長尺動画（30分超）でクリップ区間を指定する場合、本Step完了前にDemucs/STTに進んではならない。**

```bash
# 指定区間の10秒プレビューを作成して「目的の発話が含まれるか」を確認
PREVIEW_START=15309  # 予定クリップ開始秒
ffmpeg -ss ${PREVIEW_START} -i "${WORK_DIR}/full.mp4" \
  -t 10 -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "${WORK_DIR}/preview_${PREVIEW_START}.mp4" -y

# 確認方法: ffprobe で duration が 10s 近くあること
ffprobe -v quiet -show_entries format=duration -of csv=p=0 \
  "${WORK_DIR}/preview_${PREVIEW_START}.mp4"
```

**確認後**: キーワードが含まれると判断できたら Step1（クリップ本番）へ進む。含まれない場合はタイムスタンプを修正してから再プレビュー。

> 教訓: cmd_1410で2138s区間を誤指定→QC FAIL。正しい区間15309sは「ざっくり確認」で事前検出できた（2026-04-17）。

### Step1: 動画DL（1080p）
```bash
cd /home/murakami/multi-agent-shogun
mkdir -p ${WORK_DIR}/input
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
  -o "${WORK_DIR}/input/${VIDEO_ID}.mp4" \
  "${VIDEO_URL}"
```

### Step2: Demucsボーカル分離
```bash
python3 scripts/vocal_stt_pipeline.py demucs \
  --input "${WORK_DIR}/input/${VIDEO_ID}.mp4" \
  --output "${WORK_DIR}"
```
出力: `${WORK_DIR}/vocals_full.wav`

### Step3: STT（AssemblyAI）
```bash
python3 scripts/vocal_stt_pipeline.py stt \
  --input "${WORK_DIR}/vocals_full.wav" \
  --output "${WORK_DIR}"
```
出力: `${WORK_DIR}/assemblyai_vocals.json`

### Step4: 話者ID（実名変換）
```bash
python3 scripts/vocal_stt_pipeline.py speaker_id \
  --input "${WORK_DIR}/assemblyai_vocals.json" \
  --output "${WORK_DIR}"
```
出力: `${WORK_DIR}/fine_grained_${VIDEO_ID}.srt`（話者名付き）

### Step5: SRTマージ
```bash
python3 scripts/stt_merge.py \
  --input "${WORK_DIR}/fine_grained_${VIDEO_ID}.srt" \
  --output "${WORK_DIR}/merged_${VIDEO_ID}.srt"
```
出力: `${WORK_DIR}/merged_${VIDEO_ID}.srt`

### Step6: 品質検証
```bash
# 動画の尺を取得
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${WORK_DIR}/input/${VIDEO_ID}.mp4")
# SRTの最終タイムスタンプを取得
LAST_TS=$(tail -5 "${WORK_DIR}/merged_${VIDEO_ID}.srt" | grep -oP '\d+:\d+:\d+' | tail -1)
echo "動画尺: ${DURATION}秒 / SRT末尾: ${LAST_TS}"
# SRTが動画尺の90%以上をカバーしていることを確認

# 話者名チェック（アルファベットラベル不可）
grep -c "\[Speaker" "${WORK_DIR}/merged_${VIDEO_ID}.srt"
# → 0であること（全て実名変換済み）
```

### Step7: 報告
```bash
WORD_COUNT=$(wc -w < "${WORK_DIR}/merged_${VIDEO_ID}.srt")
SPEAKER_COUNT=$(grep -oP '\[\w+\]' "${WORK_DIR}/merged_${VIDEO_ID}.srt" | sort -u | wc -l)
bash scripts/inbox_write.sh karo \
  "足軽N号、subtask_XXX完了。${VIDEO_ID} STT完了。${WORD_COUNT}words・話者${SPEAKER_COUNT}名実名変換OK" \
  report_completed ashigaruN
```

## 注意事項
- **長尺動画（30分超）は必ずStep0（区間プレビュー確認）を実施してからクリップせよ**
- STTはAssemblyAIを使え（Gemini STT廃止済み）
- 話者ラベルはアルファベット不可。メンバー実名に変換済みであること
- SRTが動画尺の90%未満の場合は「不完全」として報告（完了扱いにするな）
- 中間成果物はファイルに保存（/tmp禁止）
- Demucsは重い処理。GPUメモリ不足時はチャンク分割
