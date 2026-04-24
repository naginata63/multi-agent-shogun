#!/bin/bash
# プロジェクト全体を別ドライブにrsync差分バックアップ
set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="/mnt/backup/multi-agent-shogun/full"
LOG_FILE="$PROJECT_ROOT/logs/backup_full.log"

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] フルバックアップ開始" | tee -a "$LOG_FILE"

# rsync差分コピー（初回以外は変更分のみ）
# --copy-unsafe-links: tree外への symlink を referent に変換
# --ignore-errors:     I/O エラーでも --delete を続行（exit codeは抑止しない）
# playwright-data/: Chromium プロファイル配下に /tmp 指向の dangling symlink
#                   (SingletonSocket 等) が常時生成されるため除外
rsync -a --delete \
    --copy-unsafe-links \
    --ignore-errors \
    --exclude='.git' \
    --exclude='venv_whisper/' \
    --exclude='tools/COEIROINK_*' \
    --exclude='tools/video-subtitle-remover/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='remotion-project/node_modules/' \
    --exclude='projects/note_mcp_server/playwright-data/' \
    "$PROJECT_ROOT/" "$BACKUP_DIR/"

SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完了: $SIZE" | tee -a "$LOG_FILE"
