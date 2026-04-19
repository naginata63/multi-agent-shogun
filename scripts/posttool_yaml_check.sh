#!/bin/bash
# PostToolUse hook: queue/*.yaml書き込み後にYAML構文チェック
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR="$(dirname "$SCRIPT_DIR")"
PYTHON="${WORKDIR}/.venv/bin/python3"
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)
if [[ "$FILE_PATH" == */queue/*.yaml ]]; then
  result=$("$PYTHON" -c "import yaml,sys; yaml.safe_load(open('$FILE_PATH'))" 2>&1)
  if [ $? -ne 0 ]; then
    echo "WARNING: YAML syntax error in $FILE_PATH"
    echo "$result"
  fi
fi
