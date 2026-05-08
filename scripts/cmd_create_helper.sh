#!/bin/bash
# cmd_create_helper.sh — cmd起票前に類似cmdを検索して表示するヘルパー
# 用途: cmd_helper.py rag を統合し、POST /api/cmd_create 前に existing cmds を提示
#
# 使い方:
#   bash scripts/cmd_create_helper.sh queue/cmd_payloads/cmd_1673.json
#
# 処理フロー:
#   1. JSON ペイロードから purpose / command を抽出
#   2. cmd_helper.py rag で類似 cmd を検索
#   3. 結果を表示
#   4. ユーザに起票確認
#   5. 確認後、curl -X POST /api/cmd_create を実行
#   6. rag_suggestions.json に結果を保存

set -e

PAYLOAD_PATH="${1:?Usage: cmd_create_helper.sh <payload_file>}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$PAYLOAD_PATH" ]]; then
    echo "ERROR: ペイロードファイルが見つかりません: $PAYLOAD_PATH" >&2
    exit 1
fi

# JSON から purpose を抽出（jq使用）
PURPOSE=$(jq -r '.purpose // ""' "$PAYLOAD_PATH" 2>/dev/null || echo "")
COMMAND=$(jq -r '.command_text // ""' "$PAYLOAD_PATH" 2>/dev/null || echo "")
CMD_ID=$(jq -r '.id // ""' "$PAYLOAD_PATH" 2>/dev/null || echo "")

if [[ -z "$PURPOSE" ]]; then
    echo "ERROR: purpose が見つかりません" >&2
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 類似cmd検索（cmd_helper.py rag）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 クエリ: $PURPOSE"
echo ""

# cmd_helper.py rag を実行（--json で JSON 出力）
RAG_RESULTS=$(python3 "$REPO_ROOT/scripts/cmd_helper.py" rag "$PURPOSE" --json 2>&1 || echo '{}')
RAG_SUMMARY=$(python3 "$REPO_ROOT/scripts/cmd_helper.py" rag "$PURPOSE" 2>&1 || echo "(検索失敗)")

# 結果を画面に表示
echo "$RAG_SUMMARY"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 確認: 類似 cmd を確認後、起票を進めますか？ (y/n)"
read -r CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "❌ キャンセル"
    exit 0
fi

echo ""
echo "🚀 cmd 起票中..."

# curl で /api/cmd_create を実行（--data @file 方式）
RESPONSE=$(curl -s -X POST http://192.168.2.4:8770/api/cmd_create \
    -H 'Content-Type: application/json' \
    --data @"$PAYLOAD_PATH" \
    -w "\nHTTP %{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1 | sed 's/HTTP //')
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "✅ cmd 起票成功: $CMD_ID"
    echo "$BODY"

    # rag_suggestions.json を保存（デバッグ用）
    SUGGESTIONS_FILE="$REPO_ROOT/queue/rag_suggestions.json"
    echo "$RAG_RESULTS" > "$SUGGESTIONS_FILE"
    echo "📝 RAG結果を保存: $SUGGESTIONS_FILE"
else
    echo "❌ cmd 起票失敗 (HTTP $HTTP_CODE)"
    echo "$BODY" >&2
    exit 1
fi
