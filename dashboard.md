# 📊 戦況報告
最終更新: 2026-04-24 08:22

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

---

## 🚨 要対応（殿の御判断必要）

### 🔴 cmd_1434 polish LOW4件 — 次cmd化判断（家老が1つにまとめて発令可）
- LOW_3: prediction method 表記なし（subs_3mo等が何の予測か UIに caption なし）
- LOW_4: by_duration UI ラベル英字のまま（under_30s → 30秒未満等の日本語変換要）
- LOW_5: Chart destroy() が retention のみ（他グラフ: 現状 risk 0 / 将来対応推奨）

### 🚨 スキル化候補（殿承認要）
- **yt-dlp-js-runtimes-fix**: `--js-runtimes node` でYouTube n-challenge bot検知突破。横断的汎用hotfix（軍師価値HIGH判定）→ スキル化承認願い

### ⚠️ 技術的残課題（優先度低）
- **dozle_kirinukiサブモジュール push不可**: gcloud SDK 194MB超過 → git-lfs移行 or 履歴書換が必要
- **disk使用率88%（残116GB）**: Day6 MIX前に要確認（4視点×約50GB消費見込み）

---

## 🔄 進行中

| cmd | 担当 | 状態 |
|-----|------|------|
| cmd_1435 --max-tokens削除 | 足軽1号 | subtask_1435a 実行中（work/cmd_1393フック問題あり）|
| cmd_1434 generate_dashboard.py修正 | 足軽2号 | subtask_1434b2 実行中 |
| cmd_1425 Day6 4視点集約 | 足軽5号 | subtask_1425d2 実行中 |

---

## 足軽・軍師 状態

| 足軽 | CLI | 状態 | 現タスク |
|------|-----|------|---------|
| 1号 | GLM | 🔄 in_progress | subtask_1435a（--max-tokens削除）|
| 2号 | GLM | 🔄 in_progress | subtask_1434b2（generate_dashboard.py Phase3追加）|
| 3号 | GLM | ✅ idle | — |
| 4号 | GLM | ✅ idle | subtask_1425c2 完了 |
| 5号 | GLM | 🔄 in_progress | subtask_1425d2（Day6 4視点集約）|
| 6号 | GLM | ✅ idle | — |
| 7号 | GLM | ✅ idle | — |
| 軍師 | Opus | ✅ idle | — |

---

## ✅ 本日の完了（2026-04-24）

| cmd | 内容 |
|-----|------|
| cmd_1425 シャルロットDL | ✅ subtask_1425c2 PASS（--js-runtimes node でbot検知突破・9パート分割完了）|
| cmd_1434 | ✅ Phase1+2+3+by_duration4区分完了。index.html restore済み・generate_dashboard.py修正中 |
| nightly_audit_20260424_video | ✅ 動画制作系矛盾検出（CRITICAL×0 HIGH×0・MEDIUM×1 outro stderr deadlock）|
| cmd_1428 | ✅ done化（殿判断: YouTube非公開アップ完結）|
| cmd_1411/1413/1414 | ✅ done化（DoZ5日目ヒーラー漫画ショート・ゼピュロス3版投稿済みで終了・殿判断）|

> 過去の完了記録 → `dashboard_archive_2026-04.md`

---

## APIキー状況
- **Vertex AI ADC**: ✅ 正常
- **GLM**: ✅ 足軽全員GLMで稼働中

## チャンネル実績（2026-04-24更新）
- 登録者**2,740人** / 総再生**348万回** / 動画**74本**
- 過去365日視聴時間: 横長**4,786h** / ショート**19,360h**
- YPP条件: 横長4,786h > 4,000h ✅ / 登録2,740 > 1,000 ✅ → **条件達成・YouTube判定通知待ち（1週間遅延中・あす明後日見込み）**
- ドズル社MCN加入・ライセンス契約: 未申請（申請文v1ドラフト work/dozle_application/）

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
