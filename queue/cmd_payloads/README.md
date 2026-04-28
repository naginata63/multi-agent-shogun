# queue/cmd_payloads/

cmd起票時のJSONペイロードを格納するディレクトリ。
API投入後もファイルを保持し、殿原文+指示の永続監査ログとする。

## 命名規則

`cmd_XXXX.json` — cmd_idベース・1 cmd 1ファイル

## フォーマット

```json
{
  "id": "cmd_XXXX",
  "priority": "high|medium|low",
  "project": "project-id",
  "lord_original": "殿の発言原文",
  "north_star": "ビジネス目標との紐付け",
  "purpose": "完了条件（1文）",
  "command_text": "タスク詳細（共通ルール含む）",
  "acceptance_criteria": ["条件1", "条件2"],
  "notify_karo": true
}
```

必須: `id`, `priority`, `lord_original`, `purpose`, `command_text`, `acceptance_criteria`
任意: `project`, `north_star`, `notify_karo`

## API投入

```bash
# cmd起票
curl -s -X POST http://192.168.2.7:8770/api/cmd_create \
  -H 'Content-Type: application/json' \
  --data @queue/cmd_payloads/cmd_XXXX.json

# inbox通知
curl -s -X POST http://192.168.2.7:8770/api/inbox_write \
  -H 'Content-Type: application/json' \
  -d '{"to":"agent","from":"agent","type":"type","message":"text"}'
```

**注意**: cmd_create は `--data @file` で投入。`-d '{...}'` 直書きは CHK10 で BLOCK される。
inbox_write の短文メッセージ（3行以下）は `-d '{...}'` 許可。

## ライフサイクル

| タイミング | 操作 |
|-----------|------|
| cmd起票時 | JSON作成 → API投入 |
| 進行中 | ファイル保持（変更不要） |
| cmd完了後 | 保持（監査ログ） |
| 半年以上経過 | 家老判断で queue/cmd_archive/ に移動 |

## テンプレート

`context/cmd_template.md` を参照。全フィールドの説明・タスク種別ルール付き。
