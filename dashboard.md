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
### 🚨 cmd_1670 inbox_write WAL修復済 — server.py要再起動 (2026-05-09)
WAL有効化 + subprocess timeout延長 + スキーマ初期化コード追加 実装済 (commit c56fe38)。
**変更は server.py プロセス再起動後に有効**。
- 次回定期再起動 (dashboard_lifecycle.sh・1時間毎) で自動反映予定
- 緊急の場合: 将軍が手動再起動

⚠️ **新知見**: 今朝 (04:30頃) server.py が約2時間ハングしていた実証あり。
  バックグラウンドcurlが `real 124m28s` 後に HTTP 400 を受信 → ハング期間中に全エージェントのAPI呼び出しが止まっていた可能性。
  再発抑止のため、server.py再起動後に WAL+スキーマ初期化が有効になることが重要。

### 🚨 cmd_1669 watcher代替機構: 殿判断待ち (2026-05-09)
軍師設計書完了。推奨案 **D** (SSE Monitor + 軽量中央 1 daemon)。
**殿への質問 Q1-Q6**:
- Q1: CONTEXT-RESET ハード(/clear) vs ソフト(Claude内処理) 既定 → 推奨: 既定ソフト・フラグで上書き可
- Q2: dispatcher SPOF 許容度 → 推奨: systemd Restart=always のみで開始
- Q3: nudge 完全廃止 OK か → 推奨: 廃止 (SSE 100%実証済)
- Q4: watcher 段階廃止 P3経由 vs 即時廃止 → 推奨: P3経由必須 (1週間 safety net)
- Q5: SSE multiplex 改修 → 推奨: MVP は 9並列curl・後日改善
- Q6: cmd_1668 C1 CHECK制約修正を P0 に組み込む → 推奨: YES・今週中に別cmd
詳細: `queue/reports/2026-05-09_cmd_1669_watcher_replacement_design.md`

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

### 🚨 cmd_1671: remotion-project/ 設計変更 — 殿判断待ち (2026-05-09)
軍師矛盾検出で remotion-project/ (殿の personal workspace・.gitignore 除外) に 5件の判断事項:
- **V_H007** `bg_full.mp4` 不在 → DozFull コンポジション render 不能。(a) public/に配置 or (b) DozFull削除か
- **V_H007b** remotion-project/ 起動手順・コンポジション使用法が未文書化 → context/ に 1ページ追記するか否か (推奨:追記)
- **H003/V_M008/V_M009** Root.tsx ハードコード (FULL_SEC/OrarishTelop duration/text) → defaultProps+CLI引数化するか否か
殿の yes/no でよい。詳細: queue/reports/2026-05-09_cmd_1671_all_findings_remediation.md §(d)

### 🚨 Dashboard API 自己文書化 cmd — 殿確認待ち
server.py 全30+エンドポイントの error/success response に expected/example/doc を同梱する改修。
家老が purpose/acceptance_criteria 案を起票予定 → 殿OK後発令。
(根拠: 2026-05-06 inbox body/from typo で5通読み損ね・殿激怒)

## ⚔️ 戦果 (夜間矛盾検出)

### cmd_1668 完了 — 夜間矛盾検出: インフラ系 (2026-05-09 03:45)
- **報告書**: `queue/reports/2026-05-09_cmd_1668_infra_mujun_detection.md`
- **対象**: inbox_write/watcher, ntfy, cron, agent管理系, context_monitor, sessionstart/precompact hook, settings.yaml
- **read-only 遵守**: テスト作成・コード修正ゼロ ✅

| Severity | 件数 |
|----------|------|
| CRITICAL | 4 |
| HIGH | 5 |
| MEDIUM | 6 |
| LOW | 4 |
| **TOTAL** | **19** |

**主要 findings:**
- 🚨 **C1**: SQLite `inbox_messages.type` CHECK 制約と送信側 type 値の乖離 — error_report/nightly_audit/ntfy_received が SQLite で drop される dual-path 静かな破綻
- 🚨 **C2**: precompact_hook.sh の dashboard.md パス誤り (`queue/dashboard.md` → 存在しない) — compaction snapshot に dashboard 抜粋が載らない
- **C3**: inbox_watcher.sh の SQLite-only mark-read による YAML 残置 — stop_hook_inbox.sh 誤検知源
- **C4**: get_unread_info の SQLite/YAML 経路で normal_count 算出ロジック非対称
- follow-up cmd 13件推奨 (報告書末尾参照)

### cmd_1667 完了 — 夜間矛盾検出: 動画制作スクリプト群 (2026-05-08 02:32)
- **報告書**: `queue/reports/2026-05-08_cmd_1667_video_mujun_detection.md` (commit b22f17b)
- **監査対象**: 8ファイル 2596行 (main.py/make_expression_shorts.py/vertical_convert.py/remotion-project/src/ 全5ファイル)
- **read-only 遵守**: テスト作成・コード修正ゼロ ✅

| Severity | 前回 (04-28) | RESOLVED | PERSISTING | NEW | 合計 |
|---|---|---|---|---|---|
| CRITICAL | 2 | 0 | 2 | 0 | **2** |
| HIGH | 6 | 1 (partial) | 5 | 2 | **7** |
| MEDIUM | 6 | 0 | 6 | 4 | **10** |
| LOW | 8 | 0 | 8 | 3 | **11** |
| **TOTAL** | 22 | 1 partial | 21 | 9 | **30** |

**主要 findings:**
- 🚨 **C001 (3回目)**: WhisperX 残存 (main.py --diarize) — 殿激怒 (04-18) から20日経過も未撤去。是正怠慢
- 🚨 **C002 (2回目)**: vertical_convert.py argparse 4引数欠落 — コラボ動画 CLI 検証不能継続
- 🆕 **V_H007**: remotion-project/public/bg_full.mp4 不在 → DozFull コンポジション render 不能 (silent fail)
- 🆕 **V_H007b**: remotion-project/ 運用ドキュメント不在 — 起動手順・use case が context/ 未記載
- **H005 PARTIAL**: vertical_convert sys.path 追加 (cmd_1626) ✅ / main.py 側 importlib は健在

**対処優先度 (軍師推奨):**
1. C001 WhisperX撤去 → 2. C002 argparse追加 → 3. V_H007 bg_full.mp4配置/修正 → 4. V_H007b 運用ドキュメント1ページ追記 → 5. V_M010 main_speaker default統一 → 6. H001/H006

## ✅ 最近の完了

### cmd_1672 完了 — cmd_helper.py RAG D2 fix + 消費者実装 (2026-05-09 07:38)
- D2 fix: --source フィルタ外し → Python 後フィルタ方式に変更
- 消費者: Z案 (cmd_create_helper.sh 新設) 採用・新 cmd 起票時に類似 cmd 自動提示
- commit f2c10b4 / push 済 / 報告書: queue/reports/2026-05-09_cmd_1672_rag_pipeline_fix.md

### cmd_1671 完了 — harness全49件矛盾解消 (2026-05-09 07:35)
- (a)修復29件 commit済 + origin/main push済 (multi-agent-shogun + dozle_kirinuki)
- (b)別cmd 3件: H005 importlib/M2 ntfy archive/M4 monitor cron登録 → 後日起票
- (c)defer 12件: 意図的設計・低優先
- (d)殿許諾待ち 5件: remotion-project/ H003/V_H007/V_H007b/V_M008/V_M009 → 🚨要対応記載済
- 報告書: queue/reports/2026-05-09_cmd_1671_all_findings_remediation.md

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

## 🔄 進行中 (harness-cleanup)

### cmd_1669 委任済 — ashigaru watcher 代替機構設計 (2026-05-09 03:59)
- **担当**: 軍師 (gunshi_watcher_design_1669)
- **報告書予定**: `queue/reports/2026-05-09_cmd_1669_watcher_replacement_design.md`
- **目的**: inbox_watcher.sh (inotifywait×9体) を廃止し代替機構を3案設計・推奨案確定・殿提示
- **設計対象**: watcher 4機能 (clear_command/model_switch/CONTEXT-RESET/hang recovery) 全て
- **評価対象**: 過去暴走4種 (silent_fail誤検知/clear二重発火/nudge連投/Enter迷子) 再発リスク
- **lord_original**: 「え？作ればいいじゃん代替手段　軍師に設計させよ」
