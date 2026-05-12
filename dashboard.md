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

## 🚨 要対応
## 🚨 要対応

### 🚨 diarize.py 運用方針確定 (cmd_1679 STT_C002)
- **内容**: diarize.py (78行) は完全孤立dead script。pyannote直接経路 vs vocal_stt_pipeline AssemblyAI+ECAPA-TDNN の二重話者分離経路の方針未確定
- **選択肢**: (a)完全削除 (b)legacy/移動 (c)vocal_stt_pipeline統合
- **殿の判断が必要**: どの経路を正規とするか決定せよ
- **詳細**: queue/reports/gunshi_stt_contradiction_20260511.yaml STT_C002

### 🚨 cmd_1678 follow-up: YouTube/外部連携 解消作業 (2026-05-10)
- **YT_C001**: auto_fetch.py CHANNEL_ID yaml single source 化
- **YT_H001**: add_chapters.py dead code 削除
- **YT_H002/H003**: WhisperX残骸・gsutil vs gcloud 統一
- **follow-up cmd_1678-A〜E 起票待ち**

### 🚨 cmd_1679 follow-up: STT残課題 (cmd_1663 残7件+新3件)
- **STT_C001**: transcribe_with_speakers.py 完全削除
- **STT_C003/H001**: PROJECT_DIR fix + ECAPA-TDNN 共通化
- **follow-up cmd_1679-A〜E 起票待ち**

## 🚨 要対応

### 🚨【要殿判断】cmd_1676 実装方針確認 (軍師設計完了)
軍師推奨: **案A（誤key → HTTP 400 + typo_hint 即返）を即実装** + 案C(完全対称化)は別cmd(cmd_1676b)で段階移行
殿への質問:
- Q1: 案A単独で進めて良いか？(軍師推奨: YES)
- Q2: cmd_create/task_create 等 passthrough 系 endpoint にも ALLOWED_KEYS チェックを適用するか？
- Q3: 案C(完全対称化)を採用する場合、alias 期限は何ヶ月か？
- Q4: KNOWN_TYPOS dict に hint を入れることで LLM 誤学習の懸念はあるか？(軍師見解: 問題なし)
報告書: queue/reports/2026-05-09_cmd_1676_api_symmetric_keys.md

### 🚨【要殿判断】cmd_1656 Revert の意図確認
- 殿が cf0e7fd Revert で ashigaru4 の commit (work_video_map.md 4-5月分追記) を取り消した
- 再着手するか？ or cmd_1656 を cancelled 扱いで終結か？

### 🚨【要殿判断】instructions/generated.deprecated/ 完全削除判断
- cmd_1675-D で generated/ → generated.deprecated/ にリネーム済
- 完全削除するか？

## 🚨 要対応

### 🚨【要殿判断】cmd_1656 Revert の意図確認
- 殿が `cf0e7fd Revert` で ashigaru4 の commit (work_video_map.md 4-5月分追記・stt_index_status.md) を取り消した
- 「1656とめよ」命令後に Revert 実行と思われるが、**再着手する必要があるか？**
  - 不要 → cmd_1656 を cancelled 扱いで終結
  - 必要 → 別タイミングで再起票

### 🚨【要殿判断】instructions/generated/ 削除判断 (cmd_1673 C001)
- `instructions/generated.deprecated/` にリネーム済 (cmd_1675-D で実施)
- 完全削除するか？ → 家老は殿の判断を待つ

## 🚨 要対応

### 🚨【要殿判断】instructions/generated/ 削除 or deprecated リネーム (cmd_1673 C001)
- `instructions/generated/` 配下 (codex/copilot/kimi 系 7-8ファイル) がAPI化前 (2026-02頃) のスナップショットで停止
- codex/copilot/kimi CLI を今後使う予定があるか？
  - **不要** → 削除 or `instructions/generated.deprecated/` にリネーム推奨
  - **使う予定あり** → 最新 instructions から再生成が必要
- **家老は殿の判断を待ち、follow-up cmd_1673c を起票する**

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

## 🔄 進行中
## 🔄 進行中

### cmd_1650 — Phase3 SSE全agent展開 (in_progress)
- subtask_1650_a1: ashigaru1 assigned (2026-05-12 起動通知済)

### cmd_1680 — STTパイプライン残課題修正 (in_progress)
- subtask_1680_c2: ashigaru7 in_progress (vocab_helper import統合)
- subtask_1680_h001: ashigaru6 assigned (STT_H001 _compute_speaker_match新設)
- subtask_1680_reqc: gunshi blocked (c2+h001完了後 最終QC)
- submodule projects/dozle_kirinuki コミット済 (8822999)

## 🔄 進行中

### cmd_1650 SSE Monitor 全10agent展開 (2026-05-07~)
- **目的**: Phase 3 SSE Monitor 全agent展開・1週間安全網維持
- **担当**: 足軽1 (subtask_1650_a1_sse_phase3)
- **状態**: 長期観察中 (1週間後に最終判定書作成)

## 🔄 進行中

### cmd_1679 夜間矛盾検出: STTパイプライン (2026-05-11)
- **目的**: vocal_stt_pipeline.py/stt_merge.py/speaker_id系 矛盾検出
- **担当**: 軍師 (gunshi_1679_stt_audit)
- **期限**: 朝06:00 JST

### cmd_1650 SSE Monitor 全10agent展開 (2026-05-07~)
- **目的**: Phase 3 SSE Monitor 全agent展開・1週間安全網維持
- **担当**: 足軽1 (subtask_1650_a1_sse_phase3)
- **状態**: 長期観察中 (1週間後に最終判定書作成)

## 🔄 進行中

### cmd_1650 SSE Monitor 全10agent展開 (2026-05-07~)
- **目的**: Phase 3 SSE Monitor 全agent展開・1週間安全網維持
- **担当**: 足軽1 (subtask_1650_a1_sse_phase3)
- **状態**: 長期観察中 (1週間後に最終判定書作成)

## 🔄 進行中

### cmd_1678 夜間矛盾検出: YouTube/外部連携 (2026-05-10)
- **目的**: youtube_uploader.py/downloader.py/note系/API連携 矛盾検出
- **担当**: 軍師 (gunshi_1678_youtube_audit)
- **期限**: 朝06:00 JST

### cmd_1650 SSE Monitor 全10agent展開 (2026-05-07~)
- **目的**: Phase 3 SSE Monitor 全agent展開・1週間安全網維持
- **担当**: 足軽1 (subtask_1650_a1_sse_phase3)
- **状態**: 長期観察中 (1週間後に最終判定書作成)

## ✅ 最近の戦果
## ✅ 最近の戦果
- **cmd_1664** (2026-05-09) — server.py遅延解消・_init_db_pragmas+timeout統一・並列10curl 4.5ms平均・Phase 3土台固め完了 (軍師QC PASS)
- **cmd_1675** A/B/D (2026-05-09) — API前提ルール統一・instructions/*.md+agent_common.md+CLAUDE.md修正・generated.deprecated化 (C完了待ち)
- **cmd_1673** (2026-05-09) — API前提未更新ルール監査完了・19件finding
- **cmd_1661** (2026-05-09) — cmd_cancel subtask自動伝播 実装完了

## ✅ 最近の戦果
- **cmd_1673** (2026-05-09) — API前提未更新ルール監査完了・19件finding (C2/H7/M5/L5)・報告書 queue/reports/2026-05-09_cmd_1673_pre_api_rules_audit.md
- **cmd_1661** (2026-05-09) — cmd_cancel subtask自動伝播 実装完了・軍師QC PASS・git push済
- **cmd_1672** (2026-05-08) — RAG実装完了 (D2 fix + server.py統合)
- **cmd_1671** (2026-05-09) — cmd_1667/1668 49件findings全件解消完了

## ✅ 最近の戦果
- **cmd_1661** (2026-05-09) — cmd_cancel subtask自動伝播 実装完了・軍師QC PASS・git push済
- **cmd_1672** (2026-05-08) — RAG実装完了 (D2 fix + server.py統合)
- **cmd_1671** (2026-05-09) — cmd_1667/1668 49件findings全件解消完了

## ✅ 戦果
## ✅ 戦果

### cmd_1679 夜間矛盾検出: STTパイプライン ✅ (2026-05-11 02:37 JST)
- **結果**: 15件 (CRITICAL×3 / HIGH×4 / MEDIUM×5 / LOW×3)
- **新発見 CRITICAL**: transcribe_with_speakers.py 完全dead (154行・呼出元ゼロ) / diarize.py 完全dead (78行・殿判断要) / PROJECT_DIR 4-up depth 未修正継続
- **cmd_1663 残課題 7件依然未修正** (H002/H004/M001/M002/L001/L002/L003)
- **報告書**: queue/reports/gunshi_stt_contradiction_20260511.yaml
- **推奨**: cmd_1679-A(transcribe_with_speakers削除) / cmd_1679-B(diarize.py方針=殿判断) / cmd_1679-C(PROJECT_DIR) / D/E

### cmd_1678 夜間矛盾検出: YouTube/外部連携 ✅ (2026-05-10 02:30 JST)
- **結果**: 15件 (CRITICAL×1 / HIGH×4 / MEDIUM×5 / LOW×5)
- **最重要**: YT_C001 auto_fetch.py CHANNEL_ID yaml single source 違反
- **報告書**: queue/reports/gunshi_youtube_contradiction_20260510.yaml

## ✅ 戦果

### cmd_1678 夜間矛盾検出: YouTube/外部連携 ✅ (2026-05-10 02:30 JST)
- **結果**: 15件 (CRITICAL×1 / HIGH×4 / MEDIUM×5 / LOW×5)
- **最重要**: YT_C001 auto_fetch.py CHANNEL_ID ハードコード (yaml single source 違反)
- **主要HIGH**: add_chapters.py ハードコードチャプター(dead code) / merged_whisperx.srt 残骸 / gsutil vs gcloud storage 混在 / flock なし書込競合
- **報告書**: queue/reports/gunshi_youtube_contradiction_20260510.yaml
- **推奨follow-up**: cmd_1678-A(CRITICAL解消) / cmd_1678-B(H001) / cmd_1678-C(H002) / cmd_1678-D(OAuth共通化) / cmd_1678-E(M001)

## 🚨要対応
## 🚨要対応

### 🚨【殿判断】Shorts feed SHORTS% 崖落ち対策テスト (cmd_1681)

**背景**: 5/7以降 SHORTS feed流入 39,283→1,807 (-95.4%)。2つの有力仮説:

**仮説A**: 4/28 YPP「再利用コンテンツ」NG → 推薦エンジン遅延反映 (9日ラグ)
**仮説B**: 5/7から title/tags/description に AI関連キーワード初登場 → アルゴリズム影響の可能性

**提案**: 次回投稿で AI関連キーワード (`#ai漫画`・`AI画像生成`) 完全除外テスト

**詳細**: queue/reports/2026-05-12_cmd_1681_shorts_shadowban_analysis.md

---

### ✅【完了】cmd_1687: CRITICAL/HIGH インフラ修正 (2026-05-13)

- **C1 (CRITICAL)**: precompact_hook.sh dashboard.md パス regression → 足軽3号が修正・commit 826b6e8
- **H2 (HIGH)**: monitor.sh + context_watcher.sh が PC換装後4日間未稼働 → 足軽4号が watcher_supervisor に自動起動ロジック追加・commit 82109e0

両件解消・push済み。

## 🚨要対応

### 🚨【殿判断】Shorts feed SHORTS% 崖落ち対策テスト (cmd_1681)

**背景**: 5/7以降 SHORTS feed流入 39,283→1,807 (-95.4%)。ashigaru3 調査で2つの有力仮説が浮上:

**仮説A (最有力)**: 4/28 YPP「再利用コンテンツ」NG → 推薦エンジン遅延反映 (9日ラグ) 
**仮説B (新発見)**: 5/7から title/tags/description に AI関連キーワード初登場 (`AI漫画` `AI画像生成`) → YouTubeアルゴリズム影響の可能性

**殿への提案**: 次回投稿 (1-2本) で AI関連キーワードを完全除外してテスト
- title の `#ai漫画` 削除
- tags から AI漫画 除外
- description の「AI画像生成」記載を削除またはぼかす
→ SHORTS% が 20%以上に回復すれば仮説B確定・復帰策が判明

**詳細**: queue/reports/2026-05-12_cmd_1681_shorts_shadowban_analysis.md

---

### 🚨【検討】cmd_1650 (SSE Phase 3) 停滞中 (5日経過)

5/7起票から進捗なし。継続するか別アプローチに切替えるか殿判断仰ぐ。
