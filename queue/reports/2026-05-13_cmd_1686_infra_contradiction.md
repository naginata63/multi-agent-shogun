# cmd_1686 夜間矛盾検出レポート — インフラ系

- **作成日時**: 2026-05-13 02:30 JST
- **作成者**: 軍師 (subtask_1686_infra)
- **対象カテゴリ**: インフラ (inbox_write/watcher, ntfy, cron, agent管理, context_monitor, sessionstart/precompact hook)
- **形式**: cmd_828 準拠 (severity / file:line / observed / impact / prior_audit_ref)
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-09 cmd_1668 infra audit (`queue/reports/2026-05-09_cmd_1668_infra_mujun_detection.md`) との差分を flag

## サマリ

| Severity | 件数 (内訳) |
|----------|------|
| CRITICAL | 1 (NEW regression) |
| HIGH     | 2 (NEW 1 + cmd_1668継続 1) |
| MEDIUM   | 5 (cmd_1668継続 3 + NEW 2) |
| LOW      | 3 (cmd_1668継続 3) |

## cmd_1668 (5/9) からの進捗 (RESOLVED — 報告書冒頭で評価)

5/9 audit から **11件 解消** (全体 19件中):

| 5/9 finding | 現状 | evidence |
|--|--|--|
| C1 inbox_messages.type CHECK 制約欠落 | **解消** | `queue/cmds.db` schema に `error_report, nightly_audit, ntfy_received, model_switch, cli_restart` 追加済 |
| C3 inbox_watcher SQLite-only mark-read | **解消** | `inbox_watcher.sh:438-468` SQLite + YAML 同時更新 (PY_YAML_SYNC heredoc) |
| C4 get_unread_info 非対称 | **解消** | C3 と一体で修正 (L470) |
| H1 cron_health TARGETS C12/13/15 欠落 | **解消** | `cron_health_check.sh:26-41` に C12/C13/C14/C15 全て追加 |
| H2 ntfy.sh IP置換 2行重複 | **解消** | `ntfy.sh:26` 1行のみ |
| H3 stop_hook STOP_HOOK_ACTIVE LAST_MSG 二重発火 | **解消** | `stop_hook_inbox.sh:170-174` で LAST_MSG="" skip ガード |
| H4 stop_hook YAML grep vs watcher SQLite乖離 | **機能解消** | watcher 側で YAML 同時更新するため grep が正しく動く |
| H5 fix_panes.sh フォールバック CLI 乖離 | **解消** | `fix_panes.sh:66-72` で sonnet(i=0) / haiku(中間) / opus[1m](末尾) に修正 |
| M1 ntfy.sh _update_cmd_done assigned/blocked 強制done化 | **解消** | `ntfy.sh:55` で `pending\|in_progress\|suspended` のみに縮小 |
| M5 inbox_write.sh _update_task_done fallback grep | **解消** | `inbox_write.sh:132-147` で fallback 削除・cmd_id 無い時は silent log のみ |
| L1 inbox_watcher ASW_DISABLE_ESCALATION 未参照 | **解消** | grep hit 0件 (削除済み) |
| (memory 5/12) sessionstart_hook.sh nohup orphan SSE | **解消** | `sessionstart_hook.sh:34-38` でコメント化 + 削除済 |

→ **5/9 audit の指摘事項は半数以上が修正完了している**。本書は残課題と新規発見を主眼とする。

---

## CRITICAL

### C1 [NEW・cmd_1668 C2 修正の二次regression]: precompact_hook.sh の dashboard.md パスが project root 親dir を指す

- **file:line**: `scripts/precompact_hook.sh:21,160`
- **observed**:
  ```bash
  # L21
  SCRIPT_DIR="${__PRECOMPACT_HOOK_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
  # → SCRIPT_DIR = /home/murakami/multi-agent-shogun (project root)

  # L160
  DASHBOARD_FILE="$SCRIPT_DIR/../dashboard.md"
  # → /home/murakami/dashboard.md  ← 存在しない
  ```
  ls 検証: `/home/murakami/multi-agent-shogun/dashboard.md` は実在 (17K, 5/12 更新)・`/home/murakami/dashboard.md` は **No such file**。
- **impact**:
  - L161 `if [ -f "$DASHBOARD_FILE" ]` が常に false
  - shogun/karo の compaction snapshot に dashboard 抜粋が**一切載らない** (沈黙故障)
  - 5/9 cmd_1668 C2 で「project root に統一」とした修正が**過剰修正**で「project root の親」を指してしまった
- **recommendation**: `DASHBOARD_FILE="$SCRIPT_DIR/dashboard.md"` (`/..` 削除) に修正
- **prior_audit_ref**: cmd_1668 C2 (precompact_hook.sh dashboard.md パス) — 旧 `$SCRIPT_DIR/queue/dashboard.md` から `$SCRIPT_DIR/../dashboard.md` に変えたが行き過ぎた

---

## HIGH

### H1 [NEW]: silent_fail_watcher.sh 起動毎に WARN_BUFFER を強制 truncate

- **file:line**: `scripts/silent_fail_watcher.sh:30,34`
- **observed**:
  ```bash
  WARN_BUFFER="$STATE_DIR/warn_buffer.log"
  : > "$WARN_BUFFER" 2>/dev/null || true   # L34 — 起動毎 truncate
  ```
- **impact**:
  - 異常終了 → 再起動時に未 flush の WARN/FALLBACK エントリが全消失
  - 300s 集約 ntfy 通知の sample 行に「直前の異常」が反映されない (cmd_1443_p04 H4 の本来目的が損なわれる)
  - 現状 PID 2110 で稼働中だが、systemctl/cron 起動でない手動起動経路ゆえ kill 9 等で死ぬと sample lost
- **recommendation**:
  - (a) WARN_BUFFER は append 専用にし、flush 時のみ rotate/clear する
  - (b) 起動時に flush_warn_buffer() を最初に呼んで既存分を 1 通で送出してから truncate
- **prior_audit_ref**: 新規 (cmd_1668 で未指摘)

### H2 [cmd_1668 M4 継続・現実プロセス未稼働で深刻度上昇]: monitor.sh と context_watcher.sh が cron 未登録 + 実プロセス未稼働

- **file:line**: `scripts/monitor.sh:1-12`, `scripts/context_watcher.sh:4`
- **observed**:
  - `crontab -l | grep -iE "monitor|context_watcher"` → **0 件**
  - `ps -eo pid,cmd | grep -E "monitor|context_watcher"` → **0 プロセス** (silent_fail_watcher.sh のみ生存)
  - `scripts/watcher_supervisor.sh:43-54` の対象は inbox_watcher のみ・monitor/context_watcher は対象外
  - `context_watcher.sh:4` 自己宣言: 「起動経路: 手動バックグラウンド実行のみ (cron未登録・watcher_supervisor.sh非経由)」
- **impact**:
  - context_watcher 不在 → context 75% 超で /handoff → /clear → /rehydrate の自動運用が停止
  - monitor.sh 不在 → GPU/CPU/温度 ログが残らない (重処理時の温度警告経路喪失)
  - PC換装 (2026-05-04) 後の手動起動忘れが**現実化している** (cmd_1668 5/9 時点で「沈黙故障リスク」と指摘・4日間放置)
- **recommendation**:
  - (a) watcher_supervisor.sh に monitor.sh と context_watcher.sh の起動ロジックを追加 (5秒 loop で `pgrep -f` し起動)
  - (b) または crontab `@reboot` で自動起動
- **prior_audit_ref**: cmd_1668 M4 (沈黙故障リスク) — 5/9 から未対応・**実プロセス未稼働が確認できたため HIGH 昇格**

---

## MEDIUM

### M1 [cmd_1668 M2 継続]: ntfy.sh `_archive_old_done_cmds` が ntfy 呼出毎に実行される

- **file:line**: `scripts/ntfy.sh:74-147`
- **observed**: L86 の閾値 100 件超で実行され、毎呼出ごとに `wc`/`grep`/python パイプ + flock を取得。条件分岐の前に必ず `shogun_to_karo.yaml` を grep する。
- **impact**: ntfy 通知 1 件ごとに shogun_to_karo.yaml フルスキャン + lock 待ち。大量通知時 (毎時0分の dashboard_lifecycle 等) でロック競合
- **recommendation**: cron 化 (1日1回) もしくは ntfy.sh 起動時 5% 確率 sampling 化
- **prior_audit_ref**: cmd_1668 M2 — 5/9 から未対応

### M2 [cmd_1668 M3 継続]: dashboard_lifecycle.sh コメント (廃止宣言) と実コード乖離

- **file:line**: `scripts/dashboard_lifecycle.sh:13,66,69-161`
- **observed**: L66 コメント「(1) [SKIP] dashboard.md 廃止済 (cmd_1556) — 全ロジックskip動作」← だが直下 L69-161 の `clean_dashboard_md` が実 dashboard.md を読み・archive・書き戻し
- **impact**: 「廃止済み」と読んで安全と判断した家老が dashboard.md を編集すると lifecycle が書き戻す競合発生
- **recommendation**: コメント文言を「(1) dashboard.md 自動 clean — cmd_1556 後も active」等に訂正
- **prior_audit_ref**: cmd_1668 M3 — 5/9 から未対応

### M3 [cmd_1668 M6 継続]: ntfy_listener.sh emoji 集合が hard-coded

- **file:line**: `scripts/ntfy_listener.sh:296-298`
- **observed**:
  ```bash
  case "$MSG" in
      ✅*|🎬*|🐑*|🌟*|🎤*|📊*|🚨*|📰*|🖼️*|🔍*|❌*|🌐*|📋*) IS_AGENT_MSG=true ;;
  ```
- **impact**: 家老の ntfy 通知ルール (CLAUDE.md) が新絵文字に拡張された時、shogun が誤って起こされる (false positive) or 起きない (false negative)
- **recommendation**: `config/ntfy_emoji_filter.yaml` 等に外出し
- **prior_audit_ref**: cmd_1668 M6 — 5/9 から未対応

### M4 [NEW]: inbox_write.sh YAML 側 key `from` と SQLite カラム `from_agent` の dual-path key 名乖離

- **file:line**: `scripts/inbox_write.sh:185,238`
- **observed**:
  - YAML: L185 `new_msg = { 'id': msg_id, 'from': from_, ...}` ← key名 `from`
  - SQLite: L238 `INSERT ... (id, agent, from_agent, ...)` ← カラム名 `from_agent`
  - 一方 `dashboard_api_usage.md:165` レスポンス JSON は **`from_agent`** が正規
- **impact**:
  - bash 直叩き `inbox_write.sh` 経由で書かれた YAML inbox を直接 Read するエージェントは `from` key で取れるが、API 経由 `inbox_messages` レスポンスは `from_agent`
  - dual-path で「同じ msg を SQLite/YAML 経由で読むと from の取り出し方が変わる」既存スクリプトが存在する余地
  - server.py 経由の `/api/inbox_write` ルートは正規化済 (cmd_1494) なので主経路は OK・bash fallback 経路でのみ発生
- **recommendation**: inbox_write.sh の YAML 側 key も `from_agent` に統一 (もしくは server.py で読込時 alias 吸収)
- **prior_audit_ref**: 新規

### M5 [NEW]: watcher_supervisor.sh が 5秒間隔 polling (F004 哲学との整合明示なし)

- **file:line**: `scripts/watcher_supervisor.sh:43-55`
- **observed**:
  ```bash
  while true; do
      start_watcher_if_missing "shogun" ...
      ... (全 agent 起動チェック)
      sleep 5
  done
  ```
- **impact**:
  - 動作上の問題はない (intended polling・watcher の存在チェック)
  - ただし CLAUDE.md「Forbidden Actions F004 polling」と表面上矛盾する見え方 (実態は supervisor として正当だが)
  - 一行ヘッダコメントで「F004 適用外: supervisor として意図的 polling」と明記すべき
- **recommendation**: スクリプト冒頭にコメント追加 (またはコード変更なしの policy 整理)
- **prior_audit_ref**: 新規

---

## LOW

### L1 [cmd_1668 L3 継続]: ntfy_listener.sh `SINCE_TS=$(date +%s)` 再接続毎リセット

- **file:line**: `scripts/ntfy_listener.sh:243-312`
- **observed**: L243 `SINCE_TS=$(date +%s)` を while ループ前で 1 回設定するように見えるが、L245 のループ内では同じ since パラメータで curl し続ける構造 (cmd_1668 audit 時の指摘より改善されている可能性がある — 5/9 audit は「ループ内で再リセット」と記載・現状 L243 はループ外)
- **impact**:
  - 修正済 (L243 がループ外) なら OK・但しループ内で curl が EOF した後、L312 で sleep → 再 curl 時に SINCE_TS は変わらない → 切断中の取りこぼし問題は **解消方向**
  - **再検証必要**: 5/9 audit との差分が部分修正の可能性 (本書では確定 PASS とせず LOW 残置)
- **recommendation**: 別 cmd で動作 trace (logs/ntfy_listener.log で接続切断時の since パラメータ確認)
- **prior_audit_ref**: cmd_1668 L3 — 部分修正済の可能性

### L2 [cmd_1668 L4 継続]: start_ashigaru_glm.sh advisor_proxy 暗黙依存

- **file:line**: `scripts/start_ashigaru_glm.sh:51`
- **observed**: `ANTHROPIC_BASE_URL=http://localhost:8780` (advisor_proxy 前提) を export するが proxy 起動確認なし
- **impact**: GLM 復帰運用時の落とし穴 (advisor_proxy 未起動なら最初のリクエストでハング)
- **recommendation**: curl ヘルスチェック追加・もしくは GLM 経路廃止 (memory 2026-05-06 殿確定: Haiku 切替)
- **prior_audit_ref**: cmd_1668 L4 — 5/9 から未対応 (実害低・現状 Haiku 経路稼働中)

### L3 [cmd_1668 L2 継続]: inbox_watcher.sh Codex/Copilot 初期 idle flag 未作成

- **file:line**: `scripts/inbox_watcher.sh:72-75`
- **observed**: cmd_1668 audit 時は「Claude のみ初期 idle flag 作成」とあったが、現状 L74 は **全 CLI 共通で `touch idle_flag` を実行する形に改修済**の可能性。要再 trace
- **impact**: 改修済なら解消・要 verify
- **prior_audit_ref**: cmd_1668 L2 — 解消方向

---

## crontab drift 確認 (cmd_1668 H1 関連)

`diff shared_context/crontab.snapshot.txt <(crontab -l)`:
```
47a48
>   (空行 1 行の追加のみ・実効 cron 行の追加削除なし)
```

→ **実害なし** (snapshot と現 crontab の cron job entry は完全一致・コメント直後の空行 1 行だけ snapshot に余分)。
nightly_audit.sh の `_check_cron_drift` 関数は `grep -vE '^\s*#|^\s*$'` でコメント・空行を除外してから diff するため、この差分は **drift 検知発火しない**。

---

## dashboard_api_usage.md との乖離 (タスク要件 step 3)

| script | API 利用パターン | 乖離・残課題 |
|--|--|--|
| `inbox_write.sh` | YAML 直書き + SQLite 直 INSERT (bash 経由・fallback) | bash 直叩きは API 経由 `/api/inbox_write` に移行推奨 (dashboard_api_usage.md L36 移行ポリシー) |
| `nightly_audit.sh:42-43` | API ファースト + bash fallback | OK (推奨パターン) |
| `stop_hook_inbox.sh:196-199` | API ファースト + bash fallback | OK |
| `ntfy_listener.sh:300-306` | API ファースト + bash fallback | OK |
| `silent_fail_watcher.sh` | API 利用なし (`ntfy.sh` のみ呼出) | OK (scope外) |

API 利用パターンは全体的に dashboard_api_usage.md 準拠 (cmd_1494 移行ポリシー遵守)。**乖離は inbox_write.sh の bash 直叩き経路のみ・但し fallback として残置必要**。

---

## 推奨 follow-up cmd (家老・殿判断用)

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **CRITICAL C1**: `precompact_hook.sh:160` の `$SCRIPT_DIR/../dashboard.md` を `$SCRIPT_DIR/dashboard.md` に修正 (1行修正・足軽1人で 5分)
2. **HIGH H1**: silent_fail_watcher.sh の WARN_BUFFER truncate ロジック改修 (起動時 flush 先行)
3. **HIGH H2**: watcher_supervisor.sh に monitor.sh / context_watcher.sh の起動ロジック追加 (PC換装 2026-05-04 後の沈黙故障解消)
4. **MEDIUM M1-M3**: cmd_1668 から 4日経過しても未対応・優先度低・cmd_1690 等で家老まとめて処置
5. **MEDIUM M4**: inbox_write.sh の YAML key を `from_agent` 統一 (dual-path 整合性)
6. **MEDIUM M5**: watcher_supervisor.sh 冒頭コメントで polling 意図明示 (F004 例外宣言)

---

## メタ情報

- **精読 (全文)**: inbox_write.sh / ntfy.sh / watcher_supervisor.sh / nightly_audit.sh / cron_health_check.sh / silent_fail_watcher.sh / context_watcher.sh / monitor.sh / sessionstart_hook.sh / precompact_hook.sh (主要 region) / dashboard_lifecycle.sh (前半 200 行) / stop_hook_inbox.sh (主要 region) / ntfy_listener.sh (主要 region) / inbox_watcher.sh (主要 region L1-100/L380-510) / fix_panes.sh
- **schema 確認**: `sqlite3 queue/cmds.db ".schema inbox_messages"` (CHECK 制約・index・trigger)
- **設定確認**: `crontab -l` vs `shared_context/crontab.snapshot.txt` / live `ps -eo pid,cmd` でプロセス生存確認
- **未精読**: pretool_check.sh (39K・本 audit scope の主眼外・別カテゴリ「pre-tool hook」で別cmd扱い推奨) / dashboard_lifecycle.sh L200-末尾 / inbox_watcher.sh の escalation 部分 (L500-末尾)
- **baseline**: `queue/reports/2026-05-09_cmd_1668_infra_mujun_detection.md`
- **advisor()**: 作業前 1 回呼出 (方針確認・tier 分類・known issue verify 観点)
- **時間**: 02:03 受領 → 02:30 報告書作成完了 (約 27 分)

## north_star_alignment

- status: aligned
- reason: cmd_1668 から 4 日経過・主要 11 件解消は前進だが、CRITICAL regression 1 件 (precompact dashboard path) と HIGH 2 件 (silent_fail_watcher truncate / monitor & context_watcher 死蔵) が現運用を silent 故障させている。本書で flag することで朝の家老/殿の対応に時間予算を渡す。
- risks_to_north_star:
  - C1 を放置すると compaction 後の shogun/karo が dashboard 情報を失い意思決定遅延
  - H2 (monitor / context_watcher 死蔵) を 4 日放置している実態を踏まえると、優先度を上げて即対応すべき
