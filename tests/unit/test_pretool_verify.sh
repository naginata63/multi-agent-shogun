#!/usr/bin/env bash
# test_pretool_verify.sh — cmd_1442 H1 PreToolUse hook CHK5 動作確認
#
# pretool_check.sh (CHK5 done_gate 委譲) が Edit/Write on queue/tasks/*.yaml で
# status:done 遷移を verify ゲートを介して正しく BLOCK するか検証。

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK="$SCRIPT_DIR/scripts/pretool_check.sh"
PASS=0
FAIL=0

run_case() {
    local name="$1"; shift
    local expect="$1"; shift
    local input="$1"; shift
    local out actual
    # Unset TMUX_PANE so hook skips agent-id-specific checks (CHK2 /tmp block, etc)
    # but CHK5 (verify gate) still triggers because it only keys off TOOL_NAME+FILE_PATH.
    out=$(TMUX_PANE="" echo "$input" | TMUX_PANE="" bash "$HOOK" 2>&1)
    actual=$?
    if [ "$actual" -eq "$expect" ]; then
        echo "PASS: $name (exit=$actual)"
        PASS=$((PASS+1))
    else
        echo "FAIL: $name (expect=$expect actual=$actual)"
        echo "  output: $out"
        FAIL=$((FAIL+1))
    fi
}

TMP=$(mktemp -d "${TMPDIR:-/tmp}/pretool_verify_test.XXXXXX")
trap "rm -rf '$TMP'" EXIT

mkdir -p "$TMP/queue/tasks" "$TMP/logs"

# --- Case 1: verify: 宣言なし task の status:done 遷移 → 素通り (exit 0) ---
cat > "$TMP/queue/tasks/ashigaru4.yaml" << 'YAMLEOF'
tasks:
- task_id: subtask_legacy
  status: assigned
  description: "no verify"
YAMLEOF

INPUT1=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TMP/queue/tasks/ashigaru4.yaml',
        'old_string': '  status: assigned',
        'new_string': '  status: done',
    }
}))
")
run_case "CHK5 legacy task (verify欄なし) → 素通り" 0 "$INPUT1"

# --- Case 2: verify: 宣言 + verify_result:pass + status:done → 素通り (exit 0) ---
# Note: advisor 呼出チェックは done_gate.sh 内で実施されるが、
# CHK5 内で advisor ログ参照は repo 全体の logs/ なので、
# REPO_DIR を $TMP に切替する経路がない→実ログに依存してしまう。
# 代わりに opt-in のロジック(verify:無しは素通り)を主対象とする。

# --- Case 3: verify: 宣言 + verify_result なし + status:done → BLOCK (exit 2) ---
cat > "$TMP/queue/tasks/ashigaru4.yaml" << 'YAMLEOF'
tasks:
- task_id: subtask_1442_h1
  status: assigned
  verify:
    command: "echo hello"
YAMLEOF

INPUT3=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TMP/queue/tasks/ashigaru4.yaml',
        'old_string': '  status: assigned',
        'new_string': '  status: done',
    }
}))
")
# Note: hook calls done_gate.sh which uses REPO_DIR based on SCRIPT_DIR.
# The simulated yaml is in $TMP but done_gate refers to logs/advisor_calls.log in repo.
# Since verify_result is missing, done_gate returns BLOCK before advisor check → exit 2 expected.
run_case "CHK5 verify_result欠落 + status:done → BLOCK" 2 "$INPUT3"

# --- Case 4: verify: 宣言 + verify_result:fail + status:done → BLOCK ---
cat > "$TMP/queue/tasks/ashigaru4.yaml" << 'YAMLEOF'
tasks:
- task_id: subtask_1442_h1
  status: assigned
  verify:
    command: "false"
  verify_result: fail
YAMLEOF

INPUT4=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TMP/queue/tasks/ashigaru4.yaml',
        'old_string': '  status: assigned',
        'new_string': '  status: done',
    }
}))
")
run_case "CHK5 verify_result=fail + status:done → BLOCK" 2 "$INPUT4"

# --- Case 5: status 遷移が done 以外 (in_progress) → 素通り ---
INPUT5=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TMP/queue/tasks/ashigaru4.yaml',
        'old_string': '  status: assigned',
        'new_string': '  status: in_progress',
    }
}))
")
run_case "CHK5 status:in_progress → 素通り" 0 "$INPUT5"

# --- Case 6: queue/tasks/ 以外のファイル → 素通り ---
INPUT6=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TMP/some_other.yaml',
        'old_string': '  status: assigned',
        'new_string': '  status: done',
    }
}))
")
run_case "CHK5 queue/tasks 以外 → 素通り" 0 "$INPUT6"

echo ""
echo "── Summary ──"
echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
