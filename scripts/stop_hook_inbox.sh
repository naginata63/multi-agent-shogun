#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# stop_hook_inbox.sh — Claude Code Stop Hook for inbox delivery
# ═══════════════════════════════════════════════════════════════
# When a Claude Code agent finishes its turn and is about to go idle,
# this hook:
#   1. Analyzes last_assistant_message to detect task completion/error
#   2. Auto-notifies karo via inbox_write (background, non-blocking)
#   3. Checks the agent's inbox for unread messages
#   4. If unread messages exist, BLOCKs the stop and feeds them back
#
# Usage: Registered as a Stop hook in .claude/settings.json
#   The hook receives JSON on stdin; outputs JSON to stdout.
#
# Environment:
#   TMUX_PANE — used to identify which agent is running
#   __STOP_HOOK_SCRIPT_DIR — override for testing (default: auto-detect)
#   __STOP_HOOK_AGENT_ID  — override for testing (default: from tmux)
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="${__STOP_HOOK_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# ─── Read stdin (hook input JSON) ───
INPUT=$(cat)

# ─── Identify agent ───
if [ -n "${__STOP_HOOK_AGENT_ID+x}" ]; then
    AGENT_ID="$__STOP_HOOK_AGENT_ID"
elif [ -n "${TMUX_PANE:-}" ]; then
    AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
else
    AGENT_ID=""
fi

# If we can't identify the agent, approve (exit 0 with no output = approve)
if [ -z "$AGENT_ID" ]; then
    exit 0
fi

# Shogun doesn't need inbox watching — Lord interacts directly
if [ "$AGENT_ID" = "shogun" ]; then
    exit 0
fi

# ─── ntfy送信漏れ自動検出（家老のみ） ───
_check_ntfy_missed() {
    local WATERMARK_FILE="/tmp/ntfy_check_watermark_karo"
    local NTFY_LOG="$SCRIPT_DIR/queue/ntfy_sent.log"
    local YAML_FILE="$SCRIPT_DIR/queue/shogun_to_karo.yaml"

    # 前提ファイルが無ければスキップ
    [ ! -f "$NTFY_LOG" ] && return 0
    [ ! -f "$YAML_FILE" ] && return 0

    # ウォーターマーク読み込み（デフォルト: cmd_1100）
    local LAST_CHECKED="cmd_1100"
    [ -f "$WATERMARK_FILE" ] && LAST_CHECKED=$(cat "$WATERMARK_FILE")

    # ウォーターマーク以降のdone cmd を抽出し、ntfy未送信を検出
    local MISSING
    MISSING=$(YAML_FILE="$YAML_FILE" NTFY_LOG="$NTFY_LOG" LAST_CHECKED="$LAST_CHECKED" \
        python3 -c "
import os, re

yaml_file = os.environ['YAML_FILE']
ntfy_log = os.environ['NTFY_LOG']
last_checked = os.environ['LAST_CHECKED']

with open(ntfy_log) as f:
    ntfy_text = f.read()

with open(yaml_file) as f:
    text = f.read()

# Split into cmd blocks to avoid cross-block status contamination
blocks = re.split(r'\n(?=- id: )', text)

missing = []
latest_cmd = None
found_watermark = False

for block in blocks:
    if not block.strip().startswith('- id:'):
        continue
    m = re.search(r'^- id: (cmd_\d+)', block, re.MULTILINE)
    if not m:
        continue
    cmd_id = m.group(1)

    if not found_watermark:
        if cmd_id == last_checked:
            found_watermark = True
        continue  # Skip cmds before watermark

    # Only check cmds with explicit 'status: done' in their own block
    if re.search(r'^  status: done\s*$', block, re.MULTILINE):
        latest_cmd = cmd_id
        if cmd_id not in ntfy_text:
            missing.append(cmd_id)

if latest_cmd:
    print('WATERMARK:' + latest_cmd)
for cmd in missing:
    print(cmd)
" 2>/dev/null || true)

    # 未送信cmdを自動送信 + ウォーターマーク更新
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        if [[ "$line" == WATERMARK:* ]]; then
            echo "${line#WATERMARK:}" > "$WATERMARK_FILE"
            continue
        fi
        bash "$SCRIPT_DIR/scripts/ntfy.sh" "✅ ${line}完了（自動検出）" &
    done <<< "$MISSING"
}

# Karo: ntfy送信漏れチェックのみ → 即exit 0（inotifywait不要）
if [ "$AGENT_ID" = "karo" ]; then
    _check_ntfy_missed
    exit 0
fi

# Gunshi: 即exit 0（inotifywait不要）
if [ "$AGENT_ID" = "gunshi" ]; then
    exit 0
fi

# ─── Define inbox path early (used in multiple places below) ───
INBOX="$SCRIPT_DIR/queue/inbox/${AGENT_ID}.yaml"

# ─── Infinite loop prevention ───
# When stop_hook_active=true, the agent is already continuing from a
# previous Stop hook block. Allow it to stop this time to prevent loops.
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stop_hook_active', False))" 2>/dev/null || echo "False")
if [ "$STOP_HOOK_ACTIVE" = "True" ]; then
    # Agent is going idle (exit 0) regardless of unread count.
    # ALWAYS create the idle flag so inbox_watcher knows the agent is idle
    # and can send nudges. Previously, removing the flag here when unread > 0
    # caused a deadlock: agent idle but watcher thinks busy → no nudge → stuck.
    FLAG="${IDLE_FLAG_DIR:-/tmp}/agent_idle_${AGENT_ID}"
    touch "$FLAG"
    # stop_hook_active=True 時も inotifywait 待機（連続処理ループ対応）
    # タイムアウト(55秒)でexit 0 → ループは有限回で終了
    WATCH_TARGETS_ACTIVE=("$INBOX")
    if [ "$AGENT_ID" = "shogun" ]; then
        WATCH_TARGETS_ACTIVE+=("$SCRIPT_DIR/dashboard.md")
    fi
    if command -v inotifywait &>/dev/null; then
        inotifywait -e close_write -e moved_to \
            --timeout 55 \
            "${WATCH_TARGETS_ACTIVE[@]}" 2>/dev/null || true
    fi
    UNREAD_COUNT=$(grep -c 'read: false' "$INBOX" 2>/dev/null || true)
    if [ "${UNREAD_COUNT:-0}" -eq 0 ]; then
        exit 0
    fi
    # 未読あり → fall through to block response (but still from active state)
    # Reset STOP_HOOK_ACTIVE flag logic: treat as fresh inbox check
fi

# ─── Analyze last_assistant_message (v2.1.47+) ───
# Shogun skips karo notification (shogun doesn't report to karo)
# but still falls through to inbox check below.
LAST_MSG=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('last_assistant_message', ''))" 2>/dev/null || echo "")

if [ -n "$LAST_MSG" ]; then
    NOTIFY_TYPE=""
    NOTIFY_CONTENT=""

    # Completion detection (日本語 + 英語)
    if echo "$LAST_MSG" | grep -qiE '任務完了|完了でござる|報告YAML.*更新|report.*updated|task completed|タスク完了'; then
        NOTIFY_TYPE="report_completed"
        NOTIFY_CONTENT="${AGENT_ID}、タスク完了。report確認されたし。"
    # Error detection (require verb+context to avoid false positives)
    elif echo "$LAST_MSG" | grep -qiE 'エラー.*中断|失敗.*中断|見つからない.*中断|abort|error.*abort|failed.*stop'; then
        NOTIFY_TYPE="error_report"
        NOTIFY_CONTENT="${AGENT_ID}、エラーで停止。確認されたし。"
    fi

    # Send notification to karo (background, non-blocking)
    # Shogun doesn't report to karo — skip notification
    if [ -n "$NOTIFY_TYPE" ] && [ "$AGENT_ID" != "shogun" ]; then
        bash "$SCRIPT_DIR/scripts/inbox_write.sh" karo \
            "$NOTIFY_CONTENT" \
            "$NOTIFY_TYPE" "$AGENT_ID" &
    fi
fi

# ─── Check inbox for unread messages ───
# INBOX is already defined at L48 (stop_hook_inbox.sh INBOX二重定義修正)

if [ ! -f "$INBOX" ]; then
    exit 0
fi

# Count unread messages using grep (fast, no python dependency)
UNREAD_COUNT=$(grep -c 'read: false' "$INBOX" 2>/dev/null || true)

FLAG="${IDLE_FLAG_DIR:-/tmp}/agent_idle_${AGENT_ID}"
if [ "${UNREAD_COUNT:-0}" -eq 0 ]; then
    touch "$FLAG"
    # inotifywait で inbox 変更を最大55秒待機
    # dashboard.md も監視（shogunの場合のみ）
    WATCH_TARGETS=("$INBOX")
    if [ "$AGENT_ID" = "shogun" ]; then
        WATCH_TARGETS+=("$SCRIPT_DIR/dashboard.md")
    fi
    if command -v inotifywait &>/dev/null; then
        inotifywait -e close_write -e moved_to \
            --timeout 55 \
            "${WATCH_TARGETS[@]}" 2>/dev/null || true
    else
        # inotifywait not available: fall through to exit 0
        :
    fi
    # 待機後に再チェック
    UNREAD_COUNT=$(grep -c 'read: false' "$INBOX" 2>/dev/null || true)
    if [ "${UNREAD_COUNT:-0}" -eq 0 ]; then
        exit 0
    fi
    # 未読あり → fall through to block response below
fi
# NOTE: Do NOT rm -f the flag here. The old logic removed the flag when
# unread > 0 and blocked the stop, expecting the re-fired stop_hook
# (with stop_hook_active=True) to restore it. But if the agent processes
# the unread messages and then the second stop_hook doesn't fire or
# stop_hook_active isn't set, the flag is permanently lost → deadlock.
# Instead, keep the flag alive. The watcher will see the agent as idle
# and send a nudge, which is the correct behavior — the agent IS idle
# between the block response and the next turn.
# The flag will be removed naturally when the agent starts its next turn
# (Claude Code removes it via the busy detection mechanism).

# ─── Extract unread message summaries ───
SUMMARY=$(INBOX_PATH="$INBOX" python3 -c "
import yaml, sys, json, os
try:
    with open(os.environ['INBOX_PATH'], 'r') as f:
        data = yaml.safe_load(f)
    msgs = data.get('messages', []) if data else []
    unread = [m for m in msgs if not m.get('read', True)]
    parts = []
    for m in unread[:5]:  # Max 5 messages in summary
        frm = m.get('from', '?')
        typ = m.get('type', '?')
        content = str(m.get('content', ''))[:80]
        parts.append(f'[{frm}/{typ}] {content}')
    print(' | '.join(parts))
except Exception as e:
    print(f'inbox parse error: {e}')
" 2>/dev/null || echo "inbox未読${UNREAD_COUNT}件あり")

# ─── Block the stop — feed inbox info back to agent ───
INBOX_SUMMARY="$SUMMARY" INBOX_AGENT_ID="$AGENT_ID" INBOX_UNREAD_COUNT="$UNREAD_COUNT" python3 -c "
import json, os
count = int(os.environ['INBOX_UNREAD_COUNT'])
summary = os.environ['INBOX_SUMMARY']
agent_id = os.environ['INBOX_AGENT_ID']
reason = f'inbox未読{count}件あり。queue/inbox/{agent_id}.yamlを読んで処理せよ。内容: {summary}'
print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
" 2>/dev/null || echo "{\"decision\":\"block\",\"reason\":\"inbox未読${UNREAD_COUNT}件あり。queue/inbox/${AGENT_ID}.yamlを読んで処理せよ。\"}"
