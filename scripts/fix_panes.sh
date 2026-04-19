#!/bin/bash
# fix_panes.sh — pane復元スクリプト
# 消失したpaneを作成し、Claude CLIを起動し、agent_idを設定する
#
# Usage: bash scripts/fix_panes.sh
#   - 足りないpaneを自動で作成
#   - bashのままのpaneにClaude CLIを起動
#   - 全paneのagent_idを正しく設定

set -euo pipefail

SESSION="multiagent"
WINDOW=0
WORKDIR="/home/murakami/multi-agent-shogun"

# CLI Adapter読み込み（settings.yaml の type/model に従って起動コマンドを構築）
if [ -f "$WORKDIR/lib/cli_adapter.sh" ]; then
  # shellcheck disable=SC1091
  source "$WORKDIR/lib/cli_adapter.sh"
  CLI_ADAPTER_LOADED=true
else
  CLI_ADAPTER_LOADED=false
fi

# 正しいpane配置
AGENTS=(karo ashigaru1 ashigaru2 ashigaru3 ashigaru4 ashigaru5 ashigaru6 ashigaru7 gunshi)
TOTAL=9

echo "=== fix_panes.sh: pane復元開始 ==="

# Step 1: 現在のpane数を確認
CURRENT=$(tmux list-panes -t "${SESSION}:${WINDOW}" 2>/dev/null | wc -l)
echo "現在のpane数: ${CURRENT} / 必要: ${TOTAL}"

# Step 2: 足りないpaneを作成
if [ "$CURRENT" -lt "$TOTAL" ]; then
  NEED=$((TOTAL - CURRENT))
  echo "${NEED}個のpaneを追加作成..."
  for i in $(seq 1 "$NEED"); do
    tmux split-window -t "${SESSION}:${WINDOW}" -v -c "$WORKDIR"
    # レイアウトを均等化（paneが小さすぎてsplitできなくなるのを防ぐ）
    tmux select-layout -t "${SESSION}:${WINDOW}" tiled 2>/dev/null || true
  done
  echo "pane作成完了"
fi

# Step 3: pane数を再確認
CURRENT=$(tmux list-panes -t "${SESSION}:${WINDOW}" 2>/dev/null | wc -l)
if [ "$CURRENT" -ne "$TOTAL" ]; then
  echo "ERROR: pane数が${TOTAL}にならない（現在${CURRENT}）。手動で確認してください。"
  exit 1
fi

# Step 4: bashのままのpaneにCLI起動（settings.yamlに従いClaude/GLM/Codex等を選択）
echo "CLI起動チェック..."
NEW_PANES=()  # 新規起動したpaneのインデックスを記録
for i in $(seq 0 $((TOTAL - 1))); do
  CMD=$(tmux list-panes -t "${SESSION}:${WINDOW}" -F '#{pane_index} #{pane_current_command}' | awk -v idx="$i" '$1 == idx {print $2}')
  AGENT_ID="${AGENTS[$i]}"
  if [ "$CMD" = "bash" ] || [ "$CMD" = "zsh" ]; then
    if [ "$CLI_ADAPTER_LOADED" = true ]; then
      LAUNCH_CMD=$(build_cli_command "$AGENT_ID")
      CLI_TYPE=$(get_cli_type "$AGENT_ID")
    else
      # フォールバック（cli_adapter.sh不在時のみ）
      if [ "$i" -eq 0 ] || [ "$i" -eq $((TOTAL - 1)) ]; then
        LAUNCH_CMD="claude --model 'opus[1m]' --dangerously-skip-permissions"
      else
        LAUNCH_CMD="claude --model 'sonnet' --dangerously-skip-permissions"
      fi
      CLI_TYPE="claude"
    fi
    echo "  0.${i} (${AGENT_ID}): bashを検出 → ${CLI_TYPE}起動"
    tmux send-keys -t "${SESSION}:${WINDOW}.${i}" "cd ${WORKDIR} && ${LAUNCH_CMD}" Enter
    NEW_PANES+=("$i")
    sleep 2
  else
    echo "  0.${i} (${AGENT_ID}): ${CMD}（既にCLI起動済み）"
  fi
done

# Step 4.5: 新規起動したpaneに /advisor sonnet を自動送信
if [ "${#NEW_PANES[@]}" -gt 0 ]; then
  echo "新規起動paneに /advisor sonnet を送信..."
  echo "CLI起動完了を待機中（10秒）..."
  sleep 10
  for i in "${NEW_PANES[@]}"; do
    echo "  0.${i}: /advisor sonnet 送信"
    tmux send-keys -t "${SESSION}:${WINDOW}.${i}" "/advisor sonnet" Enter
    sleep 0.3
  done
  echo "  /advisor sonnet送信完了。"
fi

# Step 5: agent_idを設定
echo "agent_id設定..."
for i in $(seq 0 $((TOTAL - 1))); do
  tmux set-option -t "${SESSION}:${WINDOW}.${i}" -p @agent_id "${AGENTS[$i]}"
done

# Step 6: 確認
echo ""
echo "=== 復元結果 ==="
for i in $(seq 0 $((TOTAL - 1))); do
  ID=$(tmux display-message -t "${SESSION}:${WINDOW}.${i}" -p '#{@agent_id}' 2>/dev/null)
  CMD=$(tmux list-panes -t "${SESSION}:${WINDOW}" -F '#{pane_index} #{pane_current_command}' | awk -v idx="$i" '$1 == idx {print $2}')
  echo "  0.${i} = ${ID} (${CMD})"
done
echo "=== fix_panes.sh: 完了 ==="
