# 縦型クロップ→YouTube非公開アップ手順

## パラメータ
- `${INPUT_FILE}` — 入力動画ファイルパス（mkvまたはmp4）
- `${OUTPUT_FILE}` — 出力mp4ファイルパス（例: tono_edit_vertical.mp4）
- `${TITLE}` — YouTubeタイトル
- `${VIDEO_ID}` — YouTube動画ID（アップ後に取得）
- `${ORIGINAL_VIDEO_ID}` — 元動画のYouTube ID（説明欄リンク用）

## Step1: 入力ファイル確認

```bash
ffprobe -v quiet -show_entries stream=width,height -of csv=p=0 "${INPUT_FILE}"
ls -la "${INPUT_FILE}"
```

## Step2: 縦型クロップ（1080x1920）

入力が3412x1918の場合:
```bash
ffmpeg -i "${INPUT_FILE}" \
  -vf "crop=1080:1918:1166:0,pad=1080:1920:0:1" \
  -c:v h264_nvenc -preset p4 -rc vbr -cq 23 -b:v 8M -maxrate 10M -bufsize 16M \
  -c:a aac -b:a 192k \
  "${OUTPUT_FILE}"
```

※ 実際のサイズに合わせてcrop値を調整すること。
※ h264_nvenc必須（libx264禁止）。
※ -iの後に -vf を置くこと（-ss の前後位置注意）。
※ **ビットレート指定必須**（`-rc vbr -cq 23 -b:v 8M -maxrate 10M`）。これを省くとNVENCデフォルト低ビットレート（数百kbps）になり画質劣化する（2026-04-19 cmd_1420で実証：439kbps/2.79MB出力の事故）。
※ 完了後ffprobeで bit_rate を確認。1080x1920で1Mbps未満なら品質不足、再エンコードせよ。

## Step3: YouTube非公開アップロード

```bash
cd /home/murakami/multi-agent-shogun
python3 projects/dozle_kirinuki/scripts/youtube_uploader.py upload \
  "${OUTPUT_FILE}" \
  --title "${TITLE}" \
  --privacy private
```

アップロード完了後、表示されたYouTube URLとVideo IDを記録する。

## Step4: 説明欄更新

```bash
python3 projects/dozle_kirinuki/scripts/youtube_uploader.py update-description \
  --video-id "${VIDEO_ID}" \
  --description "$(cat <<'EOF'
お題漫画「争わないで」

📌 元動画
仲間の気持ちがわかればチートになる世界でエンドラ討伐！【マイクラ】
https://www.youtube.com/watch?v=${ORIGINAL_VIDEO_ID}

🎮 ドズル社本家
https://www.youtube.com/@dozle

※この動画の漫画パートはAI画像生成を使用しています
※ドズル社公式ガイドラインに基づいて運営しています
https://www.dozle.jp/rule/

#ドズル社 #切り抜き #マイクラ #shorts #漫画
EOF
)"
```

※ update-descriptionコマンドが存在しない場合は `python3 projects/dozle_kirinuki/scripts/youtube_uploader.py --help` で確認してから代替コマンドを使え。

## Step5: 完了報告

```bash
bash scripts/inbox_write.sh karo \
  "足軽N号、subtask_XXX完了。YouTube非公開アップ完了。URL: ${YOUTUBE_URL}" \
  report_completed ashigaruN
```

## 注意事項
- **private必須。unlistedにするな**
- h264_nvenc必須（libx264禁止）
- 新規.py禁止。youtube_uploader.pyを使え
