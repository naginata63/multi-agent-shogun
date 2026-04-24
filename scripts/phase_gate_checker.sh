#!/usr/bin/env bash
# phase_gate_checker.sh — cmd_1443 p07 H9 Phase 間殿ゲート必須化
#
# 多 Phase cmd (例: cmd_1434 Phase1→2→3) で各 Phase 完了時に殿確認を必須化するためのゲート。
# PreToolUse/PostToolUse hook から自動起動させない (手動実行・LOW 1h 実装範囲・advisor 推奨)。
# 家老が Phase 完了を検知した時点で本スクリプトを呼ぶ:
#   bash scripts/phase_gate_checker.sh <cmd_id> <phase_n> [summary]
#     → ntfy で殿に通知
#     → dashboard.md の 🚨 要対応セクションに自動追加 (flock で直列化)
#
# scan モード (cmd 登録状況チェック):
#   bash scripts/phase_gate_checker.sh --scan
#     → shogun_to_karo.yaml 全 cmd を走査し、多 Phase なのに phase_gate: 欄なしの
#       cmd を PHASE_GATE_WARNING: 行で出力 (exit 0・future hook 連携用)
#
# schema: shared_context/task_yaml_schema.md §2.2 参照

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SHOGUN_YAML="${REPO_DIR}/queue/shogun_to_karo.yaml"
DASHBOARD="${REPO_DIR}/dashboard.md"
NTFY_SCRIPT="${REPO_DIR}/scripts/ntfy.sh"

# ────────────────────────── subcommands ──────────────────────────

usage() {
    cat <<'USAGE' >&2
usage:
  phase_gate_checker.sh <cmd_id> <phase_n> [summary]   — Phase 完了時呼出 (ntfy + dashboard🚨)
  phase_gate_checker.sh --scan [--yaml <path>]         — shogun_to_karo.yaml 走査・未設定 cmd 警告
  phase_gate_checker.sh --help                          — 本ヘルプ

examples:
  bash scripts/phase_gate_checker.sh cmd_1434 3 "Phase3 完了: panel_review.html 5本生成"
  bash scripts/phase_gate_checker.sh --scan
USAGE
}

if [ $# -eq 0 ]; then
    usage
    exit 2
fi

case "$1" in
    --help|-h)
        usage
        exit 0
        ;;
    --scan)
        shift
        SCAN_YAML="$SHOGUN_YAML"
        while [ $# -gt 0 ]; do
            case "$1" in
                --yaml) SCAN_YAML="$2"; shift 2 ;;
                *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
            esac
        done
        if [ ! -f "$SCAN_YAML" ]; then
            echo "ERROR: yaml not found: $SCAN_YAML" >&2
            exit 2
        fi
        SCAN_YAML="$SCAN_YAML" python3 <<'PYEOF'
import os, re, sys
yaml_path = os.environ['SCAN_YAML']
with open(yaml_path) as f:
    content = f.read()
# split by cmd entries
entries = re.split(r'(?=^- id:\s*cmd_)', content, flags=re.MULTILINE)
warnings = 0
for entry in entries:
    if not entry.strip().startswith('- id:'):
        continue
    idm = re.search(r'^- id:\s*(\S+)', entry, re.MULTILINE)
    if not idm:
        continue
    cmd_id = idm.group(1).strip().strip('"').strip("'")
    # multi-phase detection: 2+ occurrences of "Phase N" or "Wave [A-Z]" in command
    # case-sensitive, whole-word boundary
    phase_matches = re.findall(r'\bPhase\s*[0-9]+\b', entry)
    wave_matches = re.findall(r'\bWave\s*[A-Z]\b', entry)
    if len(phase_matches) + len(wave_matches) < 2:
        continue
    # has phase_gate declared?
    if re.search(r'^\s+phase_gate:\s*(required|optional)', entry, re.MULTILINE):
        continue
    phases = sorted(set(phase_matches + wave_matches))
    print(f'PHASE_GATE_WARNING: {cmd_id} keywords={",".join(phases)} — no phase_gate: declared in shogun_to_karo.yaml')
    warnings += 1
if warnings:
    print(f'PHASE_GATE_SUMMARY: {warnings} cmd(s) need phase_gate review', file=sys.stderr)
PYEOF
        exit 0
        ;;
    -*)
        echo "Unknown flag: $1" >&2
        usage
        exit 2
        ;;
esac

# 通常モード: <cmd_id> <phase_n> [summary]
CMD_ID="$1"
PHASE_N="${2:-}"
SUMMARY="${3:-}"

if [ -z "$CMD_ID" ] || [ -z "$PHASE_N" ]; then
    echo "ERROR: cmd_id と phase_n は必須" >&2
    usage
    exit 2
fi

# cmd が実在するか確認 (ないなら警告のみ・fail はしない)
if [ -f "$SHOGUN_YAML" ]; then
    if ! grep -qE "^- id:\s*${CMD_ID}\b" "$SHOGUN_YAML"; then
        echo "WARNING: ${CMD_ID} is not found in ${SHOGUN_YAML} (continuing anyway)" >&2
    fi
fi

TS=$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)
HEADLINE="🚨 ${CMD_ID} Phase ${PHASE_N} 完了・殿確認要"
if [ -n "$SUMMARY" ]; then
    BODY="${HEADLINE}\n${SUMMARY}"
else
    BODY="${HEADLINE}"
fi

# ────────────────────────── ntfy 送信 ──────────────────────────
NTFY_EXIT=0
if [ -x "$NTFY_SCRIPT" ]; then
    if ! bash "$NTFY_SCRIPT" "$(printf '%b' "$BODY")" 2>>"${REPO_DIR}/logs/phase_gate_checker.log"; then
        NTFY_EXIT=$?
        echo "WARNING: ntfy.sh failed (exit $NTFY_EXIT) — dashboard append は継続" >&2
    fi
else
    echo "WARNING: ntfy.sh が見つからない or 実行不可 — skip" >&2
    NTFY_EXIT=127
fi

# ────────────────────────── dashboard.md 🚨 追加 ──────────────────────────
# flock で直列化 (家老/軍師の同時編集衝突回避)
# 追加位置: 「## 🚨 要対応」セクション末尾 = 次の「## 」見出し直前
DASHBOARD_EXIT=0
if [ -f "$DASHBOARD" ]; then
    DASHBOARD_FP="$DASHBOARD" CMD_ID="$CMD_ID" PHASE_N="$PHASE_N" \
    SUMMARY="$SUMMARY" TS="$TS" python3 <<'PYEOF' || DASHBOARD_EXIT=$?
import os, re, fcntl, sys
path = os.environ['DASHBOARD_FP']
cmd_id = os.environ['CMD_ID']
phase_n = os.environ['PHASE_N']
summary = os.environ.get('SUMMARY', '')
ts = os.environ['TS']

entry_header = f'### 🚨 {cmd_id} Phase {phase_n} 完了・殿確認要 ({ts})'
entry_body_lines = []
if summary:
    entry_body_lines.append(f'- 成果物: {summary}')
entry_body_lines.append(f'- 次 Phase: Phase {int(phase_n) + 1 if phase_n.isdigit() else "?"} 着手は殿判断 (OK / NG / 修正) 後')
entry_body_lines.append(f'- 出典: `scripts/phase_gate_checker.sh {cmd_id} {phase_n}` (H9)')
entry = entry_header + '\n' + '\n'.join(entry_body_lines) + '\n\n'

with open(path, 'r+') as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    try:
        content = f.read()
        # insertion point: end of "## 🚨 要対応" section = just before next "## " heading
        section_hdr = re.search(r'^##\s*🚨\s*要対応[^\n]*\n', content, re.MULTILINE)
        if not section_hdr:
            # fallback: append at end of file
            new_content = content.rstrip() + '\n\n' + entry
        else:
            section_start = section_hdr.end()
            # find next top-level "## " (non-🚨) after section_start
            rest = content[section_start:]
            # match next ^## (including with optional emoji/space)
            next_hdr = re.search(r'^##\s', rest, re.MULTILINE)
            if next_hdr:
                insert_at = section_start + next_hdr.start()
                new_content = content[:insert_at] + entry + content[insert_at:]
            else:
                new_content = content.rstrip() + '\n\n' + entry
        f.seek(0)
        f.truncate()
        f.write(new_content)
    finally:
        fcntl.flock(f, fcntl.LOCK_UN)

print(f'DASHBOARD_APPEND_OK: {cmd_id} Phase {phase_n}')
PYEOF
else
    echo "WARNING: ${DASHBOARD} が存在しない — skip" >&2
    DASHBOARD_EXIT=127
fi

# ────────────────────────── サマリ ──────────────────────────
echo "phase_gate_checker: ${CMD_ID} Phase ${PHASE_N} processed (ntfy=${NTFY_EXIT} dashboard=${DASHBOARD_EXIT})"

exit 0
