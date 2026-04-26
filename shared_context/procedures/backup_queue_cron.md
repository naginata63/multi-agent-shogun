# queue/運用データ定期バックアップ手順 (cmd_1369)

## 作成するファイル
- `scripts/backup_queue.sh` — バックアップスクリプト
- `backups/queue/README.md` — リストア手順書

## scripts/backup_queue.sh の内容

```bash
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

echo "[$(date '+%Y-%m-%d %H:%M:%S')] バックアップ開始: $ARCHIVE" | tee -a "$LOG_FILE"

# rsync → tar.gz
rsync -a --exclude='*.tmp' "$QUEUE_DIR/" "$BACKUP_PATH/"
tar czf "$ARCHIVE" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$BACKUP_PATH"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完了: $(du -sh "$ARCHIVE" | cut -f1)" | tee -a "$LOG_FILE"

# 7日以上前のバックアップを自動削除
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -exec rm -f {} \; -exec echo "削除: {}" \; | tee -a "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] クリーンアップ完了" | tee -a "$LOG_FILE"
```

## .gitignore への追記
`backups/queue/*.tar.gz` を .gitignore に追加

## テスト手順
1. `bash /home/murakami/multi-agent-shogun/scripts/backup_queue.sh` を手動実行
2. `ls /home/murakami/multi-agent-shogun/backups/queue/` で *.tar.gz 生成確認
3. `tar tzf /home/murakami/multi-agent-shogun/backups/queue/*.tar.gz | head -20` で中身確認（tasks/, inbox/, reports/ 含まれるか）
4. ファイルサイズ確認

## 完了処理
```bash
git add scripts/backup_queue.sh backups/queue/README.md .gitignore
git commit -m "feat(cmd_1369): queue/定期バックアップスクリプト作成（7日保持・tar.gz）"
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽2号、subtask_1369a完了。バックアップサイズとtar.gz中身を報告。" report_completed ashigaru2
```
