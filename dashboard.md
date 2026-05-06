## 🎯 進行中

### cmd_1649 — SSE 24h観察 [in_progress] (2026-05-06)
- **担当**: 軍師 (subtask_1649_sse_observation)
- **状態**: 24h観察継続中 (完了予定: 2026-05-08 06:28)・実運用 100% 受信率・取りこぼし 0
- /handoff 副作用で SSE Monitor task 生存確認中 (軍師に確認依頼済)
- 最終判定書受領後 → cmd_1650 Phase 3 着手

### 🛑 全足軽停止整理 [in_progress] (2026-05-07 07:14 殿命)
- weekly limit 節約のため将軍以外停止 (軍師は cmd_1649 継続)
- ash1/4/6/7: clear済 ✅ / ash5: /clearキュー積み (自然停止待ち) / ash2: /clearキュー積み / ash3: 停止命令inbox送信済
- 家老も停止整理完了後 /handoff → /clear 予定

## ⏸ 保留中 (再開待ち)

### cmd_1650 — Phase 3 SSE Monitor 全10agent展開 [pending] ← 着手可能
- busy_timeout修復完了 (commit 2ce5d13 push済み) → server.py 安定化
- cmd_1649 軍師最終判定書 + steady-state 取りこぼしゼロ確認後に着手
- warm-up 30秒・既存 inbox_watcher.sh 並走1週間

### cmd_1656 — ドズル社 STT/index 状態管理スクリプト化 [pending] (2026-05-06)
- 殿指示で pause (2026-05-06)
- ash3 が gen_stt_index_status.py 完成済み (151エントリ・テストOK)
- ash1 (work_video_map 4-5月追記) + ash2 (実行検証) は blocked 待機中
- 再開サイン待ち

## 🚨 要対応 (殿の判断が必要な事項)

### 🚨 STT_N001: --gemini help文と実装の乖離 — 殿判断待ち
`vocal_stt_pipeline.py` L903 で `--gemini` の help が「[DEPRECATED — 無視されます]」だが、
実装は stt_merge.py に転送して実際に speaker 割当に使用 (HIGH)。
選択肢:
- (a) 真に無視するなら L920-925/L1010 の gemini 経路を削除
- (b) 機能維持するなら help 文を「(deprecated・互換のため動作)」に修正
詳細: queue/reports/gunshi_stt_contradiction_20260507.yaml → STT_N001

### 🚨 Udemy v5 中級 Phase 3 出品準備 — 殿判断待ち
cmd_1655 全 5 Phase 完了・軍師 QC 11/11 PASS (2026-05-06)。
次フェーズ候補:
- cmd_1659: Phase 3 出品準備 (Udemy アップロード・説明文・価格設定等)
- cmd_1660: 殿最終レビュー (http://192.168.2.4:8773/ で全12章確認)
殿の GO サインで家老が起票する。

### 🚨 Dashboard API 自己文書化 cmd — 殿確認待ち
server.py 全30+エンドポイントの error/success response に expected/example/doc を同梱する改修。
家老が purpose/acceptance_criteria 案を起票予定 → 殿OK後発令。
(根拠: 2026-05-06 inbox body/from typo で5通読み損ね・殿激怒)

## ✅ 最近の完了

### cmd_1661 完了 — /api/cmd_cancel subtask 自動伝播実装 (2026-05-07)
- cmd cancel 時に parent_cmd マッチ全 subtask を自動 cancelled + agent inbox 通知
- cancelled_reason / cancelled_at 自動付与 + API レスポンス拡張
- SQLite + YAML dual-path 整合維持 / feedback_cmd_cancel_propagation.md 作成
- commit 541328b (ash5)

### cmd_1666 完了 — server.py dead remnant 清掃 (2026-05-07)
- 軍師QC CONDITIONAL_PASS で発覚した逆作用コード (L2829: PRAGMA busy_timeout=5000) 削除
- L2826 dead import + L2827 dead variable + L2954-2955 + L3009-3010 合計7行全削除 (ash3)
- commit 31b6070 / py_compile OK / API 正常応答確認

### cmd_1664 完了 — server.py 応答遅延 調査・修復 (2026-05-07)
- 根本原因: PRAGMA busy_timeout 23箇所未設定 → writer直列化タイムアウト
- 修復: get_db() busy_timeout=10000 追加 + query_db() エラー可視化 (ash3, commit 2ce5d13)
- 将軍 commit 185827b: TRIGGER補修 + inbox_mark_read typo改善
- cmd_1666 dead remnant 清掃 (commit 31b6070) で完全解消 / Phase 3 (cmd_1650) 着手条件充足

### cmd_1663 完了 — 夜間矛盾検出 STTパイプライン (2026-05-07)
- 前回20件: 16件 RESOLVED・1件 PARTIAL・3件 ACTUALLY_RESOLVED
- 新規矛盾 11件: HIGH 1件 (STT_N001 --gemini help乖離) / MEDIUM 3件 / LOW 7件
- **STT_N001**: `--gemini` help「無視されます」→ 実際は stt_merge.py に転送して使用 (HIGH)
- **STT_N002**: Part.from_bytes dead code 残存 (MEDIUM) → 物理削除で60行負債解消
- 詳細: queue/reports/gunshi_stt_contradiction_20260507.yaml

### cmd_1659 完了 — work/直下書込 BLOCK hook 拡張
- ash2 実装: pretool_check.sh L96-98 置換・Bash全対応・8項目テスト PASS (commit 499145e)

### cmd_1660 cancelled — panels_horn_otita CDP生成 (将軍 ChatGPT 直接実行に切替)
- ash4 が p1〜p7 の7枚生成済み (projects/dozle_kirinuki/work/20260506_.../output/cmd_1660/)
- 殿比較材料として保管・cmd 自体は cancelled

### cmd_1658 完了 — ドズル社切り抜き素材DL
- projects/dozle_kirinuki/work/20260506_【マイクラ】最強ソード VS 最強の弓 エンドラ討伐対決！/ (119MB・36分16秒)
- 字幕: IP制限で取得不可 (切り抜き作業は動画のみで進行可)

### cmd_1655 完了 — v5全12章 v4スタイル統一 + 品質補修
- 全5 Phase (執筆→スタイル→QC→speakerNote補修→最終QC) 完了
- 軍師 QC 11/11 全件 PASS
- 殿レビューURL: http://192.168.2.4:8773/

### cmd_1647 完了 — v5中級12章執筆
- 全12章 (ch00〜ch11) 執筆・udemy-checker反映・軍師QC PASS

### cmd_1636 cancelled — ドズル社動画video-pipeline
- DL完了済・ドズル社本編STT対象外確定 (殿命2026-05-06)・残処理close
- Phase A 試運転1本目 (IKu8Dad0YyY) は2並列PASS・メモリ正常・A-F=0で完了

## 🔧 技術負債

- cmd_1641 infra矛盾 H5/M9: ntfy.sh二重置換・inbox_watcher drift等 — 別cmd対応予定
- cmd_1623 矛盾検出 H1 (main.py:remotion-overlay/project不一致) — 別cmd対応予定
