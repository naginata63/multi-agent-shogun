#!/usr/bin/env bash
# lecture-speaker-notes-grep-check — Marp講義スライド品質チェッカー
# Usage: bash check.sh [file1.md file2.md ...]
set -uo pipefail

WAR_PATTERNS=('御意' 'つかまつる' 'ござる' '拙者' '候[^補選手者]')
WAR_NAMES=('御意' 'つかまつる' 'ござる' '拙者' '候(非候補等)')
REAL_NAME_PAT='村上'

PASS_COUNT=0
FAIL_COUNT=0
FAIL_DETAILS=""

for f in "$@"; do
  [ -f "$f" ] || { echo "[WARN] File not found: $f"; continue; }
  file_fail=0
  file_detail=""

  # --- Speaker Notes Check (python3) ---
  stripped=$(CHECK_FILE="$f" python3 << 'PYEOF'
import os
f = os.environ.get("CHECK_FILE", "")
if not f:
    raise SystemExit(1)
content = open(f).read()
if content.startswith('---'):
    end = content.find('---', 3)
    if end != -1:
        content = content[end+3:]
slides = content.split('\n---')
for i, s in enumerate(slides):
    s = s.strip()
    if not s:
        continue
    has_notes = '<!--' in s and '-->' in s
    status = 'OK' if has_notes else 'MISSING'
    print(f'slide_{i+1}:{status}')
PYEOF
  ) || stripped=""

  total_slides=0
  missing_count=0
  if [ -n "$stripped" ]; then
    total_slides=$(echo "$stripped" | grep -c '^slide_')
    missing_count=$(echo "$stripped" | grep -c ':MISSING$') || missing_count=0
    if [ "$missing_count" -gt 0 ]; then
      missing_which=$(echo "$stripped" | grep ':MISSING$' | sed 's/:MISSING$//' | tr '\n' ',' | sed 's/,$//')
      file_fail=1
      file_detail+="  [FAIL] Speaker notes: ${missing_count}/${total_slides} slides missing (${missing_which})\n"
    else
      file_detail+="  [PASS] Speaker notes: ${total_slides}/${total_slides} slides OK\n"
    fi
  else
    file_detail+="  [WARN] Could not parse slides (python3 unavailable?)\n"
  fi

  # --- Forbidden Words Check ---
  for i in "${!WAR_PATTERNS[@]}"; do
    pat="${WAR_PATTERNS[$i]}"
    name="${WAR_NAMES[$i]}"
    matches=$(grep -nP "$pat" "$f" 2>/dev/null || true)
    if [ -n "$matches" ]; then
      count=$(echo "$matches" | wc -l)
      file_fail=1
      file_detail+="  [FAIL] 戦国用語(${name}): ${count} hit(s)\n"
      while IFS= read -r line; do
        file_detail+="    ${line}\n"
      done <<< "$(echo "$matches" | head -3)"
    fi
  done

  # --- Real Name Check ---
  matches=$(grep -nP "$REAL_NAME_PAT" "$f" 2>/dev/null || true)
  if [ -n "$matches" ]; then
    count=$(echo "$matches" | wc -l)
    file_fail=1
    file_detail+="  [FAIL] 本名(${REAL_NAME_PAT}): ${count} hit(s)\n"
    while IFS= read -r line; do
      file_detail+="    ${line}\n"
    done <<< "$(echo "$matches" | head -3)"
  fi

  if [ "$file_fail" -eq 0 ]; then
    echo "[PASS] $(basename "$f")"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "[FAIL] $(basename "$f")"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_DETAILS+="$(basename "$f"):\n${file_detail}\n"
  fi
done

echo ""
echo "=== Summary ==="
TOTAL=$((PASS_COUNT + FAIL_COUNT))
echo "PASS: ${PASS_COUNT}/${TOTAL} files"
echo "FAIL: ${FAIL_COUNT}/${TOTAL} files"

if [ -n "$FAIL_DETAILS" ]; then
  echo ""
  echo "=== FAIL Details ==="
  echo -e "$FAIL_DETAILS"
fi

exit "$FAIL_COUNT"
