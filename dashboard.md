## 🎯 進行中

### cmd_1655 — v5全12章 v4スタイル統一 [in_progress] (2026-05-06)
- **目的**: Udemy中級v5が v4と見栄えバラバラ → v4同等フォーマットに統一
- Phase A: ash1 (v4正典抽出 → shared_context/marp_v4_style_template.md + ch00/ch01適用)
- Phase B: ash2-7 (ch02-ch11 各章 v4スタイル適用・blocked_by Phase A)
- Phase C: gunshi QC (全12章確認・blocked_by Phase B全件)
- 完了後: ntfy で殿に殿レビューURL 再通知

### cmd_1649 — SSE 24h観察 [in_progress] (2026-05-06)
- **担当**: 軍師 (subtask_1649_sse_observation)
- **状態**: 24h観察継続中 (完了予定: 2026-05-07 06:28)

## 🚨 要対応 (殿の判断が必要な事項)

### 🚨 Dashboard API 自己文書化 cmd — 殿確認待ち
server.py 全30+エンドポイントの error/success response に expected/example/doc を同梱する改修。
家老が purpose/acceptance_criteria 案を起票予定 → 殿OK後発令。
(根拠: 2026-05-06 inbox body/from typo で5通読み損ね・殿激怒)

## ✅ 最近の完了 (2026-05-06)

### cmd_1647 完了 — v5中級12章執筆
- 全12章 (ch00〜ch11) 執筆・udemy-checker反映・軍師QC PASS
- 殿レビューURL: http://192.168.2.4:8773/ (index.html 参照)

### cmd_1653 完了 — v5設計書7件指摘差し戻し改訂
- 困りごと章順・ch03再設計・長文context・実例変更・橋渡し・handoff・doc化 7件対応

### cmd_1652 完了 — dashboard キャンセルボタン追加

### cmd_1648 完了 — SSE endpoint server.py実装

### cmd_1646 完了 — SSE設計QC

### cmd_1636 cancelled — ドズル社動画video-pipeline
- DL完了済・ドズル社本編STT対象外確定 (殿命2026-05-06)・残処理close

## 🔧 技術負債

- cmd_1641 infra矛盾 H5/M9: ntfy.sh二重置換・inbox_watcher drift等 — 別cmd対応予定
- cmd_1623 矛盾検出 H1 (main.py:remotion-overlay/project不一致) — 別cmd対応予定
