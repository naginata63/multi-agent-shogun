# cmd_1615 完了報告書 — 雪合戦縦型クロップ + YouTube非公開アップ

## 概要
tono_edit.mkv (1920x1080 FFV1) を縦型 1080x1920 h264_nvenc にクロップし、YouTube非公開アップロード完了。

## 処理詳細

### 入力
- ファイル: `projects/dozle_kirinuki/work/20260503_季節外れの雪合戦でガチ対決！【マイクラ】/tono_edit.mkv`
- 解像度: 1920x1080 / 60fps / FFV1 / FLAC
- 容量: 1.8GB

### クロップ・エンコード
- フィルタ: `crop=608:1080:656:0,scale=1080:1920`
- コーデック: h264_nvenc / yuv420p / CBR 8Mbps
- 出力: tono_edit_vertical.mp4 (1080x1920 / 60fps / 7.98Mbps / 70.7MB)

### 品質確認 (ffprobe)
- width=1080 / height=1920 / codec=h264 / pix_fmt=yuv420p
- video bitrate: 7,978 kbps (>5Mbps ✅)
- r_frame_rate: 60/1 ✅
- duration: 72.48s ✅

### YouTube
- Video ID: **ADbvr9TduZI**
- URL: https://www.youtube.com/watch?v=ADbvr9TduZI
- Privacy: **private** ✅
- タイトル: 季節外れの雪合戦でガチ対決！【マイクラ切り抜き】
- 概要欄: 元動画URL + ドズル社本家 + ハッシュタグ (#ドズル社 #切り抜き #マイクラ #shorts)

### 元動画
- ID: 4mlCQ7dVKXM
- URL: https://youtu.be/4mlCQ7dVKXM
- タイトル: 季節外れの雪合戦でガチ対決！【マイクラ】

### 備考
- 1回目エンコード (VBR+CQ23): yuv444p + 1.5Mbps → YouTube非互換・受入基準未達
- 2回目 (VBR+CQ20+pix_fmt yuv420p): 1.87Mbps → まだ5Mbps未満
- 3回目 (CBR 8Mbps+pix_fmt yuv420p): 7.98Mbps → PASS
- FFV1ソースがyuv444pだったため明示的pix_fmt指定が必須だった

## 成果物
- `projects/dozle_kirinuki/work/20260503_.../tono_edit_vertical.mp4`
- `projects/dozle_kirinuki/work/20260503_.../sync_record.yaml`
- `queue/reports/2026-05-04_cmd_1615_yukigassen_vertical_upload.md`
