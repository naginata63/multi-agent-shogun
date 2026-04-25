# MCP Dashboard API 利用ガイド

cmd/inbox/task の操作は YAML 直読み・直書きではなく **HTTP API 経由** を第一選択とする。
背景: cmd_1488 で SQLite dual-path 完成・cmd_1494 で read 側も SQLite 切替。
API がデータ整合性 (flock + dual-path + 自動通知) を一元担保するため、各エージェントは API を使え。

## エンドポイント (LAN内・認証なし・http://192.168.2.7:8770/)

### GET 系 (read)

| Path | パラメータ | 用途 |
|------|-----------|------|
| `/api/cmd_list` | `status=`, `q=`, `limit=` (**default 20**), `slim=1` | cmds 一覧 (slim=1 で command_text 等の重 field 除外・約-89%) |
| `/api/cmd_detail` | `id=cmd_XXX` (必須) | 1件分 full データ (acceptance_criteria 等 JSON parse 済) |
| `/api/task_list` | `agent=`, `status=`, `cmd=`, `limit=50` | tasks 一覧 (agent/status/parent_cmd filter) |
| `/api/inbox_messages` | `agent=`, `unread=1`, `limit=20` | inbox 取得 (未読のみ可・SQLite から累積アクセス) |
| `/api/report_list` | `cmd=`, `worker=`, `task=`, `limit=20` | reports 一覧 |
| `/api/report_detail` | `id=<report_id>` (必須) | 1件分 full データ + YAML 全文 (`content_yaml` フィールド) |
| `/api/dashboard` | `slim=1` (家老 context 削減用) | 集計+検出ルール (R1〜R6) 込み・slim=1 で約 1/12 に縮小 |
| `/api/agent_health` | なし | 各エージェント pane生存・inbox mtime・タスク状態 |
| `/api/dashboard_md` | なし | dashboard.md の markdown 全文取得 (家老の Read 直叩き廃止) |
| `/api/job_status` | `id=<job_id>` | 非同期ジョブ進捗 |

### POST 系 (write)

| Path | body キー | 用途 |
|------|----------|------|
| `/api/cmd_create` | `id`, `purpose`, `priority`, `lord_original`, `notify_karo` (optional・default true) | cmd 起票 (YAML+SQLite dual-path・家老inbox自動通知) |
| `/api/inbox_write` | `to`, `message`, `type`, `from` | inboxメッセージ送信 (cmd_1492で実装) |
| `/api/task_create` | `agent`, `task_id`, `status`, `priority`, `title`, `parent_cmd`, `target_path`, `acceptance_criteria` 等 | タスク起票 (queue/tasks/{agent}.yaml + SQLite tasks dual-path) |
| `/api/report_create` | `report_id`, `worker_id`, `status`, `task_id`, `parent_cmd`, `qa_decision`, `summary`, `report_path` (optional) | レポート起票 (queue/reports/{report_id}.yaml + SQLite reports dual-path) |
| `/api/dashboard_update` | `content` (全文上書き) or `section` + `section_content` (部分置換) | dashboard.md 書換え (家老の Edit 直叩き廃止)・自動で .bak 退避 |
| `/api/save_panels_json` | (manga short用) | 漫画パネル設計保存 |
| `/api/suggest_director_notes` | (manga short用) | director_notes 生成 |

## 部下別 推奨利用シナリオ

### 家老 (karo)
- **dashboard.md 生成時**: `curl /api/dashboard` で stats/active_cmds/action_required を一発取得
  - 旧: `yaml.safe_load(SHOGUN_TO_KARO)` → 廃止移行
- **cmd 状態確認**: `curl '/api/cmd_list?status=in_progress'` で進行中のみ
- **cmd 詳細確認**: `curl '/api/cmd_detail?id=cmd_XXX'` で acceptance_criteria + lord_original
- **inbox 通知**: `curl -X POST /api/inbox_write -d '{"to":"ashigaru3", ...}'` (bash inbox_write.sh 直叩き廃止)

### 足軽 (ashigaru)
- **割当cmdの詳細**: `curl '/api/cmd_detail?id=$PARENT_CMD'` で north_star/lord_original/acceptance_criteria 把握
- **既存 cmd 履歴検索**: `curl '/api/cmd_list?q=keyword'` で類似 cmd を参照

### 軍師 (gunshi)
- **QC対象の入力データ**: `curl '/api/cmd_detail?id=cmd_XXX'` で acceptance_criteria を直接取得
- **過去 QC 履歴**: `curl '/api/cmd_list?q=qc'` で軍師 QC タスク串刺し検索

### 将軍 (shogun)
- **戦況確認**: ブラウザで http://192.168.2.7:8770/ (HTML経由)
- **cmd 起票**: `curl -X POST /api/cmd_create -d '{...}'` (家老 inbox 自動通知込み)

## curl 実行例

```bash
# in_progress な cmd 一覧
curl -s http://192.168.2.7:8770/api/cmd_list?status=in_progress | jq

# cmd_1487 の詳細
curl -s 'http://192.168.2.7:8770/api/cmd_detail?id=cmd_1487' | jq

# キーワード "inbox" で検索 (id/purpose/lord_original/assigned_to を LIKE)
curl -s 'http://192.168.2.7:8770/api/cmd_list?q=inbox&limit=5' | jq '.cmds[] | {id,purpose}'

# inbox メッセージ送信 (足軽3号へ)
curl -X POST http://192.168.2.7:8770/api/inbox_write \
  -H 'Content-Type: application/json' \
  -d '{"to":"ashigaru3","from":"karo","type":"task_assigned","message":"subtask_1494a 着手せよ"}'

# 新 cmd 起票 (家老inbox自動通知)
curl -X POST http://192.168.2.7:8770/api/cmd_create \
  -H 'Content-Type: application/json' \
  -d '{
    "id":"cmd_1500",
    "priority":"high",
    "purpose":"...",
    "lord_original":"殿の発言原文",
    "notify_karo":true
  }'
```

## YAML 直読みからの移行ポリシー

- 既存スクリプトの `yaml.safe_load(queue/shogun_to_karo.yaml)` は **段階的に curl 経由へ**置換
- 緊急性: 5+ ファイル横断する集計処理 / 高頻度 (cron) 呼出 / dashboard 系
- 後回し可: 1回限りの調査・特殊フィールド (full_yaml_blob 等) アクセス
- API 障害時のフォールバック: SQLite 直読み (`sqlite3 queue/cmds.db ...`) は許可・ただし書込 fallback は禁止 (dual-path 整合崩壊)

## 関連
- スキーマ: `sqlite3 queue/cmds.db ".schema commands"`
- dual-path 設計: cmd_1488 の `gunshi_design_sqlite_migration_1481.yaml`
- read 切替実装: cmd_1494 commit 1d4d763 + 07181c7
