#!/bin/bash
# scripts/dashboard_rotate.sh
# dashboard.mdが肥大化した際に自動バックアップ＆完了セクションをクリアするスクリプト
#
# Usage: bash scripts/dashboard_rotate.sh [--force]
#   --force: 閾値チェックをスキップして強制実行
#
# 残すセクション: ヘッダー、🚨要対応、🔄進行中、⏸️待機中、❓伺い事項
# 削除するセクション: ✅最近の完了、✅本日の戦果、🛠️生成されたスキル

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DASHBOARD="$PROJECT_ROOT/dashboard.md"
ARCHIVE_DIR="$PROJECT_ROOT/dashboard_archive"
THRESHOLD_LINES=200
THRESHOLD_BYTES=10240  # 10KB

# dashboard.md の存在確認
if [[ ! -f "$DASHBOARD" ]]; then
  echo "Error: dashboard.md が見つかりません: $DASHBOARD" >&2
  exit 1
fi

# 閾値チェック
lines=$(wc -l < "$DASHBOARD")
bytes=$(wc -c < "$DASHBOARD")

if [[ "${1:-}" != "--force" ]] && [[ $lines -le $THRESHOLD_LINES ]] && [[ $bytes -le $THRESHOLD_BYTES ]]; then
  echo "dashboard.mdは閾値以下（${lines}行 / ${bytes}bytes）。ローテーション不要。"
  exit 0
fi

echo "dashboard.mdをローテーション実行（${lines}行 / ${bytes}bytes）..."

# バックアップ
mkdir -p "$ARCHIVE_DIR"
timestamp=$(date "+%Y%m%d_%H%M%S")
backup_file="$ARCHIVE_DIR/dashboard_${timestamp}.md"
cp "$DASHBOARD" "$backup_file"
echo "バックアップ完了: $backup_file"

# クリア後のdashboard.mdを生成
# 削除対象セクション: ✅（最近の完了・本日の戦果）、🛠️（生成されたスキル）
python3 - "$DASHBOARD" <<'PYEOF'
import sys

dashboard_path = sys.argv[1]

with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

remove_patterns = ['✅', '🛠️']

lines = content.split('\n')
output = []
skip = False

for line in lines:
    if line.startswith('## '):
        # セクション開始 — 削除対象かどうか判定
        skip = any(p in line for p in remove_patterns)
    if not skip:
        output.append(line)

# 末尾の余分な空行を整理
while output and output[-1].strip() == '':
    output.pop()
output.append('')  # ファイル末尾に改行1つ

new_content = '\n'.join(output)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

removed_lines = len(lines) - len(output)
print(f"クリア完了。{len(output)}行に削減（{removed_lines}行削除）。")
PYEOF

echo "dashboard_rotate完了。"
