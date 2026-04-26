# Bロール合成確認手順

FINAL_COMPOSED.mp4にBロールオーバーレイが正しく入っているか確認する。

## パラメータ

- `video_path`: 確認対象の動画ファイルパス
- `broll_design_json`: Bロールタイムスタンプ定義JSON
- `compose_script`: 再実行用スクリプト（NG時のみ）

## 手順

### Step1: Bロールタイムスタンプ取得

```bash
cat {broll_design_json} | python3 -c "import json,sys; d=json.load(sys.stdin); [print(s['broll']['time_start']) for s in d.get('sections',[]) if 'broll' in s]" | head -3
```

### Step2: 静止画抽出（最低3箇所）

```bash
ffmpeg -ss {time1} -i {video_path} -vframes 1 /tmp/broll_check_1.jpg -y
ffmpeg -ss {time2} -i {video_path} -vframes 1 /tmp/broll_check_2.jpg -y
ffmpeg -ss {time3} -i {video_path} -vframes 1 /tmp/broll_check_3.jpg -y
```

Readツールで画像を読み込み、右上にBロール画像が映っているか目視確認。

### Step3: 動画長確認

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 {video_path}
```

### Step4: 判定

- **OK（Bロールあり）**: ntfy送信→Karo報告へ
- **NG（Bロールなし）**: `python3 {compose_script}` を再実行 → 再度Step2で確認

### Step5: 報告

```bash
bash /home/murakami/multi-agent-shogun/scripts/ntfy.sh "✅ cmd_1334完了: Bロール確認済み duration={X}s"
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽1号、subtask_1334a2完了。Bロール{あり/なし}・duration={X}s。" report_completed ashigaru1
```
