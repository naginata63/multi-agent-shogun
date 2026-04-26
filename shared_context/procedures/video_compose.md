# パネルPNG→音声合成→動画出力手順

## パラメータ
- `${PANELS_JSON}` — panels JSONファイルパス
- `${PNG_DIR}` — パネルPNGディレクトリ
- `${AUDIO_FILE}` — 音声ソースファイル（元動画 or クリップ）
- `${OUTPUT_FILE}` — 出力動画ファイルパス

## 前提
- パネルPNGが全て${PNG_DIR}に生成済み
- panels JSONにaudio_start/audio_endが定義済み（ない場合はstart_sec/duration_secで代用）

## 手順

### Step1: panels JSON確認
```bash
python3 -c "
import json
with open('${PANELS_JSON}') as f:
    d = json.load(f)
for p in d['panels']:
    audio_s = p.get('audio_start', p['start_sec'])
    audio_e = p.get('audio_end', p['start_sec'] + p['duration_sec'])
    print(f'{p[\"id\"]}: audio {audio_s}-{audio_e}s, display {p[\"start_sec\"]}-{p[\"start_sec\"]+p[\"duration_sec\"]}s')
"
```

### Step2: 既存スクリプトで合成
```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels ${PANELS_JSON} \
  --output ${PNG_DIR} \
  --skip-gen
```

**スクリプトが動かない場合のffmpeg手動合成:**

各パネルの音声区間をカット→パネルPNGと結合→連結:
```bash
mkdir -p /tmp/manga_compose

# 各パネルの音声カット+画像結合
for i in $(seq 0 $((PANEL_COUNT-1))); do
  PANEL_ID=$(python3 -c "import json; d=json.load(open('${PANELS_JSON}')); print(d['panels'][$i]['id'])")
  AUDIO_START=$(python3 -c "import json; d=json.load(open('${PANELS_JSON}')); p=d['panels'][$i]; print(p.get('audio_start', p['start_sec']))")
  AUDIO_END=$(python3 -c "import json; d=json.load(open('${PANELS_JSON}')); p=d['panels'][$i]; print(p.get('audio_end', p['start_sec']+p['duration_sec']))")
  DURATION=$(python3 -c "print($AUDIO_END - $AUDIO_START)")

  ffmpeg -y \
    -loop 1 -i "${PNG_DIR}/${PANEL_ID}.png" \
    -ss ${AUDIO_START} -t ${DURATION} -i "${AUDIO_FILE}" \
    -c:v h264_nvenc -preset p4 -pix_fmt yuv420p \
    -c:a aac -b:a 192k \
    -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
    -t ${DURATION} -shortest \
    "/tmp/manga_compose/part_${i}.mp4"
done

# 連結リスト作成
ls /tmp/manga_compose/part_*.mp4 | sort -V | sed "s/^/file '/" | sed "s/$/'/" > /tmp/manga_compose/concat.txt

# 連結
ffmpeg -y -f concat -safe 0 -i /tmp/manga_compose/concat.txt \
  -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "${OUTPUT_FILE}"
```

### Step3: 出力確認
```bash
ls -la ${OUTPUT_FILE}
ffprobe -v quiet -show_entries format=duration -of csv=p=0 ${OUTPUT_FILE}
# 想定秒数と一致するか確認
```

### Step4: 報告
```bash
bash scripts/inbox_write.sh karo \
  "足軽N号、subtask_XXX完了。動画合成完了。${OUTPUT_FILE}" \
  report_completed ashigaruN
```

## 注意事項
- ffmpegエンコードはh264_nvenc必須（libx264禁止）
- パネルPNGは768x1376 → 動画は1080x1920にスケール
- audio_start/audio_endがある場合はそちらを優先（start_sec/duration_secは出力タイミング用）
