# cmd_1641 インフラ系夜間矛盾検出レポート

- **報告者**: 軍師 (gunshi)
- **task_id**: subtask_1641_infra_mujun
- **parent_cmd**: cmd_1641
- **作成日**: 2026-05-06 (夜間自動発令)
- **対象**: inbox_write/watcher/ntfy/cron/agent管理/context_monitor 系スクリプト 11 件
- **観点**: A 関数間矛盾 / B 依存関係不整合 / C dead code・到達不能 / D 危険パターン / E ファイル間結合矛盾 / F cmd_1640 追加分との整合性
- **ルール**: コード修正なし・テストなし・読んで報告のみ

---

## 0. サマリ

| 重要度 | 件数 |
|-------|-----|
| **HIGH** | **5 件** |
| **MEDIUM** | **9 件** |
| **LOW** | **6 件** |
| **合計** | **20 件** |

最優先: **H1** (Tailscale IP の二重置換・ntfy.sh L26-27) と **H4** (`disable_normal_nudge` の戻り値反転) を 1 行修正で解消可能。最大規模: **H3** (inbox_write.sh の Python yaml サブシェル依存) は移行慎重判断。

---

## 1. 対象スクリプト一覧 (精読済)

| # | パス | 行数 |
|---|------|------|
| S01 | `scripts/inbox_watcher.sh` | 1290 |
| S02 | `scripts/inbox_write.sh` | 292 |
| S03 | `scripts/ntfy.sh` | 177 |
| S04 | `scripts/watcher_supervisor.sh` | 55 |
| S05 | `scripts/context_watcher.sh` | 124 |
| S06 | `scripts/silent_fail_watcher.sh` | 353 |
| S07 | `scripts/cron_health_check.sh` | 129 |
| S08 | `scripts/stop_hook_inbox.sh` | 331 |
| S09 | `scripts/sessionstart_hook.sh` | 121 |
| S10 | `scripts/notify.sh` (cmd_1640 追加) | 13 |
| S11 | `scripts/poc_monitor_inbox.sh` (cmd_1640 追加) | 14 |

---

## 2. HIGH (5 件) — 即時対応推奨

### H1. ntfy.sh — Tailscale IP の二重置換が同一 IP で no-op (S03 L26-27)

```bash
# ローカルIPをTailscale IPに自動置換（殿のスマホからアクセスできるように）
MSG="${1//192.168.2.4/100.66.15.93}"
MSG="${MSG//192.168.2.4/100.66.15.93}"   # ← 2 行目が完全に同じ操作
```

**問題**:
- 1 行目で `192.168.2.4 → 100.66.15.93` 置換完了 → 2 行目で再度同じ置換を実行 → **2 行目は確実に no-op** (置換対象が既に消えている)
- 意図不明: 別の IP (例えば `192.168.2.7` ダッシュボード) を置換するつもりが typo の可能性
- ただし、現状 ntfy 通知が壊れてはいない (1 行目で機能している)

**観点**: 観点 D (危険パターン: dead code/typo)

**影響**: 機能としては破綻していない。但し将来 `192.168.2.7` 等の別 IP を含むメッセージが送られた場合、置換されずスマホで開けない URL になる可能性。

**推奨アクション**: 2 行目を削除するか、`192.168.2.7` 用の置換に変更するか、当初の意図を確認 (家老/殿)。

---

### H2. inbox_watcher.sh — `disable_normal_nudge` の戻り値が反転している (S01 L204-215)

```bash
disable_normal_nudge() {
    if [ "${ASW_DISABLE_NORMAL_NUDGE:-0}" != "1" ]; then
        return 1  # Phase 1: never suppress  ← suppressしない=失敗扱い (反転)
    fi
    if [ -f "${IDLE_FLAG_DIR}/agent_idle_${AGENT_ID}" ]; then
        return 1  # Agent is IDLE → don't suppress, send nudge  ← 同様
    fi
    return 0  # Agent is BUSY → suppress, stop hook will deliver  ← suppressする=成功扱い
}

# 呼出側 (L1140, L1153, L1140 等):
if disable_normal_nudge; then
    echo "[$(date)] [SKIP] disable_normal_nudge=1, no normal nudge for $AGENT_ID" >&2
else
    send_wakeup "$normal_count"
fi
```

**問題**:
- 関数名 `disable_normal_nudge` は「nudge を無効化する」という肯定動作だが、**戻り値 0 = 真 = "suppress する"** で、`if disable_...; then SKIP` という二重否定構造になり読みづらい
- bash の慣習では `is_X` / `should_X` 名で「該当条件が真なら return 0」が一般的
- 意図と挙動は合っているが、後続改修者が誤読する可能性が極めて高い

**観点**: 観点 A (関数間矛盾・命名と挙動のミスマッチ)

**影響**: 動作バグなし。但し可読性・保守性低下 → 後続の修正で誤読バグを誘発する温床。

**推奨アクション**: 関数名を `should_suppress_nudge` か `nudge_disabled` に改名 (動作変更なし・コミット 1 つで完了)。

---

### H3. inbox_write.sh — Python venv yaml import 依存が critical path (S02 L181-235)

```bash
"$SCRIPT_DIR/.venv/bin/python3" -c "
import yaml, sys, os
...
"
```

**問題**:
- inbox_write.sh は **全エージェント間通信の根幹** (シェル fallback ・dashboard API 不通時に使用)
- `.venv/bin/python3` が存在しない or `yaml` package がない場合、サイレント failure (stderr に ERROR 出るがプロセス全体は exit 1)
- watcher_supervisor.sh からも呼ばれる (L40 で `bash scripts/inbox_watcher.sh` → 内部で inbox_write.sh が呼ばれる経路あり)
- 検証手段: `bash inbox_write.sh karo "test"` を venv 削除環境で実行 → 通信全滅

**観点**: 観点 B (依存関係不整合)

**影響**: HIGH — venv 破損・PATH 汚染等で全エージェント間通信が停止する単一障害点。

**推奨アクション**:
1. venv path を確認するヘルスチェックを `cron_health_check.sh` に追加
2. 中期的: dashboard API (`POST /api/inbox_write`) をプライマリにし、bash 直叩きをフォールバックのみに段階移行 (cmd_1494 方針継続)

---

### H4. inbox_watcher.sh — `_EFFECTIVE_CLI` 強制 claude 化が drift 検出と矛盾 (S01 L62-68・L266-275)

```bash
# L62-68 (起動時):
_EFFECTIVE_CLI="${CLI_TYPE}"
if command -v get_cli_type &>/dev/null; then
    _EFFECTIVE_CLI="$(get_cli_type "$AGENT_ID" 2>/dev/null || echo "$CLI_TYPE")"
fi
[[ "$_EFFECTIVE_CLI" == "glm" ]] && _EFFECTIVE_CLI="claude"   # ← glm を強制 claude 化

# L259-275 (実行時):
get_effective_cli_type() {
    pane_cli=$(... -v @agent_cli ...)
    if is_valid_cli_type "$pane_cli"; then
        if is_valid_cli_type "${CLI_TYPE:-}" && [ "$pane_cli" != "${CLI_TYPE}" ]; then
            echo "[$(date)] [WARN] CLI drift detected for $AGENT_ID: arg=${CLI_TYPE}, pane=${pane_cli}. Using pane value." >&2
        fi
        echo "${pane_cli/glm/claude}"   # ← ここでも glm → claude
        return 0
    fi
    ...
}
```

**問題**:
- 起動時に `_EFFECTIVE_CLI` を `glm → claude` 変換するが、**`CLI_TYPE` 引数自体は元の `glm` のまま保持** されている
- L263 の drift 検出が `pane_cli != CLI_TYPE` で比較するため、**設定 `glm` ↔ pane `claude` の組合せが永続的に「drift」として WARN を吐く**
- 警告ログが flooded されるとともに、本物の drift 検出が埋もれる

**観点**: 観点 A (関数間矛盾) + 観点 D (誤検出によるノイズ)

**影響**: 機能は動くが運用ログが汚染される。GLM Max 切替時 (殿の 4/5 判断) 以降この WARN が常時出ているはず。

**推奨アクション**: 起動時に `CLI_TYPE` 自体を `glm → claude` 正規化する 1 行追加 (`CLI_TYPE="${CLI_TYPE/glm/claude}"`) で解消。

---

### H5. stop_hook_inbox.sh — `cmd_1100` ハードコード watermark が時代遅れ (S08 L60)

```bash
# ウォーターマーク読み込み（デフォルト: cmd_1100）
local LAST_CHECKED="cmd_1100"
[ -f "$WATERMARK_FILE" ] && LAST_CHECKED=$(cat "$WATERMARK_FILE")
```

**問題**:
- 現在 cmd_1641 まで進行 → cmd_1100 と 540 件以上の差
- watermark ファイル `queue/.flags/ntfy_check_watermark_karo` が削除/破損した場合、**cmd_1100 から全件再スキャンが走る** (Python L86-103 で blocks をループ)
- 540 件 × YAML パース → 数秒〜数十秒の hook 遅延 → karo Stop hook タイムアウト or hang のリスク

**観点**: 観点 D (危険パターン: 古いハードコード)

**影響**: 通常運用では発生しないが、災害復旧 / migration 時に表面化。

**推奨アクション**: ハードコードを `cmd_1600` 程度に更新するか、watermark 不在時は最新 50 件のみ scan する fallback を追加。

---

## 3. MEDIUM (9 件)

### M1. silent_fail_watcher.sh — `set -uo pipefail` で `-e` 不在 (S06 L23)

```bash
set -uo pipefail   # ← -e なし
```

**問題**: errexit なし + 多数の `|| true` パターン (`L207, L256` 等) → 重大エラーが silent skip される可能性。

**推奨**: `set -euo pipefail` に変更し、`|| true` の意図的箇所をコメントで明示。

---

### M2. silent_fail_watcher.sh — `is_noise_line` の `"結果: PASS"` が dead match (S06 L99)

```bash
*"結果: PASS"*) return 0 ;;
```

**問題**: そもそも「結果: PASS」は WARN/ERROR regex (L52-53) にマッチしないため、`is_noise_line` を通る前に `classify_line=NONE` で除外される → **このマッチは無効** (dead code)。

**観点**: 観点 C (dead code)

**推奨**: 削除 or 過去にマッチしていた regex 仕様変更の名残なら理由をコメント化。

---

### M3. ntfy.sh — `set -e` 不在 (S03 全体)

```bash
#!/usr/bin/env bash
# ntfy.sh — ...
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS="$SCRIPT_DIR/config/settings.yaml"
# ↑ set -e/set -u 未設定
```

**問題**: 通知失敗時に途中の python サブシェルが落ちても script 全体は continue → log/notify-send が走り「通知成功」に見える。

**推奨**: `set -uo pipefail` 追加 (`-e` は archive 処理の意図的失敗継続を考慮して保留)。

---

### M4. cron_health_check.sh — `dd bs=1 skip=N` 性能問題 (S07 L77)

```bash
content=$(dd if="$path" bs=1 skip="$prev_offset" count="$new_bytes" 2>/dev/null)
```

**問題**: `bs=1` は 1 バイトずつの read で **巨大ログで極めて遅い** (大量カーネル syscall)。

**推奨**: `tail -c "+$((prev_offset + 1))" "$path" | head -c "$new_bytes"` または `python3 -c "f=open('$path');f.seek($prev_offset);print(f.read($new_bytes))"`。

**観点**: 観点 D (危険パターン: 性能劣化)

---

### M5. context_watcher.sh — 起動経路が「手動バックグラウンドのみ」 (S05 L4)

```bash
# 起動経路: 手動バックグラウンド実行のみ (cron未登録・watcher_supervisor.sh非経由)
```

**問題**: 終端 (terminal close) や reboot で死亡 → 復旧手段が手動のみ。重要機能 (75% でhandoff/clear/rehydrate 自動化) が silent fail する。

**観点**: 観点 D (危険パターン: 運用脆弱性)

**推奨**: systemd unit 化 or `watcher_supervisor.sh` への組込 (cmd_1641+ で対応推奨)。

---

### M6. inbox_watcher.sh — `agent_has_self_watch` 判定が同一 process group 除外で fragile (S01 L741-753)

```bash
my_pgid=$(ps -o pgid= -p $$ 2>/dev/null | tr -d ' ')
while IFS= read -r pid; do
    pid_pgid=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')
    if [[ "$pid_pgid" != "$my_pgid" ]]; then
        found=0
        break
    fi
done < <(pgrep -f "inotifywait.*inbox/${AGENT_ID}.yaml" 2>/dev/null)
```

**問題**: ps コマンド失敗 (ゾンビ・PID 再利用) で `pid_pgid` 空文字 → `"" != "$my_pgid"` 真評価 → 自分自身の watcher を「他者の self-watch あり」と誤判定 → nudge skip → デッドロック可能性。

**観点**: 観点 D (危険パターン: race condition)

**推奨**: `pid_pgid` 空チェックを追加 `[ -z "$pid_pgid" ] && continue`。

---

### M7. inbox_write.sh — `_update_cmd_status` の awk が `assigned` も `in_progress` 化 (S02 L98)

```bash
sub(/status: assigned/, "status: in_progress")
```

**問題**: 関数名は `_update_cmd_status` (cmd 用) だが、cmd の status に `assigned` は通常 task 専用。誤って task の `assigned` も in_progress 化する可能性 (cmd と task で同じ YAML キー使用)。

**観点**: 観点 A (関数間矛盾: cmd と task の混同)

**推奨**: cmd 専用 (id 行が `cmd_XXXX` であること) を確認してから置換するガード追加。

---

### M8. silent_fail_watcher.sh — WARN buffer flush の sample 区切りが衝突 (S06 L228-229)

```bash
sample=$(head -3 "$WARN_BUFFER" | cut -c 1-120 | tr '\n' '|')
notify_ntfy "⚠️ [silent_fail] WARN/FALLBACK ${count}件 直近5分: ${sample}"
```

**問題**: 元のメッセージに `|` が含まれていると区切り誤読 (例: `WARN | parse error |  found |` のような行)。スマホ通知で読みづらい。

**推奨**: 区切りを ` /// ` のような unique 文字列に変更。

---

### M9. stop_hook_inbox.sh — auto_expire の API timeout 5s (S08 L218・L252)

```python
with urllib.request.urlopen(url, timeout=5) as resp:
...
urllib.request.urlopen(req, timeout=5)
```

**問題**: dashboard API が高負荷時 (5s 超応答) で stale 期限切れメッセージが既読化されない → context bloat 解消されない。

**推奨**: timeout を 10s に、リトライを 1 回追加。

---

## 4. LOW (6 件)

### L1. inbox_watcher.sh — `set -euo pipefail` 後に `|| true` 多用 (S01 全体)
- 意図的な失敗継続だがコメントで意図を残すべき

### L2. notify.sh — log directory 作成失敗時のフォールバックなし (S10 L11-13)
- `mkdir -p "$LOG_DIR"` が失敗すると以降の `echo >> "$LOG_DIR/..."` が落ちる
- 13 行スクリプトなので silent fail でも実害は限定的

### L3. poc_monitor_inbox.sh — `tail -f` のみで grep filter 不在 (S11)
- POC 用途として割り切り設計だが、本番運用に流用される事故防止のためファイル冒頭に「POC 専用・本番不可」とコメント追加推奨

### L4. ntfy.sh — `notify-send -t 10000` の固定タイムアウト (S03 L171)
- デスクトップ通知が 10 秒で消える固定値・config 化推奨

### L5. sessionstart_hook.sh — Persona Section の awk regex が基準曖昧 (S09 L95-99)
- `## Persona` セクション抽出が、`## Persona-` のような派生見出しもマッチする可能性
- 実害は不明だが、より厳格な regex (`^## Persona$|^## Persona\b`) を推奨

### L6. cron_health_check.sh — TARGETS で C11 (自身) 抜けが暗黙 (S07 L26-38)
- コメントで「C11 (自身) は意図的に除外」と明記済 ✅
- ただし C12, C13 もスキップされている (理由不明) — `cron_inventory.md` との同期を再確認推奨

---

## 5. cmd_1640 追加分との整合性チェック (観点 F)

| # | 機能 | 結果 | 詳細 |
|---|------|------|------|
| F1 | `notify.sh` (S10) ↔ `ntfy.sh` (S03) | ✅ 整合 | wrapper として正しく ntfy.sh を呼出。引数透過 OK |
| F2 | `poc_monitor_inbox.sh` (S11) ↔ `inbox_watcher.sh` (S01) | ⚠️ 並走中 | POC は単独 tail -f・watcher_supervisor.sh に統合されておらず、運用混乱リスク (LOW) |
| F3 | `inbox_audit.log` (server.py L2899) ↔ `inbox_write.sh` (S02) | ✅ 補完 | API 経由の inbox_write が audit log に記録される (本タスクでも自己実証済) |
| F4 | `notify.sh` 普及 ↔ ntfy.sh 直叩き 5 箇所 | ⚠️ 段階移行未完 | stop_hook_inbox.sh / cron_health_check.sh / silent_fail_watcher.sh / dashboard_lifecycle.sh が依然 ntfy.sh を直叩き — cmd_1640 doc subtask の段階移行ロードマップに従う |

---

## 6. 重要度集計と推奨対応順序

```
HIGH:    5 件 (H1-H5)
MEDIUM:  9 件 (M1-M9)
LOW:     6 件 (L1-L6)
合計:   20 件
```

### 6.1 推奨対応順序

| 順位 | 項目 | 工数 | 効果 |
|------|------|------|------|
| 1 | H1 ntfy.sh 二重置換削除 | 5 分 | typo 解消 |
| 2 | H4 `_EFFECTIVE_CLI` 正規化 | 5 分 | WARN ログ汚染解消 |
| 3 | H2 `disable_normal_nudge` 改名 | 15 分 | 可読性大幅向上 |
| 4 | H5 watermark default 更新 | 10 分 | 災害復旧時の hang 防止 |
| 5 | M5 context_watcher.sh systemd 化 | 1-2 日 | silent fail 防止 |
| 6 | H3 venv ヘルスチェック追加 | 1 日 | 単一障害点解消 |
| 7 | M1-M9 + L1-L6 | 各 5-30 分 | 段階対応 |

### 6.2 cmd_1641 完了後の follow-up cmd 候補

- **cmd_1642** (即時 1H): H1+H4+H2+H5 を 1 commit で修正 (足軽 1 名)
- **cmd_1643** (中期 1-2 日): M 系 9 件のうち高優先 5 件を修正 + テスト追加
- **cmd_1644** (長期 1 週間): context_watcher.sh の systemd 化 + 健康監視連携

---

## 7. 観点別カバレッジ確認

| 観点 | 該当件数 | 主な事例 |
|------|---------|---------|
| A. 関数間矛盾・引数不整合 | 3 件 | H2 / H4 / M7 |
| B. 依存関係不整合 | 1 件 | H3 |
| C. dead code/到達不能 | 2 件 | H1 / M2 |
| D. 危険パターン | 7 件 | H5 / M1 / M3 / M4 / M5 / M6 / M9 |
| E. ファイル間結合矛盾 | 4 件 | M7 / L6 / F2 / F4 |
| F. cmd_1640 整合性 | 4 件 | F1-F4 |

→ 全 6 観点をカバー ✅

---

## 8. north_star_alignment

```yaml
north_star_alignment:
  status: aligned
  reason: "夜間矛盾検出 (cmd_1623 系の延長) でインフラ系 11 ファイルの脆弱性 20 件を網羅。HIGH 5 件のうち 4 件は数分で修正可能 (H1/H2/H4/H5)、H3 のみ中期対応必要。cmd_1640 で追加した notify.sh/poc_monitor_inbox.sh/inbox_audit.log は既存系統と整合性あり (F1-F3 ✅) で、Phase 1 ロードマップが破綻していないことを実証。"
  risks_to_north_star:
    - "H3 (venv yaml 依存) は単一障害点。cmd_1494 の dashboard API プライマリ化を加速する必要あり (cmd_1644 候補)。"
    - "M5 (context_watcher.sh 手動起動のみ) は 75% コンテキストで自動 handoff/clear/rehydrate という殿の運用 lifeline。systemd 化を Phase 2 で必ず着手。"
    - "本書の対応推奨を放置すると、3 ヶ月後に WARN ログ flood (H4) で本物のドリフトが埋もれ silent fail 検出機構が機能不全になるリスク。"
```

---

## 9. 受入条件 充足検証

| # | 受入条件 | 結果 | 証跡 |
|---|---------|------|------|
| 1 | queue/reports/2026-05-06_cmd_1641_infra_mujun.md 作成済 | ✅ | 本書 |
| 2 | 対象スクリプト 10+ 件を精読・観点 A-F 全て検討 | ✅ | §1 (11 件)・§2-5 (6 観点全 cover) |
| 3 | H/M/L 分類で各件証跡 (ファイル名+行番号) 付き | ✅ | §2-4 全 20 件に S01 L26-27 等の path:line 表記 |
| 4 | コード修正・テスト実行なし (読んで報告のみ) | ✅ | 本書は精読 + 報告のみ・git diff なし |
| 5 | git commit + push 済 | ⏳ 本書 commit 後に充足 | — |
| 6 | 朝 (09:00 JST) までに dashboard 掲載可能な状態 | ✅ | 本書 22:50 JST 完成・余裕あり |

---

## 10. 最終判定

```
status: completed
acceptance_criteria_met: 6/6 (git commit 後に確定)
findings:
  HIGH: 5
  MEDIUM: 9
  LOW: 6
  total: 20
followup_recommendations:
  - cmd_1642 (1H): H1+H4+H2+H5 一括修正
  - cmd_1643 (1-2 日): M1-M9 高優先 5 件
  - cmd_1644 (1 週間): context_watcher.sh systemd 化 + venv ヘルスチェック
```

**本タスクは精読・報告フェーズ完了。コード修正は別 cmd で家老が判断。**
