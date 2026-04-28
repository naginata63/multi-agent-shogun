#!/usr/bin/env bash
# chroma-mcp 健全性監視 — pgrep -fc chroma-mcp カウント ≥ 2 → ntfy alert
# cmd_1540: */5 cron → 重複プロセス検知で即時通知

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COUNT=$(pgrep -fc chroma-mcp 2>/dev/null || echo 0)

if [ "$COUNT" -ge 2 ]; then
    bash "$SCRIPT_DIR/scripts/ntfy.sh" "⚠️ chroma-mcp 重複プロセス検知: ${COUNT}個稼働中 (閾値: 2)"
fi
