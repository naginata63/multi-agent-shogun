# cmd_1683: YouTube字幕並列DL IP BAN 再発防止ルール更新 — 報告書

## 成果物

- `memory/feedback_youtube_subtitle_ip_ban.md` — 新規作成 (cookie認証時厳格化ルール + grep点検結果)

## 修正内容

### 追加ルール

| 状態 | 並列数 | 間隔 | 1h上限 | アカウント影響 |
|------|--------|------|--------|---------------|
| Cookie認証時 | **直列1本のみ** | **10秒以上** | **10本** | あり (スパムフラグ長期化) |
| 認証なし時 | 1-2本 | 5秒以上 | 20本 | IP BANのみ |

### cmd_1681 教訓追記

- 5/5 cookie認証並列DL → bot判定 → 5/5-5/7 SHORTS% 49→10% 崖落ち
- 影響期間: 2-7日
- コード変更禁止 (memory feedback管理)

## grep点検結果

| ファイル | 箇所 | 並列制約 | 対応 |
|---------|------|---------|------|
| scripts/downloader.py:245 | --cookies-from-browser help | cmd_1636教訓言及済 | 不要 |
| scripts/downloader.py:198 | download_subtitles() | 単発呼出 | 不要 |
| scripts/auto_fetch.py:131 | download_video() | 順次1本 | 不要 |
| scripts/auto_fetch.py:165 | download_subtitles() | 単発呼出 | 不要 |
| scripts/chat_analyzer.py:34 | download_live_chat() | 単発呼出 | 不要 |
| scripts/comment_analyzer.py:143 | コメント取得 | 単発呼出 | 不要 |
| scripts/highlight_compilation.py:78 | yt-dlp cookies | 単発呼出 | 不要 |
| queue/tasks/ashigaru4.yaml:9 | bot検出blocked | blocked理由記載済 | 不要 |
| queue/tasks/ashigaru1.yaml:158 | yt-dlp cookies使用 | cookies記載あり | 不要 |
| CLAUDE.md | DL制約セクションなし | — | 家老判断 |

**結論**: 全スクリプト順次1本呼出のためスクリプト修正不要。本feedbackが参照先。

## 変更なし (コード)

コード変更なし。ルール文書 (memory/feedback) のみ作成。

## Acceptance Criteria チェック

- [x] memory/feedback/feedback_youtube_subtitle_ip_ban.md にcookie認証時の厳格化ルール追記済
- [x] grep点検結果一覧 (該当箇所・対応要否) 報告書に含む
- [x] 報告書 queue/reports/2026-05-12_cmd_1683_youtube_dl_rules_update.md 格納
- [x] コード変更なし (ルール文書のみ)
- [ ] git commit 済 (これから実施)
