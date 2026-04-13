# queue/ バックアップ リストア手順

## バックアップの一覧

```bash
ls -lh /home/murakami/multi-agent-shogun/backups/queue/*.tar.gz
```

## リストア手順

```bash
# 1. バックアップを選択（例: 20260413_100100）
BACKUP_FILE="20260413_100100.tar.gz"
BACKUP_DIR="/home/murakami/multi-agent-shogun/backups/queue"
QUEUE_DIR="/home/murakami/multi-agent-shogun/queue"

# 2. 現在のqueue/を退避（上書き防止）
mv "$QUEUE_DIR" "${QUEUE_DIR}.bak_$(date +%Y%m%d_%H%M%S)"

# 3. バックアップを展開
mkdir -p "$QUEUE_DIR"
tar xzf "$BACKUP_DIR/$BACKUP_FILE" -C "$BACKUP_DIR"
cp -a "$BACKUP_DIR/${BACKUP_FILE%.tar.gz}/" "$QUEUE_DIR/"

# 4. 展開済み一時ディレクトリを削除
rm -rf "$BACKUP_DIR/${BACKUP_FILE%.tar.gz}"

# 5. 確認
ls "$QUEUE_DIR/tasks/" "$QUEUE_DIR/inbox/" "$QUEUE_DIR/reports/"
```

## 自動バックアップ

- スクリプト: `scripts/backup_queue.sh`
- 保持期間: 7日（自動削除）
- フォーマット: tar.gz（タイムスタンプ付き）
