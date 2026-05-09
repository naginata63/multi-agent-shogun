# YouTube非公開アップロード手順

## パラメータ
- `${VIDEO_FILE}` — アップロードする動画ファイルパス
- `${TITLE}` — 動画タイトル
- `${DESCRIPTION}` — 概要欄テキスト（オプション）
- `${PRIVACY}` — private（デフォルト。unlisted/public禁止）

## 手順

### Step1: 動画ファイル確認
```bash
ls -la ${VIDEO_FILE}
ffprobe -v quiet -show_entries format=duration,size -of csv=p=0 ${VIDEO_FILE}
```

### Step2: アップロード
```bash
cd /home/murakami/multi-agent-shogun
python3 projects/dozle_kirinuki/scripts/youtube_uploader.py upload \
  "${VIDEO_FILE}" \
  --title "${TITLE}" \
  --privacy private
```

概要欄がある場合:
```bash
python3 projects/dozle_kirinuki/scripts/youtube_uploader.py upload \
  "${VIDEO_FILE}" \
  --title "${TITLE}" \
  --description "${DESCRIPTION}" \
  --privacy private
```

### Step3: URL取得・報告
アップロード完了後に表示されるURLを報告に含める。

```bash
curl -s -X POST http://192.168.2.4:8770/api/inbox_write -H 'Content-Type: application/json' -d '{"to":"karo","from":"ashigaru{N}","type":"report_received","message":"足軽N号、subtask_XXX完了。YouTube非公開アップ完了。URL: ${YOUTUBE_URL}"}'
```

## 注意事項
- **private必須。unlistedにするな**（殿が明示的に指示した場合のみ変更可）
- YouTube Data API v3のクォータ制限に注意
- アップロード失敗時はエラーメッセージを報告（リトライはkaro判断）
