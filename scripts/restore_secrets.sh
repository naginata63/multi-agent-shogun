#!/bin/bash
# backups/secrets/ の *.gpg を /tmp/restore_secrets/ に復号化
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups/secrets"
RESTORE_DIR="/tmp/restore_secrets_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESTORE_DIR"

echo "=== 秘密鍵リストア（復号化先: $RESTORE_DIR） ==="
for f in "$BACKUP_DIR"/*.gpg; do
    [ -f "$f" ] || { echo "バックアップファイルが見つかりません"; exit 1; }
    outfile="$RESTORE_DIR/$(basename "${f%.gpg}")"
    echo "復号化: $(basename "$f") → $outfile"
    gpg --decrypt --batch --passphrase-fd 3 --output "$outfile" "$f" 3< /dev/tty
done
echo "=== リストア完了: $RESTORE_DIR ==="
echo "確認後、必要に応じて $PROJECT_ROOT/config/ に手動コピーしてください"
