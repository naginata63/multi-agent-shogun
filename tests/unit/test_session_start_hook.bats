#!/usr/bin/env bats
# test_session_start_hook.bats — sessionstart_hook.sh unit tests

SCRIPT_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/scripts/sessionstart_hook.sh"

@test "T-SSTART-001: unknown agent exits 0 with empty output" {
    __SESSION_START_HOOK_AGENT_ID="" \
    run bash "$HOOK_SCRIPT" <<< '{"source":"startup"}'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "T-SSTART-002: resolved agent emits SessionStart additionalContext JSON" {
    __SESSION_START_HOOK_AGENT_ID="ashigaru3" \
    run bash "$HOOK_SCRIPT" <<< '{"source":"startup"}'
    [ "$status" -eq 0 ]
    echo "$output" | grep -q '"hookEventName": "SessionStart"'
    echo "$output" | grep -q "ashigaru3"
    echo "$output" | grep -q "tmux display-message"
}
