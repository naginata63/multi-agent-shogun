---
name: gemini-video-transcribe
description: |
  Gemini APIを使って動画ファイルからSRT字幕を一発生成する。
  話者分離（Speaker ID）ありまたはなしを選択可能。
  モデル別コスト目安を実行前に表示する。
  「字幕生成」「文字起こし」「transcribe」「SRT生成」「gemini字幕」「話者付き字幕」で起動。
  Do NOT use for: WhisperXによる字幕生成（別途 speaker_id.py を使え）。
argument-hint: "<video_path> -o <output.srt> [--model MODEL] [--no-speaker-diarize] [--dry-run]"
allowed-tools: Bash, Read
---

# /gemini-video-transcribe - Gemini動画字幕生成スキル

## North Star

このスキルの北極星は**GPU不要・低コスト・高品質な字幕生成によるパイプライン効率化**。
Gemini APIの動画理解能力を活用し、WhisperX + Demucs の重いGPU処理なしで
話者付きSRT字幕を生成する。

## Input

`$ARGUMENTS` = 動画ファイルパスとオプション（例: `video.mp4 -o output.srt`）

## コスト目安（2026-03時点）

| モデル | 45分動画 | 推奨用途 |
|--------|----------|---------|
| gemini-3.1-flash-lite-preview（デフォルト） | $0.05 | 通常字幕生成 |
| gemini-3-flash-preview | $0.20 | 高精度が必要な場合 |
| gemini-3.0-pro-preview | $0.61 | 最高精度（高コスト） |

## 実行手順

### Step 1: コスト確認（--dry-run）

```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc && python3 skills/gemini-video-transcribe/transcribe.py \
  "$VIDEO_PATH" \
  --output "$OUTPUT_SRT" \
  --dry-run
```

コスト目安を確認し、ユーザーに承認を求める。

### Step 2: 字幕生成

#### 話者分離あり（推奨: Speaker IDでdozle/bon等のラベルを付与）

```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc && python3 skills/gemini-video-transcribe/transcribe.py \
  "$VIDEO_PATH" \
  --output "$OUTPUT_SRT" \
  --model gemini-3.1-flash-lite-preview
```

#### 話者分離なし（GPU不要、高速）

```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc && python3 skills/gemini-video-transcribe/transcribe.py \
  "$VIDEO_PATH" \
  --output "$OUTPUT_SRT" \
  --no-speaker-diarize
```

#### 既存Gemini SRTを再利用（API再呼出しをスキップ）

```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc && python3 skills/gemini-video-transcribe/transcribe.py \
  "$VIDEO_PATH" \
  --output "$OUTPUT_SRT" \
  --gemini-srt work/pipeline_XXX/gemini_XXX.srt
```

### Step 3: 結果確認

```bash
# エントリ数確認
grep -c '^[0-9][0-9]*$' "$OUTPUT_SRT"

# 最終タイムスタンプ（カバレッジ確認）
grep -oP '\d{2}:\d{2}:\d{2}' "$OUTPUT_SRT" | tail -1

# 話者数（話者分離ありの場合）
grep -oP '^\[.*?\]' "$OUTPUT_SRT" | sort -u | wc -l

# ハルシネーション確認（最頻出テキストが全体の5%以下であること）
grep -oP '^\[.*?\]: (.*)' "$OUTPUT_SRT" | sort | uniq -c | sort -rn | head -5
```

## オプション一覧

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `video_path` | 必須 | 入力動画ファイルパス（MP4） |
| `-o / --output` | 必須 | 出力SRTファイルパス |
| `--model` | gemini-3.1-flash-lite-preview | Geminiモデル |
| `--no-speaker-diarize` | OFF | 話者分離をスキップ（GPU不要） |
| `--dry-run` | OFF | コスト確認のみ（実行しない） |
| `--gemini-srt` | なし | 既存Gemini SRTを再利用 |
| `--profile-dir` | 自動検出 | 声紋プロファイルディレクトリ |
| `--threshold` | 0.25 | Speaker ID類似度閾値 |

## ハルシネーション防止ルール

gemini_transcribe.py内のプロンプトに以下のルールが含まれている（cmd_609で追加済み）:

- 同一テキストを3回以上連続で出力しない
- 動画の実際の尺を超えるタイムスタンプを生成しない
- 動画全体を最初から最後まで網羅する
- 5分ごとに内容が進行していることを自己確認する

## Guidelines

- **大きな動画（45分+）はFlash Liteで十分**: $0.05/本で高品質な字幕が得られる
- **話者分離ありはGPU推奨**: ECAPA-TDNNを使うのでRTX 4060 Ti推奨
- **既存SRTがある場合は再利用**: `--gemini-srt`でAPIコスト削減
- **ハルシネーション検出**: 最頻出テキストが全体の5%超の場合は再実行
- **タイムアウト**: Gemini API呼び出しは600秒（10分）を想定
