#!/usr/bin/env bash
# pretool_kill_shogun_only.sh — PreToolUse hook
# kill / killall / pkill を将軍以外のpaneで弾く。
# settings.json deny list から "Bash(kill *)" を外したことの代替。
# CLAUDE.md D006 (tmux kill-server/kill-session 禁止) は別系統で継続。

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

# Bash 以外は無関係
if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0
fi

# kill/killall/pkill が含まれているか（先頭 or パイプ後 or && 後 or ; 後）
if ! echo "$COMMAND" | grep -qE '(^|[;&|]\s*)\s*(kill|killall|pkill)\b'; then
  exit 0
fi

# 将軍判定
AGENT_ID=""
if [ -n "${TMUX_PANE:-}" ]; then
  AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
fi

if [[ "$AGENT_ID" == "shogun" ]]; then
  exit 0
fi

echo "BLOCKED: kill/killall/pkill は将軍paneのみ許可。現エージェント=${AGENT_ID:-unknown}。家老/足軽/軍師は kill 禁止。プロセス停止が必要なら将軍に依頼せよ。" >&2
exit 2
