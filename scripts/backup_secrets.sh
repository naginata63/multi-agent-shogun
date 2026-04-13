#!/bin/bash
# config/ 配下の秘密鍵をGPG暗号化してバックアップ
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups/secrets"
CONFIG_DIR="$PROJECT_ROOT/config"
mkdir -p "$BACKUP_DIR"

TARGETS=(
    "$CONFIG_DIR/vertex_api_key.env"
    "$CONFIG_DIR/assemblyai_key.env"
    "$CONFIG_DIR/config.json"
    "$CONFIG_DIR/projects.yaml"
)

echo "=== config秘密鍵バックアップ ==="
echo "出力先: $BACKUP_DIR"
for f in "${TARGETS[@]}"; do
    [ -f "$f" ] || { echo "スキップ（存在しない）: $f"; continue; }
    outfile="$BACKUP_DIR/$(basename "$f").gpg"
    echo "暗号化: $(basename "$f") → $(basename "$outfile")"
    gpg --symmetric --cipher-algo AES256 --batch --passphrase-fd 3 --output "$outfile" "$f" 3< /dev/tty
    echo "完了: $outfile"
done
echo "=== バックアップ完了 ==="
