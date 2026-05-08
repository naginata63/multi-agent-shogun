# cmd_1668 夜間矛盾検出レポート — インフラ系

- **作成日時**: 2026-05-09 JST (軍師執筆・gunshi_mujun_infra_1668)
- **対象カテゴリ**: インフラ（inbox_write/watcher, ntfy, cron, agent管理, context_monitor, sessionstart/precompact hook, settings.yaml）
- **形式**: cmd_828 準拠（severity / file:line / observed / impact）
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **完了条件**: 矛盾一覧本書 + 家老 inbox `report_received` 通知

---

## サマリ

| Severity | 件数 |
|----------|------|
| CRITICAL | 4 |
| HIGH     | 5 |
| MEDIUM   | 6 |
| LOW      | 4 |

---

## CRITICAL

### C1. SQLite `inbox_messages.type` CHECK 制約と送信側 type 値の乖離（dual-path 静かな破綻）

- **観測**: `queue/cmds.db` の `inbox_messages.type` CHECK 制約は以下の15種に閉じている:
  ```
  CHECK (type IN (
      'task_assigned','clear_command','cmd_new','cmd_revised',
      'cmd_correction','cmd_spec_confirmed','task_cancelled',
      'report_received','report_completed','report_blocked','report_error',
      'qc_request','qc_result','qc_done','wake_up'
  ))
  ```
  一方、bash 経由で送られる以下 type は CHECK 外で、`inbox_write.sh:257` の `INSERT OR IGNORE` により**SQLite 側だけ静かに drop** される:
  - `error_report` — `scripts/stop_hook_inbox.sh:181`（completion 検知時の karo 通知）
  - `nightly_audit` — `scripts/nightly_audit.sh:43` のフォールバック（API 不達時に bash 経由で送る）
  - `ntfy_received` — `scripts/ntfy_listener.sh:304`（API 不達時のフォールバック）
  - 注: `model_switch` / `cli_restart` は `inbox_watcher.sh:287-313` で消費されるが、`scripts/`/`lib/` 配下では送信元（inbox_write 呼出側）を本タスク内で特定できなかった。スキル `shogun-model-switch` 等から発せられている可能性があるが、ファイル外での送信は本書スコープ外
- **Impact**:
  - YAML inbox には書かれるが SQLite には入らない → `inbox_watcher.sh:407-449` の SQLite fast-path が specials を見逃す
  - memory ルール「書込フォールバック (SQLite 直書き) は禁止 (dual-path 整合崩壊)」(CLAUDE.md「Dashboard API 利用」節) が静かに破られている
  - cmd_1494 の dual-path 整合性前提が成立しない
- **CHK trace**: `scripts/inbox_write.sh:257-263` (INSERT OR IGNORE), `queue/cmds.db` (CHECK constraint)

### C2. precompact_hook.sh の dashboard.md パスが project root 外を指している

- **観測**:
  - `scripts/precompact_hook.sh:138` — `DASHBOARD_FILE="$SCRIPT_DIR/queue/dashboard.md"`
  - `scripts/dashboard_lifecycle.sh:26` — `DASHBOARD_MD="${SCRIPT_DIR}/dashboard.md"` (project root)
  - 実ファイル: `dashboard.md`（project root）のみ存在。`queue/dashboard.md` は存在しない（`ls /home/murakami/multi-agent-shogun/queue/dashboard.md` → No such file）
- **Impact**:
  - `precompact_hook.sh:139-141` の `if [ -f "$DASHBOARD_FILE" ]` 条件が常に false
  - shogun/karo の compaction snapshot に dashboard 抜粋が一切載らない（沈黙故障）
  - 同じ「dashboard.md」概念に対し2スクリプトでパスが別 → 単一情報源原則違反
- **CHK trace**: `scripts/precompact_hook.sh:138-141` vs `scripts/dashboard_lifecycle.sh:26`

### C3. inbox_watcher.sh の SQLite-only mark-read による YAML 残置

- **観測**: `scripts/inbox_watcher.sh:434-449` (sqlite3 利用可時)
  ```
  sqlite3 ... "UPDATE inbox_messages SET read=1, read_at=datetime('now')
               WHERE agent='$AGENT_ID' AND read=0
               AND type IN ('clear_command','model_switch','cli_restart')"
  ```
  この経路は **SQLite だけ** read=1 化する。同関数の YAML 経路 (L451-498) は sqlite3 が無い時のみ動く。
- **Impact**:
  - 通常運用 (sqlite3 あり) では `queue/inbox/{agent}.yaml` 内の specials が `read: false` のまま残置
  - YAML 直読みする stop_hook_inbox.sh:267 (`grep -c 'read: false' "$INBOX"`) が「未読あり」と誤検知 → stop block の温床
  - C1 と合わさるとさらに悪化（model_switch/cli_restart は SQLite に存在しないのに UPDATE は0件成功 → YAML だけ未読として残る）
  - memory「書込フォールバック (SQLite 直書き) は禁止」に明確に違反
- **CHK trace**: `scripts/inbox_watcher.sh:434-449`（SQLite 直 UPDATE）

### C4. inbox_watcher.sh の get_unread_info SQLite/YAML 経路で normal_count 算出ロジックが非対称

- **観測**:
  - SQLite path L439: `normal_count = SELECT COUNT(*) FROM inbox_messages WHERE agent=$ID AND read=0 AND type NOT IN ('clear_command','model_switch','cli_restart')` ←mark-read 前に取得
  - YAML path L484: `normal_count = len(unread) - len(specials)` ←specials を read=true 化した直後（同一トランザクション内）
- **Impact**:
  - SQLite 経路では UPDATE (L446) がL439 より後で動くが、L439 の SELECT 時点で未読 specials がカウントから既に除外されている → 意図上は同じ
  - だが YAML 経路と異なり SQLite 経路は **specials の YAML 状態を変えない** ため、次回起動時 stop_hook_inbox.sh:267 が YAML を grep して未読再カウント → C3 と同根のループ
- **CHK trace**: `scripts/inbox_watcher.sh:438-498` の二経路差分

---

## HIGH

### H1. cron_health_check.sh TARGETS に C12/C13/C15 が未登録

- **観測**: `scripts/cron_health_check.sh:26-38` の TARGETS 配列は C01-C10 + C14 のみ。C11 は自身のため意図的除外（コメント記載あり）。
  - `shared_context/cron_inventory.md` には以下も登録済 (grep `^### C[0-9]+` で確認):
    - **C12** hotfix trend detector → `logs/hotfix_trend.log` (crontab L: `0 6 * * 1`)
    - **C13** monthly feedback review → `logs/monthly_feedback_review.log` (crontab L: `0 4 1 * *`)
    - **C15** chroma-mcp 健全性監視 → `logs/chroma_mcp_health.log` (crontab L: `*/5 * * * *`)
- **Impact**:
  - これら3つの cron job が Traceback/ERROR を吐いても silent → ntfy 警告ゼロ
  - cron_inventory.md の「C11 で異常検知される」前提が C12/C13/C15 では破綻
  - 実害最大は C15 (5分毎・MCP 障害監視そのものの可用性低下)
- **CHK trace**: `scripts/cron_health_check.sh:26-38` ↔ `shared_context/cron_inventory.md:181-220`

### H2. ntfy.sh の IP 置換が同一 substitution 2行重複

- **観測**: `scripts/ntfy.sh:26-27`
  ```bash
  MSG="${1//192.168.2.4/100.66.15.93}"
  MSG="${MSG//192.168.2.4/100.66.15.93}"
  ```
  2行目は1行目と完全同一の置換パターン（左辺だけ `$MSG`）。実効上 2行目は何も変えない。
- **Impact**:
  - 観測事実のみ: 重複行が存在し計算上の効果はない（2回目のループは置換対象がすでに空）
  - dashboard MEMORY.md / CLAUDE.md 内では `192.168.2.4:8770` と `192.168.2.7:8770` が混在記載されている。`192.168.2.7` 系列の置換は本コードでは行われない
  - 殿のスマホ(Tailscale)経由で別 LAN IP を含む通知本文を受け取った時、置換漏れの可能性がある（但し本ファイル単独では「漏れている対象 IP」を断定できない）
- **CHK trace**: `scripts/ntfy.sh:26-27`

### H3. stop_hook_inbox.sh STOP_HOOK_ACTIVE=True 経路で LAST_MSG 完了通知が二重発火する

- **観測**: `scripts/stop_hook_inbox.sh:139-198`
  - L139: `STOP_HOOK_ACTIVE` 判定
  - L143-156: True 時は idle flag + inotifywait 後、unread=0 なら exit
  - L162-164: unread > 0 で **fall through**
  - L168-198: そのまま LAST_MSG 解析 → "完了" 検出 → karo へ `report_completed` を再送する経路に入る
- **Impact**:
  - 同一 turn 内で stop_hook が複数回 fire するたびに同じ `report_completed` 通知が karo inbox に複製
  - L139 上のコメント「Allow it to stop this time to prevent loops」と実装が乖離（実際にはループ抑止ではなく「unread 0 なら抑止、0でなければ通知再送」）
- **CHK trace**: `scripts/stop_hook_inbox.sh:138-198`

### H4. stop_hook_inbox.sh が unread をカウントする経路と inbox_watcher 既読化の経路が分離している

- **観測**:
  - `scripts/stop_hook_inbox.sh:158, 267` — 共に YAML grep `'read: false'`
  - `scripts/inbox_watcher.sh:407-449` — sqlite3 利用可時は SQLite だけ更新（C3 参照）
- **Impact**:
  - stop_hook が見ている「未読」と watcher が見ている「未読」が乖離
  - SQLite 上 read=1 化された specials が YAML では未読のまま残り、stop_hook が無限に block を返し続ける可能性
- **CHK trace**: `scripts/stop_hook_inbox.sh:158,267` vs `scripts/inbox_watcher.sh:434-449`

### H5. fix_panes.sh のフォールバック CLI 起動コマンドが settings.yaml と乖離

- **観測**: `scripts/fix_panes.sh:65-72`
  ```
  if [ "$i" -eq 0 ] || [ "$i" -eq $((TOTAL - 1)) ]; then
      LAUNCH_CMD="claude --model 'opus[1m]' --dangerously-skip-permissions"
  else
      LAUNCH_CMD="claude --model 'sonnet' --dangerously-skip-permissions"
  fi
  ```
  cli_adapter.sh が読み込めない場合のみ走るフォールバック。
  現状の `config/settings.yaml:25-35`: shogun=opus[1m], **karo=sonnet, gunshi=opus[1m], ashigaru1-7=haiku**
- **Impact**:
  - フォールバック起動時、karo (i=0) が opus[1m] になり (settings は sonnet)、ashigaru1-7 が sonnet になる (settings は haiku)
  - bloom_routing 整合と Anthropic Max 枠コストの双方が崩壊
  - cli_adapter.sh 不在時しか発火しないが、PC換装直後等の状況では発生しうる
- **CHK trace**: `scripts/fix_panes.sh:65-72` vs `config/settings.yaml:25-35`

---

## MEDIUM

### M1. ntfy.sh の `_update_cmd_done` が `assigned`/`blocked` 等の status まで強制的に done に遷移させる

- **観測**: `scripts/ntfy.sh:54-63`
  ```awk
  in_block && /^  status: (pending|in_progress|suspended|assigned|blocked)$/ {
      sub(/status: (pending|in_progress|suspended|assigned|blocked)/, "status: done")
  ```
  メッセージ本文に `cmd_NNNN完了` 文字列が含まれるだけで対象 cmd の status を強制 `done` に遷移。
- **Impact**:
  - blocked 状態の cmd が ntfy 通知のたびに勝手に done 化される可能性
  - 殿への第三者通知文・archive log 等で `cmd_NNNN完了` を引用した瞬間に発火（誤動作トリガー条件が極めて緩い）
- **CHK trace**: `scripts/ntfy.sh:36-71`

### M2. ntfy.sh の `_archive_old_done_cmds` が ntfy 呼出のたびに実行される

- **観測**: `scripts/ntfy.sh:75-148`。L86 の閾値 100 件超で動き、毎呼出ごとに `wc`/`grep`/python パイプ + flock を取得。
- **Impact**:
  - ntfy 通知1件ごとに shogun_to_karo.yaml フルスキャン + flock 待ち。負荷大時に通知遅延の温床
  - cron 経由の通知が大量に走る時間帯（毎時0分の dashboard_lifecycle 等）でロック競合の可能性
- **CHK trace**: `scripts/ntfy.sh:75-148`

### M3. dashboard_lifecycle.sh のコメントとコード乖離（廃止宣言と実コード残存）

- **観測**: `scripts/dashboard_lifecycle.sh:13` コメントに「dashboard.md は cmd_1556 で廃止済み。dashboard.md関連の (1) Logic は全てskip動作」とあるが、L70-159 の `clean_dashboard_md` は実際に dashboard.md を読み・書き戻し・archive している。L161 で実呼出。
- **Impact**:
  - 「廃止済み」と読んで安全と判断した家老が dashboard.md を編集すると lifecycle スクリプトが書き戻す競合発生
  - コメントは陳腐化、実コードは生きている
- **CHK trace**: `scripts/dashboard_lifecycle.sh:13,69-161`

### M4. monitor.sh / context_watcher.sh の起動経路が手動のみ

- **観測**:
  - `scripts/monitor.sh:1-12` start/stop インターフェイス、cron 登録なし、watcher_supervisor.sh 経由なし（`crontab -l` / `scripts/watcher_supervisor.sh:43-54` で確認）
  - `scripts/context_watcher.sh:4` に「起動経路: 手動バックグラウンド実行のみ (cron未登録・watcher_supervisor.sh非経由)」と自己宣言
- **Impact**:
  - 再起動・PC換装後に手動起動を忘れると沈黙故障（context 75% 超で handoff/clear が動かない、リソース監視が止まる）
  - CLAUDE.md / instructions 配下に手動起動手順の明記なし（grep で確認）
  - **ps/supervisor 実稼働は本タスク内では未確認** → 「死蔵」断定はせず「沈黙故障リスク」として記録
- **CHK trace**: `scripts/monitor.sh`, `scripts/context_watcher.sh:1-12`, `scripts/watcher_supervisor.sh:43-54`

### M5. inbox_write.sh の `_update_task_done` が cmd_id 不一致時に「最後の status: assigned」を fallback で done 化

- **観測**: `scripts/inbox_write.sh:148-159`
  ```bash
  # Fallback: last "status: assigned" in file
  [ -z "$target_line" ] && target_line=$(grep -n "status: assigned" "$task_file" | tail -1 | cut -d: -f1)
  ```
  メッセージ本文から cmd_id 抽出に失敗または別 cmd 由来の `report_done` 通知時、「ファイル末尾の status: assigned」が誤って done 化される。
- **Impact**:
  - 全く別の assigned タスクが完了扱いになり、status corruption
  - 既知の事故事例は本タスクスコープでは未確認だが、現在の足軽運用では report_done が頻発しており発火確率は低くない
- **CHK trace**: `scripts/inbox_write.sh:132-167`

### M6. ntfy_listener.sh のエージェント判定が emoji prefix の閉集合

- **観測**: `scripts/ntfy_listener.sh:294-296`
  ```
  case "$MSG" in
      ✅*|🎬*|🐑*|🌟*|🎤*|📊*|🚨*|📰*|🖼️*|🔍*|❌*|🌐*|📋*) IS_AGENT_MSG=true ;;
  ```
- **Impact**:
  - 殿が新しい絵文字を ntfy 経由で送ったら shogun を起こさない可能性
  - 家老の ntfy 文（CLAUDE.md「ntfy通知ルール」記載）が将来的に他絵文字に変わったら shogun が起き上がる事故リスク
  - 集合の維持方針 (どのファイルが正規か) が不明
- **CHK trace**: `scripts/ntfy_listener.sh:294-296`

---

## LOW

### L1. inbox_watcher.sh の Phase flag 群に未参照の可能性

- **観測**: `scripts/inbox_watcher.sh:161-170`
  - `ASW_DISABLE_ESCALATION` / `ASW_PROCESS_TIMEOUT` を定義しているが、L300 以降本ファイル末尾までで実参照箇所が見当たらない（grep `ASW_DISABLE_ESCALATION` で確認推奨）
- **Impact**: 設定ノブが空回り。debug 用途の遺物の可能性
- **CHK trace**: `scripts/inbox_watcher.sh:161-170`

### L2. inbox_watcher.sh の Codex 起動時 idle flag 未作成

- **観測**: `scripts/inbox_watcher.sh:74-77` Claude のみ初期 idle flag を作成。Codex/Copilot/Kimi は作成しない。
- **Impact**:
  - non-Claude CLI の初回起動時 `agent_is_busy()` が pane 直接判定にフォールバック (L786-792)
  - pane が welcome screen の場合 busy 判定される可能性 → nudge 抑止の誤動作
- **CHK trace**: `scripts/inbox_watcher.sh:74-77, 766-796`

### L3. ntfy_listener.sh の `SINCE_TS=$(date +%s)` 再接続毎リセット

- **観測**: `scripts/ntfy_listener.sh:245-246`
  ```
  while true; do
      SINCE_TS=$(date +%s)
      curl -s --no-buffer ... "https://ntfy.sh/$TOPIC/json?since=${SINCE_TS}"
  ```
  L308-310: 接続切断 → 5秒 sleep → 次の SINCE_TS 計算 → since パラメータで「再接続後の」メッセージのみ取得。
- **Impact**:
  - 接続切断中(5秒+α)に到着した ntfy メッセージを永遠に取りこぼす（since=切断後時刻のため、切断中のメッセージは再取得されない）
  - 殿のスマホからの緊急メッセージが沈黙する場合あり
- **CHK trace**: `scripts/ntfy_listener.sh:242-310`

### L4. start_ashigaru_glm.sh の advisor_proxy 依存が暗黙

- **観測**: `scripts/start_ashigaru_glm.sh:51` `ANTHROPIC_BASE_URL=http://localhost:8780` (advisor_proxy 前提)
- **Impact**:
  - advisor_proxy (localhost:8780) が起動していない時、CLI 起動後の最初のリクエストでハング/タイムアウト
  - スクリプト内に proxy 起動確認なし（curl ヘルスチェック等不在）
  - GLM 復帰運用時の落とし穴。ただし memory「2026-05-06 殿確定: GLM 制限到来時 → Haiku 切替」により現状この経路は休眠中（low impact）
- **CHK trace**: `scripts/start_ashigaru_glm.sh:51-63`

---

## 推奨 follow-up cmd（軍師案・実装は別cmd）

> 本タスクは読んで報告のみのため、以下は家老/殿判断用の参考リスト（本書では実装しない）。

1. **CRITICAL C1**: `inbox_messages.type` CHECK 制約に `error_report`, `nightly_audit`, `ntfy_received`, `model_switch`, `cli_restart` を追加（DDL 修正 + マイグレーション）
2. **CRITICAL C2**: `precompact_hook.sh:138` の DASHBOARD_FILE パスを project root に統一
3. **CRITICAL C3/C4**: inbox_watcher SQLite-only mark-read を YAML 同時更新に修正、または server.py API (`/api/inbox_mark_read`) 経由に統一
4. **HIGH H1**: `cron_health_check.sh` TARGETS に C12/C13/C15 を追加
5. **HIGH H2**: `ntfy.sh:26-27` 重複行の意図確認（殿に確認: 192.168.2.7 への置換が必要かどうか）
6. **HIGH H3**: stop_hook_inbox.sh の STOP_HOOK_ACTIVE=True 経路で LAST_MSG 解析を skip するガード追加
7. **HIGH H5**: fix_panes.sh フォールバック分岐を削除し cli_adapter.sh 必須化
8. **MEDIUM M1**: ntfy.sh `_update_cmd_done` のトリガー条件厳格化（cmd 完了 inbox は API 経由のみに移行）
9. **MEDIUM M3**: dashboard_lifecycle.sh コメント整合性修正
10. **MEDIUM M4**: monitor.sh / context_watcher.sh の起動を watcher_supervisor.sh または cron に登録（手動経路を廃止）
11. **MEDIUM M5**: inbox_write.sh `_update_task_done` の fallback grep を削除（cmd_id 必須化）
12. **MEDIUM M6**: ntfy_listener.sh emoji 集合を一元管理ファイルに切り出し
13. **LOW L3**: ntfy_listener の since リセット問題（再接続前の since を保持する）

---

## メタ情報

- **読了スクリプト**: inbox_write.sh / inbox_watcher.sh (主要関数全文 + 残部分は要点抽出) / watcher_supervisor.sh / stop_hook_inbox.sh / ntfy.sh / ntfy_listener.sh / ntfy_voice.sh / notify.sh / cron_health_check.sh / cta_comment_cron.sh / agent_status.sh / start_ashigaru_haiku.sh / start_ashigaru_glm.sh / switch_ashigaru_model.sh / switch_cli.sh / reset_shutsujin.sh / fix_panes.sh / context_watcher.sh / monitor.sh / nightly_audit.sh / silent_fail_watcher.sh / userprompt_ntfy_check.sh / sessionstart_hook.sh / precompact_hook.sh / dashboard_lifecycle.sh (前半200行) / config/settings.yaml / shared_context/cron_inventory.md (C-ID部分) / queue/cmds.db スキーマ (inbox_messages)
- **未精読**: dashboard_lifecycle.sh L200-末尾、各 lib/ 配下 (cli_adapter.sh / agent_status.sh / ntfy_auth.sh) — 必要なら別cmdで補完精読
- **advisor()**: 作業前後に1回ずつ呼出済（前: 矛盾分類観点の優先度確認 / 後: 報告書執筆直前のスコープ整合確認）
