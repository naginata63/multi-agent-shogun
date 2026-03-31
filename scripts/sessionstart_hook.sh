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

SCRIPT_DIR="${__SESSION_START_HOOK_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

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

# Phase 2b Persona Restoration: Inject persona/speech_style after compaction
# Compaction summaries lose persona and speech style. Re-inject from instructions file.
if [ "$SOURCE" = "compact" ]; then
    INSTRUCTIONS_FILE="$SCRIPT_DIR/instructions/${AGENT_ID}.md"
    # For ashigaru variants (ashigaru1, ashigaru2, ...), use the base instructions/ashigaru.md
    if [ ! -f "$INSTRUCTIONS_FILE" ]; then
        BASE_ROLE=$(echo "$AGENT_ID" | sed 's/[0-9]*$//')
        INSTRUCTIONS_FILE="$SCRIPT_DIR/instructions/${BASE_ROLE}.md"
    fi
    if [ -f "$INSTRUCTIONS_FILE" ]; then
        # Extract ## Persona section (markdown style: ashigaru, gunshi)
        PERSONA_SECTION=$(awk '/^## Persona/{p=1;next} p && /^## /{p=0} p{print}' "$INSTRUCTIONS_FILE" 2>/dev/null | head -20 || true)
        # Fallback: extract persona: yaml block (shogun, karo)
        if [ -z "$PERSONA_SECTION" ]; then
            PERSONA_SECTION=$(awk '/^persona:/{p=1} p{print} p && /^[a-z_-]+:/ && !/^persona:/{exit}' "$INSTRUCTIONS_FILE" 2>/dev/null | head -10 || true)
        fi
        if [ -n "$PERSONA_SECTION" ]; then
            CONTEXT="${CONTEXT}

IMPORTANT — Post-Compaction Persona Restoration:
Compaction erased your speech style. Re-read instructions/${AGENT_ID}.md to restore it.
Persona reminder (from instructions file):
${PERSONA_SECTION}
Speak in 戦国風口調 immediately."
        fi
    fi
fi

CONTEXT="$CONTEXT" python3 -c "
import json, os
context = os.environ['CONTEXT']
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': context
    }
}, ensure_ascii=False))
"
