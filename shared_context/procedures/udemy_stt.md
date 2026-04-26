# Udemy参考動画 AssemblyAI STT 手順

## Step1: 出力ディレクトリ作成
```bash
mkdir -p projects/udemy_course/context/reference_videos/
```

## Step2: 動画DL（音声優先480p）
```bash
yt-dlp -f 'bestvideo[height<=480]+bestaudio/best[height<=480]' \
  -o "projects/udemy_course/context/reference_videos/%(id)s.%(ext)s" \
  "https://youtu.be/tqj46pUd_Tw"
```

## Step3: AssemblyAI STT実行
vocal_stt_pipeline.py を使用（AssemblyAIのみ。WhisperX/Gemini STT禁止）:
```bash
python3 projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py stt \
  --input projects/udemy_course/context/reference_videos/tqj46pUd_Tw.mp4 \
  --output projects/udemy_course/context/reference_videos/
```
出力: `tqj46pUd_Tw.srt`

話者分離不要（1人喋り想定）。検出された場合はラベルそのまま保持。

## Step4: 品質確認
```bash
# エントリ数
grep -c '^[0-9][0-9]*$' projects/udemy_course/context/reference_videos/tqj46pUd_Tw.srt

# 動画尺確認
yt-dlp --get-duration "https://youtu.be/tqj46pUd_Tw"

# 最終タイムスタンプ確認（動画尺と比較）
tail -10 projects/udemy_course/context/reference_videos/tqj46pUd_Tw.srt
```
フォールバック/反復行がないか目視確認（最頻出テキスト5%以下）。

## Step5: git commit（SRTのみ）
```bash
git add projects/udemy_course/context/reference_videos/tqj46pUd_Tw.srt
git commit -m "feat(cmd_1418): Udemy参考動画tqj46pUd_Tw STT字幕生成"
```
mp4はcommit対象外。

## Step6: 完了報告
```bash
bash scripts/inbox_write.sh karo \
  "足軽1号、subtask_1418a完了。SRT生成済・{エントリ数}件・{最終タイムスタンプ}。commit済み。" \
  report_completed ashigaru1
```
