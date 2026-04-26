#!/bin/bash
# litestream_keepalive.sh (cmd_1495)
# 5min cron で systemd user unit が落ちていたら起動・systemd 経由を最優先・直 nohup は最終 fallback
# 監視対象: queue/cmds.db を replicate するプロセス

set -u
LOG=/home/murakami/multi-agent-shogun/logs/litestream_keepalive.log
NOW=$(date '+%Y-%m-%dT%H:%M:%S%z')

# 既に replicate プロセスが動いていれば何もしない
if pgrep -fa "litestream replicate.*\.litestream\.yml" >/dev/null 2>&1; then
  exit 0
fi

echo "[$NOW] litestream not running — attempting recovery" >> "$LOG"

# 1) systemd user unit を試す (推奨経路)
if systemctl --user --quiet is-enabled litestream.service 2>/dev/null; then
  if systemctl --user start litestream.service 2>>"$LOG"; then
    echo "[$NOW] systemctl --user start litestream.service: OK" >> "$LOG"
    exit 0
  fi
fi

# 2) 最終 fallback: 直 nohup 起動 (systemd unit 故障時)
nohup /usr/bin/litestream replicate -config /home/murakami/.litestream.yml \
  >> /home/murakami/multi-agent-shogun/logs/litestream.log 2>&1 &
disown
echo "[$NOW] FALLBACK nohup launch (pid=$!)" >> "$LOG"

# ntfy 通知 (fallback 経路 = systemd 故障)
if [ -x /home/murakami/multi-agent-shogun/scripts/ntfy.sh ]; then
  /home/murakami/multi-agent-shogun/scripts/ntfy.sh \
    "🚨 litestream systemd unit 故障・nohup fallback で復旧 (pid=$!)" \
    >> "$LOG" 2>&1 || true
fi
