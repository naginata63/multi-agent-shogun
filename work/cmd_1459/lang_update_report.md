# cmd_1459 Phase A: YouTube言語設定一括更新レポート

## 実行概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-04-25T08:35〜08:40 |
| チャンネルID | UCiyY9PX64Nat6sd2vUhrTDQ |
| 対象動画数 | 100本 |
| 更新済み（既にja） | 50本 |
| 更新実施 | 50本 |
| 失敗 | 0本 |

## Before状態（内訳）

| パターン | 件数 |
|----------|------|
| defaultLanguage=ja + defaultAudioLanguage=ja | 49 |
| defaultLanguage=ja + defaultAudioLanguage=None | 13 |
| defaultLanguage=None + defaultAudioLanguage=None | 10 |
| その他（片方のみ等） | 27 |
| **合計** | **99** (1件はタイミング取得漏れだがAPI上ja確認済み) |

## After状態

- 全100本: defaultLanguage=ja + defaultAudioLanguage=ja 確認済み
- 補足: after.json取得時99件（QharlfIueqIがタイミング問題で欠落）→API直接確認でja化確認

## API Quota消費

| 項目 | 単価 | 件数 | 消費units |
|------|------|------|-----------|
| videos.list (全取得) | 1 | 4回 | 4 |
| videos.update | 50 | 50本 | 2,500 |
| channels.list | 1 | 1回 | 1 |
| playlistItems.list | 1 | 2回 | 2 |
| **合計** | | | **~2,507** |

daily quota制限: 10,000 units → 25%消費

## テスト確認

- [x] 1本テスト更新（7-KgCLSwtXo）→ title/tags/categoryId保持確認
- [x] 全50本更新 → 失敗0件
- [x] API直接確認 → QharlfIueqI含め全100本 defaultLanguage=ja + defaultAudioLanguage=ja

## 背景（オートダビング問題）

殿が08:31にYouTubeオートダビング機能を手動OFF済み。
本Phase A（ja化）は機能OFF+言語ja=二重防御として実施。

## 成果物

| ファイル | 内容 |
|---------|------|
| work/cmd_1459/lang_before.json | 更新前スナップショット |
| work/cmd_1459/lang_after.json | 更新後スナップショット |
| work/cmd_1459/lang_update_report.json | JSON形式レポート |
| work/cmd_1459/lang_update_log.txt | 更新ログ |
| scripts/youtube_lang_batch_update.py | バッチ更新スクリプト（再利用可能） |
