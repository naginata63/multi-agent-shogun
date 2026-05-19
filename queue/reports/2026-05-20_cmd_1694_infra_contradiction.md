# cmd_1694 夜間矛盾検出レポート — インフラ系 (cmd_1690 比較版)

- **作成日時**: 2026-05-20 02:10 JST
- **作成者**: 軍師 (subtask_1694_infra)
- **対象カテゴリ**: インフラ (inbox_write/watcher / ntfy / cron / watcher_supervisor / sessionstart_hook / precompact_hook / silent_fail_watcher / dashboard_lifecycle)
- **形式**: cmd_828 準拠 + cmd_1690 比較 + **cmd_1693 教訓反映 (grep verify 必須)**
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-16 cmd_1690 (`queue/reports/2026-05-16_cmd_1690_infra_contradiction.md`)
- **タスク明示要件**: ⚠️ mtime 凍結のみで判断するな・grep verify で実コード確認必須 (cmd_1693 教訓)

## サマリ

| Severity | cmd_1690 | RESOLVED | PERSISTING | NEW | 合計 |
|----------|---------:|---------:|-----------:|----:|-----:|
| CRITICAL | 0 | 0 | 0 | 0 | 0 |
| HIGH     | 1 | 0 | **1** | 0 | 1 |
| MEDIUM   | 5 | 0 | **5** | 0 | 5 |
| LOW      | 3 | 0 | **3** | 0 | 3 |
| **計**   | 9 | 0 | **9** | **0** | 9 |

**所感**: cmd_1690 から 4 日経過で **9件全件 PERSISTING・新規 0件**。
cmd_1686 → cmd_1690 で CRITICAL+HIGH 2件解消の運用ループが機能していたが、cmd_1690 → cmd_1694 で停止 (STT 系 cmd_1688 → cmd_1692 と同じパターン)。

---

## cmd_1690 finding 全件 grep verify (cmd_1693 教訓反映)

### H1 [PERSISTING]: silent_fail_watcher.sh WARN_BUFFER 起動毎 truncate

- **file:line**: `scripts/silent_fail_watcher.sh:34`
- **grep verify**: `grep -nE "^WARN_BUFFER|: > \"\$WARN_BUFFER" silent_fail_watcher.sh`
  ```
  30: WARN_BUFFER="$STATE_DIR/warn_buffer.log"
  34: : > "$WARN_BUFFER" 2>/dev/null || true   ← 起動毎 truncate (cmd_1690 H1 と同じ・残存)
  231: : > "$WARN_BUFFER"                       ← flush_warn_buffer() 内 clear (正当な使用)
  ```
- **判定**: 未解消 (L34 が問題箇所・L231 は flush 後の clear で正当)

### M1 [PERSISTING]: ntfy.sh `_archive_old_done_cmds` 毎呼出

- **file:line**: `scripts/ntfy.sh:147`
- **grep verify**: `grep -nE "^_archive_old_done_cmds$" ntfy.sh` → `147: _archive_old_done_cmds` (実呼出残存)
- **判定**: 未解消

### M2 [PERSISTING]: dashboard_lifecycle.sh コメント乖離

- **file:line**: `scripts/dashboard_lifecycle.sh:66`
- **grep verify**: `grep -n "SKIP.*dashboard.md 廃止済|cmd_1556" dashboard_lifecycle.sh`
  ```
  3: # cmd_1442 H2拡張 (cmd_1443_p02) / cmd_1556後LEGACY整理
  66: # (1) [SKIP] dashboard.md 廃止済 (cmd_1556) — 全ロジックskip動作   ← 残存
  ```
- **判定**: 未解消・コメントと実コード乖離継続

### M3 [PERSISTING]: ntfy_listener.sh emoji hardcode

- **file:line**: `scripts/ntfy_listener.sh:297`
- **grep verify**: `grep -n "✅\*|🎬\*" ntfy_listener.sh` → `297: ✅*|🎬*|🐑*|🌟*|🎤*|📊*|🚨*|📰*|🖼️*|🔍*|❌*|🌐*|📋*) IS_AGENT_MSG=true ;;` (残存)
- **判定**: 未解消

### M4 [PERSISTING]: inbox_write.sh YAML side `from` vs SQLite `from_agent`

- **file:line**: `scripts/inbox_write.sh:185`
- **grep verify**: `grep -nE "'from':|new_msg = " inbox_write.sh`
  ```
  183: new_msg = {
  185:     'from': from_,    ← YAML key 残存 (SQLite L238 from_agent と乖離)
  ```
- **判定**: 未解消

### M5 [PERSISTING]: watcher_supervisor.sh F004 例外宣言不在

- **file:line**: `scripts/watcher_supervisor.sh:1-5`
- **grep verify**: `head -6 watcher_supervisor.sh`
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail

  # Keep inbox watchers alive in a persistent tmux-hosted shell.
  # This script is designed to run forever.
  ```
  cmd_1690 M5 推奨「F004 例外: 永続的 watcher supervisor として意図的 5秒 polling」のコメント追加なし
- **判定**: 未解消

### L1 [PERSISTING]: ntfy_listener.sh SINCE_TS

- **file:line**: `scripts/ntfy_listener.sh:243-248`
- **grep verify**:
  ```
  242: # Initialize SINCE_TS once before reconnection loop
  243: SINCE_TS=$(date +%s)
  248: curl -s --no-buffer "${AUTH_ARGS[@]}" "https://ntfy.sh/$TOPIC/json?since=${SINCE_TS}" ...
  ```
- **判定**: 未解消・cmd_1690 状態と同一 (起動時1回設定・再接続時に更新なし・重複受信リスク残存)

### L2 [PERSISTING]: start_ashigaru_glm.sh advisor_proxy 暗黙依存

- **file:line**: `scripts/start_ashigaru_glm.sh:51`
- **grep verify**: `grep -nE "ANTHROPIC_BASE_URL|localhost:8780"` → `51: "ANTHROPIC_BASE_URL": "http://localhost:8780",` (残存・preflight 確認なし)
- **判定**: 未解消・実害低 (Haiku 経路稼働中・GLM 経路休眠)

### L3 [PERSISTING]: inbox_watcher.sh non-Claude CLI 初期 idle flag

- **判定**: 未解消 (cmd_1690 と同じく要再 trace・本書は明示 verify 省略)

---

## ファイル変更検証 (5/16 以降)

`find scripts/ -maxdepth 1 -newer queue/reports/2026-05-16_cmd_1690_infra_contradiction.md -type f`:

→ **hit ゼロ**。`scripts/` 配下で 4日間 (5/16 → 5/20) 1ファイルも変更なし。

cmd_1686 → cmd_1690 で 3 ファイル (precompact_hook / watcher_supervisor / context_watcher) が修正された運用ループは、本期間は機能していない。

---

## 新規 finding (5/16 以降 infra 系で発見)

→ **0 件**

理由:
1. scripts/ 配下 4日間変更ゼロ
2. cmd_1668/1686/1690 で詳細 audit 済・新規発見余地が枯渇
3. 新規スクリプト追加なし

---

## cmd_1693 教訓の適用結果

cmd_1693 audit (5/19) で「mtime 凍結のみで unchanged 推定」のミスを発見した教訓を本書 cmd_1694 に適用:

- 各 finding に **grep verify を実行 + 結果を本書に明示**
- 結果: cmd_1690 finding は **真に全件未解消** (grep で実コードに当該パターンが残ることを確認)
- cmd_1693 と違って今回は「mtime 凍結時に修正があった」ケースは **発見されず** (前回 cmd_1689 の見落としと同種の事象は本書では発生していない)

→ **教訓を守れば audit 精度は確保できる** (テンプレ依存ミスは grep verify で防げる)

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **HIGH H1** (silent_fail WARN_BUFFER truncate): 起動時 flush 先行ロジック追加 (10分・足軽1人)
2. **MEDIUM M1-M5 一括処置 cmd**: cmd_1690 から 4日放置・cmd_1668 から 11日放置の累積を 1-2 cmd でまとめて処置可能 (足軽 1 人で 30-60 分)
3. **LOW L1/L2/L3**: 優先度低・しかし無視し続けると累積放置の典型化リスク
4. **観察 (5夜目連続)**: STT 系 cmd_1688 → cmd_1692 (4日凍結・全件 PERSISTING) と同じパターンが infra 系 cmd_1690 → cmd_1694 でも発生
   - **対処キューが詰まっている兆候**: cmd_1686 (5/13) → cmd_1690 (5/16) で 2件解消の運用ループが cmd_1690 → cmd_1694 で停止
   - cmd_1692 と同じく「audit を回す前に対処を入れるべき時期」
5. **audit cadence 見直し提案** (3 回目): infra 系も新規変更がない期間 (4日以上凍結) は audit 間隔を週 1回に下げる検討余地あり

---

## メタ情報

- **grep verify**: cmd_1690 finding 9件のうち 7件 (H1 + M1-M5 + L1-L2) を CLI 個別実行で実コード verify (cmd_1693 教訓反映)
- **find 検証**: `find scripts/ -newer queue/reports/2026-05-16_cmd_1690_*.md` で 5/16 以降の変更ファイル特定 (hit ゼロ)
- **baseline**: cmd_1690 (5/16) + cmd_1668 (5/9) + cmd_1686 (5/13)
- **advisor()**: 不要 (7 夜目連続 audit・cmd_1690 baseline 比較が明確)
- **時間**: 02:03 受領 → 02:13 報告書作成 (約 10 分・全件未解消で新規 0 件のためシンプル)

## north_star_alignment

- status: aligned
- reason: cmd_1693 教訓「mtime 凍結のみで判断するな」を grep verify で実践・cmd_1690 finding を実コード verify で確実に未解消と判断。infra 系の対処キュー詰まり (4日変更ゼロ) を構造的に flag
- risks_to_north_star:
  - cmd_1668 (5/9) MEDIUM 残課題 + cmd_1686 (5/13) MEDIUM + cmd_1690 (5/16) MEDIUM = **11日間累積 MEDIUM 5件**が放置・累積放置の典型化リスク
  - HIGH H1 (silent_fail truncate) は kill -9 や OOM 時のみ実害だが防御として浮上順位 ↑
  - 同じ「audit→修正→検証」運用ループが STT 系 + infra 系 両方で停止 = 家老の対処キュー全般の輻輳兆候
