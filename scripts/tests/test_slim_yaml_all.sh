#!/usr/bin/env bash
#
# test_slim_yaml_all.sh — unit test for scripts/slim_yaml_all.sh
#
# Verifies the C09 fix: when one agent's slim fails, subsequent agents
# must still run (no more `&&` short-circuit drift).
#
# Usage: bash scripts/tests/test_slim_yaml_all.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WRAPPER="$REPO_ROOT/scripts/slim_yaml_all.sh"

TMPROOT="$(mktemp -d -p "$REPO_ROOT/work" test_slim_yaml_all_XXXX)"
trap 'rm -rf "$TMPROOT"' EXIT

FAKE_SLIM="$TMPROOT/fake_slim_yaml.sh"
TRACE="$TMPROOT/trace.log"

cat > "$FAKE_SLIM" <<'SH'
#!/usr/bin/env bash
agent="$1"
echo "CALLED:$agent" >> "$TRACE"
# Fail for a specific agent to simulate a broken YAML
if [ "$agent" = "ashigaru3" ]; then
  echo "simulated parse failure for $agent" >&2
  exit 2
fi
exit 0
SH
chmod +x "$FAKE_SLIM"

pass=0
fail=0

check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "PASS: $label"
    pass=$((pass+1))
  else
    echo "FAIL: $label (expected=$expected, actual=$actual)"
    fail=$((fail+1))
  fi
}

# Test 1: all agents attempted even when one fails mid-chain
TRACE="$TRACE" SLIM_YAML_BIN="$FAKE_SLIM" bash "$WRAPPER" > "$TMPROOT/run1.out" 2> "$TMPROOT/run1.err"
rc=$?

called_count=$(wc -l < "$TRACE")
check "all 9 agents attempted despite failure" "9" "$called_count"
check "exit code is 1 when any agent fails" "1" "$rc"

# Verify specific agents after the failing one were still called
if grep -q "^CALLED:ashigaru4$" "$TRACE" && \
   grep -q "^CALLED:ashigaru7$" "$TRACE" && \
   grep -q "^CALLED:gunshi$" "$TRACE"; then
  check "post-failure agents invoked (ashigaru4, ashigaru7, gunshi)" "yes" "yes"
else
  check "post-failure agents invoked (ashigaru4, ashigaru7, gunshi)" "yes" "no"
fi

# Test 2: all OK path — exit 0
: > "$TRACE"
cat > "$FAKE_SLIM" <<'SH'
#!/usr/bin/env bash
echo "CALLED:$1" >> "$TRACE"
exit 0
SH
chmod +x "$FAKE_SLIM"

TRACE="$TRACE" SLIM_YAML_BIN="$FAKE_SLIM" bash "$WRAPPER" > "$TMPROOT/run2.out" 2> "$TMPROOT/run2.err"
rc=$?
check "exit code is 0 when all agents succeed" "0" "$rc"

# Test 3: explicit agent list overrides default
: > "$TRACE"
TRACE="$TRACE" SLIM_YAML_BIN="$FAKE_SLIM" bash "$WRAPPER" karo gunshi > "$TMPROOT/run3.out" 2> "$TMPROOT/run3.err"
called_count=$(wc -l < "$TRACE")
check "explicit agent list limits execution to given agents" "2" "$called_count"

echo
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
