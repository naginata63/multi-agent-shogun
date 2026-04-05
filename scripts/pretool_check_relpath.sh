#!/usr/bin/env bash
# pretool_check_relpath.sh — PreToolUse hook 4
# queue/tasks/*.yaml 編集時の相対パス検出
#
# 家老が tasks/*.yaml に相対パスを書くのを防止する。
# フルパス（/home/...）のみ許可。

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)

# ツール名とファイルパスを抽出
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)

# Edit または Write ツールのみチェック
if [[ "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Write" ]]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('file_path', ti.get('path', '')))
" 2>/dev/null || true)

# queue/tasks/*.yaml のみ対象
if ! echo "$FILE_PATH" | grep -qP 'queue/tasks/.*\.yaml$'; then
  exit 0
fi

# 編集内容を取得
CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
parts = []
if 'new_string' in ti:
    parts.append(ti['new_string'])
if 'content' in ti:
    parts.append(ti['content'])
print('\n'.join(parts))
" 2>/dev/null || true)

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# 相対パス検出
# コマンド + 相対パス のパターンを検出
# 例: python3 scripts/..., bash scripts/..., source config/..., cd projects/...
RELATIVE_PATHS=$(echo "$CONTENT" | python3 -c "
import sys, re

content = sys.stdin.read()
violations = []

# コマンド + 相対パス のパターン
# /home/ または /tmp/ 等の絶対パスは除外
cmd_pattern = re.compile(
    r'(?:python3?|bash|sh|source|cd|cat|ls|mkdir|cp|mv|rm|chmod|chown|node|npm|npx|pip|git|curl|wget)\s+'
    r'((?:config|scripts|projects|work|queue|skills|instructions|context|docs|src|lib|bin|tmp|data)\S*)',
    re.MULTILINE
)

for m in cmd_pattern.finditer(content):
    path = m.group(1)
    # /home/ で始まる絶対パスはOK
    if path.startswith('/home/'):
        continue
    # / で始まる他の絶対パスもOK
    if path.startswith('/'):
        continue
    # 相対パス検出
    cmd = m.group(0).split()[0]
    violations.append(f'  Line: {cmd} {path}')

# パス代入パターン (TARGET=scripts/... 等)
assign_pattern = re.compile(
    r'(?:TARGET|PATH|DIR|ROOT|OUTPUT|INPUT|SRC|DST)\s*=\s*'
    r'((?:config|scripts|projects|work|queue|skills|instructions)\S*)',
    re.MULTILINE
)

for m in assign_pattern.finditer(content):
    path = m.group(1)
    if path.startswith('/home/'):
        continue
    if path.startswith('/'):
        continue
    violations.append(f'  Assignment: {m.group(0).split(\"=\")[0].strip()} = {path}')

if violations:
    print('\n'.join(violations))
" 2>/dev/null || true)

if [[ -n "$RELATIVE_PATHS" ]]; then
  echo "BLOCKED: queue/tasks/*.yaml 内に相対パスを検出。フルパス（/home/murakami/...）を使用せよ。" >&2
  echo "$RELATIVE_PATHS" >&2
  echo "" >&2
  echo "相対パスは足軽の作業ディレクトリに依存し、解決に失敗するバグの原因になります。" >&2
  echo "cmd_1165 で報告された根本原因: ref_images に相対パスを書いた結果、画像生成に失敗。" >&2
  exit 2
fi

exit 0
