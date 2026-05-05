#!/usr/bin/env bash
# notify.sh — PushNotification wrapper (ntfy.sh呼出 + 将来PushNotification tool呼出点)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ntfy.sh に丸投げ
bash "$SCRIPT_DIR/scripts/ntfy.sh" "$@"

# 送信ログ
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
echo "[$(date '+%Y-%m-%dT%H:%M:%S')] sent: $*" >> "$LOG_DIR/notify_sent.log"
