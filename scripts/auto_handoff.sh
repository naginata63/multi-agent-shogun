#!/usr/bin/env bash
# auto_handoff.sh - pre_compact hook: コンテキスト圧縮前に作業状態を自動保存
# Usage: echo '{"session_id":"...","transcript_path":"...","trigger":"auto"}' | bash scripts/auto_handoff.sh
# Always exits 0 to prevent Claude Code from stopping

set -euo pipefail

# プロジェクトルートへ移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# stdinからJSON読み込み
INPUT="$(cat)"

# jqが使えるか確認、なければpython3で代替
if command -v jq &>/dev/null; then
    SESSION_ID="$(echo "$INPUT" | jq -r '.session_id // "unknown"')"
    TRANSCRIPT_PATH="$(echo "$INPUT" | jq -r '.transcript_path // ""')"
    TRIGGER="$(echo "$INPUT" | jq -r '.trigger // "unknown"')"
else
    SESSION_ID="$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('session_id','unknown'))")"
    TRANSCRIPT_PATH="$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('transcript_path',''))")"
    TRIGGER="$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('trigger','unknown'))")"
fi

# agent_idをtmuxから取得
AGENT_ID="$(tmux display-message -p '#{@agent_id}' 2>/dev/null || echo "unknown")"

# タイムスタンプ生成
TIMESTAMP="$(date "+%Y%m%d-%H%M")"

# handoffディレクトリ作成
mkdir -p queue/handoff queue/handoff/transcripts

# 出力ファイルパス
HANDOFF_FILE="queue/handoff/${AGENT_ID}_${TIMESTAMP}.md"

# タスクYAML読み込み（失敗しても無視）
TASK_YAML=""
if [ -f "queue/tasks/${AGENT_ID}.yaml" ]; then
    TASK_YAML="$(cat "queue/tasks/${AGENT_ID}.yaml" 2>/dev/null || echo "(読み込み失敗)")"
else
    TASK_YAML="(ファイルなし: queue/tasks/${AGENT_ID}.yaml)"
fi

# handoffファイルへ書き出し
COPIED_TRANSCRIPT=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    COPY_DEST="queue/handoff/transcripts/${AGENT_ID}_${TIMESTAMP}.jsonl"
    cp "$TRANSCRIPT_PATH" "$COPY_DEST" 2>/dev/null || true
    COPIED_TRANSCRIPT="$COPY_DEST"
fi

cat > "$HANDOFF_FILE" <<HANDOFF
# Handoff: ${AGENT_ID} @ ${TIMESTAMP}

## Agent
- agent_id: ${AGENT_ID}
- timestamp: ${TIMESTAMP}
- session_id: ${SESSION_ID}
- trigger: ${TRIGGER}

## Task State
\`\`\`yaml
${TASK_YAML}
\`\`\`

## Transcript Path
- original: ${TRANSCRIPT_PATH}
- copied: ${COPIED_TRANSCRIPT:-"(コピー失敗またはパス未指定)"}

## Next Actions
1. queue/tasks/${AGENT_ID}.yaml を読んで作業状態を確認し再開せよ
2. 引き継ぎファイル（このファイル）の内容を参照して文脈を復元せよ
3. inbox に未読メッセージがあれば処理してから作業再開せよ
HANDOFF

# 必ず exit 0（hookエラーでClaude Codeが止まらないように）
exit 0
