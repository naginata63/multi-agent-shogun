#!/usr/bin/env bash
# dashboard_lifecycle.sh — cmd_1442 H2拡張 (cmd_1443_p02)
#
# 目的:
#   (1) dashboard.md 🚨要対応セクションの「解決済」残骸行を自動アーカイブ＋削除
#   (2) MCPダッシュボード (http://192.168.2.7:8770/api/dashboard) の残骸
#       (action_required に cmd_id があるのに recent_done に同一 cmd_id がある状態)
#       を検出し、家老に ntfy で削除依頼通知
#
# 設計メモ:
#   - plan v3 §3 Δ2 では /api/tasks と記載だが実機は /api/dashboard のみ (/api/tasks は 404)
#     → hotfix_notes に記録 (cmd_1443_p02 報告参照)
#   - dashboard.md の ✅ は進行中セクションでも多用される (live tracking data)。
#     従って「~~strikethrough~~ かつ 解決済/解消済 キーワードを含む行」のみ対象
#   - 削除前に dashboard_archive/$(date +%Y-%m).md へ append (監査証跡)
#   - flock で dashboard.md への同時書込みを防止
#
# Usage:
#   bash scripts/dashboard_lifecycle.sh [--dry-run] [--verbose]
#
# Cron:
#   既存 nightly_audit (02:02) から呼び出される

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD_MD="${SCRIPT_DIR}/dashboard.md"
ARCHIVE_DIR="${SCRIPT_DIR}/dashboard_archive"
LOG_FILE="${SCRIPT_DIR}/logs/dashboard_lifecycle.log"
MCP_URL="http://192.168.2.7:8770/api/dashboard"
NTFY="${SCRIPT_DIR}/scripts/ntfy.sh"

DRY_RUN=0
VERBOSE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --immediate) : ;;
    --verbose) VERBOSE=1 ;;
    -h|--help)
      sed -n '1,30p' "$0"
      exit 0
      ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")" "$ARCHIVE_DIR"

log() {
  local msg="[$(date '+%Y-%m-%dT%H:%M:%S%z')] $*"
  echo "$msg" >> "$LOG_FILE"
  [[ $VERBOSE -eq 1 ]] && echo "$msg"
}

ntfy_best_effort() {
  local msg="$1"
  if [[ -x "$NTFY" ]]; then
    bash "$NTFY" "$msg" >/dev/null 2>&1 || log "WARN: ntfy failed (ignored): $msg"
  else
    log "WARN: ntfy not executable at $NTFY (skipped)"
  fi
}

log "=== dashboard_lifecycle start (dry_run=${DRY_RUN}) ==="

# ─────────────────────────────────────────────────────────────
# (1) dashboard.md 解決済み残骸クリーン
# ─────────────────────────────────────────────────────────────

clean_dashboard_md() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    log "dashboard.md not found at $DASHBOARD_MD (skip)"
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local cleaned_count=0
  local tmp_output
  tmp_output="$(mktemp)"
  local removed_lines
  removed_lines="$(mktemp)"
  local count_file
  count_file="$(mktemp)"

  # 抽出ルール: ~~...~~ と 解決済/解消済 の両方を含む行だけ削除対象
  # ただし「## 」「### 」で始まる見出し行は除外 (セクション全体を消さない)
  # また 🚨 要対応セクション内でのみ適用 (安全側)
  awk -v REMOVED_FILE="$removed_lines" '
    BEGIN {
      in_action_section = 0
      cleaned = 0
    }
    {
      line = $0

      # セクション判定
      if (line ~ /^## /) {
        if (line ~ /要対応/) {
          in_action_section = 1
        } else {
          in_action_section = 0
        }
        print line
        next
      }

      # 要対応セクション内かつ strikethrough+解決済/解消済 を両方含む非見出し行だけ削除
      if (in_action_section == 1 \
          && line !~ /^#/ \
          && line ~ /~~/ \
          && (line ~ /解決済/ || line ~ /解消済/)) {
        printf "%s\n", line >> REMOVED_FILE
        cleaned++
        next
      }

      print line
    }
    END {
      print cleaned > "/dev/stderr"
    }
  ' "$DASHBOARD_MD" > "$tmp_output" 2> >(read n; echo "$n" > "$count_file"; wait)

  wait
  cleaned_count="$(cat "$count_file" 2>/dev/null || echo 0)"
  rm -f "$count_file"

  if [[ "$cleaned_count" == "0" ]]; then
    log "dashboard.md: no resolved stragglers found"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "dashboard.md: ${cleaned_count} resolved straggler line(s) detected"

  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN: would archive to ${month_archive}"
    log "DRY-RUN: removed lines preview:"
    while IFS= read -r l; do log "  - ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  # Archive 追記 (監査証跡)
  {
    echo ""
    echo "## Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z') by dashboard_lifecycle.sh"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  # flock で dashboard.md を保護しながら差し替え
  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "dashboard.md: cleaned ${cleaned_count} line(s), archived to ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}

clean_dashboard_md || log "ERROR in clean_dashboard_md (continuing)"

# ─────────────────────────────────────────────────────────────
# (2.5) 進行中テーブルの✅完了行を削除
# ─────────────────────────────────────────────────────────────

clean_inprogress_table() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    log "dashboard.md not found (skip clean_inprogress_table)"
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local tmp_output removed_lines count_file
  tmp_output="$(mktemp)"
  removed_lines="$(mktemp)"
  count_file="$(mktemp)"

  awk -v REMOVED_FILE="$removed_lines" '
    BEGIN { in_inprogress = 0; cleaned = 0 }
    {
      line = $0

      # セクション判定
      if (line ~ /^## /) {
        if (line ~ /進行中/) {
          in_inprogress = 1
        } else {
          in_inprogress = 0
        }
        print line
        next
      }

      # 進行中セクション内のテーブル行で✅を含む行を削除対象とする
      # 除外条件:
      #   - 足軽/軍師ステータス行: | [0-9]号 | パターン
      #   - 仕切り行: |---
      #   - ヘッダ行: cmd_id|担当|状態 等のテキスト（✅を含まない）
      if (in_inprogress == 1 \
          && line ~ /^\|/ \
          && line ~ /✅ \*\*/ \
          && line !~ /^\|[-]+/ \
          && line !~ /^\| *[0-9]号 *\|/ \
          && line !~ /^\| *足軽 *\|/ \
          && line !~ /^\| *軍師 *\|/) {
        printf "%s\n", line >> REMOVED_FILE
        cleaned++
        next
      }

      print line
    }
    END { print cleaned > "/dev/stderr" }
  ' "$DASHBOARD_MD" > "$tmp_output" 2> >(read n; echo "$n" > "$count_file"; wait)

  wait
  local cleaned_count
  cleaned_count="$(cat "$count_file" 2>/dev/null || echo 0)"
  rm -f "$count_file"

  if [[ "$cleaned_count" == "0" ]]; then
    log "進行中テーブル: 完了✅行なし (skip)"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "進行中テーブル: ${cleaned_count} 件の✅完了行を検出"

  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN: 以下の行を削除予定:"
    while IFS= read -r l; do log "  - ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  # アーカイブ追記
  {
    echo ""
    echo "## 進行中テーブル✅完了行 Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z')"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  # flock保護で差し替え
  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "進行中テーブル: ${cleaned_count} 件削除・アーカイブ済み → ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}

# ─────────────────────────────────────────────────────────────
# (2.7) 「本日の完了」セクションの24h超過分アーカイブ
# ─────────────────────────────────────────────────────────────

clean_daily_completed_section() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local now_ts
  now_ts="$(date +%s)"
  local cutoff_ts=$(( now_ts - 86400 ))  # 24h前

  local tmp_output removed_lines count_file
  tmp_output="$(mktemp)"
  removed_lines="$(mktemp)"
  count_file="$(mktemp)"

  awk -v REMOVED_FILE="$removed_lines" -v CUTOFF="$cutoff_ts" '
    BEGIN { in_daily = 0; cleaned = 0 }
    {
      line = $0

      if (line ~ /^## /) {
        if (line ~ /本日の完了/) {
          in_daily = 1
          print line
          next
        } else {
          in_daily = 0
        }
        print line
        next
      }

      if (in_daily == 1) {
        # 日付パターン YYYY-MM-DD を検索
        if (match(line, /[0-9]{4}-[0-9]{2}-[0-9]{2}/)) {
          date_str = substr(line, RSTART, RLENGTH)
          cmd = "date -d " date_str " +%s 2>/dev/null"
          cmd | getline line_ts
          close(cmd)
          if (line_ts != "" && line_ts+0 < CUTOFF+0) {
            printf "%s\n", line >> REMOVED_FILE
            cleaned++
            next
          }
        }
        # 日付なし行はそのまま保持
        print line
        next
      }

      print line
    }
    END { print cleaned > "/dev/stderr" }
  ' "$DASHBOARD_MD" > "$tmp_output" 2> >(read n; echo "$n" > "$count_file"; wait)

  wait
  local cleaned_count
  cleaned_count="$(cat "$count_file" 2>/dev/null || echo 0)"
  rm -f "$count_file"

  if [[ "$cleaned_count" == "0" ]]; then
    log "本日の完了セクション: 24h超過行なし (skip)"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "本日の完了セクション: ${cleaned_count} 件の24h超過行を検出"

  if [[ $DRY_RUN -eq 1 ]]; then
    while IFS= read -r l; do log "DRY-RUN:  - ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  {
    echo ""
    echo "## 本日の完了セクション24h超過分 Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z')"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "本日の完了セクション: ${cleaned_count} 件削除 → ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}

clean_inprogress_table || log "ERROR in clean_inprogress_table (continuing)"
clean_daily_completed_section || log "ERROR in clean_daily_completed_section (continuing)"

# ─────────────────────────────────────────────────────────────
# (2) MCP ダッシュボード残骸検出 → ntfy 通知
# ─────────────────────────────────────────────────────────────

check_mcp_stragglers() {
  local body
  body="$(curl -sS --max-time 10 --fail "$MCP_URL" 2>/dev/null)" || {
    log "WARN: MCP dashboard unreachable at $MCP_URL"
    return 0
  }

  if ! command -v python3 >/dev/null 2>&1; then
    log "WARN: python3 not available (skip MCP check)"
    return 0
  fi

  local py_script
  py_script="$(mktemp --suffix=.py)"
  cat > "$py_script" <<'PYEOF'
import json, sys
try:
    d = json.loads(sys.stdin.read() or "{}")
except Exception as e:
    print("PARSE_ERROR: " + str(e), file=sys.stderr)
    sys.exit(0)

action = d.get("action_required") or []
recent_done = {(r.get("id") or "") for r in (d.get("recent_done") or []) if r.get("id")}
active_cmds = d.get("active_cmds") or []

stragglers = []
for a in action:
    cmd_id = a.get("cmd_id") or ""
    if cmd_id and cmd_id in recent_done:
        rule = a.get("rule") or "?"
        title = (a.get("title") or "")[:60]
        stragglers.append("{} [{}] {}".format(cmd_id, rule, title))

status_done_in_active = []
for c in active_cmds:
    if (c.get("status") or "").lower() == "done":
        status_done_in_active.append("{} status={}".format(c.get("id"), c.get("status")))

if stragglers or status_done_in_active:
    print("STRAGGLERS:" + "|".join(stragglers))
    print("ACTIVE_DONE:" + "|".join(status_done_in_active))
else:
    print("OK")
PYEOF
  local report
  report="$(printf '%s' "$body" | python3 "$py_script")"
  rm -f "$py_script"

  if [[ -z "$report" || "$report" == "OK" ]]; then
    log "MCP dashboard: no stragglers"
    return 0
  fi

  local stragglers active_done
  stragglers="$(grep '^STRAGGLERS:' <<<"$report" | sed 's/^STRAGGLERS://')"
  active_done="$(grep '^ACTIVE_DONE:' <<<"$report" | sed 's/^ACTIVE_DONE://')"

  local count=0
  local msg="🧹 MCPダッシュボード残骸検出:"
  if [[ -n "$stragglers" ]]; then
    while IFS='|' read -ra arr; do
      for item in "${arr[@]}"; do
        [[ -z "$item" ]] && continue
        msg+=$'\n  • done済みだが action_required に残骸: '"$item"
        count=$((count+1))
      done
    done <<<"$stragglers"
  fi
  if [[ -n "$active_done" ]]; then
    while IFS='|' read -ra arr; do
      for item in "${arr[@]}"; do
        [[ -z "$item" ]] && continue
        msg+=$'\n  • active_cmds に status=done 混入: '"$item"
        count=$((count+1))
      done
    done <<<"$active_done"
  fi

  if [[ $count -eq 0 ]]; then
    log "MCP dashboard: no actionable stragglers"
    return 0
  fi

  msg+=$'\n家老: dashboard.md 更新 or 該当 cmd の done_at 反映を確認されたし。'

  log "MCP dashboard: ${count} straggler(s) detected"
  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN: would send ntfy:"
    while IFS= read -r l; do log "  $l"; done <<<"$msg"
  else
    ntfy_best_effort "$msg"
  fi
}

check_mcp_stragglers || log "ERROR in check_mcp_stragglers (continuing)"

log "=== dashboard_lifecycle end ==="
exit 0
