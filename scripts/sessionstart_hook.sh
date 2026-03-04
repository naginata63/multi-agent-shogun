#!/usr/bin/env bash
# session_start_hook.sh — Claude Code SessionStart Hook for self-identification
#
# Purpose:
#   Inject startup context so each agent always self-identifies via tmux
#   before processing inbox/tasks.
#
# Usage:
#   Registered as a SessionStart hook in .claude/settings.json
#   Receives JSON on stdin, writes JSON on stdout.

set -euo pipefail

INPUT=$(cat)

# For tests, allow override. In production, resolve from tmux pane.
if [ -n "${__SESSION_START_HOOK_AGENT_ID+x}" ]; then
    AGENT_ID="$__SESSION_START_HOOK_AGENT_ID"
elif [ -n "${TMUX_PANE:-}" ]; then
    AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
else
    AGENT_ID=""
fi

# No agent context → no-op (non-blocking).
if [ -z "$AGENT_ID" ]; then
    exit 0
fi

SOURCE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('source', 'unknown'))" 2>/dev/null || echo "unknown")

# Check GEMINI_API_KEY availability
GEMINI_STATUS=""
if [ -z "${GEMINI_API_KEY:-}" ]; then
    source ~/.bashrc 2>/dev/null || true
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        GEMINI_STATUS="GEMINI_API_KEY: loaded from ~/.bashrc"
    else
        GEMINI_STATUS="GEMINI_API_KEY: NOT SET (run: source ~/.bashrc)"
    fi
else
    GEMINI_STATUS="GEMINI_API_KEY: already set"
fi

CONTEXT=$(cat <<EOF
SessionStart hook: current agent is '${AGENT_ID}' (source=${SOURCE}).
Before any inbox/task handling, first run:
tmux display-message -t "\$TMUX_PANE" -p '#{@agent_id}'
If mismatch, stop and recover. Then execute CLAUDE.md Session Start / Recovery in order.
Env: ${GEMINI_STATUS}. When running scripts that need GEMINI_API_KEY, prepend: source ~/.bashrc &&
EOF
)

# Phase 2 PreCompact: Restore snapshot after compaction
SCRIPT_DIR="${__STOP_HOOK_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PRECOMPACT_FILE="$SCRIPT_DIR/queue/precompact/${AGENT_ID}.yaml"
if [ "$SOURCE" = "compact" ] && [ -f "$PRECOMPACT_FILE" ]; then
    SNAPSHOT=$(cat "$PRECOMPACT_FILE" 2>/dev/null || true)
    if [ -n "$SNAPSHOT" ]; then
        CONTEXT="${CONTEXT}
PreCompact snapshot (saved before compaction):
${SNAPSHOT}
Resume: Read queue/tasks/${AGENT_ID}.yaml and continue your task."
    fi
fi

python3 -c "
import json
context = '''$CONTEXT'''
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': context
    }
}, ensure_ascii=False))
"
