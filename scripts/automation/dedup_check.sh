#!/bin/bash
# dedup_check.sh — ナレッジ重複チェック（15分間隔cron）

LOCK_FILE="/tmp/automation_dedup.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || exit 0

cd /home/murakami/multi-agent-shogun
PYTHON=".venv/bin/python3"
source ~/.bashrc

# 永続ディレクトリに移行 (/tmp は再起動で消失 → 毎回全件再走査で負荷増)
FLAGS_DIR="/home/murakami/multi-agent-shogun/queue/.flags"
mkdir -p "$FLAGS_DIR"
LAST_CHECK="$FLAGS_DIR/dedup_last_check"
REPORT_FILE="queue/reports/dedup_warnings.yaml"

# 前回チェック以降に変更があったファイルを検出
CHANGED_FILES=""
if [ -f "$LAST_CHECK" ]; then
  CHANGED_FILES=$(find memory/ shared_context/ projects/*/context/ -name "*.md" -newer "$LAST_CHECK" 2>/dev/null)
else
  # 初回は全ファイル対象
  CHANGED_FILES=$(find memory/ shared_context/ projects/*/context/ -name "*.md" 2>/dev/null | head -5)
fi

if [ -z "$CHANGED_FILES" ]; then
  exit 0
fi

echo "$(date) Checking dedup for: $CHANGED_FILES" >> logs/dedup.log

# 各変更ファイルに対してdedup実行
for f in $CHANGED_FILES; do
  CONTENT=$(head -5 "$f" | tr '\n' ' ')
  $PYTHON scripts/cmd_helper.py dedup "$CONTENT" >> "$REPORT_FILE" 2>> logs/dedup.log
done

touch "$LAST_CHECK"
echo "$(date) Dedup check complete" >> logs/dedup.log
