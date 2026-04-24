#!/usr/bin/env bats
# test_done_gate.bats — cmd_1442 H1+H10改 done_gate.sh unit tests
#
# 検査対象: scripts/done_gate.sh
#   opt-in: verify: 欄無し task → exit 0 (後方互換)
#   BLOCK : verify: 宣言済 + verify_result != pass → exit 2
#   BLOCK : verify: 宣言済 + verify_result == pass + advisor 呼出 < 2 → exit 2
#   OK    : verify: 宣言済 + verify_result == pass + advisor 呼出 >= 2 → exit 0

setup_file() {
    export PROJECT_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
    export DONE_GATE="$PROJECT_ROOT/scripts/done_gate.sh"
    [ -x "$DONE_GATE" ] || skip "done_gate.sh not executable"
}

setup() {
    export TEST_TMPDIR="$(mktemp -d "$BATS_TMPDIR/done_gate_test.XXXXXX")"
    export MOCK_REPO="$TEST_TMPDIR/mock_repo"
    mkdir -p "$MOCK_REPO/scripts" "$MOCK_REPO/queue/tasks" "$MOCK_REPO/logs"
    cp "$DONE_GATE" "$MOCK_REPO/scripts/done_gate.sh"
    chmod +x "$MOCK_REPO/scripts/done_gate.sh"

    export TASK_YAML="$MOCK_REPO/queue/tasks/ashigaru4.yaml"
    export ADVISOR_LOG="$MOCK_REPO/logs/advisor_calls.log"
}

teardown() {
    rm -rf "$TEST_TMPDIR"
}

# ── T-DG-001: verify: 欄なし → 後方互換で素通り (exit 0) ──
@test "T-DG-001: task without verify: field passes (opt-in regression safety)" {
    cat > "$TASK_YAML" << 'YAML'
tasks:
- task_id: subtask_legacy_001
  status: done
  description: "legacy task without verify"
YAML

    run bash "$MOCK_REPO/scripts/done_gate.sh" ashigaru4 subtask_legacy_001 "$TASK_YAML"
    [ "$status" -eq 0 ]
}

# ── T-DG-002: verify: 宣言済 + verify_result:pass + advisor>=2 → OK (exit 0) ──
@test "T-DG-002: verify:pass + advisor>=2 allows done" {
    cat > "$TASK_YAML" << 'YAML'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "echo ok"
    pass_criteria: "exit 0"
  verify_result: pass
YAML

    cat > "$ADVISOR_LOG" << 'LOG'
2026-04-24T10:00:00+09:00	ashigaru4	subtask_1442_h1	source=pretool_hook
2026-04-24T12:00:00+09:00	ashigaru4	subtask_1442_h1	source=pretool_hook
LOG

    run bash "$MOCK_REPO/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$TASK_YAML"
    [ "$status" -eq 0 ]
}

# ── T-DG-003: verify: 宣言済 + verify_result:missing → BLOCK (exit 2) ──
@test "T-DG-003: verify declared but verify_result missing blocks done" {
    cat > "$TASK_YAML" << 'YAML'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "curl -sf http://example.com"
YAML

    run bash "$MOCK_REPO/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$TASK_YAML"
    [ "$status" -eq 2 ]
    echo "$output" | grep -q "verify_result"
}

# ── T-DG-004: verify_result:fail → BLOCK (exit 2) ──
@test "T-DG-004: verify_result=fail blocks done" {
    cat > "$TASK_YAML" << 'YAML'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "false"
  verify_result: fail
YAML

    run bash "$MOCK_REPO/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$TASK_YAML"
    [ "$status" -eq 2 ]
    echo "$output" | grep -q "fail"
}

# ── T-DG-005: verify_result:pass + advisor 0 回 → BLOCK (exit 2) ──
@test "T-DG-005: verify passes but advisor count < 2 blocks done" {
    cat > "$TASK_YAML" << 'YAML'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "true"
  verify_result: pass
YAML

    # advisor ログ空（0 回）
    : > "$ADVISOR_LOG"

    run bash "$MOCK_REPO/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$TASK_YAML"
    [ "$status" -eq 2 ]
    echo "$output" | grep -q "advisor"
}

# ── T-DG-006: 短縮形 (subtask_ 剥離) でも advisor 呼出をカウントできる ──
@test "T-DG-006: advisor log with short task_id (subtask_ prefix stripped) is counted" {
    cat > "$TASK_YAML" << 'YAML'
tasks:
- task_id: subtask_1442_h1
  status: in_progress
  verify:
    command: "true"
  verify_result: pass
YAML

    cat > "$ADVISOR_LOG" << 'LOG'
2026-04-24T10:00:00+09:00	ashigaru4	1442_h1	source=pretool_hook
2026-04-24T12:00:00+09:00	ashigaru4	1442_h1	source=pretool_hook
LOG

    run bash "$MOCK_REPO/scripts/done_gate.sh" ashigaru4 subtask_1442_h1 "$TASK_YAML"
    [ "$status" -eq 0 ]
}

# ── T-DG-007: task_id not found → skip (exit 0) (誤 BLOCK 回避) ──
@test "T-DG-007: unknown task_id skips gate (no false positive)" {
    cat > "$TASK_YAML" << 'YAML'
tasks:
- task_id: subtask_other
  status: done
YAML

    run bash "$MOCK_REPO/scripts/done_gate.sh" ashigaru4 subtask_1442_missing "$TASK_YAML"
    [ "$status" -eq 0 ]
}

# ── T-DG-008: 引数不足 → BLOCK (exit 2) ──
@test "T-DG-008: missing arguments exit 2 with usage message" {
    run bash "$MOCK_REPO/scripts/done_gate.sh"
    [ "$status" -eq 2 ]
    echo "$output" | grep -q "usage"
}
