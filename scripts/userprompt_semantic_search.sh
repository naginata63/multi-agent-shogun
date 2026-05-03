#!/usr/bin/env bash
# userprompt_semantic_search.sh — UserPromptSubmit hook (cmd_1607)
# ユーザー入力(prompt)から関連 procedure/script を自動検索し候補表示
# shogun/karo のみ実行。その他のエージェントは即座 exit 0

set -uo pipefail

# agent filter
AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
[[ "$AGENT_ID" != "shogun" && "$AGENT_ID" != "karo" ]] && exit 0

# read stdin JSON
INPUT=$(cat 2>/dev/null || true)
[[ -z "$INPUT" ]] && exit 0

PROMPT=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null || true)
[[ -z "$PROMPT" ]] && exit 0

# min length check
((${#PROMPT} < 5)) && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEARCH_PY="${SCRIPT_DIR}/semantic_search.py"

[[ ! -f "$SEARCH_PY" ]] && exit 0

# D2 fix: search all sources (no --source filter, avoids faiss reconstruct error)
# D1 fix: timeout 30s (embedding model load takes ~10s)
RESULTS=$(source ~/.bashrc && timeout 30 python3 "$SEARCH_PY" query "$PROMPT" --top 5 --json 2>/dev/null || true)

[[ -z "$RESULTS" || "$RESULTS" == "[]" ]] && exit 0

# parse JSON, filter by threshold, format output
# D4 fix: threshold 0.55 → 0.45
FORMATTED=$(echo "$RESULTS" | python3 -c "
import sys, json

THRESHOLD = 0.45
results = json.load(sys.stdin)
hits = [r for r in results if r.get('score', 0) >= THRESHOLD]
if not hits:
    sys.exit(0)

print('📚 関連 procedure/script (自動検索):')
for h in hits[:5]:
    f = h.get('file', '')
    s = h.get('score', 0)
    t = h.get('text', '')
    # snippet: first non-empty, non-comment line, max 80 chars
    snippet = ''
    for line in t.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('//'):
            snippet = line[:80]
            break
    print(f'  -> {f} (score={s:.2f})')
    if snippet:
        print(f'     {snippet}')
" 2>/dev/null || true)

[[ -n "$FORMATTED" ]] && echo "$FORMATTED"

exit 0
