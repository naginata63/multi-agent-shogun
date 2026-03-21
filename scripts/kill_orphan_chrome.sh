#!/bin/bash
# kill_orphan_chrome.sh
# ppid=1 (init) or ppid=2421 (systemd) のchrome-headless-shellをkill
# 起動後5分以内のプロセスは除外（レンダリング中の誤killを防止）

THRESHOLD_SEC=300  # 5分

for pid in $(pgrep -f chrome-headless-shell); do
    ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
    if [ "$ppid" = "1" ] || [ "$ppid" = "2421" ]; then
        elapsed=$(ps -o etimes= -p "$pid" 2>/dev/null | tr -d ' ')
        if [ -n "$elapsed" ] && [ "$elapsed" -gt "$THRESHOLD_SEC" ]; then
            kill "$pid" 2>/dev/null
            echo "$(date '+%Y-%m-%d %H:%M:%S') killed orphan chrome pid=$pid (elapsed=${elapsed}s)" >> /home/murakami/multi-agent-shogun/logs/orphan_chrome_cleanup.log
        fi
    fi
done
