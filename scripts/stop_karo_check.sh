#!/bin/bash
# stop_karo_check.sh — 家老セッション終了時の安全網
# Stopフックで発火。dashboard.md更新漏れとntfy送信漏れをキャッチ。
#
# チェック1: task YAML done → dashboard.mdに記載なし → 自動追記
# チェック2: dashboard.md完了 → ntfy_sent.logに送信なし → 自動ntfy送信
# 2026-04-24 殿指示によりdashboard自動追記無効化（古い完了エントリが混入するため）
exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD="$SCRIPT_DIR/dashboard.md"
NTFY_LOG="$SCRIPT_DIR/queue/ntfy_sent.log"
TASKS_DIR="$SCRIPT_DIR/queue/tasks"

# 家老ペインでのみ実行
AGENT_ID=""
if [ -n "${TMUX_PANE:-}" ]; then
  AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
fi
[ "$AGENT_ID" != "karo" ] && exit 0

# === チェック1: task YAML done → dashboard.md記載漏れ ===
MISSING_CMDS=""
for yaml in "$TASKS_DIR"/ashigaru*.yaml "$TASKS_DIR"/gunshi.yaml; do
  [ ! -f "$yaml" ] && continue
  # done状態のタスクからparent_cmdを抽出
  DONE_CMDS=$(python3 -c "
import yaml, sys
try:
    with open('$yaml') as f:
        data = yaml.safe_load(f)
    if not data or 'tasks' not in data:
        sys.exit(0)
    for t in data['tasks']:
        if isinstance(t, dict) and t.get('status') == 'done':
            pcmd = t.get('parent_cmd', '')
            if pcmd:
                print(pcmd)
except:
    pass
" 2>/dev/null | sort -u)

  for cmd in $DONE_CMDS; do
    # dashboard.mdに記載があるか
    if ! grep -qF "$cmd" "$DASHBOARD" 2>/dev/null; then
      MISSING_CMDS="$MISSING_CMDS $cmd"
    fi
  done
done

# 漏れがあれば自動追記
if [ -n "$MISSING_CMDS" ]; then
  TIMESTAMP=$(date '+%H:%M')
  for cmd in $MISSING_CMDS; do
    # タスクYAMLからタイトルを取得
    TITLE=$(grep -r "parent_cmd: $cmd" "$TASKS_DIR"/*.yaml -l 2>/dev/null | head -1 | xargs grep "title:" 2>/dev/null | tail -1 | sed 's/.*title: *//' | tr -d '"' | head -c 60)
    [ -z "$TITLE" ] && TITLE="(タイトル不明)"

    # dashboard.mdの完了セクションに追記
    if grep -q "^## ✅" "$DASHBOARD" 2>/dev/null; then
      # 完了テーブルの最後の行の後に追記
      sed -i "/^## ✅/,/^$/{/^$/i\\| $cmd | $TITLE | $(date '+%-m/%-d') |
}" "$DASHBOARD" 2>/dev/null || true
    fi

    echo "[stop_karo_check] dashboard.md漏れ追記: $cmd $TITLE" >&2
  done
fi

# === チェック2: dashboard.md完了 → ntfy未送信 ===
# dashboard.mdの完了セクションからcmd_XXXを抽出
DASHBOARD_CMDS=$(grep -oP 'cmd_\d+' "$DASHBOARD" 2>/dev/null | sort -u)

for cmd in $DASHBOARD_CMDS; do
  # ntfyログに送信済みか
  if ! grep -qF "${cmd}完了" "$NTFY_LOG" 2>/dev/null; then
    # 完了セクションにあるか確認（進行中セクションのcmdは除外）
    IN_DONE=$(sed -n '/^## ✅/,/^## /p' "$DASHBOARD" | grep -F "$cmd" || true)
    [ -z "$IN_DONE" ] && continue

    # タイトル取得
    TITLE=$(echo "$IN_DONE" | head -1 | sed 's/.*| *//' | sed 's/ *|.*//' | head -c 60)
    # タイトル取得できない場合は送信しない（家老の正式ntfyを待つ）
    [ -z "$TITLE" ] && continue

    # ntfy送信
    bash "$SCRIPT_DIR/scripts/ntfy.sh" "✅ ${cmd}完了: $TITLE" &
    echo "[stop_karo_check] ntfy漏れ送信: $cmd $TITLE" >&2
  fi
done

exit 0
