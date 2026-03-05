#!/bin/bash
# scripts/cmd_rotate.sh
# shogun_to_karo.yaml が肥大化した際に完了済みcmdをアーカイブへ退避するスクリプト
#
# Usage: bash scripts/cmd_rotate.sh [--force]
#   --force: 閾値チェックをスキップして強制実行
#
# アーカイブ対象: status: done または status: cancelled のエントリ
# 残すもの: commands: ヘッダー + status: pending のエントリ

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET="$PROJECT_ROOT/queue/shogun_to_karo.yaml"
ARCHIVE_DIR="$PROJECT_ROOT/queue/cmd_archive"
THRESHOLD_LINES=500
THRESHOLD_BYTES=30720  # 30KB

# shogun_to_karo.yaml の存在確認
if [[ ! -f "$TARGET" ]]; then
  echo "Error: shogun_to_karo.yaml が見つかりません: $TARGET" >&2
  exit 1
fi

# PyYAML の確認
python3 -c "import yaml" 2>/dev/null || {
  echo "Error: PyYAML がインストールされていません。pip install pyyaml でインストールしてください。" >&2
  exit 1
}

# 閾値チェック
lines=$(wc -l < "$TARGET")
bytes=$(wc -c < "$TARGET")

if [[ "${1:-}" != "--force" ]] && [[ $lines -le $THRESHOLD_LINES ]] && [[ $bytes -le $THRESHOLD_BYTES ]]; then
  echo "shogun_to_karo.yaml は閾値以下（${lines}行 / ${bytes}bytes）。ローテーション不要。"
  exit 0
fi

echo "cmd_rotate実行（${lines}行 / ${bytes}bytes）..."

# アーカイブディレクトリ作成
mkdir -p "$ARCHIVE_DIR"
timestamp=$(date "+%Y%m%d_%H%M%S")
archive_file="$ARCHIVE_DIR/cmds_${timestamp}.yaml"

# テキストベースで各エントリを分割し、status: done/cancelled をアーカイブに退避
# PyYAML のパースではなく、`^- id:` を区切りとしたテキスト分割で処理
python3 - "$TARGET" "$archive_file" <<'PYEOF'
import sys
import re

target_path = sys.argv[1]
archive_path = sys.argv[2]

with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ヘッダー行（commands:）と各エントリを分割
# エントリは "^- id:" で始まる行から次の "^- id:" の手前まで
header = "commands:\n"
lines = content.split('\n')

# ヘッダー部分（最初の commands: 行）をスキップして各エントリを収集
entries = []
current_entry_lines = []
in_entry = False

for line in lines:
    if re.match(r'^- id:', line):
        if current_entry_lines:
            entries.append('\n'.join(current_entry_lines))
        current_entry_lines = [line]
        in_entry = True
    elif in_entry:
        current_entry_lines.append(line)

if current_entry_lines:
    entries.append('\n'.join(current_entry_lines))

# 各エントリを pending / archived に振り分け
# status: は通常 "  status: done" のような形式で記述される
STATUS_RE = re.compile(r'^\s+status:\s+(done|cancelled)\s*$', re.MULTILINE)

pending_entries = []
archived_entries = []

for entry in entries:
    # エントリ内に status: done または status: cancelled があるか確認
    # ただしネストされた status（サブタスク等）を誤検知しないよう
    # トップレベルの status フィールド（インデント2スペース）のみ対象
    top_status_match = re.search(r'^  status:\s+(\S+)', entry, re.MULTILINE)
    if top_status_match:
        status_val = top_status_match.group(1).rstrip("'\"")
        if status_val in ('done', 'cancelled'):
            archived_entries.append(entry)
        else:
            pending_entries.append(entry)
    else:
        # status フィールドがない場合は pending 扱い
        pending_entries.append(entry)

# アーカイブファイル書き出し（完全なYAML形式）
with open(archive_path, 'w', encoding='utf-8') as f:
    f.write("commands:\n")
    for entry in archived_entries:
        f.write(entry)
        if not entry.endswith('\n'):
            f.write('\n')

# 本体ファイルを pending のみに書き換え
with open(target_path, 'w', encoding='utf-8') as f:
    f.write("commands:\n")
    for entry in pending_entries:
        f.write(entry)
        if not entry.endswith('\n'):
            f.write('\n')

print(f"アーカイブ: {len(archived_entries)}件 → {archive_path}")
print(f"残留(pending): {len(pending_entries)}件")
PYEOF

new_lines=$(wc -l < "$TARGET")
new_bytes=$(wc -c < "$TARGET")
echo "削減完了: ${lines}行→${new_lines}行 / ${bytes}bytes→${new_bytes}bytes"
echo "cmd_rotate完了。"
