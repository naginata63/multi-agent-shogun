#!/bin/bash
# cmd_rag_hook.sh — cmd_new時にRAG自動実行
# inbox_write.shからバックグラウンド呼び出しされる

LOCK_FILE="/tmp/automation_cmd_rag.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || { echo "already running"; exit 0; }

cd /home/murakami/multi-agent-shogun
source venv/bin/activate
source ~/.bashrc

# shogun_to_karo.yamlの末尾のcmdを取得
LAST_CMD_ID=$(python3 -c "
import yaml
with open('queue/shogun_to_karo.yaml') as f:
    data = yaml.safe_load(f)
cmds = data.get('commands', [])
if cmds:
    print(cmds[-1].get('id', ''))
")

if [ -z "$LAST_CMD_ID" ]; then
  echo "$(date) No cmd found" >> logs/cmd_rag.log
  exit 0
fi

# 既に処理済みか確認
LAST_PROCESSED="/tmp/cmd_rag_last_processed"
if [ -f "$LAST_PROCESSED" ] && [ "$(cat $LAST_PROCESSED)" = "$LAST_CMD_ID" ]; then
  echo "$(date) Already processed $LAST_CMD_ID" >> logs/cmd_rag.log
  exit 0
fi

# cmdのpurpose+commandを取得してRAG実行
QUERY=$(python3 -c "
import yaml
with open('queue/shogun_to_karo.yaml') as f:
    data = yaml.safe_load(f)
cmds = data.get('commands', [])
if cmds:
    cmd = cmds[-1]
    purpose = cmd.get('purpose', '')
    command = cmd.get('command', '')[:200]
    print(f'{purpose} {command}')
")

echo "$(date) Running RAG for $LAST_CMD_ID: $QUERY" >> logs/cmd_rag.log
python3 scripts/cmd_helper.py rag "$QUERY" --json > queue/reports/rag_suggestions.yaml 2>&1

echo "$LAST_CMD_ID" > "$LAST_PROCESSED"
echo "$(date) RAG complete for $LAST_CMD_ID" >> logs/cmd_rag.log
