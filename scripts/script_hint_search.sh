#!/usr/bin/env bash
# script_hint_search.sh — PreToolUse Bash hook (cmd_1549)
# Bash実行時にスクリプト/procedureを自動検索し、候補を表示
# マッチ時 top3 結果を stderr に出力 (hook警告チャネル)

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
[[ "$TOOL_NAME" != "Bash" ]] && exit 0

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)
[[ -z "$COMMAND" || ${#COMMAND} -lt 8 ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# 自分自身のテスト実行はスキップ
echo "$COMMAND" | grep -q "script_hint_search" && exit 0

# keyword aliases: コマンド中の語 → 検索語マッピング
# ファイル名と直接一致しない alias を定義
ALIAS_FILE="${REPO_DIR}/.claude/script_hint_aliases.txt"

RESULTS=$(REPO_DIR="$REPO_DIR" COMMAND="$COMMAND" ALIAS_FILE="$ALIAS_FILE" python3 <<'PYEOF' 2>/dev/null
import os, re

repo_dir = os.environ.get('REPO_DIR', '')
command = os.environ.get('COMMAND', '').lower()
alias_file = os.environ.get('ALIAS_FILE', '')

if len(command) < 8:
    exit(0)

# Extract meaningful tokens
skip_words = {
    'sudo','bash','python3','python','source','curl','grep','find','head',
    'tail','sort','uniq','wc','awk','sed','tr','cut','xargs','tee','mktemp',
    'realpath','dirname','basename','test','echo','cat','ls','cd','rm','mv',
    'cp','chmod','chown','mkdir','touch','which','type','file','stat','date',
    'sleep','wait','kill','trap','exec','exit','set','unset','export','import',
    'git','npm','node','pip','tmux','jq','yq','make','dev','null','true',
    'false','text','json','yaml','md','log','out','err','tmp','var','opt',
    'usr','bin','etc','home','the','and','for','not','but','all','any','can',
    'has','with','this','that','from','into','run','get','put','add','del',
}

tokens = re.split(r'[\s;|&<>(){}\[\]=`"\']+', command)
keywords = []
for t in tokens:
    t = t.strip('"').strip("'").strip('`').strip()
    if len(t) < 3 or t.startswith('-') or t.startswith('$') or t.startswith('+'):
        continue
    if t in skip_words or t.replace('.','').isdigit():
        continue
    # Extract basename from paths (e.g. scripts/vertical_convert.sh → vertical_convert)
    if '/' in t:
        t = os.path.splitext(os.path.basename(t))[0]
        if len(t) < 3 or t in skip_words:
            continue
    else:
        t = os.path.splitext(t)[0] if '.' in t and not t.startswith('.') else t
    keywords.append(t)

if not keywords:
    exit(0)

# Load aliases (format: alias_name search_terms...)
aliases = {}
if os.path.isfile(alias_file):
    with open(alias_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                aliases[parts[0]] = parts[1:]

# Expand keywords with aliases
expanded = list(keywords)
for kw in keywords:
    if kw in aliases:
        expanded.extend(aliases[kw])

# Collect searchable files
files = []
for d in ['scripts', 'shared_context/procedures']:
    full_dir = os.path.join(repo_dir, d)
    if not os.path.isdir(full_dir):
        continue
    for f in os.listdir(full_dir):
        if f.startswith('.') or f == 'logs':
            continue
        full_path = os.path.join(full_dir, f)
        if os.path.isfile(full_path):
            files.append((d + '/' + f, os.path.splitext(f)[0].lower()))

# Score files
scored = []
for path, name_base in files:
    score = 0
    for kw in expanded:
        if kw in name_base:
            score += 2
        elif kw in path.lower():
            score += 1
    if score > 0:
        scored.append((score, path))

scored.sort(key=lambda x: (-x[0], x[1]))
for _, path in scored[:3]:
    print(path)
PYEOF
)

if [[ -n "$RESULTS" ]]; then
    echo "📋 script/procedure 候補:" >&2
    while IFS= read -r line; do
        [[ -n "$line" ]] && echo "  → $line" >&2
    done <<< "$RESULTS"
fi

exit 0
