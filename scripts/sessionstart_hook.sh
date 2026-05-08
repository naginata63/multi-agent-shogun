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

# Check API key availability (VERTEX_API_KEY優先)
GEMINI_STATUS=""
if [ -n "${VERTEX_API_KEY:-}" ]; then
    GEMINI_STATUS="GEMINI_API_KEY: already set (via VERTEX_API_KEY)"
elif [ -n "${GEMINI_API_KEY:-}" ]; then
    GEMINI_STATUS="GEMINI_API_KEY: already set"
else
    source ~/.bashrc 2>/dev/null || true
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        GEMINI_STATUS="GEMINI_API_KEY: loaded from ~/.bashrc"
    else
        GEMINI_STATUS="GEMINI_API_KEY: NOT SET (run: source config/vertex_api_key.env)"
    fi
fi

# Shogun: ntfy.log直近エントリを取得（セッション開始時に1回だけ）
NTFY_CONTEXT=""
if [[ "$AGENT_ID" == "shogun" ]]; then
    NTFY_LOG="$SCRIPT_DIR/queue/ntfy_sent.log"
    if [ -f "$NTFY_LOG" ]; then
        NTFY_RECENT=$(tail -10 "$NTFY_LOG" 2>/dev/null || true)
        if [ -n "$NTFY_RECENT" ]; then
            NTFY_CONTEXT="
Recent ntfy notifications (read these to stay in sync with Lord):
${NTFY_RECENT}"
        fi
    fi
fi

CONTEXT=$(cat <<EOF
SessionStart hook: current agent is '${AGENT_ID}' (source=${SOURCE}).
Before any inbox/task handling, first run:
tmux display-message -t "\$TMUX_PANE" -p '#{@agent_id}'
If mismatch, stop and recover. Then execute CLAUDE.md Session Start / Recovery in order.
Env: ${GEMINI_STATUS}. When running scripts that need GEMINI_API_KEY, prepend: source ~/.bashrc &&

## Step 0: SSE Monitor auto-start (cmd_1669 D案・watcher補完)
Session Start の Step 1 (self-identify) 直後・Step 2 以降より先に必ず実行せよ:
  1. ToolSearch(query="select:Monitor") で Monitor tool schema を取得
  2. Monitor(command='curl -N -s "http://192.168.2.4:8770/api/inbox_stream?agent=${AGENT_ID}" | grep --line-buffered "^data:"') を起動
     ★ grep フィルタ必須: server 側 SSE keepalive (':keepalive' コメント行) を除外せねば
       30秒毎に Monitor event 発火 → 毎回 turn 消費でコスト爆発する (cmd_1669γ実証で2026-05-09 軍師に発生)
  3. 起動直後 1秒以内に発生したメッセージは race condition で取りこぼし可能性あり (cmd_1649 実証60%) →
     直後に GET /api/inbox_messages?agent=${AGENT_ID}&unread=1 で catch-up 取得
  4. Monitor event の content は 'data: {"msg_id":...,"type":"...","content":"..."}' の JSON line。
     parseable な inbox message でない event は無視 (応答せず idle 継続)。
  5. Monitor stream 終了 (EOF) を受信した場合: **自動再起動するな**。Stream 終了は server restart 等の
     正規イベント — 殿か家老の指示を待ち idle 継続。再起動が要なら明示指示で行え。
  6. SSE接続失敗 (connection refused 等) は fail-soft: 既存 inbox_watcher.sh 経路で配信継続するゆえ
     エラーで halt せず Step 1 に進め${NTFY_CONTEXT}
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
