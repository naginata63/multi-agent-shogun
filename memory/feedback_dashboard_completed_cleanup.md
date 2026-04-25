---
name: dashboard完了cmd自動削除ルール
description: dashboard.md進行中テーブルの✅完了行は自動アーカイブされる・手動で残すな
type: feedback
---

dashboard.md の進行中テーブルに✅完了行を残してはならない。
`scripts/dashboard_lifecycle.sh` が自動削除する (Logic A/B)。

**Why:** 殿指摘(2026-04-25 10:05)「なんで完了したものにマークしてのこすの・仕組み化しろ」。
家老の「見える化」思想で完了済cmd をマーク付き残存させていた慢性問題を是正。

**How to apply:**
- cmd完了時に家老が進行中テーブルから削除する必要なし（lifecycle.sh が自動処理）
- ただし「殿判断要」などアクティブな 🚨 要対応 行は手動管理継続
- 1h おき cron で自動削除 (追加: `0 * * * *`)
- アーカイブ: `dashboard_archive/YYYY-MM.md` に移動済み
