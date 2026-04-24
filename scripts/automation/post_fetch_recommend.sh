#!/bin/bash
# post_fetch_recommend.sh — auto_fetch後の自動推薦+感情分析
# cron: 18:25, 19:40 （auto_fetchの10分後に実行）

LOCK_FILE="/tmp/automation_post_fetch.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || { echo "already running"; exit 0; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG="$REPO_DIR/projects/dozle_kirinuki/logs/post_fetch.log"
REPORT_DIR="$REPO_DIR/queue/reports"

cd "$REPO_DIR/projects/dozle_kirinuki"
source "$REPO_DIR/venv/bin/activate"
source ~/.bashrc  # GEMINI_API_KEY

# 最新動画IDを取得（auto_fetchのログから）— sentimentのみ使用
LATEST_VIDEO=$(tail -1 logs/auto_fetch.log 2>/dev/null | grep -oP '[a-zA-Z0-9_-]{11}' | tail -1)

# recommend実行（--videoオプション不要、常に実行）
echo "$(date) Running recommend (top 10)" >> "$LOG"
python3 scripts/embedding_analytics.py recommend \
  --top 10 \
  --output "$REPORT_DIR/auto_recommend.yaml" \
  2>> "$LOG"

# sentiment実行（最新動画IDがあればフィルタリング）
if [ -n "$LATEST_VIDEO" ]; then
  echo "$(date) Running sentiment for $LATEST_VIDEO" >> "$LOG"
  python3 scripts/embedding_analytics.py sentiment \
    --video "$LATEST_VIDEO" \
    --output "$REPORT_DIR/auto_sentiment.yaml" \
    2>> "$LOG"
else
  echo "$(date) Running sentiment (no video filter)" >> "$LOG"
  python3 scripts/embedding_analytics.py sentiment \
    --output "$REPORT_DIR/auto_sentiment.yaml" \
    2>> "$LOG"
fi

echo "$(date) Post-fetch automation complete" >> "$LOG"
