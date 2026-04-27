#!/usr/bin/env bash
# semantic_index_hook.sh — PreToolUse hook for semantic index auto-update
#
# トリガー: Write ツールで新規 .py ファイルが作成される時
# アクション: semantic_search.py update をバックグラウンド実行（3秒遅延）
#
# 設計:
#   PreToolUse はツール実行「前」に発火する。
#   新規ファイル = まだ存在しないパスへの Write を検出。
#   ファイル書き込み完了を待つため 3 秒遅延してからインデックス更新。
#   フック自体は即座に exit 0（本体作業をブロックしない）。
#   重複実行防止: ロックファイルで 60 秒以内の再実行を抑制。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCKFILE="/tmp/semantic_index_update.lock"
FLOCK_FILE="$SCRIPT_DIR/data/semantic_index/.lock"
LOGFILE="$SCRIPT_DIR/logs/semantic_index_hook.log"

# flock for concurrent write protection — exit if another instance holds the lock
exec 9>"$FLOCK_FILE"
flock -n 9 || exit 0

INPUT=$(cat 2>/dev/null || true)

# ツール名を抽出
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)

# Write ツール以外はスキップ
if [[ "$TOOL_NAME" != "Write" ]]; then
  exit 0
fi

# ファイルパスを抽出
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

# .py ファイル以外はスキップ
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# 既存ファイルへの上書きはスキップ（新規作成のみ）
if [[ -f "$FILE_PATH" ]]; then
  exit 0
fi

# 重複実行防止: 60 秒以内にすでにスケジュール済みならスキップ
if [[ -f "$LOCKFILE" ]]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCKFILE" 2>/dev/null || echo 0) ))
  if [[ $LOCK_AGE -lt 60 ]]; then
    exit 0
  fi
fi

# ロックファイル作成 + バックグラウンドで遅延更新
touch "$LOCKFILE"
(
  sleep 3
  source ~/.bashrc 2>/dev/null
  cd "$SCRIPT_DIR"
  echo "[$(date '+%Y-%m-%dT%H:%M:%S')] Auto-update triggered by new file: $FILE_PATH" >> "$LOGFILE"
  python3 scripts/semantic_search.py update >> "$LOGFILE" 2>&1
  rm -f "$LOCKFILE"
) &

exit 0
