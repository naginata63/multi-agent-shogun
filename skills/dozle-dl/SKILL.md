---
name: dozle-dl
description: |
  ドズル切り抜きプロジェクトで YouTube URL から投稿日付付き作業フォルダを作成し動画+字幕を一括DLする。
  yt-dlp でメタ取得→`projects/dozle_kirinuki/work/{YYYYMMDD投稿日付}_{動画タイトル}/input/` 作成→`download.sh` 実行→結果報告まで自動化。
  「動画DL」「URL貼ったらフォルダ作ってDL」「投稿日付フォルダ作って」「dozle dl」「YouTube DL（日付付き）」「/dozle-dl」で起動。
  Do NOT use for: video-pipeline 全体実行（それは /video-pipeline を使え）。
  Do NOT use for: 漫画ショート制作（それは /manga-short）。HL動画制作（それは /highlight）。
  Do NOT use for: dozle 以外のプロジェクト用 DL（汎用ならば scripts/download.sh 直叩きで充分）。
argument-hint: "<youtube_url>"
allowed-tools: Bash, Read
---

# dozle-dl — ドズル切り抜き 投稿日付フォルダ自動DL

## North Star

**YouTube URL を貼ったら 1 分以内に「投稿日付付き作業フォルダ + 動画 + 字幕」を揃える。**
ドズル切り抜きの素材取得は毎回同じ手順（メタ取得→フォルダ命名→DL）を踏んでいた。これを 1 アクションに圧縮する。

## いつ使うか

- 殿が新しい切り抜き対象動画 URL を貼った時
- ドズル社チャンネルのロング動画から素材取得を開始する時
- 既存 work/ フォルダ命名規則 (`YYYYMMDD_{タイトル}/input/`) に整合させて DL したい時

## いつ使わないか

| 状況 | 代わりに |
|------|---------|
| 字幕生成・話者分離・SRTマージまで一気にやりたい | `/video-pipeline` |
| 漫画ショート制作 | `/manga-short` |
| HL動画制作（長尺切り抜き編集） | `/highlight` |
| dozle 以外の汎用 youtube DL | `bash projects/dozle_kirinuki/scripts/download.sh <URL> <out>` 直叩き |
| 既に DL 済みで再 DL したいだけ | yt-dlp 直叩き |

## 入力

- 引数 1 個: YouTube URL（`youtu.be/xxx` / `youtube.com/watch?v=xxx` 形式どちらも可）

## 出力

- フォルダ: `projects/dozle_kirinuki/work/{YYYYMMDD投稿日付}_{動画タイトル}/input/`
- ファイル:
  - `<video_id>.mp4`（動画本体）
  - `<video_id>.ja.vtt`（日本語字幕／自動生成含む）
- 殿への報告: フォルダパス・MP4サイズ・VTT 字幕有無

## 実行手順

### Step 1: メタ取得（投稿日付・タイトル・尺）

```bash
yt-dlp --print "%(upload_date)s|%(title)s|%(duration)s" "<URL>"
```

出力例: `20260507|エンドラ討伐中におおはらMENだけチャーハン作ってるドッキリ【マイクラ】|3534`

- `upload_date` は YYYYMMDD（投稿日付）
- `title` はタイトル（記号・絵文字含む）
- `duration` は秒数

**Validation**:
- 出力が 3 フィールドに分割できない場合 → URL が動画ページでない可能性。STOP し殿に報告。
- `upload_date` が `NA` の場合 → ライブ配信中等。STOP し殿に確認。

### Step 2: フォルダ作成

```bash
WORK_DIR="/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/{upload_date}_{title}"
mkdir -p "${WORK_DIR}/input"
```

**Naming rule**:
- 区切り: `_`（アンダースコア 1 個）
- タイトルは sanitize しない（記号・絵文字は yt-dlp の出力そのまま）。WSL2 ext4 + Linux ファイルシステムは Unicode 全許容。
- 既存フォルダがあれば `mkdir -p` で冪等。WARN するだけで止めない（同じ動画を再DL する場合あり）。

### Step 3: download.sh 実行

```bash
bash /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/scripts/download.sh "<URL>" "${WORK_DIR}/input"
```

`download.sh` 仕様（参考）:
- yt-dlp（projects/dozle_kirinuki/venv 配下）で実行
- `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]` フォーマット
- `--write-auto-sub --sub-lang ja` で日本語字幕（自動含む）取得
- 出力: `<id>.mp4` と `<id>.ja.vtt`

**Validation**:
- 終了コード 0 を確認
- `${WORK_DIR}/input/` 配下に `*.mp4` と `*.ja.vtt` が両方存在することを `ls` で確認
- mp4 が 1MB 以下なら異常（fragmented DL 失敗等）→ STOP し殿に報告

### Step 4: 報告

殿への報告フォーマット:

```
殿、DL完了でござる。

**フォルダ**: `work/{YYYYMMDD}_{title}/input/`
- `<id>.mp4` (XX.X GB・MM:SS)
- `<id>.ja.vtt` (字幕XXKB)

投稿日付YYYYMMDDでフォルダ作成・download.sh 実行済。
```

- 動画サイズは `du -h` 等で取得し人間可読単位で表示
- 動画尺は Step 1 で取得した duration を `MM:SS` に変換
- 字幕サイズは `du -h` で

## エラーハンドリング

| 症状 | 対処 |
|------|------|
| `yt-dlp: command not found` | dozle venv の yt-dlp を直接呼べ: `projects/dozle_kirinuki/venv/bin/yt-dlp`。Path の問題なら殿に報告 |
| `Sign in to confirm your age` 等 BAN 系 | 並列叩き厳禁ルール思い出せ（memory: feedback_youtube_subtitle_ip_ban）。1 本ずつ・間隔 5 秒以上 |
| JS challenge エラー | `/yt-dlp-js-runtimes-fix` スキル参照 |
| 字幕欠落（ja.vtt が出ない） | 動画自体に字幕がない可能性。WARN だけ表示し続行可（mp4 だけでも完了扱い） |
| ライブ配信中・プレミア公開待ち | upload_date が NA。STOP し殿に確認 |
| ディスク空き不足 | DL 開始前に動画サイズ推定（duration × 1.5 MB/s 程度）し warning 表示 |

## 想定されるトリガー文言

✅ Should trigger:
- 「`https://youtu.be/xxx` 動画DLしてくれ」
- 「URL 貼ったから投稿日付フォルダ作ってDL」
- 「dozle dl してくれ」
- 「`/dozle-dl https://...`」
- 「いつもどおりフォルダを日付で作ってダウンロードスクリプト使い DL」

❌ Should NOT trigger:
- 「字幕生成して」（`/gemini-video-transcribe` or `/video-pipeline`）
- 「ハイライト作って」（`/highlight`）
- 「漫画ショート作って」（`/manga-short`）
- 「動画を編集して」（編集タスクは別）

## 注意点

- **ドズル社プロジェクト固有スキル**である。他チャンネル切り抜きを始める場合は分岐先 work/ パスが違うので汎用化必要
- **download.sh の format 指定変更時**はこのスキルの仕様欄も更新せよ（download.sh が source of truth）
- **タイトルのファイルシステム互換性**: 現在の Linux ext4 環境では Unicode 全許容。FAT32/NTFS への移植時は sanitize 必要
- **memory ルール厳守**: YouTube 字幕取得は IP BAN リスクあり。並列 4 以上禁止（memory/feedback/feedback_youtube_subtitle_ip_ban.md 参照）

## 関連スキル

| スキル | 関係 |
|--------|------|
| `/video-pipeline` | DL 後の Demucs→STT→話者ID→SRT マージ。本スキルの後段 |
| `/yt-dlp-js-runtimes-fix` | yt-dlp が JS challenge で失敗した時 |
| `/highlight` | DL 済み動画から HL 動画を制作 |
| `/manga-short` | DL 済み動画から漫画ショートを制作 |
