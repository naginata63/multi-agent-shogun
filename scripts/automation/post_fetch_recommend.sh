#!/bin/bash
# post_fetch_recommend.sh — auto_fetch後の自動推薦+感情分析
# cron: 18:25, 19:40 （auto_fetchの10分後に実行）

LOCK_FILE="/tmp/automation_post_fetch.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || { echo "already running"; exit 0; }

cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
source /home/murakami/multi-agent-shogun/venv/bin/activate
source ~/.bashrc  # GEMINI_API_KEY

# 最新動画IDを取得（auto_fetchのログから）
LATEST_VIDEO=$(tail -1 logs/auto_fetch.log | grep -oP '[a-zA-Z0-9_-]{11}' | tail -1)

if [ -z "$LATEST_VIDEO" ]; then
  echo "$(date) No new video found" >> /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/logs/post_fetch.log
  exit 0
fi

# recommend実行
echo "$(date) Running recommend for $LATEST_VIDEO" >> /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/logs/post_fetch.log
python3 scripts/embedding_analytics.py recommend \
  --video "$LATEST_VIDEO" \
  --top 10 \
  >> /home/murakami/multi-agent-shogun/queue/reports/auto_recommend.yaml 2>&1

# sentiment実行
echo "$(date) Running sentiment for $LATEST_VIDEO" >> /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/logs/post_fetch.log
python3 scripts/embedding_analytics.py sentiment \
  --video "$LATEST_VIDEO" \
  >> /home/murakami/multi-agent-shogun/queue/reports/auto_sentiment.yaml 2>&1

echo "$(date) Post-fetch automation complete" >> /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/logs/post_fetch.log
