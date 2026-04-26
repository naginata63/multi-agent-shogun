# 複数クリップ連結→1本の動画手順

## パラメータ
- `${CLIP_LIST}` — クリップ定義（番号|名前|開始秒|終了秒 のリスト or ファイルパス）
- `${SOURCE_VIDEO}` — 元動画ファイルパス
- `${OUTPUT_DIR}` — 出力先ディレクトリ
- `${OUTPUT_FILE}` — 最終連結動画ファイル名

## 手順

### Step1: 元動画確認
```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 ${SOURCE_VIDEO}
```

### Step2: 各クリップを切り出し
```bash
# クリップ定義ファイルから読み込む場合
while IFS='|' read -r num name start end; do
  DURATION=$(python3 -c "print($end - $start)")
  ffmpeg -y -ss ${start} -t ${DURATION} -i "${SOURCE_VIDEO}" \
    -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
    "${OUTPUT_DIR}/clip_${num}.mp4"
  echo "clip_${num}: ${name} (${start}-${end}s, ${DURATION}s)"
done < ${CLIP_LIST}
```

**個別指定の場合:**
```bash
ffmpeg -y -ss ${START_SEC} -t ${DURATION} -i "${SOURCE_VIDEO}" \
  -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "${OUTPUT_DIR}/clip_XX.mp4"
```

### Step3: 連結リスト作成
```bash
ls ${OUTPUT_DIR}/clip_*.mp4 | sort -V | \
  sed "s/^/file '/" | sed "s/$/'/" > ${OUTPUT_DIR}/concat_list.txt
```

### Step4: 連結
```bash
ffmpeg -y -f concat -safe 0 -i ${OUTPUT_DIR}/concat_list.txt \
  -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "${OUTPUT_DIR}/${OUTPUT_FILE}"
```

### Step5: タイムスタンプ生成（YouTube概要欄用）
```bash
python3 -c "
offset = 0
clips = []  # (name, duration) のリスト
for name, dur in clips:
    m, s = divmod(int(offset), 60)
    h, m = divmod(m, 60)
    ts = f'{m}:{s:02d}' if h == 0 else f'{h}:{m:02d}:{s:02d}'
    print(f'{ts} {name}')
    offset += dur
"
```

### Step6: 出力確認
```bash
ls -la ${OUTPUT_DIR}/${OUTPUT_FILE}
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${OUTPUT_DIR}/${OUTPUT_FILE}"
```

### Step7: 報告
```bash
bash scripts/inbox_write.sh karo \
  "足軽N号、subtask_XXX完了。クリップ連結完了。${OUTPUT_FILE}" \
  report_completed ashigaruN
```

## 注意事項
- ffmpegエンコードはh264_nvenc必須（libx264禁止）
- 元動画がDL済みか確認してからクリップ切り出し（未DLならyt-dlpで取得）
- 既にDL済みの動画はwork/配下にあるかもしれないので確認してからDL
