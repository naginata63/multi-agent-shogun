#!/usr/bin/env bash
# pretool_check.sh — PreToolUse hook
# ハーネスエンジニアリング: ルールを仕組みで強制する
#
# チェック項目:
# 1. tmux capture-pane は最低100行 (-S -100以上)
# 2. 足軽のwork/cmd_*出力防止 + /tmp/書き込み禁止

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

INPUT=$(cat 2>/dev/null || true)

# ツール名とコマンドを抽出
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

# 自分自身のテスト実行はスキップ
if [[ "$TOOL_NAME" == "Bash" ]] && echo "$COMMAND" | grep -q "pretool_check"; then
  exit 0
fi

# ── チェック1: tmux capture-pane は最低100行 (Bashツールのみ) ──
if [[ "$TOOL_NAME" == "Bash" ]] && echo "$COMMAND" | grep -q "tmux capture-pane"; then
  # -S オプションの値を抽出
  LINES_VAL=$(echo "$COMMAND" | grep -oP '\-S\s+\-?\K\d+' | head -1)
  if [[ -n "$LINES_VAL" && "$LINES_VAL" -lt 100 ]]; then
    echo "BLOCKED: pane確認は最低100行（-S -100）。-S -${LINES_VAL} は短すぎる。誤判断の元。MEMORY.mdルール参照。" >&2
    exit 2
  fi
  # -S オプションなし（デフォルト=短い）
  if ! echo "$COMMAND" | grep -q "\-S"; then
    echo "BLOCKED: tmux capture-paneに-Sオプションがない。-S -100 以上を指定せよ。" >&2
    exit 2
  fi
fi

# ── チェック2: 足軽のwork/cmd_*出力防止 + /tmp/禁止 (Write/Editツール) ──
if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
  FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

  # 足軽判定
  AGENT_ID=""
  if [ -n "${TMUX_PANE:-}" ]; then
    AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
  fi

  # 足軽のみチェック
  if [[ "$AGENT_ID" == ashigaru* ]]; then
    # Phase 2: タスクYAMLからtarget_pathを読み取り、一致するパスは許可
    AGENT_NUM="${AGENT_ID#ashigaru}"
    TASK_YAML="${REPO_DIR}/queue/tasks/ashigaru${AGENT_NUM}.yaml"
    if [ -f "$TASK_YAML" ]; then
      TARGET_PATH=$(grep -A5 'status: assigned' "$TASK_YAML" | grep 'target_path:' | head -1 | sed 's/.*target_path: *//' | tr -d '"' | tr -d "'" || true)
      if [ -n "$TARGET_PATH" ] && echo "$FILE_PATH" | grep -qF "$TARGET_PATH"; then
        exit 0  # target_pathと一致 → 許可
      fi
    fi

    # work/cmd_* パターン検出
    if echo "$FILE_PATH" | grep -qE '/work/cmd_[0-9]+/'; then
      echo "BLOCKED: 足軽はwork/cmd_*に直接書き込み禁止。タスクYAMLのtarget_pathに出力せよ。パス: $FILE_PATH" >&2
      exit 2
    fi

    # /tmp/ パターン検出
    if [[ "$FILE_PATH" == /tmp/* ]]; then
      echo "BLOCKED: /tmp/への出力禁止（再起動で消える）。work/配下またはtarget_pathに出力せよ。パス: $FILE_PATH" >&2
      exit 2
    fi
  fi
fi

exit 0
