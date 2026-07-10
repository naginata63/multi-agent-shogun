#!/usr/bin/env bash
# litestream_health_check.sh — litestream の異常を早期検知
# 直近30分の litestream.log で "compaction failed" / "consecutive_errors" が一定数以上検出されたら ntfy 通知
# cron 30分毎実行想定: */30 * * * * /home/murakami/multi-agent-shogun/scripts/litestream_health_check.sh
# 2026-04-28 殿命: A+B 恒久対策に加え再発早期検知の補助監視
set -uo pipefail

REPO_DIR="/home/murakami/multi-agent-shogun"
LOG="$REPO_DIR/logs/litestream.log"
HEALTH_LOG="$REPO_DIR/logs/litestream_health_check.log"
NTFY="$REPO_DIR/scripts/ntfy.sh"
TS=$(date "+%Y-%m-%dT%H:%M:%S%:z")

# 直近30分のログを抽出 (ts pattern: time=YYYY-MM-DDTHH:MM:SS)
SINCE=$(date -d "30 min ago" +"%Y-%m-%dT%H:%M:%S")

# compaction failed / consecutive_errors / sync error の検出件数
COMPACT=$(awk -v since="$SINCE" 'BEGIN{c=0} /compaction failed/ && $0 > "time="since {c++} END{print c}' "$LOG" 2>/dev/null || echo 0)
CONSEC=$(awk -v since="$SINCE" 'BEGIN{c=0} /consecutive_errors/ && $0 > "time="since {c++} END{print c}' "$LOG" 2>/dev/null || echo 0)
SYNC_ERR=$(awk -v since="$SINCE" 'BEGIN{c=0} /sync error/ && $0 > "time="since {c++} END{print c}' "$LOG" 2>/dev/null || echo 0)

TOTAL=$((COMPACT + CONSEC + SYNC_ERR))
echo "[$TS] compaction=$COMPACT consec=$CONSEC sync_err=$SYNC_ERR total=$TOTAL" >> "$HEALTH_LOG"

# 閾値: 直近30分で 6回以上 = 5分毎リトライが6回連続失敗 = 30分間ずっと失敗
if [ "$TOTAL" -ge 6 ]; then
    MSG="🚨 litestream 異常検知: 直近30分で compaction失敗${COMPACT}回・consecutive_errors${CONSEC}回・sync error${SYNC_ERR}回。手当て: rm 古い ltx ファイル + systemctl --user restart litestream"
    if [ -x "$NTFY" ]; then
        bash "$NTFY" "$MSG" 2>/dev/null
    fi
    echo "[$TS] ALERT sent: $MSG" >> "$HEALTH_LOG"
fi

exit 0
