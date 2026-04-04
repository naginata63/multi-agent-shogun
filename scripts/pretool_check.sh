#!/usr/bin/env bash
# pretool_check.sh — PreToolUse hook
# ハーネスエンジニアリング: ルールを仕組みで強制する
#
# チェック項目:
# 1. tmux capture-pane は最低100行 (-S -100以上)
# 2. (将来追加: セマンティック検索強制、work/パスチェック等)

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)

# ツール名とコマンドを抽出
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

# Bashツールのみチェック
if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0
fi

# 自分自身のテスト実行はスキップ
if echo "$COMMAND" | grep -q "pretool_check"; then
  exit 0
fi

# ── チェック1: tmux capture-pane は最低100行 ──
if echo "$COMMAND" | grep -q "tmux capture-pane"; then
  # -S オプションの値を抽出
  LINES_VAL=$(echo "$COMMAND" | grep -oP '\-S\s+\-?\K\d+' | head -1)
  if [[ -n "$LINES_VAL" && "$LINES_VAL" -lt 100 ]]; then
    echo "BLOCKED: pane確認は最低100行（-S -100）。-S -${LINES_VAL} は短すぎる。誤判断の元。MEMORY.mdルール参照。"
    exit 2
  fi
  # -S オプションなし（デフォルト=短い）
  if ! echo "$COMMAND" | grep -q "\-S"; then
    echo "BLOCKED: tmux capture-paneに-Sオプションがない。-S -100 以上を指定せよ。"
    exit 2
  fi
fi

exit 0
