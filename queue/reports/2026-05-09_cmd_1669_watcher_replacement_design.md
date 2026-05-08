# cmd_1669 ashigaru watcher 代替機構設計書

- **作成日時**: 2026-05-09 JST (軍師執筆・gunshi_watcher_design_1669)
- **殿原文**: 「え？作ればいいじゃん代替手段　軍師に設計させよ」
- **North Star**: 9体watcher daemon を畳み、暴走源(silent_fail/nudge連投/二重/clear)を構造的に消す。ハーネス縮小=保守コスト削減+ntfyノイズ削減
- **制約**: コード修正なし・テスト作成なし・設計のみ
- **形式**: 3案 (A/B/C) + 推奨案 D (Hybrid) + 移行ロードマップ + 殿質問

---

## 0. エグゼクティブサマリ

### 推奨

**D案 = SSE Monitor (cmd_1648/1649/1650 延長) + 軽量中央 Hang Detector daemon (1個)**

- **メイン配信路**: 各 agent pane で `Monitor(curl -N /api/inbox_stream?agent=X)` を起動。Claude Code の Monitor ツールが SSE をネイティブ受信 → Claude 自身が直接処理。tmux send-keys ゼロ
- **特殊コマンド配送 (clear_command / model_switch)**: 中央 1 daemon が SSE 購読 → 該当 type 検出時のみ tmux send-keys
- **Hang Recovery**: 同 daemon が pane busy 時間を監視 → 閾値超で /clear 送信
- **既存 inbox_watcher.sh × 9 → 全廃**

| 暴走種別 | D案での扱い |
|---------|-----------|
| silent_fail FP | inotify 廃止 → **構造的に消滅** |
| /clear 二重発火 | /clear 発行者を中央 daemon 1点に集約 → 二重不可能 |
| nudge 連投 | SSE push ベース → nudge 概念自体が消滅 |
| Enter 迷子 | send-keys は clear/model/hang 時のみ低頻度 → 失敗時即検知容易 |

### 既存路線との関係

cmd_1648 (SSE Phase 1) / cmd_1649 (Phase 2 軍師24h) は完了。cmd_1650 (Phase 3 全10 agent 展開) は pending。本設計は **cmd_1650 の上に hang detector を 1 段乗せて watcher 廃止条件を満たす形** と位置付ける。

---

## 1. 現行 watcher 4機能 整理

| # | 機能 | 現行実装 (inbox_watcher.sh) | トリガー |
|---|------|---------------------------|---------|
| F1 | **clear_command 変換** | `normalize_special_command` (L287-313) → `send_cli_command "/clear"` (L505-612) | inbox に `type: clear_command` 投函 |
| F2 | **model_switch 変換** | 同上 → `send_cli_command "/model X"` | inbox に `type: model_switch` 投函 |
| F3 | **CONTEXT-RESET** | `send_context_reset` (L658-738)・新 `task_assigned` 検出時に /clear → 新 task の文脈を清浄に | inbox に `type: task_assigned` 投函 (前段に未処理の他task有り) |
| F4 | **Hang Recovery** | escalation phase 1/2/3 (L915-982 + 関連) ・`FIRST_UNREAD_SEEN` 経過時間ベース | 未読 messages の経過時間 > 4 分 |

**補助機能** (4機能の外で watcher が担っている雑務):
- F+1 nudge (`inboxN` send-keys) — SSE 化で消滅
- F+2 idle flag 管理 — Stop hook と二重管理 (cmd_1668 H4 で報告済)
- F+3 metrics yaml 出力 — 観測用・代替先で再実装可能

---

## 2. 過去暴走 4 種 (再発リスク評価軸)

| # | 暴走 | 発生機序 (現行) | 影響 |
|---|------|---------------|------|
| B1 | **silent_fail false positive** | inotify が atomic rename / touch で modify event を多重発火 → process_unread() が空読み連発 | log 肥大・SQLite/YAML 整合監視への false 通知 |
| B2 | **/clear 二重発火** | Phase 3 escalation /clear と CONTEXT-RESET /clear が < 60s で連続発火 (cmd_1657 race事例) | 進行中作業ロスト・5分以上の stall |
| B3 | **nudge 連投** | LAST_NUDGE_COUNT throttle が unread_count 値を見るが、同値・別 message 群でも throttle されてしまう / 逆に値変動で連投 | pane に `inbox5` 等が残置・Enter 迷子の温床 |
| B4 | **Enter 迷子** | tmux send-keys でテキスト送信 → Enter 送信の間に CLI 状態遷移 → Enter が別 prompt に入る | コマンド未実行・サイレント失敗 |

---

## 3. 案比較

### A案: 純 SSE Monitor (中央 daemon なし)

各 agent pane で Claude Code 標準 Monitor ツールが `curl -N /api/inbox_stream?agent=X` を起動し、SSE 購読する。**watcher 完全廃止**。

| 機能 | A案での実現方法 |
|------|---------------|
| F1 clear_command | **❌ 構造的に困難** — Claude 自身が自分の context を /clear できない (slash command は CLI 入力としてしか受け付けない) |
| F2 model_switch | **❌ 同上** — /model も CLI 直接入力が必要 |
| F3 CONTEXT-RESET | △ 部分的可能 — Claude が「新task来た・前tasks の context は捨てるべき」と認識し、内部で「考慮しない」運用にする (ソフト reset)。ハードな /clear は不可 |
| F4 Hang Recovery | **❌ 不可能** — hang した Claude pane は SSE クライアント自身が動かないため、自己復旧の余地なし |

| 暴走 | A案での再発リスク |
|------|----------------|
| B1 silent_fail FP | ✅ 解消 (inotify 廃止) |
| B2 /clear 二重 | ✅ 解消 (/clear 発行が消滅・F1/F3 不可と引き換え) |
| B3 nudge 連投 | ✅ 解消 (nudge 概念消滅) |
| B4 Enter 迷子 | ✅ 解消 (send-keys 廃止) |

**評価**: 暴走4種は構造的に消えるが、F1/F2/F4 が機能不全。**単独採用不可**。

### B案: Stop Hook + Server-side Pull (Polling型)

Claude Code 標準の Stop hook (現 `stop_hook_inbox.sh`) を活用。turn 終了時に agent 自身が `/api/inbox_messages?agent=X&unread=1` を pull → 必要処理を agent が判断。watcher daemon 廃止。

| 機能 | B案での実現方法 |
|------|---------------|
| F1 clear_command | **❌ 不可** — agent が自分の /clear を発火できない |
| F2 model_switch | **❌ 不可** |
| F3 CONTEXT-RESET | △ ソフト reset (A案と同様) |
| F4 Hang Recovery | **❌ 不可** — hang 中は Stop hook も動かない |

| 暴走 | 再発リスク |
|------|----------|
| B1 silent_fail FP | ✅ 解消 |
| B2 /clear 二重 | ✅ 解消 |
| B3 nudge 連投 | ✅ 解消 |
| B4 Enter 迷子 | ✅ 解消 |

**評価**: A案より配信遅延大 (turn 中 inbox 着 → 次 turn 処理) で実用 NG。F1/F2/F4 不可も同じ。**単独採用不可**。

### C案: 中央集権 1 daemon (9→1 統合)

1個の常駐 daemon が server.py の SSE を全 agent 分購読 (multiplex) し、必要時に `tmux send-keys` を発火。watcher を 9→1 に統合。

| 機能 | C案での実現方法 |
|------|---------------|
| F1 clear_command | ✅ daemon → `tmux send-keys -t {pane} /clear` |
| F2 model_switch | ✅ daemon → `tmux send-keys -t {pane} /model X` |
| F3 CONTEXT-RESET | ✅ task_assigned 受信時に /clear (現行と同じロジック) |
| F4 Hang Recovery | ✅ daemon が pane の busy 時間を監視 → 閾値で /clear |

| 暴走 | 再発リスク |
|------|----------|
| B1 silent_fail FP | ✅ 解消 (SSE 化で inotify 廃止) |
| B2 /clear 二重 | ✅ 解消 (発行者が daemon 1点) |
| B3 nudge 連投 | ✅ 解消 (nudge 自体不要・特殊コマンドのみ) |
| B4 Enter 迷子 | △ 残存 — send-keys は使うが頻度激減 (clear/model/hang のみ・通常 inbox 配信は SSE) |

**評価**: 4機能維持+暴走4種ほぼ解決。だが daemon は SPOF (落ちたら F1/F2/F4 全停止)。

### D案 (推奨): Hybrid = A案 SSE + C案 軽量 daemon

通常 inbox 配信は A案、特殊コマンド (F1/F2/F4) のみ C案 1 daemon が担当する分業構成。

| 機能 | D案での実現方法 |
|------|---------------|
| F1 clear_command | C案部分が担当 (1 daemon → send-keys) |
| F2 model_switch | 同上 |
| F3 CONTEXT-RESET | A案部分で実現 — Claude 自身が SSE で task_assigned を受け取り「新 task に集中」運用 (ソフト reset)。**ハード /clear が必要なら** C案部分にフォールバック |
| F4 Hang Recovery | C案部分が担当 — pane busy 時間監視 → /clear |
| F+1 nudge | **廃止** (SSE で push) |

| 暴走 | 再発リスク |
|------|----------|
| B1 silent_fail FP | ✅ 構造的に消滅 |
| B2 /clear 二重 | ✅ 発行者が 1 daemon に集約 → 二重不可能 |
| B3 nudge 連投 | ✅ nudge 廃止で消滅 |
| B4 Enter 迷子 | △ 低頻度 (1 日 数回〜十数回程度) ・送信失敗時は daemon log で即検知可能 |

**評価**: 4機能全維持・暴走4種すべて構造的対策・SPOF は1 daemon のみ (現行は 9 daemon SPOF が分散しているだけで実質同等の単一障害)。最良。

---

## 4. 案サマリ表

| 評価軸 | A 純SSE | B Stop Hook | C 中央集権 | **D Hybrid (推奨)** |
|-------|--------|-------------|-----------|-----------------|
| F1 clear_command | ❌ | ❌ | ✅ | ✅ |
| F2 model_switch | ❌ | ❌ | ✅ | ✅ |
| F3 CONTEXT-RESET (ハード /clear) | △ ソフトのみ | △ ソフトのみ | ✅ | ✅ |
| F4 Hang Recovery | ❌ | ❌ | ✅ | ✅ |
| B1 silent_fail FP 構造解決 | ✅ | ✅ | ✅ | ✅ |
| B2 /clear 二重 構造解決 | ✅ | ✅ | ✅ | ✅ |
| B3 nudge 連投 構造解決 | ✅ | ✅ | ✅ | ✅ |
| B4 Enter 迷子 構造解決 | ✅ | ✅ | △ 低頻度残存 | △ 低頻度残存 |
| daemon 数 | 0 | 0 | 1 | 1 |
| SPOF | なし | なし | 1 daemon | 1 daemon |
| 9体 watcher 廃止可能 | 部分 (F1/F2/F4 失う) | 部分 | ✅ | ✅ |
| 既存 SSE (cmd_1648/1649) との整合 | 完全 | 別経路 | 完全 | 完全 |
| 実装コスト | 低 | 低 | 中 | 中 |

---

## 5. 推奨案 D の詳細設計

### 5.1 配信経路 (Plane A: SSE)

```
inbox_write API
    ↓ in-memory queue.put_nowait
server.py SSE generator (/api/inbox_stream?agent=X)
    ↓ event-stream
{各 agent pane} Monitor(curl -N ...) ツール
    ↓ stdout 行
Claude (gunshi/karo/ashigaru1-7) が直接受信・処理
```

### 5.2 特殊コマンド経路 (Plane B: 1 daemon)

新規実装する軽量 daemon (仮称 `harness_dispatcher.py`):

```
server.py SSE (/api/inbox_stream?agent=__dispatcher__) — 全 agent 分 fanout 購読 (新規 server.py 改修)
    OR  個別 SSE × 9 並列 curl
    ↓ event-stream
harness_dispatcher.py
    ↓ type 振分
    ├─ clear_command → tmux send-keys -t {pane} /clear (CLI別変換は cli_adapter 流用)
    ├─ model_switch  → tmux send-keys -t {pane} /model X
    └─ (内部 timer)  → pane busy>N分検知 → tmux send-keys /clear
```

### 5.3 /clear 発行者の一元化 (B2 構造対策)

- /clear を打つのは `harness_dispatcher.py` のみ
- 既存 escalation Phase 1/2/3 (inbox_watcher.sh L915-982) は廃止
- CONTEXT-RESET (現 inbox_watcher.sh L658-738) も daemon 側に集約
- Cool-down (60秒) を daemon 内 1 か所だけで管理 → 二重発火物理不可
- **F1 (clear_command) / F3 (CONTEXT-RESET) / F4 (hang recovery) の3経路すべてが同一 cool-down 状態を共有** (LAST_CLEAR_TS グローバル変数1個・実装時に経路ごとに分けない)

### 5.4 Hang 検知のしきい値

現行 inbox_watcher.sh の経験値:
- ESCALATE_PHASE2 = 240s (4分)
- ESCALATE_COOLDOWN = 300s (5分)

D案 daemon の初期値推奨:
- hang_threshold = 240s 維持 (実証済)
- /clear cooldown = 300s 維持
- 設定ファイル化 (`config/harness.yaml` 等で殿が調整可能)

### 5.5 失敗時のフォールバック

- daemon 死亡 → systemd / watcher_supervisor.sh が再起動 (既存 supervisor の枠組みを 9→1 に流用)
- SSE 接続切断 → daemon 内 with-backoff 再接続 (curl --retry でない自前実装 ・cmd_1649 §7 で warm-up 30 秒運用ルール明文化済を踏襲)
- server.py 再起動 → 1 hour 毎 (dashboard_lifecycle.sh 由来) — daemon 側で再接続 + 起動直後の SSE init push (cmd_1648 実装済) で取りこぼしゼロ

---

## 6. 移行ロードマップ

| Phase | 対象 | 期間目安 | 完了条件 |
|-------|------|---------|----------|
| P0 (前提) | cmd_1650 完了 (全10 agent SSE Monitor 並走) | 1 週間 | 取りこぼし steady-state 0件 |
| **P1** | `harness_dispatcher.py` 設計詳細 + server.py SSE multiplex 改修要否確認 | 2-3 日 | 設計書 + server.py 改修要否判定 |
| **P2** | dispatcher 実装 + 単体テスト + dry-run (clear/model 受信ログのみ・実発火しない) | 3-5 日 | 9 agent 分 SSE 受信 100% / clear/model 検出ログ100% |
| **P3** | dispatcher を本番 enable・既存 inbox_watcher.sh は **並走継続** (1 週間 safety net) | 1 週間 | dispatcher 経由 /clear・/model が正常動作・既存 watcher と二重発火しないことを確認 (排他フラグまたは inbox_watcher 側 ASW_DISABLE_ESCALATION=1 で /clear 系のみ off にする) |
| **P4** | inbox_watcher.sh 9体停止・watcher_supervisor.sh から該当 entry 削除 | 1 日 | pgrep で 9体すべて 0 件・SSE+dispatcher 単独運用で 24h 観察 |
| **P5** | inbox_watcher.sh / stop_hook の死コード掃除 + nudge 関連 code 削除 + ドキュメント更新 | 2-3 日 | git push + CLAUDE.md / instructions 反映 |

合計: 約 3 週間 (cmd_1646 SSE ロードマップと同等オーダー)

### 6.1 ロールバック手順

各 Phase で問題発生時の戻し方:

| Phase | ロールバック手順 |
|-------|---------------|
| P3 異常 | dispatcher 停止 (kill) + inbox_watcher.sh の ASW_DISABLE_ESCALATION=0 に戻す → 旧運用 100% 復帰 |
| P4 異常 | watcher_supervisor.sh 復活 + 9体 watcher 再起動 (`bash scripts/watcher_supervisor.sh &`) → 旧運用復帰 (dispatcher は並走継続でも問題なし) |
| P5 異常 | git revert で死コード復活 → P4 状態へ |

ロールバックの肝: **P3 期間中は inbox_watcher 側 /clear だけ off にし、配信路 (nudge含) は残す**。これで dispatcher が異常でも nudge が鳴るので silent stuck にならない。

---

## 7. 殿への質問事項

### Q1. CONTEXT-RESET の硬さ

新 task_assigned 受領時の context 整理を「ソフト (Claude が前 task を考慮しない)」と「ハード (/clear で context 全消去)」のどちらを既定にするか。

- ハード /clear の利点: 確実に前 task の影響を排除
- ソフトの利点: 直前会話 (殿との対話) を残せる・compaction 直後の二重リセット回避
- 推奨: **既定ソフト・instructions YAML に `hard_reset_on_task_assigned: true` フラグで cmd 個別に上書き可能**

### Q2. dispatcher の SPOF 許容度

現行 9 daemon は分散 SPOF。D案 1 daemon は集中 SPOF。systemd auto-restart で十分とみなすか、それとも standby (active-passive) を要件にするか。

- 推奨: **systemd Restart=always のみで開始・実運用で停止頻度が問題になれば standby 追加**

### Q3. nudge (`inboxN` 文字列送信) の完全廃止

A 案/D 案で nudge 概念は不要。だが「Claude が SSE event を見落とした時の保険として nudge を残すか」という意見もありうる。

- 推奨: **完全廃止**。SSE が steady-state 100% (cmd_1649 Round 2 実証済) なので保険過剰。残すと B3 暴走再発リスク復活

### Q4. inbox_watcher.sh の段階廃止 vs 即時廃止

P3 (dispatcher 並走) を経由するか、cmd_1650 完走後に即時 P4 (watcher 一掃) に飛ぶか。

- 推奨: **P3 経由必須**。cmd_1650 で SSE 配信確認済でも dispatcher (新規実装) は実戦未経験のため、1 週間並走で safety net 維持

### Q5. server.py の SSE multiplex 改修可否

dispatcher が「全 9 agent 分の SSE を 1 つの fanout endpoint で受ける」と省コネクション。だが server.py 側に `?agent=__dispatcher__` 等 fanout 仕様の追加実装が必要。

- 推奨: **MVP では `?agent=X` × 9 並列 curl で十分** (リソース消費は接続数9 = 軽微)。fanout は後日改善 (P5 以降)

### Q6. cmd_1668 で報告した dual-path 整合崩壊の同時対応

watcher 廃止と並行して inbox_messages.type CHECK 制約への `error_report` / `ntfy_received` / `nightly_audit` 追加 (cmd_1668 C1) を P0 に組み込むべきか。

- 推奨: **YES**。watcher 改修中に SQLite 側の変更を行うと 2 軸変更で原因切り分け困難。P0 前 (今週中) に CHECK 修正 cmd を別途起票して片付けるのが安全

---

## 8. dashboard.md 更新事項 (家老引継ぎ)

本書を受領後、家老には以下を 🚨要対応セクションに反映いただきたい:

```
- cmd_1669 軍師設計書受領 (2026-05-09): D案 (SSE+1 dispatcher) 推奨。殿質問 Q1-Q6 判断要。
  → queue/reports/2026-05-09_cmd_1669_watcher_replacement_design.md 参照
```

---

## 9. メタ情報

- **参照済**:
  - `scripts/inbox_watcher.sh` (主要関数全文・cmd_1668 で精読済)
  - `scripts/stop_hook_inbox.sh`
  - `scripts/dashboard/server.py` (SSE 関連 L43, L2516-2584, L3203 周辺)
  - `queue/reports/2026-05-06_cmd_1649_phase2_observation.md` (Phase 2 観察結果)
  - cmd_1648 / cmd_1649 / cmd_1650 詳細
  - cmd_1668 軍師矛盾検出レポート (本書姉妹文書・C3/C4 の watcher SQLite 整合崩壊指摘)
- **advisor() 呼出**: 本書執筆完了直前 1 回 (最終ポリッシュ確認)。なお姉妹文書 cmd_1668 では計 2 回呼出済
- **未確認事項**: server.py SSE multiplex 改修の実装難易度 (Q5 関連) — P1 で詳細評価予定
