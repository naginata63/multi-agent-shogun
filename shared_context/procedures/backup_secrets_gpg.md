# config秘密鍵GPG暗号化バックアップ手順 (cmd_1368)

## 作成するファイル
- `scripts/backup_secrets.sh` — 暗号化スクリプト
- `scripts/restore_secrets.sh` — 復号化スクリプト
- `backups/secrets/README.md` — 手順書

## scripts/backup_secrets.sh の内容

```bash
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
    gpg --symmetric --cipher-algo AES256 --output "$outfile" "$f"
    echo "✅ 完了: $outfile"
done
echo "=== バックアップ完了 ==="
```

## scripts/restore_secrets.sh の内容

```bash
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
    gpg --decrypt --output "$outfile" "$f"
done
echo "=== リストア完了: $RESTORE_DIR ==="
echo "確認後、必要に応じて $PROJECT_ROOT/config/ に手動コピーしてください"
```

## .gitignore への追記
`backups/secrets/` を .gitignore に追加（暗号化済み.gpgもgitにコミット不可）

## テスト手順
1. `bash /home/murakami/multi-agent-shogun/scripts/backup_secrets.sh` 実行（パスフレーズ入力）
2. `ls /home/murakami/multi-agent-shogun/backups/secrets/` で *.gpg 生成確認
3. `bash /home/murakami/multi-agent-shogun/scripts/restore_secrets.sh` で復号化テスト
4. 復号化結果と元ファイルを比較: `diff /tmp/restore_secrets_*/vertex_api_key.env /home/murakami/multi-agent-shogun/config/vertex_api_key.env`

## 完了処理
```bash
git add scripts/backup_secrets.sh scripts/restore_secrets.sh backups/secrets/README.md .gitignore
git commit -m "feat(cmd_1368): config秘密鍵GPG暗号化バックアップスクリプト作成"
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽1号、subtask_1368a完了。暗号化・復号化テスト結果を報告。" report_completed ashigaru1
```
