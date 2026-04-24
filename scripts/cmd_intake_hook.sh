#!/usr/bin/env bash
# cmd_intake_hook.sh — PreToolUse hook (cmd_1443_p03 / H3+H8 拡張)
#
# shogun_to_karo.yaml への新規 cmd 追記を検知し、以下を自動実行する:
#   (i)   logs/cmd_intake_obs.jsonl       監査ログ (将来 cmem POST 対応時の再取込フォーマット)
#   (ii)  queue/pending_mcp_obs.yaml       MCP memory への pending 書込 (agent が SessionStart で消化)
#   (iii) logs/lord_angry_triggers.jsonl   殿激怒キーワード検出ログ (H11 lord-angry slash への導線)
#   (iv)  dashboard_archive/YYYY-MM.md     cmd 追記 (intake 記録)
#
# mem-search hit=0 の場合は stderr に警告を出すが、書込は阻止しない (exit 0 固定)。
# 設計根拠: work/cmd_1442/execution_plan_v3.md §3 Δ3 + karo scope_approved (2026-04-24 19:26)。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${REPO_DIR}/logs"
ARCHIVE_DIR="${REPO_DIR}/dashboard_archive"
QUEUE_DIR="${REPO_DIR}/queue"

AUDIT_LOG="${LOG_DIR}/cmd_intake_obs.jsonl"
ANGRY_LOG="${LOG_DIR}/lord_angry_triggers.jsonl"
PENDING_MCP="${QUEUE_DIR}/pending_mcp_obs.yaml"
SELF_LOG="${LOG_DIR}/cmd_intake_hook.log"

mkdir -p "$LOG_DIR" "$ARCHIVE_DIR" "$QUEUE_DIR" 2>/dev/null || true

INPUT=$(cat 2>/dev/null || true)

# 早期 exit 1: JSON パース可能な tool_name を取得
TOOL_NAME=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  print(json.load(sys.stdin).get('tool_name',''))
except Exception:
  pass" 2>/dev/null || true)

case "$TOOL_NAME" in
  Write|Edit|MultiEdit|Bash) : ;;
  *) exit 0 ;;
esac

# 編集先/コマンドから shogun_to_karo.yaml 対象かを判定
TARGET_FILE=""
CONTENT=""
case "$TOOL_NAME" in
  Write)
    TARGET_FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  d=json.load(sys.stdin).get('tool_input',{})
  print(d.get('file_path',''))
except Exception:
  pass" 2>/dev/null)
    CONTENT=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  d=json.load(sys.stdin).get('tool_input',{})
  print(d.get('content',''))
except Exception:
  pass" 2>/dev/null)
    ;;
  Edit|MultiEdit)
    TARGET_FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  d=json.load(sys.stdin).get('tool_input',{})
  print(d.get('file_path',''))
except Exception:
  pass" 2>/dev/null)
    CONTENT=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  d=json.load(sys.stdin).get('tool_input',{})
  if d.get('edits'):
    print('\n'.join(e.get('new_string','') for e in d.get('edits',[])))
  else:
    print(d.get('new_string',''))
except Exception:
  pass" 2>/dev/null)
    ;;
  Bash)
    CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try:
  print(json.load(sys.stdin).get('tool_input',{}).get('command',''))
except Exception:
  pass" 2>/dev/null)
    if ! printf '%s' "$CMD" | grep -q "shogun_to_karo\.yaml"; then
      exit 0
    fi
    TARGET_FILE="shogun_to_karo.yaml"
    CONTENT="$CMD"
    ;;
esac

# shogun_to_karo.yaml に限定 (パス末尾マッチ)
case "$TARGET_FILE" in
  *shogun_to_karo.yaml) : ;;
  *) exit 0 ;;
esac

# 新規 cmd_XXXX 行を含むか
if [ -z "$CONTENT" ]; then
  exit 0
fi
if ! printf '%s' "$CONTENT" | grep -qE '^\s*-?\s*id:\s*cmd_[0-9]+' ; then
  exit 0
fi

TS=$(date +%Y-%m-%dT%H:%M:%S%z)
TS_DATE=$(date +%Y-%m-%d)
ARCHIVE_FILE="${ARCHIVE_DIR}/$(date +%Y-%m).md"

# cmd_id と purpose 1 行目を抽出
CMD_ID=$(printf '%s' "$CONTENT" | grep -oE 'cmd_[0-9]+' | head -1)
PURPOSE_LINE=$(printf '%s' "$CONTENT" | awk '
  /purpose:/ {flag=1; sub(/^[[:space:]]*purpose:[[:space:]]*\|?[[:space:]]*/,""); if (length($0)>0) {print; exit} next}
  flag && NF && !/^[[:space:]]*-/ { sub(/^[[:space:]]+/,""); print; exit }
' 2>/dev/null | head -c 160)
[ -z "$PURPOSE_LINE" ] && PURPOSE_LINE="(purpose 未記載)"

# キーワード抽出 (日本語 2+ 文字連続 + 英単語 4+ 文字) / top 5 / 除外語付き
# 入力: CONTENT (stdin) + cmd_id (argv)
KEYWORDS=$(printf '%s' "$CONTENT" | python3 -c '
import sys, re
from collections import Counter
text = sys.stdin.read()
cmd_id = sys.argv[1] if len(sys.argv) > 1 else ""
STOP = set("status timestamp priority purpose command notes project acceptance criteria subtask task_id parent from none true false https http yaml markdown advisor high low medium critical done assigned pending blocked failed in_progress scope_question scope_approved report_received report_completed task_assigned cmd_new 必須 完了 実装 確認 対応 作業 機能 追加 対象 採用 完了後 担当 以下 以上 記載 参照 既存 新規 可能 推奨 各々 項目".split())
# 英単語 regex は数字入りを弾く・末尾 _- 弾きで cmd_ 等断片を除外
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
  # 並列 curl (キーワード毎 background) — hook timeout 内に収める
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
  # 集計 (order-preserving: res_0, res_1, ...)
  FILES=$(ls "$TMP_DIR"/res_* 2>/dev/null | sort -t_ -k2 -n)
  for f in $FILES; do
    [ -f "$f" ] || continue
    KW=$(cut -f1 "$f")
    HIT=$(cut -f2 "$f")
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

# (i) 監査ログ JSONL
KW_JSON=$(printf '%s' "$KEYWORDS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().split()))" 2>/dev/null)
printf '{"ts":"%s","cmd_id":"%s","keywords":%s,"results":%s,"total_hits":%d,"source":"cmd_intake_hook","pending_sink":"cmem_api_observations"}\n' \
  "$TS" "$CMD_ID" "${KW_JSON:-[]}" "$RESULTS_JSON" "$TOTAL_HITS" >> "$AUDIT_LOG" 2>/dev/null || true

# (ii) pending MCP observation queue (shogun/karo/gunshi が SessionStart で消化)
# flock で並行書込衝突を防ぐ (inbox_write.sh と同パターン)
LOCK_FILE="${PENDING_MCP}.lock"
(
  flock -x -w 3 200 || exit 0
  # YAML 初期化 (初回のみ): entries: [] → entries: \n に変換して append 対応
  if [ ! -f "$PENDING_MCP" ]; then
    printf '# queue/pending_mcp_obs.yaml\n# cmd_intake_hook.sh が書込・shogun/karo/gunshi が SessionStart で mcp__memory__add_observations → archive\nentries:\n' > "$PENDING_MCP"
  elif grep -qE '^entries:\s*\[\s*\]\s*$' "$PENDING_MCP"; then
    # 空配列 entries: [] を entries:\n に置換して append 可能にする
    sed -i 's/^entries:\s*\[\s*\]\s*$/entries:/' "$PENDING_MCP"
  fi
  {
    printf -- '- ts: "%s"\n' "$TS"
    printf '  entity_name: rule_yaml_first\n'
    printf '  observation: "%s 起票 (%s): keywords=[%s] total_hits=%d / intake_audit=logs/cmd_intake_obs.jsonl"\n' \
      "$CMD_ID" "$TS_DATE" "$(printf '%s' "$KEYWORDS" | tr ' ' ',' | sed 's/"/\\"/g')" "$TOTAL_HITS"
    printf '  status: pending\n'
  } >> "$PENDING_MCP" 2>/dev/null || true
) 200>"$LOCK_FILE" 2>/dev/null || true

# (iii) 殿激怒キーワード検出
ANGRY_RE='(殿激怒|激怒|激オコ|ブチギレ|切腹|勘弁|いい加減|お前|黒歴史|絶対禁止|鉄則違反|是正|金銭インシデント)'
if printf '%s' "$CONTENT" | grep -qE "$ANGRY_RE" ; then
  HITS=$(printf '%s' "$CONTENT" | grep -oE "$ANGRY_RE" | sort -u | tr '\n' ',' | sed 's/,$//')
  printf '{"ts":"%s","cmd_id":"%s","triggers":"%s","suggested_slash":"/lord-angry"}\n' \
    "$TS" "$CMD_ID" "$HITS" >> "$ANGRY_LOG" 2>/dev/null || true
  echo "[cmd_intake_hook] lord-angry trigger: ${CMD_ID} ${HITS} (→ /lord-angry 検討)" >&2
fi

# (iv) dashboard_archive 追記
{
  printf -- '- %s %s intake: %s  (mem-search hits=%d / keywords=[%s])\n' \
    "$TS" "$CMD_ID" "$PURPOSE_LINE" "$TOTAL_HITS" "$(printf '%s' "$KEYWORDS" | tr ' ' ',')"
} >> "$ARCHIVE_FILE" 2>/dev/null || true

# hit=0 警告 (阻止はしない)
if [ "$TOTAL_HITS" -eq 0 ]; then
  echo "[cmd_intake_hook] ⚠️ ${CMD_ID} mem-search hit=0 (keywords=[${KEYWORDS}]) — 新規実装の可能性・先行事例なし" >&2
fi

# self log (debug 用)
printf '%s %s total_hits=%d pending_mcp=%s archive=%s\n' \
  "$TS" "$CMD_ID" "$TOTAL_HITS" "$PENDING_MCP" "$ARCHIVE_FILE" >> "$SELF_LOG" 2>/dev/null || true

exit 0
