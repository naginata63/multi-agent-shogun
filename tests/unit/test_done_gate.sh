#!/usr/bin/env bash
# test_done_gate.sh — pure-bash runner for cmd_1442 H1+H10改 done_gate.sh
#
# tests/unit/test_done_gate.bats の bats 非対応版。bats 未導入環境でも
# `bash tests/unit/test_done_gate.sh` で最低限の検証が可能。
#
# Covers:
#   T-DG-001: verify: 欄なし → exit 0 (opt-in 後方互換)
#   T-DG-002: verify:pass + advisor>=2 → exit 0
#   T-DG-003: verify: 宣言 + verify_result:missing → exit 2
#   T-DG-004: verify_result:fail → exit 2
#   T-DG-005: verify_result:pass + advisor 0 回 → exit 2
#   T-DG-006: advisor log に短縮形 task_id のみ → exit 0
#   T-DG-007: task_id 不在 → skip (exit 0)
#   T-DG-008: 引数不足 → exit 2 (usage)

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DONE_GATE="$SCRIPT_DIR/scripts/done_gate.sh"
PASS=0
FAIL=0

run_case() {
    local name="$1"; shift
    local expect="$1"; shift
    # remaining args are run command
    local out
    out=$("$@" 2>&1)
    local actual=$?
    if [ "$actual" -eq "$expect" ]; then
        echo "PASS: $name (exit=$actual)"
        PASS=$((PASS+1))
    else
        echo "FAIL: $name (expect=$expect actual=$actual)"
        echo "  output: $out"
        FAIL=$((FAIL+1))
    fi
}

[ -x "$DONE_GATE" ] || { echo "ERROR: $DONE_GATE not executable"; exit 1; }

TMP=$(mktemp -d "${TMPDIR:-/tmp}/done_gate_sh_test.XXXXXX")
trap "rm -rf '$TMP'" EXIT

mkdir -p "$TMP/scripts" "$TMP/queue/tasks" "$TMP/logs"
cp "$DONE_GATE" "$TMP/scripts/done_gate.sh"
chmod +x "$TMP/scripts/done_gate.sh"

YAML="$TMP/queue/tasks/ashigaru4.yaml"
ALOG="$TMP/logs/advisor_calls.log"

# ── T-DG-001: verify: 欄なし → skip ──
cat > "$YAML" << 'YAMLEOF'
tasks:
- task_id: subtask_legacy_001
  status: done
  description: legacy task without verify
YAMLEOF
run_case "T-DG-001 verify欄なし→skip" 0 \
    bash "$TMP/scripts/done_gate.sh" ashigaru4 subtask_legacy_001 "$YAML"

# ── T-DG-002: verify:pass + advisor>=2 ──
cat > "$YAML" << 'YAMLEOF'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "echo ok"
  verify_result: pass
YAMLEOF
cat > "$ALOG" << 'LOG'
2026-04-24T10:00:00+09:00	ashigaru4	subtask_1442_h1	source=pretool_hook
2026-04-24T12:00:00+09:00	ashigaru4	subtask_1442_h1	source=pretool_hook
LOG
run_case "T-DG-002 verify:pass+advisor>=2→OK" 0 \
    bash "$TMP/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$YAML"

# ── T-DG-003: verify: 宣言 + verify_result 欠落 ──
cat > "$YAML" << 'YAMLEOF'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "curl -sf http://x"
YAMLEOF
run_case "T-DG-003 verify_result欠落→BLOCK" 2 \
    bash "$TMP/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$YAML"

# ── T-DG-004: verify_result: fail ──
cat > "$YAML" << 'YAMLEOF'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "false"
  verify_result: fail
YAMLEOF
run_case "T-DG-004 verify_result=fail→BLOCK" 2 \
    bash "$TMP/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$YAML"

# ── T-DG-005: verify_result:pass + advisor 0 回 ──
cat > "$YAML" << 'YAMLEOF'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "true"
  verify_result: pass
YAMLEOF
: > "$ALOG"
run_case "T-DG-005 advisor=0→BLOCK" 2 \
    bash "$TMP/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$YAML"

# ── T-DG-006: 短縮形 task_id の advisor ログでもカウント ──
cat > "$YAML" << 'YAMLEOF'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "true"
  verify_result: pass
YAMLEOF
cat > "$ALOG" << 'LOG'
2026-04-24T10:00:00+09:00	ashigaru4	1442_h1	source=pretool_hook
2026-04-24T12:00:00+09:00	ashigaru4	1442_h1	source=pretool_hook
LOG
run_case "T-DG-006 短縮形でもカウント→OK" 0 \
    bash "$TMP/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$YAML"

# ── T-DG-007: task_id 不在 → skip ──
cat > "$YAML" << 'YAMLEOF'
tasks:
- task_id: subtask_other
  status: done
YAMLEOF
run_case "T-DG-007 task_id不在→skip" 0 \
    bash "$TMP/scripts/done_gate.sh" ashigaru4 subtask_1442_missing "$YAML"

# ── T-DG-008: 引数不足 ──
run_case "T-DG-008 引数不足→usage BLOCK" 2 \
    bash "$TMP/scripts/done_gate.sh"

echo ""
echo "── Summary ──"
echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
