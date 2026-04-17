#!/usr/bin/env bash
# posttool_cmd_check.sh — PostToolUse hook: 将軍cmd拡大解釈警告
# shogun_to_karo.yaml更新後、lord_originalとcommandを比較し、
# 殿が指示していない動作がcommandに含まれていればWARNING表示。
# PostToolUseはblock不可のため、WARNINGのみ（exit 0固定）。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT=$(cat 2>/dev/null || true)

# ツール名とファイルパスを抽出
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

# shogun_to_karo.yaml以外は即exit
BASH_CMD=""
if [[ "$TOOL_NAME" == "Bash" ]]; then
  BASH_CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || true)
  if [[ "$BASH_CMD" != *"shogun_to_karo.yaml"* ]]; then
    exit 0
  fi
  # Bashの場合はFILE_PATHでなくコマンド内容で判定済み
elif [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
  exit 0
elif [[ "$FILE_PATH" != *"shogun_to_karo.yaml" ]]; then
  exit 0
fi

# 将軍のみ対象
AGENT_ID=""
if [ -n "${TMUX_PANE:-}" ]; then
  AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
fi
if [[ "$AGENT_ID" != "shogun" ]]; then
  exit 0
fi

# 最新cmdのlord_originalとcommandを抽出
YAML_FILE="$(dirname "$SCRIPT_DIR")/queue/shogun_to_karo.yaml"
if [ ! -f "$YAML_FILE" ]; then
  exit 0
fi

# Python で最新cmdからlord_original + command を抽出
COMPARISON=$(YAML_FILE="$YAML_FILE" python3 -c "
import yaml, os, sys

yaml_file = os.environ['YAML_FILE']
with open(yaml_file) as f:
    data = yaml.safe_load(f) or {}

commands = data.get('commands', [])
if not commands:
    sys.exit(0)

# 最新cmd（末尾）
latest = commands[-1]
lord_original = latest.get('lord_original', '')
command = latest.get('command', '')

if not lord_original or not command:
    sys.exit(0)

# commandを500文字に切り詰め（トークンコスト制御）
command_truncated = command[:500]

print(f'LORD:{lord_original}')
print(f'CMD:{command_truncated}')
" 2>/dev/null || true)

if [ -z "$COMPARISON" ]; then
  exit 0
fi

LORD_TEXT=$(echo "$COMPARISON" | grep '^LORD:' | sed 's/^LORD://')
CMD_TEXT=$(echo "$COMPARISON" | grep '^CMD:' | sed 's/^CMD://')

if [ -z "$LORD_TEXT" ] || [ -z "$CMD_TEXT" ]; then
  exit 0
fi

# claude -p で意味的比較（30秒タイムアウト）
PROMPT="以下の殿の指示と将軍のcommandを比較せよ。commandに殿が指示していない判断・変更・追加はあるか？あれば指摘せよ。なければ「OK」とだけ答えよ。50語以内。
殿の指示: ${LORD_TEXT}
将軍のcommand: ${CMD_TEXT}"

RESULT=$(echo "$PROMPT" | timeout 30 claude -p --model opus --output-format text --max-budget-usd 0.50 2>/dev/null || echo "TIMEOUT")

if [[ "$RESULT" == "TIMEOUT" ]]; then
  exit 0
fi

# OK以外ならWARNING表示
if [[ "$RESULT" != *"OK"* ]] && [[ -n "$RESULT" ]]; then
  echo "" >&2
  echo "⚠️ cmd拡大解釈警告: $RESULT" >&2
  echo "lord_original: ${LORD_TEXT}" >&2
  echo "上記の警告が正当な展開であれば無視してよい。不要な動作を追加していたらcommandを修正せよ。" >&2
  echo "" >&2
fi

exit 0
