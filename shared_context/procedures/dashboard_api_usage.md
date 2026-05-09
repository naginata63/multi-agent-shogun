# MCP Dashboard API 利用ガイド

cmd/inbox/task の操作は YAML 直読み・直書きではなく **HTTP API 経由** を第一選択とする。
背景: cmd_1488 で SQLite dual-path 完成・cmd_1494 で read 側も SQLite 切替。
API がデータ整合性 (flock + dual-path + 自動通知) を一元担保するため、各エージェントは API を使え。

## エンドポイント (LAN内・認証なし・http://192.168.2.4:8770/)

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
| `/api/inbox_mark_read` | `agent`, **`ids`** (list) or `all_unread` (bool), `actor` (任意) | 既読化 (cmd_1495・★ キー名 `ids` であって `message_ids` ではない・cmd_1664 教訓) |
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
- **戦況確認**: ブラウザで http://192.168.2.4:8770/ (HTML経由)
- **cmd 起票**: `curl -X POST /api/cmd_create -d '{...}'` (家老 inbox 自動通知込み)

## curl 実行例

```bash
# in_progress な cmd 一覧
curl -s http://192.168.2.4:8770/api/cmd_list?status=in_progress | jq

# cmd_1487 の詳細
curl -s 'http://192.168.2.4:8770/api/cmd_detail?id=cmd_1487' | jq

# キーワード "inbox" で検索 (id/purpose/lord_original/assigned_to を LIKE)
curl -s 'http://192.168.2.4:8770/api/cmd_list?q=inbox&limit=5' | jq '.cmds[] | {id,purpose}'

# inbox メッセージ送信 (短文は直書きOK・200文字以下)
curl -X POST http://192.168.2.4:8770/api/inbox_write \
  -H 'Content-Type: application/json' \
  -d '{"to":"ashigaru3","from":"karo","type":"task_assigned","message":"subtask_1494a 着手せよ"}'

# 既読化 (★ キー名は ids ・message_ids ではない・cmd_1664 教訓)
# --max-time 必須 (timeout 未設定で詰まると context 浪費 + 残骸プロセス)
curl -sS --max-time 30 -X POST http://192.168.2.4:8770/api/inbox_mark_read \
  -H 'Content-Type: application/json' \
  -d '{"agent":"ashigaru1","ids":["msg_xxx","msg_yyy"]}' \
  -w "\nHTTP %{http_code}\n"

# 既読化 (全未読を一括)
curl -sS --max-time 30 -X POST http://192.168.2.4:8770/api/inbox_mark_read \
  -H 'Content-Type: application/json' \
  -d '{"agent":"ashigaru1","all_unread":true}' \
  -w "\nHTTP %{http_code}\n"

# 新 cmd 起票: JSON payload ファイル作成 → --data @file で投入 (cmd_1546)
# 1. payload ファイル作成
#    (context/cmd_template.md のテンプレートを参照)
# 2. API投入
curl -X POST http://192.168.2.4:8770/api/cmd_create \
  -H 'Content-Type: application/json' \
  --data @queue/cmd_payloads/cmd_XXXX.json
```

**注意**: `cmd_create` での JSON 直書き (`-d '{...}'`) は pretool_check.sh CHK10 で BLOCK される。
`queue/cmd_payloads/` にファイル保存 → `--data @<path>` で投入せよ。
inbox_write の短文 (200文字以下) は直書き許可。

## YAML 直読みからの移行ポリシー

- 既存スクリプトの `yaml.safe_load(queue/shogun_to_karo.yaml)` は **段階的に curl 経由へ**置換 (期限: 2026-Q3 までに全置換。残務は cmd_1673 follow-up cmd にて家老が起票)
- 緊急性: 5+ ファイル横断する集計処理 / 高頻度 (cron) 呼出 / dashboard 系
- 後回し可: 1回限りの調査・特殊フィールド (full_yaml_blob 等) アクセス
- API 障害時のフォールバック: SQLite 直読み (`sqlite3 queue/cmds.db ...`) は許可・ただし書込 fallback は禁止 (dual-path 整合崩壊)

## Payload ファイル必須ルール (cmd_1612)

API 投入の JSON payload は **`queue/cmd_payloads/` 配下** にファイル保存し、`curl --data @<path>` で投入せよ。

**禁止パターン**:
- `curl -d '{...}'` (JSON直書き) → CHK10 で BLOCK
- `curl --data @/tmp/xxx.json` (/tmp 経由) → CHK11 で BLOCK

**許可パターン**:
- `curl --data @queue/cmd_payloads/cmd_XXXX.json` (推奨)
- inbox_write の短文 (message値200文字以下) のみ直書き許可

**例外**: inbox_write の短文 (200文字以下) は CHK10 の例外として直書き許可。

## レスポンス JSON キー名表 (★ 重要・cmd_1654 教訓)

**家老/足軽がレスポンス JSON から値を取り出す時の正規キー名。** 推測 (body/from 等) で実装すると常に空が返る。

### `/api/inbox_messages`

```json
{
  "messages": [
    {
      "id": "msg_20260506_111327_9a00555a",       // メッセージ ID
      "agent": "karo",                              // 受信者 agent_id
      "from_agent": "shogun",                       // 送信者 agent_id (NOT "from")
      "type": "cmd_revised",                        // CANONICAL_TYPES (server.py)
      "content": "本文…(数百〜数千文字)",            // 本文 (NOT "body")
      "read": 0,                                    // 0=未読 / 1=既読
      "timestamp": "2026-05-06T11:13:27",           // 送信時刻 (JST)
      "read_at": "2026-05-06T02:13:46.667671+00:00",// 既読化時刻 (UTC)
      "actor": "karo"                               // 既読化アクター
    }
  ],
  "shown": 1,
  "full": true,
  "source": "sqlite"
}
```

**❌ 典型 typo (家老が 2026-05-06 ハマった)**:
- `m.get('body', '')` → 常に空・正解は `m.get('content', '')`
- `m.get('from', '?')` → 常に "?"・正解は `m.get('from_agent', '?')`

→ **CHK13 hook で BLOCK 化済 (pretool_check.sh 末尾)**

### `/api/cmd_list` / `/api/cmd_detail`

```json
{
  "cmds": [
    {
      "id": "cmd_1647",                             // cmd_id
      "purpose": "...",                             // 目的 1 行
      "command": "...",                             // 実行コマンド全文 (slim=1 で省略)
      "status": "done",                             // pending/in_progress/done/blocked/cancelled
      "priority": "HIGH",
      "created_at": "...",
      "completed_at": "...",
      "lord_original": "...",                       // 殿原文 (acceptance_criteria 等は parse 済 dict)
      "acceptance_criteria": {...}                  // dict (JSON parse 済)
    }
  ],
  "total": 160
}
```

### `/api/agent_health`

```json
{
  "agents": [
    {
      "agent_id": "karo",
      "pane_alive": true,                           // tmux pane 生存
      "last_task_id": "subtask_xxx",                // 最後に着手した task_id (NOT "task_id")
      "last_task_status": "done",                   // assigned/in_progress/done/blocked/idle
      "last_activity_at": "..."                     // 最終活動時刻 (空の場合あり)
    }
  ]
}
```

### `/api/inbox_write` (POST レスポンス)

```json
{
  "success": true,
  "msg_id": "msg_20260506_111327_9a00555a",
  "timestamp": "2026-05-06T11:13:27"
}
```

400 時のエラー body:
```json
{"error": "to and message are required"}
```
※ POST 時の payload キーは **`message`** (NOT `content` ・cmd_1654 教訓)。レスポンス取得時は `content`。**書込と読込でキー名が違う**。

### `/api/cmd_create` (POST レスポンス)

```json
{
  "success": true,
  "cmd_id": "cmd_XXXX",
  "notify_msg_id": "msg_..."                        // notify_karo=true の時の inbox 通知 msg_id
}
```

### `/api/inbox_mark_read` (POST request / response・cmd_1495 / cmd_1664 教訓)

**Request body**:
```json
{
  "agent": "ashigaru1",                             // 必須・受信者 agent_id
  "ids": ["msg_xxx", "msg_yyy"],                    // ★★★ "message_ids" ではない ★★★
  "all_unread": false,                              // 任意・true なら agent の全未読を一括既読化 (ids 不要)
  "actor": "shogun"                                 // 任意・audit log 用・default は agent 自身
}
```

**Response**:
```json
{
  "ok": true,
  "updated": 2,                                     // SQLite 上で実際に更新された件数
  "yaml_updated": 0,                                // YAML dual-path 上で更新された件数 (cmd_1494 以降 YAML は基本空)
  "agent": "ashigaru1"
}
```

**400 エラー body**:
```json
{"error": "agent required"}                        // agent 欠落
{"error": "ids or all_unread required (received key 'message_ids' is invalid — use 'ids' (list of msg_id))",
 "expected_body": {
   "agent": "<agent_id>",
   "ids": ["msg_xxx","msg_yyy"],
   "all_unread": "(or true to mark all)",
   "actor": "(optional)"
 }}
```

★ サーバ側で **`message_ids` / `msg_ids` / `messageIds` / `id` (単数)** を含む typo を検出し、エラー本文に正解を案内するヒントが入る (cmd_1664 改修・2026-05-07)。受信した時点で `expected_body` フィールドにスキーマ全体も同梱されるため、スキーマを忘れた agent もログだけで自己修復できる。

**典型 typo (2026-05-07 cmd_1664 教訓)**:
- `"message_ids": [...]` → 400 エラー・**正解は `"ids"`**
- 将軍が curl で代理 mark_read した際にハマった。足軽1 も同じ typo で永久ハング (timeout 未設定で server.py 遅延と組み合わさって)
- → 本ドキュメント L29 の POST 系テーブルにも明記済

## キー名サマリ表 (即参照用)

| API | 書込 (POST body) | 読込 (response) |
|-----|------------------|-----------------|
| inbox_write | `to`, **`message`**, `type`, `from` | (success/msg_id/timestamp) |
| inbox_messages | (GET) | `messages[].id`, `agent`, **`from_agent`**, `type`, **`content`**, `read`, `timestamp` |
| inbox_mark_read | `agent`, **`ids`** (list) or `all_unread` (bool), `actor` (任意) | (ok/updated/yaml_updated/agent) |
| cmd_create | `id`, `purpose`, `priority`, `lord_original`, **`command`** (lord_original 丸写し必須・CHK14), `notify_karo` | (success/cmd_id) |
| cmd_list | (GET) | `cmds[].id`, `purpose`, `status`, `priority`, `lord_original`, `acceptance_criteria` |
| agent_health | (GET) | `agents[].agent_id`, `pane_alive`, `last_task_id`, `last_task_status` |

★ **太字**は typo 多発キー (推測で別名にしないこと)

## 関連
- スキーマ: `sqlite3 queue/cmds.db ".schema inbox_messages"` (or `.schema commands` 等)
- dual-path 設計: cmd_1488 の `gunshi_design_sqlite_migration_1481.yaml`
- read 切替実装: cmd_1494 commit 1d4d763 + 07181c7
- キー名 typo BLOCK hook: `scripts/pretool_check.sh` CHK13 (2026-05-06 cmd_1654 家老ハマり教訓)
- レスポンス検証 (-w "%{http_code}\n" 必須・tail truncate 禁止): `scripts/pretool_check.sh` CHK12
- inbox_mark_read キー `ids` (NOT `message_ids`): 2026-05-07 cmd_1664 教訓 (将軍・足軽1 同 typo・足軽1 は --max-time 未設定で永久ハング → ループ事故・将軍が API 直叩きで救済)
- cmd_create `command` フィールド lord_original 丸写し必須: CHK14 (cmd_1656 教訓・要約・言い換え禁止)
