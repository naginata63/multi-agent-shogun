#!/usr/bin/env bash
# inbox_write.sh — メールボックスへのメッセージ書き込み（排他ロック付き）
# Usage: bash scripts/inbox_write.sh <target_agent> <content> [type] [from]
# Example: bash scripts/inbox_write.sh karo "足軽5号、任務完了" report_received ashigaru5

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$1"
CONTENT="$2"
TYPE="${3:-wake_up}"
FROM="${4:-unknown}"

INBOX="$SCRIPT_DIR/queue/inbox/${TARGET}.yaml"
LOCKFILE="${INBOX}.lock"

# Validate arguments
if [ -z "$TARGET" ] || [ -z "$CONTENT" ]; then
    echo "Usage: inbox_write.sh <target_agent> <content> [type] [from]" >&2
    exit 1
fi

# Initialize inbox if not exists
if [ ! -f "$INBOX" ]; then
    mkdir -p "$(dirname "$INBOX")"
    echo "messages: []" > "$INBOX"
fi

# Generate unique message ID (timestamp-based)
MSG_ID="msg_$(date +%Y%m%d_%H%M%S)_$(head -c 4 /dev/urandom | xxd -p)"
TIMESTAMP=$(date "+%Y-%m-%dT%H:%M:%S")

# Cross-platform lock: flock (Linux) or mkdir (macOS fallback)
LOCK_DIR="${LOCKFILE}.d"

_acquire_lock() {
    if command -v flock &>/dev/null; then
        exec 200>"$LOCKFILE"
        flock -w 5 200 || return 1
    else
        local i=0
        while ! mkdir "$LOCK_DIR" 2>/dev/null; do
            sleep 0.1
            i=$((i + 1))
            [ $i -ge 50 ] && return 1  # 5s timeout
        done
    fi
    return 0
}

_release_lock() {
    if command -v flock &>/dev/null; then
        exec 200>&-
    else
        rmdir "$LOCK_DIR" 2>/dev/null
    fi
}

# === cmd status auto-update (task_assigned時) ===
# type="task_assigned"の場合、メッセージからcmd_XXXを抽出し、
# shogun_to_karo.yamlの該当cmd: pending → in_progress に更新
_update_cmd_status() {
    [ "$TYPE" != "task_assigned" ] && return 0

    local cmd_id
    cmd_id=$(echo "$CONTENT" | grep -oP 'cmd_\d+' | head -1)
    [ -z "$cmd_id" ] && return 0

    local yaml_file="$SCRIPT_DIR/queue/shogun_to_karo.yaml"
    [ ! -f "$yaml_file" ] && return 0

    local lock_file="${yaml_file}.lock"
    local tmp_file="${yaml_file}.tmp.$$"

    (
        flock -w 5 200 || exit 0

        # Find "- id: cmd_XXX" block, replace next "status: pending" → "status: in_progress"
        # If no status line exists, insert "  status: in_progress" after the id line
        if mawk -v cmd="$cmd_id" '
            /- id: / {
                if (in_block && !found_status) {
                    print "  status: in_progress"
                    updated = 1
                }
                in_block = ($0 ~ "- id: " cmd)
                found_status = 0
            }
            in_block && /status:/ {
                sub(/status: pending/, "status: in_progress")
                sub(/status: assigned/, "status: in_progress")
                found_status = 1
                in_block = 0
                updated = 1
            }
            in_block && /^[^ ]/ && !/^-/ {
                # Hit next top-level key without finding status — insert before it
                print "  status: in_progress"
                updated = 1
                found_status = 1
                in_block = 0
            }
            { print }
            END {
                if (in_block && !found_status) {
                    print "  status: in_progress"
                    updated = 1
                }
                exit (updated ? 0 : 1)
            }
        ' "$yaml_file" > "$tmp_file"; then
            mv "$tmp_file" "$yaml_file"
        else
            rm -f "$tmp_file"
        fi
    ) 200>"$lock_file" 2>/dev/null

    return 0  # Never fail — message delivery must succeed
}

# === task done auto-update (report_done時) ===
# type="report_done"/"report_completed"の場合、送信元のtasks YAMLの
# 該当タスク status: assigned → done に更新
_update_task_done() {
    [ "$TYPE" != "report_done" ] && [ "$TYPE" != "report_completed" ] && return 0

    local task_file="$SCRIPT_DIR/queue/tasks/${FROM}.yaml"
    [ ! -f "$task_file" ] && return 0
    [ "$FROM" = "unknown" ] && return 0

    local cmd_id
    cmd_id=$(echo "$CONTENT" | grep -oP 'cmd_\d+' | head -1)

    local lock_file="${task_file}.lock"
    (
        flock -w 5 200 || exit 0

        local target_line=""

        if [ -n "$cmd_id" ]; then
            # Find last task with matching parent_cmd and status: assigned
            target_line=$(mawk -v cmd="$cmd_id" '
                /^- task_id:/ { found_parent = 0 }
                /parent_cmd:/ && $0 ~ cmd { found_parent = 1 }
                /status: assigned/ && found_parent { target = NR }
                END { if (target > 0) print target }
            ' "$task_file")
        fi

        # Fallback: last "status: assigned" in file
        [ -z "$target_line" ] && target_line=$(grep -n "status: assigned" "$task_file" | tail -1 | cut -d: -f1)

        [ -z "$target_line" ] && exit 0

        sed -i "${target_line}s/status: assigned/status: done/" "$task_file"
    ) 200>"$lock_file" 2>/dev/null

    return 0  # Never fail — message delivery must succeed
}

# Atomic write with lock (3 retries)
attempt=0
max_attempts=3

while [ $attempt -lt $max_attempts ]; do
    if _acquire_lock; then
        INBOX_PATH="$INBOX" \
        INBOX_MSG_ID="$MSG_ID" \
        INBOX_FROM="$FROM" \
        INBOX_TIMESTAMP="$TIMESTAMP" \
        INBOX_TYPE="$TYPE" \
        INBOX_CONTENT="$CONTENT" \
        "$SCRIPT_DIR/.venv/bin/python3" -c "
import yaml, sys, os

try:
    inbox_path = os.environ['INBOX_PATH']
    msg_id     = os.environ['INBOX_MSG_ID']
    from_      = os.environ['INBOX_FROM']
    timestamp  = os.environ['INBOX_TIMESTAMP']
    type_      = os.environ['INBOX_TYPE']
    content    = os.environ['INBOX_CONTENT']

    # Load existing inbox
    with open(inbox_path) as f:
        data = yaml.safe_load(f)

    # Initialize if needed
    if not data:
        data = {}
    if not data.get('messages'):
        data['messages'] = []

    # Add new message
    new_msg = {
        'id': msg_id,
        'from': from_,
        'timestamp': timestamp,
        'type': type_,
        'content': content,
        'read': False
    }
    data['messages'].append(new_msg)

    # Overflow protection: keep max 50 messages
    if len(data['messages']) > 50:
        msgs = data['messages']
        unread = [m for m in msgs if not m.get('read', False)]
        read = [m for m in msgs if m.get('read', False)]
        # Keep all unread + newest 30 read messages
        data['messages'] = unread + read[-30:]

    # Atomic write: tmp file + rename (prevents partial reads)
    import tempfile
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(inbox_path), suffix='.tmp')
    try:
        with os.fdopen(tmp_fd, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
        os.replace(tmp_path, inbox_path)
    except:
        os.unlink(tmp_path)
        raise

except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
"
        STATUS=$?
        # Force close_write event for inotifywait
        # (atomic rename alone doesn't trigger modify/close_write)
        [ $STATUS -eq 0 ] && touch "$INBOX" 2>/dev/null
        _release_lock

        # cmd_new時にRAG自動実行（バックグラウンド、失敗してもinbox配信に影響しない）
        [ "$TYPE" = "cmd_new" ] && bash "$(dirname "$0")/automation/cmd_rag_hook.sh" >> "$SCRIPT_DIR/logs/cmd_rag.log" 2>&1 &
        if [ $STATUS -eq 0 ]; then
            _update_cmd_status
            _update_task_done
            exit 0
        fi
        attempt=$((attempt + 1))
        [ $attempt -lt $max_attempts ] && sleep 1
    else
        # Lock timeout
        attempt=$((attempt + 1))
        if [ $attempt -lt $max_attempts ]; then
            echo "[inbox_write] Lock timeout for $INBOX (attempt $attempt/$max_attempts), retrying..." >&2
            sleep 1
        else
            echo "[inbox_write] Failed to acquire lock after $max_attempts attempts for $INBOX" >&2
            exit 1
        fi
    fi
done
