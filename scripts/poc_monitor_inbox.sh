#!/usr/bin/env bash
# poc_monitor_inbox.sh — Monitor tool POC: inbox YAML の変更を stdout に垂れ流す
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$SCRIPT_DIR/queue/inbox/karo.yaml}"

if [ ! -f "$TARGET" ]; then
    echo "ERROR: $TARGET not found" >&2
    exit 1
fi

echo "[poc_monitor] Watching: $TARGET"
tail -f "$TARGET" 2>/dev/null
