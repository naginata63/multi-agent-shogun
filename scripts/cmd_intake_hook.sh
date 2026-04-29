#!/usr/bin/env bash
# cmd_intake_hook.sh — PreToolUse hook (cmd_1552b)
#
# Bash tool で curl /api/cmd_create が実行される際に発火し、以下を自動実行する:
#   (i)   mem-search top3 表示 (keywords抽出→cmem search→将軍context表示)
#   (ii)  queue/pending_mcp_obs.yaml MCP pending 書込 (agent が SessionStart で消化)
#
# mem-search hit=0 の場合は stderr に警告を出すが、書込は阻止しない (exit 0 固定)。
# 設計根拠: cmd_1552b (Bash+API trigger化・(iii)(iv)(v)削除 → server.py cmd_1552a側に移行)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${REPO_DIR}/logs"
QUEUE_DIR="${REPO_DIR}/queue"

PENDING_MCP="${QUEUE_DIR}/pending_mcp_obs.yaml"
SELF_LOG="${LOG_DIR}/cmd_intake_hook.log"

mkdir -p "$LOG_DIR" "$QUEUE_DIR" 2>/dev/null || true

INPUT=$(cat 2>/dev/null || true)

# 早期 exit: Bash tool のみ対象
TOOL_NAME=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  print(json.load(sys.stdin).get('tool_name',''))
except Exception:
  pass" 2>/dev/null || true)

[ "$TOOL_NAME" = "Bash" ] || exit 0

# Bash command を取得
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  print(json.load(sys.stdin).get('tool_input',{}).get('command',''))
except Exception:
  pass" 2>/dev/null)

# api/cmd_create が含まれる場合のみ発火
printf '%s' "$CMD" | grep -q 'api/cmd_create' || exit 0

# payload file path を抽出 (--data @path があれば内容を CONTENT に使用)
PAYLOAD_PATH=$(printf '%s' "$CMD" | python3 -c "
import sys, re, os
m = re.search(r'--data\s+@(\S+)', sys.stdin.read())
if m:
  p = m.group(1)
  if not os.path.isabs(p):
    p = os.path.join('${REPO_DIR}', p)
  print(p)
" 2>/dev/null || true)

if [ -n "$PAYLOAD_PATH" ] && [ -f "$PAYLOAD_PATH" ]; then
  CONTENT=$(cat "$PAYLOAD_PATH" 2>/dev/null || true)
fi
# fallback: CONTENT が空ならコマンド文字列を使用
[ -z "$CONTENT" ] && CONTENT="$CMD"

# cmd_id を抽出 (payload → command の順)
CMD_ID=$(printf '%s' "$CONTENT" | grep -oE 'cmd_[0-9]+' | head -1)
if [ -z "$CMD_ID" ]; then
  CMD_ID=$(printf '%s' "$CMD" | grep -oE 'cmd_[0-9]+' | head -1)
fi
[ -z "$CMD_ID" ] && exit 0

TS=$(date +%Y-%m-%dT%H:%M:%S%z)

# キーワード抽出 (日本語 2+ 文字連続 + 英単語 4+ 文字) / top 5 / 除外語付き
KEYWORDS=$(printf '%s' "$CONTENT" | python3 -c '
import sys, re
from collections import Counter
text = sys.stdin.read()
cmd_id = sys.argv[1] if len(sys.argv) > 1 else ""
STOP = set("status timestamp priority purpose command notes project acceptance criteria subtask task_id parent from none true false https http yaml markdown advisor high low medium critical done assigned pending blocked failed in_progress scope_question scope_approved report_received report_completed task_assigned cmd_new 必須 完了 実装 確認 対応 作業 機能 追加 対象 採用 完了後 担当 以下 以上 記載 参照 既存 新規 可能 推奨 各々 項目".split())
eng = [w for w in re.findall(r"[A-Za-z][A-Za-z_\-]{3,}", text) if not w.endswith(("_","-"))]
jpn = re.findall(r"[一-鿿゠-ヿ]{2,12}", text)
pool = [w for w in eng+jpn if w.lower() not in STOP and w != cmd_id]
freq = Counter(pool)
top = [w for w,_ in freq.most_common(8) if len(w) >= 2]
print(" ".join(top[:5]))
' "$CMD_ID" 2>/dev/null || true)

# mem-search (キーワード毎 hit 数集計)
RESULTS_JSON="["
TOTAL_HITS=0
FIRST=1
if [ -n "$KEYWORDS" ]; then
  TMP_DIR=$(mktemp -d 2>/dev/null || echo "/tmp/cmd_intake_$$")
  mkdir -p "$TMP_DIR" 2>/dev/null
  IDX=0
  for kw in $KEYWORDS; do
    (
      HIT=$(timeout 3 curl -s -G "${CMEM_URL:-http://localhost:37777}/api/search" \
        --data-urlencode "query=${kw}" --data-urlencode "limit=3" --max-time 3 2>/dev/null \
        | python3 -c "import sys,json,re
try:
  d=json.load(sys.stdin); txt=(d.get('content') or [{}])[0].get('text','')
  m=re.search(r'\((\d+)\s+obs', txt)
  print(m.group(1) if m else 0)
except Exception:
  print(0)" 2>/dev/null || echo 0)
      printf '%s\t%s\n' "$kw" "${HIT:-0}" > "$TMP_DIR/res_$IDX"
    ) &
    IDX=$((IDX+1))
  done
  wait
  FILES=$(ls "$TMP_DIR"/res_* 2>/dev/null | sort -t_ -k2 -n)
  for f in $FILES; do
    [ -f "$f" ] || continue
    KW=$(head -1 "$f" | cut -f1)
    HIT=$(head -1 "$f" | cut -f2 | tr -d '[:space:]')
    HIT=${HIT:-0}
    SAFE_KW=$(printf '%s' "$KW" | sed 's/"/\\"/g')
    [ $FIRST -eq 0 ] && RESULTS_JSON="${RESULTS_JSON},"
    RESULTS_JSON="${RESULTS_JSON}{\"kw\":\"${SAFE_KW}\",\"hits\":${HIT}}"
    TOTAL_HITS=$((TOTAL_HITS + HIT))
    FIRST=0
  done
  rm -rf "$TMP_DIR" 2>/dev/null
fi
RESULTS_JSON="${RESULTS_JSON}]"

# (ii) pending MCP observation queue (shogun/karo/gunshi が SessionStart で消化)
LOCK_FILE="${PENDING_MCP}.lock"
(
  flock -x -w 3 200 || exit 0
  if [ ! -f "$PENDING_MCP" ]; then
    printf '# queue/pending_mcp_obs.yaml\n# cmd_intake_hook.sh が書込・shogun/karo/gunshi が SessionStart で mcp__memory__add_observations → archive\nentries:\n' > "$PENDING_MCP"
  elif grep -qE '^entries:\s*\[\s*\]\s*$' "$PENDING_MCP"; then
    sed -i 's/^entries:\s*\[\s*\]\s*$/entries:/' "$PENDING_MCP"
  fi
  TS_DATE=$(date +%Y-%m-%d)
  {
    printf -- '- ts: "%s"\n' "$TS"
    printf '  entity_name: rule_yaml_first\n'
    printf '  observation: "%s 起票 (%s): keywords=[%s] total_hits=%d"\n' \
      "$CMD_ID" "$TS_DATE" "$(printf '%s' "$KEYWORDS" | tr ' ' ',' | sed 's/"/\\"/g')" "$TOTAL_HITS"
    printf '  status: pending\n'
  } >> "$PENDING_MCP" 2>/dev/null || true
) 200>"$LOCK_FILE" 2>/dev/null || true

# hit=0 警告 (阻止はしない)
if [ "$TOTAL_HITS" -eq 0 ]; then
  echo "[cmd_intake_hook] ⚠️ ${CMD_ID} mem-search hit=0 (keywords=[${KEYWORDS}]) — 新規実装の可能性・先行事例なし" >&2
fi

# self log (debug 用)
printf '%s %s total_hits=%d pending_mcp=%s\n' \
  "$TS" "$CMD_ID" "$TOTAL_HITS" "$PENDING_MCP" >> "$SELF_LOG" 2>/dev/null || true

exit 0
