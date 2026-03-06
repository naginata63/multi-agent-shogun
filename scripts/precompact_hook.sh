#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# precompact_hook.sh — Claude Code PreCompact Hook
# ═══════════════════════════════════════════════════════════════
# Purpose:
#   Save agent state snapshot before compaction.
#   The snapshot is restored by sessionstart_hook.sh (source=compact).
#
# Design:
#   - stdout is IGNORED by Claude Code (PreCompact is side-effect only)
#   - Script must never fail (exit 0 always) — errors must not block compaction
#   - Saves to queue/precompact/{agent_id}.yaml (overwrite)
#
# Usage:
#   Registered as a PreCompact hook in .claude/settings.json
#   Receives JSON on stdin: {"session_id": "...", "trigger": "auto"|"manual", ...}

# Safety: do NOT use set -e. Hook must never fail.
set -uo pipefail

SCRIPT_DIR="${__PRECOMPACT_HOOK_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON="$SCRIPT_DIR/.venv/bin/python3"
# Fallback to system python3 if venv not available
[ -x "$PYTHON" ] || PYTHON="python3"

# ─── Read stdin (hook input JSON) ───
INPUT=$(cat 2>/dev/null || true)

# ─── Extract trigger from input ───
TRIGGER=$("$PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('trigger','unknown'))" <<< "$INPUT" 2>/dev/null || echo "unknown")

# ─── Identify agent ───
if [ -n "${__PRECOMPACT_HOOK_AGENT_ID+x}" ]; then
    AGENT_ID="$__PRECOMPACT_HOOK_AGENT_ID"
elif [ -n "${TMUX_PANE:-}" ]; then
    AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
else
    AGENT_ID=""
fi

# No agent context → silently exit
if [ -z "$AGENT_ID" ]; then
    exit 0
fi

# ─── Paths ───
TASK_FILE="$SCRIPT_DIR/queue/tasks/${AGENT_ID}.yaml"
SNAPSHOT_DIR="$SCRIPT_DIR/queue/precompact"
SNAPSHOT_FILE="$SNAPSHOT_DIR/${AGENT_ID}.yaml"

# ─── Create snapshot directory ───
mkdir -p "$SNAPSHOT_DIR" 2>/dev/null || exit 0

# ─── Extract task info from YAML ───
TASK_ID=""
PARENT_CMD=""
STATUS=""
if [ -f "$TASK_FILE" ]; then
    TASK_ID=$("$PYTHON" -c "
import yaml, sys
try:
    with open('$TASK_FILE') as f:
        d = yaml.safe_load(f) or {}
    t = d.get('task', d)
    print(t.get('task_id', ''))
except Exception:
    print('')
" 2>/dev/null || true)
    PARENT_CMD=$("$PYTHON" -c "
import yaml, sys
try:
    with open('$TASK_FILE') as f:
        d = yaml.safe_load(f) or {}
    t = d.get('task', d)
    print(t.get('parent_cmd', ''))
except Exception:
    print('')
" 2>/dev/null || true)
    STATUS=$("$PYTHON" -c "
import yaml, sys
try:
    with open('$TASK_FILE') as f:
        d = yaml.safe_load(f) or {}
    t = d.get('task', d)
    print(t.get('status', ''))
except Exception:
    print('')
" 2>/dev/null || true)
fi

# ─── Role-specific summary ───
case "$AGENT_ID" in
    shogun)    ROLE="将軍。全体指揮。殿へのレポート。" ;;
    karo)      ROLE="家老。タスク管理・配分・品質管理。実装禁止（必ず足軽に委任）。" ;;
    gunshi)    ROLE="軍師。戦略分析・品質検査・助言。Shogunへ直接報告禁止。足軽管理禁止。" ;;
    ashigaru*) ROLE="足軽${AGENT_ID#ashigaru}号。タスク実行担当。git push禁止。他足軽YAML編集禁止。" ;;
    *)         ROLE="不明（${AGENT_ID}）" ;;
esac

# ─── Active cmds from shogun_to_karo.yaml (shogun/karo) ───
CMD_QUEUE="$SCRIPT_DIR/queue/shogun_to_karo.yaml"
ACTIVE_CMDS=""
if [ -f "$CMD_QUEUE" ] && { [ "$AGENT_ID" = "shogun" ] || [ "$AGENT_ID" = "karo" ]; }; then
    ACTIVE_CMDS=$("$PYTHON" -c "
import yaml, sys
try:
    with open('$CMD_QUEUE') as f:
        d = yaml.safe_load(f) or {}
    cmds = d.get('commands', [])
    active = []
    for c in cmds:
        st = c.get('status', 'pending')
        if st in ('pending', 'in_progress', 'blocked'):
            cid = c.get('id', '?')
            proj = c.get('project', '')
            purp = c.get('purpose', '')[:80]
            active.append(f'{cid} [{st}] ({proj}) {purp}')
    print('\n'.join(active) if active else '')
except Exception:
    print('')
" 2>/dev/null || true)
fi

# ─── Agent-managed subtasks (karo) ───
MANAGED_AGENTS=""
if [ "$AGENT_ID" = "karo" ]; then
    MANAGED_AGENTS=$("$PYTHON" -c "
import yaml, sys, glob, os
try:
    results = []
    for f in sorted(glob.glob('$SCRIPT_DIR/queue/tasks/*.yaml')):
        name = os.path.basename(f).replace('.yaml','')
        if name in ('shogun', 'karo'):
            continue
        with open(f) as fh:
            d = yaml.safe_load(fh) or {}
        t = d.get('task', d)
        tid = t.get('task_id', '')
        st = t.get('status', '')
        if tid and st and st not in ('idle', ''):
            results.append(f'{name}: {tid} [{st}]')
    print('\n'.join(results) if results else '')
except Exception:
    print('')
" 2>/dev/null || true)
fi

# ─── Dashboard summary (shogun/karo) ───
DASHBOARD_SUMMARY=""
DASHBOARD_FILE="$SCRIPT_DIR/queue/dashboard.md"
if [ -f "$DASHBOARD_FILE" ] && { [ "$AGENT_ID" = "shogun" ] || [ "$AGENT_ID" = "karo" ]; }; then
    DASHBOARD_SUMMARY=$(head -30 "$DASHBOARD_FILE" 2>/dev/null || true)
fi

# ─── Pane capture (conversation context) ───
# Full scrollback, then extract Lord's input lines (❯ prompt) with 2 lines of context each
PANE_CAPTURE=""
if [ -n "${TMUX_PANE:-}" ]; then
    PANE_CAPTURE=$(tmux capture-pane -t "$TMUX_PANE" -p -S - 2>/dev/null | grep -B1 -A2 '❯' 2>/dev/null | tail -80 || true)
fi

# ─── Unread inbox messages ───
INBOX_FILE="$SCRIPT_DIR/queue/inbox/${AGENT_ID}.yaml"
UNREAD_COUNT=0
if [ -f "$INBOX_FILE" ]; then
    UNREAD_COUNT=$("$PYTHON" -c "
import yaml
try:
    with open('$INBOX_FILE') as f:
        d = yaml.safe_load(f) or {}
    msgs = d.get('messages', [])
    print(sum(1 for m in msgs if not m.get('read', False)))
except Exception:
    print(0)
" 2>/dev/null || echo 0)
fi

# ─── Write snapshot (heredoc, no python dependency for write) ───
cat > "$SNAPSHOT_FILE" <<SNAPSHOT_EOF
# PreCompact snapshot — auto-generated by precompact_hook.sh
# Do NOT edit manually. Overwritten on every compaction.
agent_id: "${AGENT_ID}"
timestamp: "$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z')"
trigger: "${TRIGGER}"
task:
  task_id: "${TASK_ID}"
  parent_cmd: "${PARENT_CMD}"
  status: "${STATUS}"
role: "${ROLE}"
forbidden:
  - "git push 禁止（足軽。家老がcmd完了時に実施）"
  - "git add . 禁止（git add <dir> のみ）"
  - "rm -rf 禁止（プロジェクト外パス）"
  - "sudo / kill / tmux kill-* 禁止"
  - "inbox to shogun 禁止（dashboard.md経由のみ）"
  - "polling loop 禁止"
active_cmds: |
$(if [ -n "$ACTIVE_CMDS" ]; then echo "$ACTIVE_CMDS" | sed 's/^/  /'; else echo "  (none)"; fi)
managed_agents: |
$(if [ -n "$MANAGED_AGENTS" ]; then echo "$MANAGED_AGENTS" | sed 's/^/  /'; else echo "  (none)"; fi)
unread_inbox: ${UNREAD_COUNT}
dashboard_head: |
$(if [ -n "$DASHBOARD_SUMMARY" ]; then echo "$DASHBOARD_SUMMARY" | sed 's/^/  /'; else echo "  (no dashboard)"; fi)
pane_last_lines: |
$(if [ -n "$PANE_CAPTURE" ]; then echo "$PANE_CAPTURE" | sed 's/^/  /'; else echo "  (no tmux pane)"; fi)
recovery_hint: |
  Compaction後の手順:
  1. tmux display-message -t "\$TMUX_PANE" -p '#{@agent_id}' で自己識別
  2. CLAUDE.md Session Start / Recovery の手順に従う
  3. queue/tasks/${AGENT_ID}.yaml を読んでタスク継続
  4. pane_last_lines で殿との直近会話を確認し、文脈を復元せよ
Resume: Read active_cmds and pane_last_lines above, then queue/shogun_to_karo.yaml for full context.
SNAPSHOT_EOF

# ─── transcript copy (if provided) ───
TRANSCRIPT_PATH=$("$PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('transcript_path',''))" <<< "$INPUT" 2>/dev/null || true)
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    HANDOFF_TRANSCRIPT_DIR="$SCRIPT_DIR/queue/handoff/transcripts"
    mkdir -p "$HANDOFF_TRANSCRIPT_DIR" 2>/dev/null || true
    TS=$(date +%Y%m%d-%H%M 2>/dev/null || echo "unknown")
    cp "$TRANSCRIPT_PATH" "$HANDOFF_TRANSCRIPT_DIR/${AGENT_ID}_${TS}.jsonl" 2>/dev/null || true
fi

# ─── handoff markdown (for /rehydrate) ───
HANDOFF_DIR="$SCRIPT_DIR/queue/handoff"
mkdir -p "$HANDOFF_DIR" 2>/dev/null || true
TS=$(date +%Y%m%d-%H%M 2>/dev/null || echo "unknown")
HANDOFF_FILE="$HANDOFF_DIR/${AGENT_ID}_${TS}.md"
TASK_YAML_CONTENT=""
if [ -f "$TASK_FILE" ]; then
    TASK_YAML_CONTENT=$(cat "$TASK_FILE" 2>/dev/null || true)
fi
cat > "$HANDOFF_FILE" <<HANDOFF_EOF
# Handoff: ${AGENT_ID} @ ${TS}
auto-generated by precompact_hook.sh (PreCompact event)

## Agent
- agent_id: ${AGENT_ID}
- timestamp: ${TS}
- trigger: ${TRIGGER}

## Role
${ROLE}

## Task State (queue/tasks/${AGENT_ID}.yaml)
\`\`\`yaml
${TASK_YAML_CONTENT}
\`\`\`

## Active Commands (from shogun_to_karo.yaml)
${ACTIVE_CMDS:-"(none)"}

## Managed Agent Subtasks
${MANAGED_AGENTS:-"(none)"}

## Unread Inbox
${UNREAD_COUNT} unread messages

## Dashboard Head (queue/dashboard.md)
${DASHBOARD_SUMMARY:-"(no dashboard)"}

## Pane Capture (last 50 lines of conversation)
\`\`\`
${PANE_CAPTURE:-"(no tmux pane)"}
\`\`\`

## Next Actions
1. queue/tasks/${AGENT_ID}.yaml を読んで作業状態を確認
2. instructions/*.md を読んでロールを確認（compaction後は必須）
3. CLAUDE.md Session Start / Recovery 手順に従う
4. active_cmds の進行中cmdについて shogun_to_karo.yaml で詳細確認
5. pane_captureで殿との直近会話を確認し、文脈を復元
HANDOFF_EOF

# ─── Log (stderr only, stdout is ignored by Claude Code) ───
echo "[$(date)] PreCompact snapshot saved: ${SNAPSHOT_FILE} (agent=${AGENT_ID}, task=${TASK_ID}, trigger=${TRIGGER})" >&2

exit 0
