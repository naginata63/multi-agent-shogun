# 漫画パイプライン手順書

## 話者識別 QC フェーズ

Gemini 動画解析で話者が「不明」と判定された行を、字幕色から再識別する。

### 前提条件

- raw.json (`*_raw.json`) に `speaker: "不明"` の行が含まれていること
- 字幕焼き込み済みの最終動画またはスクリーンショットが利用可能であること
- `context/member_profiles.yaml` にメンバーカラーが定義されていること

### 手順

```bash
# 1. strict mode でレポート確認
python3 scripts/subtitle_speaker_qc.py \
  --input work/{video_dir}/panels_*_raw.json \
  --video work/{video_dir}/final_with_subtitles.mp4 \
  --method pil \
  --mode strict \
  --output queue/reports/{date}_subtitle_qc_report.md

# 2. レポートを確認し、識別結果が妥当か判断

# 3. 問題なければ update mode で speaker を更新
python3 scripts/subtitle_speaker_qc.py \
  --input work/{video_dir}/panels_*_raw.json \
  --video work/{video_dir}/final_with_subtitles.mp4 \
  --method pil_ocr \
  --mode update \
  --output queue/reports/{date}_subtitle_qc_report.md
```

### 判定方式

| 方式 | コマンド | 特徴 |
|------|----------|------|
| PIL (`--method pil`) | デフォルト | 高速・無料。字幕領域（下部18%固定）の色ピクセルを分析 |
| PIL+OCR (`--method pil_ocr`) | `--method pil_ocr` | EasyOCRでテキスト領域を動的検出→縁取り色分析。マイクラUI誤認低減 |
| Gemini Vision (`--method gemini`) | `--method gemini` | 高精度。Gemini 2.0 Flash でAI判定。API利用 |

### 注意事項

- **ベース動画（字幕なし）では正確な判定不可**。最終動画またはスクリーンショットを使用すること
- PIL 方式は confidence が低い（<40%）場合、ゲーム画面等のノイズの可能性が高い
- Gemini 方式は API コストが発生（gemini-2.0-flash: ~$0.001/画像）
- 同一タイムスタンプの複数行は同一フレームから判定（キャッシュ機能）
