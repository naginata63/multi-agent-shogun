#!/usr/bin/env bash
# chroma-mcp 健全性監視 — uvx重複 or プロセス大量発生 → ntfy alert
# cmd_1540: */5 cron → 重複プロセス検知で即時通知
# cmd_1540b: false positive修正 (正常=uvx1+python1=2個)
# ^/home anchor でshell wrapperを除外し正確にカウント

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ^/home anchor: bash wrapperは/bin/bashで始まるためマッチしない
UVX_COUNT=$(pgrep -f "^/home.*uv tool uvx.*chroma-mcp" 2>/dev/null | wc -l)
TOTAL_COUNT=$(pgrep -f "^/home.*chroma-mcp --client-type" 2>/dev/null | wc -l)

ALERT=false
REASON=""

if [ "$UVX_COUNT" -ge 2 ]; then
    ALERT=true
    REASON="uvx wrapper重複: ${UVX_COUNT}個 (閾値: 2)"
fi

if [ "$TOTAL_COUNT" -ge 5 ]; then
    ALERT=true
    REASON="${REASON:+${REASON} / }プロセス大量発生: ${TOTAL_COUNT}個 (閾値: 5)"
fi

if [ "$ALERT" = true ]; then
    bash "$SCRIPT_DIR/scripts/ntfy.sh" "⚠️ chroma-mcp 異常検知: ${REASON}"
fi
