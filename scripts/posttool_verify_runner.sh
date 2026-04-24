#!/usr/bin/env bash
# posttool_verify_runner.sh — PostToolUse hook (cmd_1442 H1 harness)
#
# 役割: queue/tasks/{ashigaru*,gunshi}.yaml が Edit/Write された直後、
#        verify_result: run_now 宣言のある task block を検出し、
#        verify.command を実行 → 結果で verify_result を上書き。
#
# opt-in: verify_result: run_now を明示した task のみ起動対象。
#         通常の task 編集には副作用なし（exit 0）。
#
# 実行時制約:
#   - timeout 60秒 (verify.timeout_seconds override 可、最大 120)
#   - 危険コマンドは reject (rm -rf / sudo / git push --force / git reset --hard)
#   - 出力 log は logs/verify_{task_id}_{YYYYMMDD_HHMMSS}.log
#   - flock で task YAML 書き戻しを直列化
#
# PostToolUse は BLOCK 不可 (exit 0 固定)。異常時は WARNING のみ。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

INPUT=$(cat 2>/dev/null || true)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

# Only Write/Edit on queue/tasks/ashigaru*.yaml or gunshi.yaml
if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
  exit 0
fi
if ! echo "$FILE_PATH" | grep -qE 'queue/tasks/(ashigaru[0-9]+|gunshi)\.yaml$'; then
  exit 0
fi
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

mkdir -p "$REPO_DIR/logs"

# Run verify for all blocks tagged run_now. Python does all parsing + execution + write-back.
VERIFY_FILE_PATH="$FILE_PATH" REPO_DIR="$REPO_DIR" python3 <<'PYEOF' 2>>"$REPO_DIR/logs/verify_runner.log" || true
import os, re, subprocess, time, fcntl, sys

FILE_PATH = os.environ['VERIFY_FILE_PATH']
REPO_DIR = os.environ['REPO_DIR']

DANGER_PATTERNS = [
    r'\brm\s+-rf\s+/',
    r'\bsudo\b',
    r'git\s+push\s+.*--force\b',
    r'git\s+push\s+-f\b',
    r'git\s+reset\s+--hard',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r'tmux\s+kill-server',
    r'\brm\s+-rf\s+~',
    r'\bchown\s+-R\s+/',
    r'\bchmod\s+-R\s+/',
]
DANGER_RE = re.compile('|'.join(DANGER_PATTERNS))

with open(FILE_PATH) as f:
    content = f.read()

blocks = re.split(r'(?=^- task_id:)', content, flags=re.MULTILINE)

# Collect targets: blocks with verify_result: run_now AND verify: declared
targets = []
for idx, block in enumerate(blocks):
    if not block.strip().startswith('- task_id:'):
        continue
    tid_m = re.search(r'^- task_id:\s*(\S+)', block, re.MULTILINE)
    if not tid_m:
        continue
    task_id = tid_m.group(1).strip().strip('"').strip("'")

    vr_m = re.search(r'^\s+verify_result:\s*([^\s\n#]+)', block, re.MULTILINE)
    if not vr_m:
        continue
    vr = vr_m.group(1).strip().strip('"').strip("'")
    if vr != 'run_now':
        continue

    # Extract verify.command (block-form)
    # Supports:
    #   verify:
    #     command: "..."
    #     pass_criteria: "..."
    #     timeout_seconds: 60
    cmd_m = re.search(r'^\s+verify:\s*\n((?:\s+.*\n)+?)(?=^\s{0,4}\S|\Z)', block, re.MULTILINE)
    if not cmd_m:
        continue
    verify_body = cmd_m.group(1)
    vcmd_m = re.search(r'^\s+command:\s*(.*)$', verify_body, re.MULTILINE)
    if not vcmd_m:
        continue
    verify_cmd = vcmd_m.group(1).strip()
    # Strip surrounding quotes
    if (verify_cmd.startswith('"') and verify_cmd.endswith('"')) or \
       (verify_cmd.startswith("'") and verify_cmd.endswith("'")):
        verify_cmd = verify_cmd[1:-1]
    # timeout
    to_m = re.search(r'^\s+timeout_seconds:\s*(\d+)', verify_body, re.MULTILINE)
    timeout = min(int(to_m.group(1)), 120) if to_m else 60
    targets.append((idx, task_id, verify_cmd, timeout))

if not targets:
    sys.exit(0)

for idx, task_id, verify_cmd, timeout in targets:
    if DANGER_RE.search(verify_cmd):
        sys.stderr.write(f'[{task_id}] verify command rejected (danger pattern): {verify_cmd[:120]}\n')
        new_result = 'fail'
        log_path = ''
        output_snippet = 'rejected: danger pattern'
    else:
        ts = time.strftime('%Y%m%d_%H%M%S')
        log_path = f'logs/verify_{task_id}_{ts}.log'
        abs_log = os.path.join(REPO_DIR, log_path)
        try:
            with open(abs_log, 'w') as lf:
                lf.write(f'# verify_cmd: {verify_cmd}\n# timeout: {timeout}s\n# started: {ts}\n\n')
                lf.flush()
                proc = subprocess.run(
                    verify_cmd, shell=True, timeout=timeout,
                    stdout=lf, stderr=subprocess.STDOUT,
                    cwd=REPO_DIR,
                )
            new_result = 'pass' if proc.returncode == 0 else 'fail'
            output_snippet = f'exit={proc.returncode}'
        except subprocess.TimeoutExpired:
            new_result = 'fail'
            output_snippet = f'timeout after {timeout}s'
            with open(abs_log, 'a') as lf:
                lf.write(f'\n# TIMEOUT after {timeout}s\n')
        except Exception as e:
            new_result = 'fail'
            output_snippet = f'exception: {e}'
            try:
                with open(abs_log, 'a') as lf:
                    lf.write(f'\n# EXCEPTION: {e}\n')
            except Exception:
                pass

    # Write back: replace verify_result: run_now with pass/fail, add/update verify_output_path
    with open(FILE_PATH, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            cur = f.read()
            cur_blocks = re.split(r'(?=^- task_id:)', cur, flags=re.MULTILINE)
            updated = False
            for i, b in enumerate(cur_blocks):
                if not b.strip().startswith('- task_id:'):
                    continue
                m = re.search(r'^- task_id:\s*(\S+)', b, re.MULTILINE)
                if not m:
                    continue
                if m.group(1).strip().strip('"').strip("'") != task_id:
                    continue
                # Replace verify_result: run_now → verify_result: pass|fail
                b2 = re.sub(
                    r'(^\s+verify_result:\s*)run_now\s*$',
                    rf'\g<1>{new_result}',
                    b, count=1, flags=re.MULTILINE,
                )
                # Update or insert verify_output_path
                if re.search(r'^\s+verify_output_path:\s*', b2, re.MULTILINE):
                    b2 = re.sub(
                        r'^(\s+verify_output_path:\s*).*$',
                        rf'\g<1>"{log_path}"',
                        b2, count=1, flags=re.MULTILINE,
                    )
                else:
                    # Insert after verify_result line
                    indent_m = re.search(r'^(\s+)verify_result:', b2, re.MULTILINE)
                    indent = indent_m.group(1) if indent_m else '  '
                    b2 = re.sub(
                        r'(^\s+verify_result:\s*\S+\s*$)',
                        rf'\g<1>\n{indent}verify_output_path: "{log_path}"',
                        b2, count=1, flags=re.MULTILINE,
                    )
                cur_blocks[i] = b2
                updated = True
                break
            if updated:
                f.seek(0)
                f.truncate()
                f.write(''.join(cur_blocks))
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    sys.stderr.write(f'[verify_runner] {task_id}: {new_result} ({output_snippet}) log={log_path}\n')

PYEOF

exit 0
