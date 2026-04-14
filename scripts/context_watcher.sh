#!/bin/bash
# context_watcher.sh — コンテキスト残量監視 → 自動handoff/clear/rehydrate
# 使い方: bash scripts/context_watcher.sh &
#
# statusline.shが /tmp/claude_context_{pane_id}.txt に used_percentage を書き出す
# このスクリプトが定期的にチェックし、閾値を超えたら:
#   1. /handoff 送信
#   2. handoffファイル生成を検知（最大60秒待ち）
#   3. 検知後に /clear 送信
#   4. /rehydrate 送信

set -u

THRESHOLD=${CONTEXT_THRESHOLD:-75}  # used%がこの値を超えたらトリガー
CHECK_INTERVAL=30                    # 秒
COOLDOWN=300                         # 同一ペインへの再送信クールダウン（秒）
HANDOFF_TIMEOUT=60                   # handoffファイル生成の最大待ち時間（秒）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HANDOFF_DIR="${PROJECT_DIR}/queue/handoff"
LOG_FILE="${PROJECT_DIR}/logs/context_watcher.log"

mkdir -p "$(dirname "$LOG_FILE")" "$HANDOFF_DIR"

declare -A last_triggered  # pane_id -> last trigger timestamp

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

wait_for_handoff() {
  local agent_id="$1"
  local before_ts="$2"
  local elapsed=0

  while [ "$elapsed" -lt "$HANDOFF_TIMEOUT" ]; do
    # handoffファイルを探す（before_tsより新しいもの）
    latest=$(ls -t "${HANDOFF_DIR}/${agent_id}_"*.md 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
      file_ts=$(stat -c %Y "$latest" 2>/dev/null || echo 0)
      if [ "$file_ts" -gt "$before_ts" ]; then
        log "HANDOFF DETECTED: ${latest} (waited ${elapsed}s)"
        return 0
      fi
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done

  log "HANDOFF TIMEOUT: agent=${agent_id} (waited ${HANDOFF_TIMEOUT}s)"
  return 1
}

log "context_watcher started (threshold=${THRESHOLD}%, interval=${CHECK_INTERVAL}s, cooldown=${COOLDOWN}s)"

while true; do
  for ctx_file in /tmp/claude_context_*.txt; do
    [ -f "$ctx_file" ] || continue

    # ファイルが古すぎる（5分以上前）ならスキップ（セッション終了済み）
    file_age=$(( $(date +%s) - $(stat -c %Y "$ctx_file" 2>/dev/null || echo 0) ))
    if [ "$file_age" -gt 300 ]; then
      continue
    fi

    pane_id=$(basename "$ctx_file" .txt | sed 's/claude_context_//')
    used_pct=$(cat "$ctx_file" 2>/dev/null | tr -d '[:space:]')

    # 数値チェック
    if ! [[ "$used_pct" =~ ^[0-9]+\.?[0-9]*$ ]]; then
      continue
    fi

    # 整数に変換（切り捨て）
    used_int=${used_pct%%.*}

    if [ "$used_int" -ge "$THRESHOLD" ]; then
      now=$(date +%s)
      last=${last_triggered[$pane_id]:-0}

      if [ $(( now - last )) -lt "$COOLDOWN" ]; then
        continue
      fi

      # ペインのagent_idを取得
      agent_id=$(tmux display-message -t "%${pane_id}" -p '#{@agent_id}' 2>/dev/null || echo "unknown")

      if [ "$agent_id" = "unknown" ] || [ -z "$agent_id" ]; then
        log "SKIP: pane=%${pane_id} has no agent_id"
        continue
      fi

      log "TRIGGER: pane=%${pane_id} agent=${agent_id} used=${used_pct}% (>= ${THRESHOLD}%)"

      # Step 1: /handoff 送信
      before_ts=$(date +%s)
      tmux send-keys -t "%${pane_id}" "/handoff" Enter
      log "SENT: /handoff to pane=%${pane_id}"

      # Step 2: handoffファイル生成を待つ
      if wait_for_handoff "$agent_id" "$before_ts"; then
        # Step 3: handoff確認 → /clear 送信
        sleep 3  # handoffの最終書き込み猶予
        tmux send-keys -t "%${pane_id}" "/clear" Enter
        log "SENT: /clear to pane=%${pane_id}"

        sleep 5  # clear完了待ち

        # Step 4: /rehydrate 送信
        tmux send-keys -t "%${pane_id}" "/rehydrate" Enter
        log "SENT: /rehydrate to pane=%${pane_id}"

        last_triggered[$pane_id]=$now
        log "COMPLETE: handoff→clear→rehydrate for pane=%${pane_id} agent=${agent_id}"
      else
        # handoffファイルが生成されなかった → clearしない（安全側）
        log "ABORT: handoff not confirmed. Skipping clear for pane=%${pane_id} agent=${agent_id}"
        last_triggered[$pane_id]=$now  # クールダウンは設定
      fi
    fi
  done

  sleep "$CHECK_INTERVAL"
done
