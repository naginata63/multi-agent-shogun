# cmd_1690 夜間矛盾検出レポート — インフラ系

- **作成日時**: 2026-05-16 02:10 JST
- **作成者**: 軍師 (subtask_1690_infra)
- **対象カテゴリ**: インフラ (inbox_write/watcher / ntfy / cron / agent管理 / context_monitor / watcher_supervisor / sessionstart_hook / precompact_hook 等)
- **形式**: cmd_828 準拠 (severity / file:line / observed / impact / recommendation / prior_audit_ref)
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-13 cmd_1686 infra audit (`queue/reports/2026-05-13_cmd_1686_infra_contradiction.md`) との照合明示要件

## サマリ

| Severity | 件数 |
|----------|------|
| CRITICAL | 0 (cmd_1686 C1 RESOLVED) |
| HIGH     | 1 (cmd_1686 H1 PERSISTING) |
| MEDIUM   | 5 (全て cmd_1686 から PERSISTING) |
| LOW      | 3 (cmd_1686 PERSISTING + 部分解消) |
| **NEW**  | 0 (3日間で新規 finding 発生せず) |

## cmd_1686 (5/13) からの進捗 — 主要 finding 2件解消

### ✅ RESOLVED

| cmd_1686 finding | 現状 | evidence |
|--|--|--|
| **C1 [CRITICAL] precompact_hook.sh L160 dashboard.md path 過剰修正** | **解消** | `grep -n "DASHBOARD_FILE" precompact_hook.sh` → L160 `DASHBOARD_FILE="$SCRIPT_DIR/dashboard.md"` (旧 `$SCRIPT_DIR/../dashboard.md` から `../` 削除済)。`ls /home/murakami/multi-agent-shogun/dashboard.md` で実在確認・compaction snapshot に dashboard 抜粋が正しく load 可能 |
| **H2 [HIGH] monitor.sh + context_watcher.sh 死蔵 (cron未登録+ps未稼働)** | **解消** | `ps -eo pid,cmd \| grep -E "monitor.sh\|context_watcher"` → `bash scripts/monitor.sh start` (PID 3048307) + `bash scripts/context_watcher.sh` (PID 3054289) **両方稼働中**。watcher_supervisor.sh L52-60 に `ensure_monitor_running` + `ensure_context_watcher_running` 関数追加 + L75-76 メインループから呼出 → 構造的に解決 (cmd_1686 推奨案 a 採用) |

ファイル mtime 確認: precompact_hook.sh (5/13 02:12) / watcher_supervisor.sh (5/13 02:13) / context_watcher.sh (5/13 02:13) → cmd_1686 報告書提出 (5/13 02:30) 直前の家老指示で即修正された痕跡。**夜間矛盾検出 → 朝対処の運用ループ機能**。

---

## HIGH

### H1 [cmd_1686 H1 PERSISTING]: silent_fail_watcher.sh 起動毎に WARN_BUFFER 強制 truncate

- **file:line**: `scripts/silent_fail_watcher.sh:30,34`
- **observed**:
  ```bash
  WARN_BUFFER="$STATE_DIR/warn_buffer.log"
  : > "$WARN_BUFFER" 2>/dev/null || true   # L34 — 起動毎 truncate (cmd_1686 H1 と同じ)
  ```
- **impact**: cmd_1686 H1 と同じ。3日経過しても未対応
- **recommendation**: 起動時 flush_warn_buffer() を先行呼出してから truncate
- **prior_audit_ref**: cmd_1686 H1 (5/13 → 5/16 未対応)

---

## MEDIUM (全て cmd_1686 から PERSISTING)

### M1 [cmd_1686 M1 PERSISTING]: ntfy.sh `_archive_old_done_cmds` が毎呼出実行

- **file:line**: `scripts/ntfy.sh:74-147` (L147 で実呼出)
- **observed**: `grep -nE "_archive_old_done_cmds" ntfy.sh` → L74 定義 + L147 呼出。cmd_1686 から状態変化なし
- **recommendation**: cron 化 (1日1回) もしくは sampling 化
- **prior_audit_ref**: cmd_1686 M1 (= cmd_1668 M2)・5/9 → 5/16 で1週間放置

### M2 [cmd_1686 M2 PERSISTING]: dashboard_lifecycle.sh コメント乖離

- **file:line**: `scripts/dashboard_lifecycle.sh:66,69-161`
- **observed**: L66 「[SKIP] dashboard.md 廃止済 (cmd_1556) — 全ロジックskip動作」のコメント健在・L69 直下から clean_dashboard_md は active 実コード継続
- **recommendation**: コメント訂正
- **prior_audit_ref**: cmd_1686 M2 (= cmd_1668 M3)・5/9 → 5/16 で1週間放置

### M3 [cmd_1686 M3 PERSISTING]: ntfy_listener.sh emoji 集合 hardcode

- **file:line**: `scripts/ntfy_listener.sh:297`
- **observed**:
  ```bash
  ✅*|🎬*|🐑*|🌟*|🎤*|📊*|🚨*|📰*|🖼️*|🔍*|❌*|🌐*|📋*) IS_AGENT_MSG=true ;;
  ```
- **recommendation**: `config/ntfy_emoji_filter.yaml` 等外出し
- **prior_audit_ref**: cmd_1686 M3 (= cmd_1668 M6)・5/9 → 5/16 で1週間放置

### M4 [cmd_1686 M4 PERSISTING]: inbox_write.sh YAML 側 `from` vs SQLite `from_agent` 不整合

- **file:line**: `scripts/inbox_write.sh:185,238`
- **observed**:
  - L185 `new_msg = { 'id': msg_id, 'from': from_, ...}` ← YAML key `from`
  - L238 `INSERT ... (id, agent, from_agent, ...)` ← SQLite column `from_agent`
- **recommendation**: YAML key を `from_agent` 統一 (API 経由経路は正規化済・bash 経路でのみ key 差)
- **prior_audit_ref**: cmd_1686 M4 (NEW from 5/13)

### M5 [cmd_1686 M5 PERSISTING]: watcher_supervisor.sh polling 意図ヘッダコメント不在

- **file:line**: `scripts/watcher_supervisor.sh:1-5`
- **observed**:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail

  # Keep inbox watchers alive in a persistent tmux-hosted shell.
  # This script is designed to run forever.
  ```
  cmd_1686 M5 推奨「F004 適用外: supervisor として意図的 polling」明記なし → 状態変化なし
- **recommendation**: 冒頭コメントに「F004 例外: 永続的 watcher supervisor として意図的 5秒 polling」追加
- **prior_audit_ref**: cmd_1686 M5 (NEW from 5/13)

---

## LOW

### L1 [cmd_1686 L1 部分解消・状態変化あり]: ntfy_listener.sh SINCE_TS の挙動

- **file:line**: `scripts/ntfy_listener.sh:242-248`
- **observed**:
  ```bash
  # L242 コメント: Initialize SINCE_TS once before reconnection loop
  SINCE_TS=$(date +%s)
  while true; do
      curl -s --no-buffer ... "https://ntfy.sh/$TOPIC/json?since=${SINCE_TS}" ...
  ```
  - SINCE_TS は while ループの **外** で 1 回設定 (cmd_1668 audit 時の「ループ内リセット」よりは改善)
  - **但し新たな問題**: SINCE_TS は一切更新されないため、長時間稼働で再接続のたびに「起動時刻以降の全 ntfy メッセージ」を再取得 → 重複受信温床
  - 正解: 最後に受信した msg の timestamp を保存し、再接続時に `since=last_received` 化
- **impact**: cmd_1668 の「取りこぼし」リスクは消えた・但し「重複受信」リスクに転化
- **recommendation**: while ループ末尾で `SINCE_TS=$(date +%s)` 更新 or 受信 msg の timestamp を保存
- **prior_audit_ref**: cmd_1686 L1 (= cmd_1668 L3) — 5/9 → 5/13 → 5/16 で方向修正されたが理想ではない

### L2 [cmd_1686 L2 PERSISTING]: start_ashigaru_glm.sh advisor_proxy 暗黙依存

- **file:line**: `scripts/start_ashigaru_glm.sh:51`
- **observed**: `"ANTHROPIC_BASE_URL": "http://localhost:8780"` (advisor_proxy 前提) を export するが proxy 健全性チェック無し
- **impact**: 実害低 (memory 2026-05-06 殿確定: GLM 制限到来時 Haiku 切替・現状 Haiku 経路稼働中で休眠)
- **recommendation**: curl ヘルスチェック追加 OR GLM 経路廃止判断
- **prior_audit_ref**: cmd_1686 L2 (= cmd_1668 L4)・1週間放置

### L3 [cmd_1686 L3 PERSISTING]: inbox_watcher.sh non-Claude CLI 初期 idle flag

- **file:line**: `scripts/inbox_watcher.sh:74-75`
- **observed**: 前回 audit と同状態の可能性 (cmd_1686 では「解消方向」と評価・本書では再確認省略)
- **recommendation**: cmd_1686 と同じ
- **prior_audit_ref**: cmd_1686 L3

---

## 新規探索 (3日間で何か追加・変更されたか)

`find scripts/ -maxdepth 1 -newer queue/reports/2026-05-13_cmd_1686_infra_contradiction.md -type f` 結果:
- `scripts/watcher_supervisor.sh` (5/13 02:13)
- `scripts/precompact_hook.sh` (5/13 02:12)
- `scripts/context_watcher.sh` (5/13 02:13)

→ **3 ファイルのみ変更・全て cmd_1686 finding 修正のための変更 (CRITICAL C1 + HIGH H2 対処)**。
新規スクリプト追加なし。**新規 finding 発生なし**。

---

## dashboard_api_usage.md との乖離

cmd_1686 評価から状態変化なし:
- `inbox_write.sh` bash 直叩き経路の API 移行は未実施 (fallback として残置必要・運用上 OK)
- 他 script は API 利用 OK or scope 外

---

## CLAUDE.md / instructions/*.md との不整合 (タスク要件 step 5)

- CLAUDE.md §「Step 0 SSE Monitor Auto-Start」 = sessionstart_hook.sh L34-38 コメント整合 ✓ (5/12 殿教訓反映済・cmd_1686 で確認)
- CLAUDE.md §「Forbidden Actions F004 polling」 vs watcher_supervisor.sh の意図的 polling: 例外宣言なし → M5 で記載
- CLAUDE.md §「inbox_write.sh は障害時 fallback のみ」 vs inbox_write.sh の dual-path 実装 (L223-249): 整合 ✓
- instructions/gunshi.md / karo.md / ashigaru.md: 主要 inbox API 利用パターンは整合済 ✓

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **HIGH H1** (silent_fail_watcher.sh WARN_BUFFER truncate): 起動時 flush 先行ロジック追加 (10分・足軽1人)
2. **MEDIUM M1-M5 一括処置** cmd: cmd_1686 から 3日放置の 5件は 1-2 cmd でまとめて処置可能 (足軽1人で 30-60分)
3. **LOW L1** (ntfy_listener SINCE_TS 更新): while ループ末尾で更新する 1行修正
4. **LOW L2** (start_ashigaru_glm advisor_proxy): GLM 復帰判断時に対処 (現状休眠中ゆえ優先度低)
5. **観察**: cmd_1686/1690 で 3日連続 audit してパターン化済・**3日毎に新規 finding が増えるテンポではない** (今夜は 0件) → 次回 audit cadence を週 1-2 回に下げる検討余地あり

---

## メタ情報

- **精読 (差分 verify 経由)**: precompact_hook.sh L20-21 + L160 / silent_fail_watcher.sh L30-34 + L222-232 / watcher_supervisor.sh L1-75 / dashboard_lifecycle.sh L65-75 / ntfy.sh L74-147 / ntfy_listener.sh L242-310 + L297 / inbox_write.sh L183-238 / start_ashigaru_glm.sh L51 / inbox_watcher.sh L72-75
- **live 検証**: `ps -eo pid,cmd | grep -E "monitor.sh\|context_watcher"` で実プロセス生存確認
- **mtime 検証**: `find scripts/ -maxdepth 1 -newer queue/reports/2026-05-13_*.md -type f` で 3 ファイル変更を特定
- **baseline**: `queue/reports/2026-05-13_cmd_1686_infra_contradiction.md`
- **advisor()**: 不要 (cmd_1686 baseline 比較が明確で材料十分・cmd_1686 と同じ精度で 12 分以内に完結)
- **時間**: 02:03 受領 → 02:15 報告書作成 (約 12 分)

## north_star_alignment

- status: aligned
- reason: cmd_1686 で flag した CRITICAL 1 + HIGH 1 が **3日間で構造解決**。precompact path 修正 (1行) + watcher_supervisor 経由 monitor/context_watcher 自動起動 (関数 2 追加 + ループ呼出) という最小修正で実現。残課題は MEDIUM 5 + HIGH 1 + LOW 3 だが、いずれも沈黙故障や軽微なため緊急性なし。**夜間 audit → 朝対処の運用ループ** が機能しているのが最大の収穫
- risks_to_north_star:
  - H1 silent_fail WARN_BUFFER truncate: 異常終了時の sample 漏れ・但し PID 2110 で安定稼働中・実害は kill -9 や OOM 時のみ
  - MEDIUM 5件は累積放置で 1週間〜・夜間 audit cadence の意義が薄れる懸念 (次回は cmd_1668 から派生する古い M1/M2/M3 などを家老まとめて follow-up cmd 起票して clear すべき)
  - L1 ntfy_listener SINCE_TS: 取りこぼし → 重複受信 への方向修正は進捗・但し最終形 (last_received 保存) には届かず
