#!/bin/bash
# queue/ 配下をタイムスタンプ付きtar.gzにバックアップ
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
QUEUE_DIR="$PROJECT_ROOT/queue"
BACKUP_DIR="$PROJECT_ROOT/backups/queue"
LOG_FILE="$PROJECT_ROOT/logs/backup_queue.log"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
ARCHIVE="$BACKUP_PATH.tar.gz"

mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] バックアップ開始: $ARCHIVE" | tee -a "$LOG_FILE"

# rsync → tar.gz
# -L: シンボリックリンクを追従して実ファイルをコピー（inbox/がsymlinkのため必須）
rsync -aL --exclude='*.tmp' "$QUEUE_DIR/" "$BACKUP_PATH/"
tar czf "$ARCHIVE" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$BACKUP_PATH"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完了: $(du -sh "$ARCHIVE" | cut -f1)" | tee -a "$LOG_FILE"

# 7日以上前のバックアップを自動削除
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -exec rm -f {} \; -exec echo "削除: {}" \; | tee -a "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] クリーンアップ完了" | tee -a "$LOG_FILE"
