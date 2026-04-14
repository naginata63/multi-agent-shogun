#!/usr/bin/env bash
# UserPromptSubmit hook: 殿がメッセージを送るたびにntfy_sent.logの新着をチェック
# 将軍のみ実行。新着があればコンテキストに注入する。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 将軍のみ実行
AGENT_ID=""
if [ -n "${TMUX_PANE:-}" ]; then
    AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
fi
if [[ "$AGENT_ID" != "shogun" ]]; then
    exit 0
fi

NTFY_LOG="$SCRIPT_DIR/queue/ntfy_sent.log"
FLAGS_DIR="$SCRIPT_DIR/queue/.flags"
mkdir -p "$FLAGS_DIR"
LAST_LINE_FILE="$FLAGS_DIR/shogun_ntfy_last_line"

if [ ! -f "$NTFY_LOG" ]; then
    exit 0
fi

CURRENT=$(wc -l < "$NTFY_LOG")
LAST=$(cat "$LAST_LINE_FILE" 2>/dev/null || echo "$CURRENT")

if [ "$CURRENT" -gt "$LAST" ]; then
    NEW_COUNT=$((CURRENT - LAST))
    NEW_LINES=$(tail -n "$NEW_COUNT" "$NTFY_LOG")
    echo "【ntfy新着 ${NEW_COUNT}件】"
    echo "$NEW_LINES"
fi

# 現在の行数を記録
echo "$CURRENT" > "$LAST_LINE_FILE"

exit 0
