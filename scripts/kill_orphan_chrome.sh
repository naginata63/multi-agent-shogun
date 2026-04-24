#!/bin/bash
# kill_orphan_chrome.sh
# ppid=1 (init) or ppid name=systemd のchrome-headless-shellをkill
# 起動後5分以内のプロセスは除外（レンダリング中の誤killを防止）

THRESHOLD_SEC=300  # 5分
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/orphan_chrome_cleanup.log"

for pid in $(pgrep -f chrome-headless-shell); do
    ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
    ppid_name=$(ps -o comm= -p "$ppid" 2>/dev/null || echo "")
    if [ "$ppid" = "1" ] || [ "$ppid_name" = "systemd" ]; then
        elapsed=$(ps -o etimes= -p "$pid" 2>/dev/null | tr -d ' ')
        if [ -n "$elapsed" ] && [ "$elapsed" -gt "$THRESHOLD_SEC" ]; then
            kill "$pid" 2>/dev/null
            echo "$(date '+%Y-%m-%d %H:%M:%S') killed orphan chrome pid=$pid (elapsed=${elapsed}s)" >> "$LOG_FILE"
        fi
    fi
done
