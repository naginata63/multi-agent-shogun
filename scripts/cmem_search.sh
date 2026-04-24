#!/bin/bash
# cmem_search.sh - claude-mem 横断検索ヘルパー
# Usage: bash scripts/cmem_search.sh "<query>" [limit]
# 軍師はQC開始前、足軽は実装前に本コマンドで過去知見を確認せよ。

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"<query>\" [limit=5]" >&2
  exit 2
fi

QUERY="$1"
LIMIT="${2:-5}"
URL="${CMEM_URL:-http://localhost:37777}"

RESPONSE=$(curl -s -G "${URL}/api/search" \
  --data-urlencode "query=${QUERY}" \
  --data-urlencode "limit=${LIMIT}" \
  --max-time 10) || {
  echo "[cmem_search] curl failed against ${URL}" >&2
  exit 1
}

if [ -z "${RESPONSE}" ]; then
  echo "[cmem_search] empty response from ${URL}" >&2
  exit 1
fi

echo "${RESPONSE}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f'[cmem_search] JSON parse error: {e}', file=sys.stderr)
    sys.exit(1)
content = data.get('content') or []
if not content:
    print('[cmem_search] no content in response', file=sys.stderr)
    sys.exit(0)
print(content[0].get('text', ''))
"
