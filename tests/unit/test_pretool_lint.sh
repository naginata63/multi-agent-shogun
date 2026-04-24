#!/usr/bin/env bash
# test_pretool_lint.sh — cmd_1443_p06 H5 (CHK7 task lint + CHK8 git add BLOCK)
#
# 検査対象:
#   CHK7: queue/tasks/{ashigaru*,gunshi}.yaml に新規 task を追加する edit で
#         必須 9 フィールド欠落 → BLOCK。既存 task の編集は素通り (regression 回避)。
#   CHK8: Bash で `git add .` / `git add -A` / `git add --all` / `git add *` → BLOCK
#         `git add -p` / `git add <path>` → 許可

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

TMP=$(mktemp -d "${TMPDIR:-/tmp}/pretool_lint_test.XXXXXX")
trap "rm -rf '$TMP'" EXIT

mkdir -p "$TMP/queue/tasks"

# ═══ CHK7: task YAML lint ═══

# Case 1: 既存 task の status 変更 (NEW task_id なし) → 素通り
cat > "$TMP/queue/tasks/ashigaru4.yaml" << 'YAMLEOF'
tasks:
- task_id: subtask_legacy
  status: assigned
  assigned_to: ashigaru4
  bloom_level: L3
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
run_case "CHK7 既存task status変更 → 素通り (regression 回避)" 0 "$INPUT1"

# Case 2: 新規 task 追加 (全フィールド揃い) → 素通り
cat > "$TMP/queue/tasks/ashigaru4.yaml" << 'YAMLEOF'
tasks:
- task_id: subtask_old
  status: done
YAMLEOF

INPUT2=$(YAMLFILE="$TMP/queue/tasks/ashigaru4.yaml" python3 << 'PYEOF'
import json, os
old = '- task_id: subtask_old\n  status: done\n'
new = (
    '- task_id: subtask_old\n  status: done\n'
    '- task_id: subtask_new\n'
    '  parent_cmd: cmd_1234\n'
    '  bloom_level: L4\n'
    '  status: assigned\n'
    '  target_path: /home/murakami/multi-agent-shogun/scripts/new.sh\n'
    '  timestamp: "2026-04-24T20:00:00+09:00"\n'
    '  description: "new task"\n'
    '  steps: "Step1: implement"\n'
    '  acceptance_criteria:\n'
    '    - "script created"\n'
)
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': os.environ['YAMLFILE'],
        'old_string': old,
        'new_string': new,
    }
}))
PYEOF
)
run_case "CHK7 新規task 全フィールド揃い → 素通り" 0 "$INPUT2"

# Case 3: 新規 task 追加 (必須フィールド欠落) → BLOCK
cat > "$TMP/queue/tasks/ashigaru4.yaml" << 'YAMLEOF'
tasks:
- task_id: subtask_old
  status: done
YAMLEOF

INPUT3=$(YAMLFILE="$TMP/queue/tasks/ashigaru4.yaml" python3 << 'PYEOF'
import json, os
old = '- task_id: subtask_old\n  status: done\n'
new = (
    '- task_id: subtask_old\n  status: done\n'
    '- task_id: subtask_missing\n'
    '  status: assigned\n'
    '  description: "missing fields"\n'
)
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': os.environ['YAMLFILE'],
        'old_string': old,
        'new_string': new,
    }
}))
PYEOF
)
run_case "CHK7 新規task 必須欠落 → BLOCK" 2 "$INPUT3"

# Case 4: queue/tasks 以外 → 素通り
INPUT4=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TMP/other.yaml',
        'old_string': 'x',
        'new_string': '- task_id: subtask_xxx\\n  status: assigned',
    }
}))
")
run_case "CHK7 queue/tasks 以外 → 素通り" 0 "$INPUT4"

# ═══ CHK8: git add BLOCK ═══

mk_bash_input() {
    python3 -c "
import json, sys
print(json.dumps({
    'tool_name': 'Bash',
    'tool_input': {'command': sys.argv[1]}
}))
" "$1"
}

# Case 5: `git add .` → BLOCK
run_case "CHK8 git add . → BLOCK" 2 "$(mk_bash_input 'git add .')"

# Case 6: `git add -A` → BLOCK
run_case "CHK8 git add -A → BLOCK" 2 "$(mk_bash_input 'git add -A')"

# Case 7: `git add --all` → BLOCK
run_case "CHK8 git add --all → BLOCK" 2 "$(mk_bash_input 'git add --all')"

# Case 8: `git add *` → BLOCK
run_case "CHK8 git add * → BLOCK" 2 "$(mk_bash_input 'git add *')"

# Case 9: `git add -f .` → BLOCK
run_case "CHK8 git add -f . → BLOCK" 2 "$(mk_bash_input 'git add -f .')"

# Case 10: `git add -p` → 許可
run_case "CHK8 git add -p → 許可" 0 "$(mk_bash_input 'git add -p')"

# Case 11: `git add --patch` → 許可
run_case "CHK8 git add --patch → 許可" 0 "$(mk_bash_input 'git add --patch')"

# Case 12: `git add specific/path.sh` → 許可
run_case "CHK8 git add 具体パス → 許可" 0 "$(mk_bash_input 'git add scripts/foo.sh')"

# Case 13: `git add .gitignore` → 許可 (具体ファイル名がドットで始まる)
run_case "CHK8 git add .gitignore → 許可" 0 "$(mk_bash_input 'git add .gitignore')"

# Case 14: `cd /tmp && git add .` → BLOCK (チェーン内でも検出)
run_case "CHK8 chain内 git add . → BLOCK" 2 "$(mk_bash_input 'cd /tmp && git add .')"

# Case 15: `git add -f specific.sh` → 許可 (-f と具体パス)
run_case "CHK8 git add -f 具体パス → 許可" 0 "$(mk_bash_input 'git add -f scripts/x.sh')"

# Case 16: 引用符内の "git add ." は誤検知しない (commit message 等)
run_case "CHK8 引用符内 'git add .' → 許可 (誤検知回避)" 0 \
    "$(mk_bash_input "git commit -m 'CHK8 では git add . を BLOCK する'")"

# Case 17: ヒアドキュメント内の "git add ." は誤検知しない
HEREDOC_CMD='git commit -m "$(cat <<'"'"'EOF'"'"'
CHK8 は git add . を BLOCK する。
EOF
)"'
run_case "CHK8 heredoc内 'git add .' → 許可 (誤検知回避)" 0 "$(mk_bash_input "$HEREDOC_CMD")"

echo ""
echo "── Summary ──"
echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
