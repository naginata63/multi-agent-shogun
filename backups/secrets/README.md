# config秘密鍵GPG暗号化バックアップ

## 概要

`config/` 配下の秘密鍵ファイルをGPG対称鍵暗号（AES256）でバックアップ・リストアするスクリプト群。

## ファイル構成

```
scripts/backup_secrets.sh   — 暗号化バックアップ
scripts/restore_secrets.sh  — 復号化リストア
backups/secrets/*.gpg       — 暗号化済みバックアップ（git管理外）
```

## バックアップ対象

| ファイル | 内容 |
|----------|------|
| config/vertex_api_key.env | Vertex AI API鍵 |
| config/assemblyai_key.env | AssemblyAI API鍵 |
| config/config.json | 各種API設定 |
| config/projects.yaml | プロジェクト設定 |

存在しないファイルは自動スキップ。

## 使い方

### バックアップ（暗号化）

```bash
bash scripts/backup_secrets.sh
```

パスフレーズを2回入力（GPG対話プロンプト）。`backups/secrets/` に `.gpg` ファイルが生成される。

### リストア（復号化）

```bash
bash scripts/restore_secrets.sh
```

パスフレーズを入力。`/tmp/restore_secrets_YYYYMMDD_HHMMSS/` に復号化される。

### 往復テスト（バックアップ→リストア→diff確認）

```bash
# 1. バックアップ
bash scripts/backup_secrets.sh

# 2. リストア
bash scripts/restore_secrets.sh

# 3. 比較（出力なし＝一致）
RESTORE_DIR=$(ls -td /tmp/restore_secrets_* | head -1)
diff "$RESTORE_DIR/vertex_api_key.env" config/vertex_api_key.env
```

## 注意事項

- **パスフレーズの管理**: パスフレーズを紛失すると復号化不可。安全な場所に保管すること。
- **.gpgファイルはgit管理外**: `.gitignore` で除外済み。リポジトリにコミットされない。
- **定期実行**: cronで自動化する場合は環境変数 `SECRETS_PASSPHRASE` を設定し、`--passphrase "$SECRETS_PASSPHRASE"` を使用。
  環境変数は `.bashrc` や `.env` には書かず、cron環境限定で設定すること。
- **外部保管推奨**: `.gpg` ファイルはUSBメモリやクラウドストレージ（暗号化済み）に別途コピーすること。
  プロジェクトディレクトリ内のみだとディスク障害時に喪失する。
