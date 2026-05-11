---
name: youtube-subtitle-ip-ban
description: YouTube字幕・動画並列DL時のIP BAN / Google アカウントスパムフラグ再発防止ルール
metadata:
  type: feedback
---

# YouTube 字幕・動画並列DL IP BAN 再発防止ルール (cmd_1683)

**Why:** cmd_1681 で 5/5 に cookie 認証 (`--cookies-from-browser chrome`) で並列DL実施 → Google に bot 判定され IP BAN + アカウントスパムフラグ付与。5/5→5/7 の間 SHORTS% が 49→10% に崖落ち (長期影響)。cmd_1636 でも大量並列DLで bot 判定の実例あり。

**How to apply:** 全エージェントは YouTube (字幕/動画/チャット) を DL する際、以下ルールを厳守せよ。

## ルール

### 1. Cookie認証時 (一番危険)

- **直列1本のみ** — 複数動画の同時DLは厳禁
- **間隔10秒以上** — 連続DLの間に必ず10秒以上の待機
- **1時間あたり最大10本** — 超過すると bot 判定リスク急上昇
- **Google アカウントへの長期影響** — スパムフラグは数日〜1週間持続。SHORTS公開後の推薦アルゴリズムへの悪影響が実証済 (cmd_1681 AC6: SHORTS% 49→10%崖落ち)

### 2. 認証なし時 (リスク低いがゼロではない)

- 並列 1-2 本まで許容
- 間隔 5 秒以上
- 1時間あたり最大 20 本
- ※ IP BAN のみ発生する可能性あり (アカウント影響なし)

### 3. 共通ルール

- `--cookies-from-browser chrome` 使用時は必ず上記 cookie 認証時ルールを適用
- `youtube-transcript-api` も YouTube API を叩くため同様のレート制限対象
- batch 処理 (cmd_1636 等) では **順次処理 (sequential)** を徹底。並列は不可
- bot 判定エラー (`Sign in to confirm you're not a bot`) が出たら即停止 → 家老に報告

## cmd_1681 教訓

- 5/5 に cookie 認証で並列DL → 即 bot 判定
- 5/5→5/7: SHORTS% が 49%→10% に急減 (スパムフラグの長期影響)
- 影響期間: 約 2-7 日間 (Google のスパムフラグ自動解除まで)
- **コード変更禁止** — このルールは memory feedback として管理。スクリプト側の強制 sleep 実装は別 cmd で検討

## grep 点検結果 (2026-05-12)

| ファイル | 該当箇所 | 並列DL制約明記 | 対応要否 |
|---------|---------|--------------|---------|
| `scripts/downloader.py:245` | `--cookies-from-browser` help文 | cmd_1636 教訓言及あり | 不要 (help文で言及済) |
| `scripts/downloader.py:198-236` | `download_subtitles()` | なし (youtube-transcript-api使用) | 不要 (単発呼出・並列なし) |
| `scripts/auto_fetch.py:131-164` | `download_video()` | なし | 不要 (順次1本のみ) |
| `scripts/auto_fetch.py:165-188` | `download_subtitles()` | なし | 不要 (youtube-transcript-api使用) |
| `scripts/chat_analyzer.py:34-51` | `download_live_chat()` | なし | 不要 (単発呼出) |
| `scripts/comment_analyzer.py:143-164` | コメント取得 | なし | 不要 (単発呼出) |
| `scripts/highlight_compilation.py:78` | yt-dlp cookies | cookies使用 | 不要 (単発呼出) |
| `queue/tasks/ashigaru4.yaml:9` | bot検出blocked | blocked理由記載済 | 不要 |
| `queue/tasks/ashigaru1.yaml:158` | yt-dlp cookies使用 | cookies使用記載あり | 不要 |
| `CLAUDE.md` | DL制約セクションなし | — | 家老判断 (既存feedback linkで対応) |

**結論**: 既存スクリプトはすべて順次1本呼出のため、スクリプト側の修正は不要。ルール違反リスクは batch cmd 実行時の task YAML steps に依存。本 feedback が全エージェントの参照先となる。
