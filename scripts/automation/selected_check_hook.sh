#!/bin/bash
# selected_check_hook.sh <selected.json_path>
# main.pyからselected.json出力後に呼ばれる

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$REPO_DIR/logs/selected_check.log"

SELECTED_PATH="$1"
if [ -z "$SELECTED_PATH" ] || [ ! -f "$SELECTED_PATH" ]; then
  echo "$(date) No selected.json: $SELECTED_PATH" >> "$LOG_FILE"
  exit 0
fi

LOCK_FILE="/tmp/automation_selected_check.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || exit 0

cd "$REPO_DIR/projects/dozle_kirinuki"
source "$REPO_DIR/venv/bin/activate"
source ~/.bashrc

VIDEO_ID=$(python3 -c "import json,sys; d=json.load(open('$SELECTED_PATH')); print(d.get('video_id','unknown'))")

echo "$(date) Running autotag+overlap for $VIDEO_ID" >> "$LOG_FILE"

# autotag
python3 scripts/embedding_analytics.py autotag \
  --output "$REPO_DIR/queue/reports/selected_autotag_${VIDEO_ID}.yaml" \
  2>> "$LOG_FILE"

# overlap
python3 scripts/embedding_analytics.py overlap \
  --selected "$SELECTED_PATH" \
  --output "$REPO_DIR/queue/reports/selected_overlap_${VIDEO_ID}.yaml" \
  2>> "$LOG_FILE"

echo "$(date) Selected check complete for $VIDEO_ID" >> "$LOG_FILE"
