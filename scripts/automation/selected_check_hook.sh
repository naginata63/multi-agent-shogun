#!/bin/bash
# selected_check_hook.sh <selected.json_path>
# main.pyからselected.json出力後に呼ばれる

SELECTED_PATH="$1"
if [ -z "$SELECTED_PATH" ] || [ ! -f "$SELECTED_PATH" ]; then
  echo "$(date) No selected.json: $SELECTED_PATH" >> /home/murakami/multi-agent-shogun/logs/selected_check.log
  exit 0
fi

LOCK_FILE="/tmp/automation_selected_check.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || exit 0

cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
source /home/murakami/multi-agent-shogun/venv/bin/activate
source ~/.bashrc

VIDEO_ID=$(python3 -c "import json,sys; d=json.load(open('$SELECTED_PATH')); print(d.get('video_id','unknown'))")

echo "$(date) Running autotag+overlap for $VIDEO_ID" >> /home/murakami/multi-agent-shogun/logs/selected_check.log

# autotag
python3 scripts/embedding_analytics.py autotag \
  --output /home/murakami/multi-agent-shogun/queue/reports/selected_autotag_${VIDEO_ID}.yaml \
  2>> /home/murakami/multi-agent-shogun/logs/selected_check.log

# overlap
python3 scripts/embedding_analytics.py overlap \
  --selected "$SELECTED_PATH" \
  --output /home/murakami/multi-agent-shogun/queue/reports/selected_overlap_${VIDEO_ID}.yaml \
  2>> /home/murakami/multi-agent-shogun/logs/selected_check.log

echo "$(date) Selected check complete for $VIDEO_ID" >> /home/murakami/multi-agent-shogun/logs/selected_check.log
