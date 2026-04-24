#!/usr/bin/env bash
# done_gate.sh — cmd_1442 H1+H10改 統合ゲート
#
# 足軽/軍師が task YAML で status:done を宣言する前に満たすべき条件を検査。
# opt-in: 該当 task に verify: 欄が無い場合は skip（既存 subtask 後方互換）。
#
# 使い方:
#   bash scripts/done_gate.sh <agent_id> <task_id> <task_yaml_path>
#   exit 0 = OK (done 許可)
#   exit 2 = BLOCK (done 不可・理由は stderr に出力)
#
# 検査項目:
#   1. verify_result: pass が書込済であること (verify.command を走らせた痕跡)
#   2. logs/advisor_calls.log に当該 task_id の advisor 呼出が 2 件以上あること
#      (ashigaru.md step 3.8 / 4.8 の before + after advisor 履行検証)
#
# 依存: python3 (YAML 解析)・grep (advisor ログ集計)・yq 不使用 (yaml lib 未導入環境対応)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

AGENT_ID="${1:-}"
TASK_ID="${2:-}"
TASK_YAML="${3:-}"

if [ -z "$AGENT_ID" ] || [ -z "$TASK_ID" ] || [ -z "$TASK_YAML" ]; then
  echo "usage: done_gate.sh <agent_id> <task_id> <task_yaml_path>" >&2
  exit 2
fi

if [ ! -f "$TASK_YAML" ]; then
  # 呼出元エラーは gate の責務でないので即 OK (ハーネス失敗≠タスク失敗)
  exit 0
fi

ADVISOR_LOG="${REPO_DIR}/logs/advisor_calls.log"

# ── post_steps marker 存在チェック (H_post_step_completion_detector) ──
POST_STEPS_MISSING=$(TASK_YAML="$TASK_YAML" TASK_ID="$TASK_ID" REPO_DIR="$REPO_DIR" python3 <<'PYEOF' 2>/dev/null
import os,re,sys;c=open(os.environ['TASK_YAML']).read();t=os.environ['TASK_ID'];R=os.environ['REPO_DIR']
for b in re.split(r'(?=^- task_id:)',c,flags=re.M):
 m=re.search(r'^- task_id:\s*(\S+)',b,re.M)
 if not m or m.group(1).strip('"\'')!=t: continue
 ps=re.search(r'^\s+post_steps:\s*\n((?:\s+-\s+.+\n)*)',b,re.M)
 if not ps: sys.exit(0)
 for l in ps.group(1).splitlines():
  k=re.match(r'\s+-\s+(.+?)\s*(?:#.*)?$',l)
  if k:
   v=k.group(1).strip('"\'');p=v if os.path.isabs(v) else os.path.join(R,v)
   if v and not os.path.isfile(p): print(v)
 sys.exit(0)
PYEOF
)
[ -z "$POST_STEPS_MISSING" ] || { echo "BLOCK: ${TASK_ID} post_steps 未完了 ($(echo "$POST_STEPS_MISSING"|wc -l) 件欠落)" >&2
  echo "欠落 marker:" >&2;echo "$POST_STEPS_MISSING"|sed 's/^/  - /' >&2
  echo "対応: post-step を完了させてから status:done / QC 依頼せよ" >&2;exit 2; }

# ── 該当 task block を抽出し verify 有無・verify_result を判定 ──
GATE_RESULT=$(TASK_YAML="$TASK_YAML" TASK_ID="$TASK_ID" python3 <<'PYEOF' 2>/dev/null
import os, re, sys
path = os.environ['TASK_YAML']
target = os.environ['TASK_ID']
try:
    with open(path) as f:
        content = f.read()
except Exception:
    print('SKIP:file_read_error')
    sys.exit(0)

blocks = re.split(r'(?=^- task_id:)', content, flags=re.MULTILINE)
for block in blocks:
    if not block.strip().startswith('- task_id:'):
        continue
    m = re.search(r'^- task_id:\s*(\S+)', block, re.MULTILINE)
    if not m:
        continue
    tid = m.group(1).strip().strip('"').strip("'")
    if tid != target:
        continue

    # opt-in: verify: 欄宣言なしなら skip
    if not re.search(r'^\s+verify:\s*(\{|$|\n)', block, re.MULTILINE):
        print('SKIP:no_verify_field')
        sys.exit(0)

    vr_m = re.search(r'^\s+verify_result:\s*([^\s\n#]+)', block, re.MULTILINE)
    vr = vr_m.group(1).strip().strip('"').strip("'") if vr_m else 'missing'
    print(f'VERIFY_RESULT:{vr}')
    sys.exit(0)

print('SKIP:task_not_found')
sys.exit(0)
PYEOF
)

case "$GATE_RESULT" in
  SKIP:*)
    # 後方互換: verify 欄なし or task 不在 → 素通り
    exit 0
    ;;
  VERIFY_RESULT:pass)
    : # verify pass 確認済 → advisor チェックへ進む
    ;;
  VERIFY_RESULT:*)
    VR="${GATE_RESULT#VERIFY_RESULT:}"
    echo "BLOCK: ${TASK_ID} verify_result=${VR} (pass 未達)" >&2
    echo "対応: (1) verify.command を実行 (2) verify_result: pass 書込 (3) status: done" >&2
    echo "auto 実行: verify_result: run_now と書込→PostToolUse (posttool_verify_runner.sh) が verify を走らせる" >&2
    exit 2
    ;;
  *)
    # 想定外出力は skip 扱い (gate 起因の誤 BLOCK 回避)
    exit 0
    ;;
esac

# ── advisor 呼出回数チェック (最低 2 回) ──
# log は pane の @current_task 短縮形 (e.g., subtask_1442_h1 → 1442_h1) で記録されるため、
# 短縮形 (subtask_ 接頭辞剥離) と完全形 の両方で照合する。
TASK_ID_SHORT="${TASK_ID#subtask_}"
if [ -f "$ADVISOR_LOG" ]; then
  if [ "$TASK_ID" = "$TASK_ID_SHORT" ]; then
    ADVISOR_COUNT=$(grep -cE $'\t'"${TASK_ID}"$'(\t|$)' "$ADVISOR_LOG" 2>/dev/null || echo 0)
  else
    ADVISOR_COUNT=$(grep -cE $'\t''('"${TASK_ID}"'|'"${TASK_ID_SHORT}"')'$'(\t|$)' "$ADVISOR_LOG" 2>/dev/null || echo 0)
  fi
else
  ADVISOR_COUNT=0
fi

# 数値でなかった場合のガード
if ! [[ "$ADVISOR_COUNT" =~ ^[0-9]+$ ]]; then
  ADVISOR_COUNT=0
fi

if [ "$ADVISOR_COUNT" -lt 2 ]; then
  echo "BLOCK: ${TASK_ID} advisor 呼出 ${ADVISOR_COUNT} 回 (必須 2 回: 実装前 + 完了前)" >&2
  echo "log: ${ADVISOR_LOG}" >&2
  echo "対応: advisor() を呼んでから status:done にせよ (ashigaru.md step 3.8 / 4.8)" >&2
  exit 2
fi

exit 0
