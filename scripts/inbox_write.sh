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

        # === MCP Phase 3: Dual-write (副系) ===
        # ファイル書き込み成功後、MCP SQLite DBにも書き込む
        # 失敗はログに記録するだけで、主系に影響しない
        if [ $STATUS -eq 0 ]; then
            MCP_DB="$SCRIPT_DIR/work/cmd_1068/experiment.db"
            MCP_LOG="$SCRIPT_DIR/logs/mcp_dual_write.log"
            if [ -d "$(dirname "$MCP_DB")" ]; then
                MCP_DB="$MCP_DB" \
                MCP_TO="$TARGET" \
                MCP_FROM="$FROM" \
                MCP_TYPE="$TYPE" \
                MCP_CONTENT="$CONTENT" \
                MCP_TS="$TIMESTAMP" \
                MCP_MSG_ID="$MSG_ID" \
                python3 -c "
import sqlite3, os, sys
try:
    db_path = os.environ['MCP_DB']
    if not os.path.exists(os.path.dirname(db_path)):
        sys.exit(0)
    conn = sqlite3.connect(db_path, timeout=3)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_agent TEXT NOT NULL,
        from_agent TEXT NOT NULL,
        content TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'message',
        file_msg_id TEXT,
        file_timestamp TEXT,
        read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )''')
    conn.execute('INSERT INTO messages (to_agent, from_agent, content, type, file_msg_id, file_timestamp) VALUES (?, ?, ?, ?, ?, ?)',
        (os.environ['MCP_TO'], os.environ['MCP_FROM'], os.environ['MCP_CONTENT'],
         os.environ['MCP_TYPE'], os.environ['MCP_MSG_ID'], os.environ['MCP_TS']))
    conn.commit()
    conn.close()
except Exception as e:
    print(f'[{os.environ.get(\"MCP_TS\",\"?\")}] MCP dual-write failed: {e}', file=sys.stderr)
    sys.exit(1)
" >>"$MCP_LOG" 2>&1 || true &
            fi
        fi
        # === MCP Phase 3 end ===

        # cmd_new時にRAG自動実行（バックグラウンド、失敗してもinbox配信に影響しない）
        [ "$TYPE" = "cmd_new" ] && bash "$(dirname "$0")/automation/cmd_rag_hook.sh" >> "$SCRIPT_DIR/logs/cmd_rag.log" 2>&1 &
        [ $STATUS -eq 0 ] && exit 0
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
