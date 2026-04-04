---
name: youtube-stats
description: |
  YouTubeチャンネルの統計情報を取得・分析し、日次スナップショットを生成する。
  Data API（チャンネル/動画別リアルタイム）+Analytics API（日別/トラフィック）→前日比計算→Claude CLI分析→snapshot.md→ntfy通知まで一貫して担当。
  「YouTube統計」「youtube-stats」「チャンネル分析」「日次レポート」「/youtube-stats」で起動。
  Do NOT use for: 動画アップロード（それは/highlightや/manga-shortを使え）。
argument-hint: "[--setup-cron]"
allowed-tools: Bash, Read
---

# /youtube-stats — YouTube統計取得スキル

## North Star

YouTube Data API + Analytics APIでチャンネルの最新統計を取得し、前日比・Claude LLM分析つきのスナップショットを生成すること。

## スクリプトパス（プロジェクトルート相対）

| スクリプト | パス |
|-----------|------|
| メインスクリプト | `scripts/youtube_analytics_snapshot.py` |
| ntfy通知 | `scripts/ntfy.sh` |

出力先: `projects/dozle_kirinuki/analytics/`

## 認証フロー

### 初回セットアップ（OAuth2）

スクリプトは `projects/dozle_kirinuki/token.json` を参照する。
スコープ:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`
- `https://www.googleapis.com/auth/yt-analytics.readonly`

token.jsonが存在しない、またはAnalytics APIスコープが不足している場合は再認証が必要:
```bash
cd /home/murakami/multi-agent-shogun
source venv/bin/activate
python3 scripts/youtube_analytics_snapshot.py
# → ブラウザ認証URLが表示される。ブラウザで開いて認証する
```

必要ファイル:
- `projects/dozle_kirinuki/client_secret.json` — Google Cloud OAuth2クライアント設定
- `projects/dozle_kirinuki/token.json` — 認証済みトークン（初回認証後に自動生成）

## 実行手順

### 手動実行

```bash
cd /home/murakami/multi-agent-shogun
source venv/bin/activate
python3 scripts/youtube_analytics_snapshot.py
```

### crontab セットアップ（毎日5:57自動実行）

```bash
cd /home/murakami/multi-agent-shogun
source venv/bin/activate
python3 scripts/youtube_analytics_snapshot.py --setup-cron
```

または手動でcrontabに追加:
```
57 5 * * * cd /home/murakami/multi-agent-shogun && venv/bin/python3 scripts/youtube_analytics_snapshot.py >> projects/dozle_kirinuki/analytics/cron.log 2>&1
```

現在のcrontab確認:
```bash
crontab -l | grep youtube_analytics
```

## 出力ファイル

実行するたびに以下を生成/更新（`projects/dozle_kirinuki/analytics/`配下）:

| ファイル | 内容 |
|---------|------|
| `{YYYY-MM-DD}_snapshot.md` | 人間向けMarkdownレポート（Claude LLM分析含む） |
| `{YYYY-MM-DD}_raw.json` | 生データJSON（前日比計算用に次回参照） |
| `cron.log` | crontab実行ログ |

### raw.json 構造

```json
{
  "date": "2026-03-17",
  "channel": {
    "name": "毎日ドズル社切り抜き",
    "subscribers": 8,
    "total_views": 486,
    "video_count": 29
  },
  "videos": [
    {
      "id": "video_id",
      "title": "動画タイトル",
      "duration_sec": 34,
      "views": 2747,
      "likes": 18,
      "dislikes": 2,
      "comments": 1
    }
  ]
}
```

### snapshot.md 構造

- チャンネル概要（登録者数・総再生回数・動画数）
- 日別統計（Analytics API: 直近14日分）
- トラフィックソース別内訳
- 動画別リアルタイム統計（前日比付き）
- Claude CLI Opus 4.6 AI分析（好調点・課題・戦略示唆）

## ntfy通知

以下の条件を満たすとntfy.sh経由でプッシュ通知が届く:
- 再生数 +500 以上
- 登録者 +1 以上
- いいね +10 以上

ntfyスクリプト: `scripts/ntfy.sh`

## Analytics API データ遅延

Analytics API には**1-2日の遅延**がある。
- スクリプトは `TODAY - 2日` までのデータを取得（`ANALYTICS_END`）
- `TODAY - 16日` から `TODAY - 2日` の14日分（`ANALYTICS_START`）
- リアルタイムデータ（再生数・いいね数）はData APIで取得（遅延なし）

## 前日比の読み方

snapshot.md の「前日比」列:
- `+15` = 昨日比+15再生
- `—` = 前日データなし（初回実行時、または新規アップロード動画）
- `0` = 変動なし

前日比は `{前日}_raw.json` との差分で計算。raw.jsonが存在しない日は `—` になる。

## 報告フォーマット

```
## youtube-stats 完了報告
- 実行日: {YYYY-MM-DD}
- snapshot: projects/dozle_kirinuki/analytics/{YYYY-MM-DD}_snapshot.md
- チャンネル登録者: {N}人
- 総再生: {N}回
- 動画数: {N}本
- ntfy通知: 送信 / 送信なし（条件未満）
```
