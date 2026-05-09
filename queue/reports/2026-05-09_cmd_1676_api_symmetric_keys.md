# cmd_1676 server.py API endpoint key 対称化 設計

- **作成**: 2026-05-09 09:30 JST / 軍師
- **対象**: scripts/dashboard/server.py の POST/GET endpoint
- **殿原文**: 「別cmdで対称に あと間違い時はエラーかえせないのか」
- **背景**: karo (Sonnet) が response field名 (`from_agent` / `content`) を request にも誤用し 35秒 hang 事故 (2026-05-09)
- **制約**: 設計のみ・コード修正禁止 (実装は後続 cmd の足軽に委任)

---

## Executive Summary (推奨案)

**推奨**: **案A (誤key検出 → HTTP 400 + typo_hint 即返)** を即時実装。**案C (response/request 完全対称化)** は alias 期間付きで後続 cmd に分離。

**理由**:
1. 案A は 1 endpoint あたり 15-30 行で実装可能・破壊的変更なし
2. 35 秒 hang のような silent fail を即座に潰せる (LLM が typo した瞬間に 400 で即帰還)
3. 案C は consumer (dashboard UI / SSE 受信側) の大規模追従が必要・big bang リスクあり別 cmd で段階移行
4. 案B (alias 受入) は「なぜか動く・動かない」現象の温床・**学習機会喪失**なので不採用
5. 案D (A+B 併用) は実装複雑度 vs 効果が薄い・案 A単独で十分

**実装順序 (sequenced・hybrid 化しない)**:
- **cmd_1676a** (即時): 案A を全 POST endpoint に適用 → typo BLOCK
- **cmd_1676b** (中期): 案C を alias 期間付きで段階移行 (consumer 追従確認後に旧 key 削除)
- 案E/F/G (付録) は out of scope・将来検討

---

## 1. 背景: 35秒 hang 事故 (2026-05-09)

karo session で `/api/inbox_write` を叩いた際 35 秒で curl がハング → background fallback。原因仮説:

| 仮説 | 根拠 | 検証結果 |
|------|------|---------|
| (a) request に `from_agent`/`content` (response key) を誤送信 → message='' で 400 即時 | server.py:3293-3312 の validation コード | **不該当**: 400 即時返却なら 35 秒 hang しない |
| (b) request key 正しいが subprocess `bash inbox_write.sh` (L3329-3332) が flock 競合で 30 秒 timeout | subprocess.run(..., timeout=30) が L3331 にあり、bash subprocess hang 時 30 秒待ちで TimeoutExpired raise | **可能性大**: 35s hang はこれ + curl 側の retry/buffering |
| (c) /api/inbox_messages を /api/inbox_write と取り違え誤投 | endpoint 文字列の typo | **未検証** (logs/inbox_audit.log 直近 60 entry 全て `karo -` 形式・送信 key 不明) |

**結論**: 35秒 hang 自体の根本原因は **subprocess 経由 (L3329) の inbox_write.sh hang 説 (b) が最も濃厚**。これは別 cmd で潰す問題 (例: `/api/inbox_write` 内製化・bash 排除)。本 cmd_1676 は **typo 検出強化** に scope を絞り、key 非対称が再発防止に直接寄与する設計を提示する。

**北極星**: 「LLM が typo しても silent fail せず 400 で即帰還する API 設計」を確立し、Sonnet/Haiku など試行錯誤しがちな弱モデルでも詰まらない構造にする。

---

## 2. 全 POST/GET endpoint 対比表 (request key ↔ response key)

| endpoint | method | request 必須 key | request 任意 key | response key (主要) | 非対称箇所 |
|---|---|---|---|---|---|
| `/api/inbox_write` | POST | `to`, `message` | `from`, `type`, `task_id` | `success`, `msg_id`, `timestamp` | inbox_messages の response との **3点非対称** (下記 §2.1) |
| `/api/inbox_messages` | GET | (query) `agent` | `unread`, `limit`, `full` | `messages[].{id, agent, from_agent, type, content, read, timestamp, read_at, actor}` | inbox_write request と非対称 |
| `/api/inbox_mark_read` | POST | `agent`, `ids` or `all_unread` | `actor` | `ok`, `updated`, `yaml_updated`, `agent` | OK (対称) |
| `/api/cmd_create` | POST | `id`, `purpose`, `lord_original` | passthrough任意 (status/priority/timestamp/depends_on/notes/redo_of/north_star/acceptance_criteria/...) | (詳細未確認・要 audit) | `id` (request) vs `cmd_id` (各所 response) — **微差** |
| `/api/cmd_status_change` | POST | `id`, `status` | `actor` | `ok`, `cmd_id`, `status`, `completed_at`, `actor` | request `id` vs response `cmd_id` |
| `/api/cmd_cancel` | POST | `id` | `actor` | `ok`, `cmd_id`, `status`, `actor`, `cancelled_subtasks`, `notified_agents` | request `id` vs response `cmd_id` |
| `/api/task_create` | POST | `agent`, `task_id`, `status` | passthrough任意 | `success`, `task_id`, ... (詳細要 audit) | OK (対称) |
| `/api/task_update` | POST | `task_id`, `status` | `reason`, `updated_by` | `ok`, `task_id`, `status`, `agent`, `completed_at`, `updated_by` | OK (対称) |
| `/api/report_create` | POST | `report_id`, `worker_id`, `status` | `type`, `qa_decision`, ... | `success`, `report_id`, `yaml_path`, `timestamp` | OK (対称) |
| `/api/dashboard_update` | POST | `content` or (`section` + `section_content`) | - | `success`, `mode`, `bytes_written` | OK (対称) |

### 2.1 inbox 系の 3点非対称 (最大の問題)

| 概念 | request (`/api/inbox_write`) | response (`/api/inbox_messages`) | 不一致度 |
|------|------------------------------|----------------------------------|---------|
| 受信エージェント | `to` | `agent` | ★★★ |
| 送信エージェント | `from` | `from_agent` | ★★★ |
| 本文 | `message` | `content` | ★★★ |
| ID | (新規生成・request 不要) | `id` | - |
| タスク紐付け | `task_id` | (response にない) | - |

**実証**: 本セッションで実測。
```bash
# request expected
target = body.get('to', '').strip()              # server.py:3293
message = body.get('message', '').strip()        # server.py:3294
msg_type = body.get('type', 'wake_up')            # server.py:3295
from_agent = body.get('from', 'unknown')          # server.py:3296

# response actual (sample)
curl -s 'http://192.168.2.4:8770/api/inbox_messages?agent=gunshi&limit=1&full=1' | jq '.messages[0]|keys'
# => ["actor","agent","content","from_agent","id","read","read_at","timestamp","type"]
```

LLM (特に Sonnet/Haiku) は response を見て request を組むため、`{to:..., from_agent:..., content:...}` のような mixed-style を作りがち。silent fail (key default で 'unknown' 等を吸収) で気付かない。

### 2.2 cmd 系の `id` vs `cmd_id` 微非対称

`/api/cmd_create` request は `id`、`/api/cmd_status_change` `/api/cmd_cancel` の response は `cmd_id`。LLM は `id` `cmd_id` どちらも妥当に見えるため学習負荷あり (★ 軽度・LOW priority)。

---

## 3. 候補案 A/B/C/D 比較

| 観点 | 案A: 400 + typo_hint | 案B: alias 受入 | 案C: 完全対称化 | 案D: A+B 併用 |
|------|---------------------|----------------|----------------|--------------|
| 後方互換性 | △ (旧 client が 400 になる) | ◎ (破壊なし) | × (consumer 全追従要) | ○ (alias 期間中 OK) |
| 実装コスト | ○ (15-30 行/endpoint) | ○ (5-10 行/endpoint) | ✕ (response 全 endpoint + consumer 追従) | △ (両方実装) |
| エラー体験 | ◎ (LLM 即学習) | × (silent 通過・学習機会喪失) | ○ (key 1セット覚えれば OK) | △ (混在で曖昧) |
| 殿の意図適合 | ◎ (「間違い時はエラーかえせ」直撃) | △ (エラー返さず) | ○ (対称化メイン部分) | △ |
| 移行リスク | 低 (現状クライアントが正規 key を送っていれば影響なし) | 低 | 高 (big bang) | 中 |
| 維持コスト | 低 | 中 (alias 一覧の dictionary 維持) | 低 (key 1セット) | 高 (両方維持) |

### 案A 詳細: 誤 key 検出 → HTTP 400 + typo_hint

**実装イメージ** (server.py /api/inbox_write 例):
```python
# L3289-3296 の直後・L3298 (CANONICAL_TYPES check) の前に追加
ALLOWED_KEYS_INBOX_WRITE = {'to', 'from', 'type', 'message', 'task_id'}
KNOWN_TYPOS_INBOX_WRITE = {
    'agent': 'to',           # response の field 誤用
    'from_agent': 'from',
    'content': 'message',
    'msg': 'message',
}

unknown = set(body.keys()) - ALLOWED_KEYS_INBOX_WRITE
if unknown:
    hints = {}
    for u in unknown:
        if u in KNOWN_TYPOS_INBOX_WRITE:
            hints[u] = f"unknown field {u!r}; did you mean {KNOWN_TYPOS_INBOX_WRITE[u]!r}? (response field の誤用)"
        else:
            hints[u] = f"unknown field {u!r}; allowed: {sorted(ALLOWED_KEYS_INBOX_WRITE)}"
    self.send_response(400)
    self.send_header('Content-Type', 'application/json; charset=utf-8')
    self.end_headers()
    self.wfile.write(json.dumps(
        {'error': 'unknown fields', 'hints': hints}, ensure_ascii=False
    ).encode('utf-8'))
    return
```

**効果**:
- LLM が `from_agent` を送った瞬間に `{"error":"unknown fields","hints":{"from_agent":"unknown field 'from_agent'; did you mean 'from'? (response field の誤用)"}}` を即返却
- silent fail ゼロ・35秒 hang 系の事故も「subprocess より前で 400 即返却」のため subprocess に到達せず

**変更対象 endpoint と概算 LOC**:
| endpoint | server.py 該当行 | ALLOWED_KEYS 候補 | 概算 LOC |
|----------|-----------------|-------------------|---------|
| /api/inbox_write | L3288-3375 | to, from, type, message, task_id | +25 |
| /api/inbox_mark_read | L3726- | agent, ids, all_unread, actor | +15 |
| /api/cmd_create | L2880-3084 | id, purpose, lord_original, status, priority, timestamp, command_text, north_star, project, parent_cmd, depends_on, notes, redo_of, acceptance_criteria, assigned_to | +30 (passthrough 多い) |
| /api/cmd_status_change | L3085-3141 | id, status, actor | +15 |
| /api/cmd_cancel | L3142-3287 | id, actor | +15 |
| /api/task_create | L3376-3463 | agent, task_id, status, parent_cmd, priority, title, project, description, target_path, procedure, steps, acceptance_criteria, notes, params, assigned_to, assignee, report_to, safety, redo_of, timestamp, bloom_level, gunshi_qc | +30 |
| /api/task_update | L3464-3543 | task_id, status, reason, updated_by | +15 |
| /api/report_create | L3621-3725 | report_id, worker_id, task_id, parent_cmd, type, status, qa_decision, timestamp, report_path, summary | +20 |
| /api/dashboard_update | L3544-3620 | content, section, section_content | +15 |
| **合計** | - | - | **約180 LOC** |

passthrough 系 (cmd_create/task_create) は ALLOWED 集合が大きくなるが、機械生成可。

### 案B 詳細: alias 受入 + deprecation warning

**実装イメージ**:
```python
# L3293-3296 を変更
target = (body.get('to') or body.get('agent', '')).strip()  # alias: agent
message = (body.get('message') or body.get('content', '')).strip()  # alias: content
from_agent = body.get('from') or body.get('from_agent', 'unknown')  # alias: from_agent

# response に warning 追加
deprecation = []
if 'agent' in body and 'to' not in body: deprecation.append("'agent' is deprecated; use 'to'")
if 'content' in body and 'message' not in body: deprecation.append("'content' is deprecated; use 'message'")
if 'from_agent' in body and 'from' not in body: deprecation.append("'from_agent' is deprecated; use 'from'")
resp = {'success': True, 'msg_id': ..., 'timestamp': ..., '_deprecated': deprecation}
```

**問題**: 殿原文「**間違い時はエラーかえせないのか**」と方針逆行。silent 通過は学習機会喪失。**不採用**。

### 案C 詳細: response/request 完全対称化

**実装イメージ** (response 側を request key に合わせる):
```python
# /api/inbox_messages の response を変える
# 現状: {id, agent, from_agent, type, content, read, timestamp, read_at, actor}
# 案C: {id, to, from, type, message, read, timestamp, read_at, actor}
#  + 移行期間: 両 key 同梱 → consumer 確認後に旧 key 削除

row_dict = {
    'id': row['id'],
    'to': row['agent'],       # NEW
    'agent': row['agent'],    # LEGACY (alias)
    'from': row['from_agent'],     # NEW
    'from_agent': row['from_agent'],  # LEGACY
    'type': row['type'],
    'message': row['content'],  # NEW
    'content': row['content'],  # LEGACY
    'read': row['read'],
    'timestamp': row['timestamp'],
    'read_at': row['read_at'],
    'actor': row['actor'],
}
```

**問題**:
- consumer 全追従要 (dashboard UI / SSE 受信側 / inbox_watcher.sh / stop_hook_inbox.sh / 他 LLM ロジック)
- 期間管理 (旧 key 削除タイミング) の合意必要
- 案A 単独で typo 即時 BLOCK されれば、対称化の緊急度は下がる

**結論**: cmd_1676 の北極星 (typo 即 BLOCK) は **案A だけで充足**。案C は別 cmd で段階移行が妥当。

### 案D 詳細: A + B 併用

**問題**:
- A の strict 400 と B の silent alias は方針対立 (どちらが優先かルール定義必要)
- LLM 側の混乱要因増加 (どの key が pass する/しない の境界が曖昧)
- **不採用**

---

## 4. 推奨案: A 即時実装 + C を follow-up cmd

### 4.1 cmd_1676a (即時実装: 案A)

**スコープ**: 全 9 POST endpoint に ALLOWED_KEYS チェック追加・KNOWN_TYPOS dict で hint 提供。

**実装担当足軽向け 変更対象行リスト** (上記 §3 案A 詳細 表 参照):
- 全合計 約 180 LOC・1 ファイル (server.py) のみ修正
- KNOWN_TYPOS dict は inbox_write が最大 (3 entry: agent/from_agent/content)、他 endpoint は 0-1 entry
- テスト: 各 endpoint に対し正規 key + typo key を curl で計2回叩き、200 / 400 を確認 (合計 18 回)

**AC**:
1. server.py に ALLOWED_KEYS_<ENDPOINT> 9セット定義済
2. 9 endpoint 全てで unknown key 受信時 400 + hints 返却
3. 既存 client が正規 key を送っている限り 200 維持 (regression なし)
4. KNOWN_TYPOS dict に inbox response field (agent/from_agent/content) 含む
5. CHK12 (curl response の HTTP code 必須) と整合

### 4.2 cmd_1676b (follow-up: 案C 段階移行)

**スコープ**: /api/inbox_messages response に alias 期間付きで request key (to/from/message) を追加・consumer 全追従後に旧 key 削除。

**前提**: cmd_1676a 完了後 (typo 物理 BLOCK 済) で、consumer 改修の risk が低くなってから着手。

**移行 phase**:
1. **Phase 1**: response に新旧両 key 同梱 (`{id, to:agent, agent, from, from_agent, message:content, content, ...}`)
2. **Phase 2**: consumer (dashboard UI / SSE / inbox_watcher) を新 key 経路に切替
3. **Phase 3**: 旧 key 削除 (alias period 終了)

---

## 5. 殿への質問事項

1. **Q1**: 案A 単独で進めて良いか・案C も同時にやるか?
   - 軍師推奨: A 即時 → C は別 cmd
2. **Q2**: 案A の ALLOWED_KEYS で「未知 key を 400 で BLOCK」する厳格度を、`cmd_create` `task_create` の **passthrough 系**にも適用すべきか?
   - 軍師推奨: 適用する。passthrough も whitelist 拡張で済む (拡張時に ALLOWED 1行追加するだけ)
3. **Q3**: alias 受入 (案B / 案C Phase 1) を採用する場合、**alias 期限**は?
   - 候補: 1ヶ月 / 3ヶ月 / 6ヶ月 / 期限なし
   - 軍師推奨: 案A 単独なら不要・案C 採用なら 1ヶ月 (consumer 数が限定的なため短期で打ち切れる)
4. **Q4**: KNOWN_TYPOS の dict に `from_agent → from` のような hint を入れることで「hint があれば動く」と LLM が誤学習する懸念はあるか?
   - 軍師見解: **問題なし**。400 で reject するため動かない・hint は再試行用情報

---

## 6. 検証手順 (家老向け)

1. server.py を `wc -l scripts/dashboard/server.py` (現状 約 4500 行) で baseline 確認
2. 9 endpoint 全てで本報告書の §3 案A 詳細 表の LOC 概算 (約 180 LOC) 適合確認
3. 案A 実装後 smoke test:
   ```bash
   # 正規 key (200 期待)
   curl -s -w "\nHTTP %{http_code}\n" -X POST -H 'Content-Type: application/json' \
     -d '{"to":"karo","from":"gunshi","type":"wake_up","message":"test"}' \
     http://192.168.2.4:8770/api/inbox_write

   # typo key (400 + hint 期待)
   curl -s -w "\nHTTP %{http_code}\n" -X POST -H 'Content-Type: application/json' \
     -d '{"agent":"karo","from_agent":"gunshi","type":"wake_up","content":"test"}' \
     http://192.168.2.4:8770/api/inbox_write
   # → expect: HTTP 400, hints={agent:"unknown field 'agent'; did you mean 'to'? ...", ...}
   ```
4. 既存 client (本セッションの軍師 inbox_write call 含む) が 200 維持を確認

---

## 7. 付録: 殿原文に無い追加候補 (out of scope・将来検討)

殿は A/B/C/D を提示済。以下は軍師が思考検討した案だが本 cmd の scope 外:

### 案E: /api/_schema endpoint (各 endpoint の input/output JSON Schema を返す)
- LLM に prompt 内で「事前に schema 取れ」と書ける・OpenAPI 風
- 維持コスト中・案A だけで typo 0 にできるなら不要

### 案F: /api/inbox_write response に echo back
- 受信した key を `{success, msg_id, request_received: {to, from, ...}, normalized}` で返す
- LLM が「自分が送った key が正しく解釈された」を毎回確認可能
- 案A の strict 400 で typo は事前に潰れるため過剰

### 案G: Python SDK (`scripts/api_client.py`) を作成
- `api_client.inbox_write(to=..., from_=..., type_=..., message=...)` で typo 物理排除
- LLM (家老/軍師/足軽) が直接 curl ではなく SDK 経由
- 全 LLM のワークフロー変更コスト大・別 cmd で要殿判断
- 軍師見解: **案G が長期的には最善**だが、案A で 80% 効果が得られるため後回し

---

## 8. 結論

- **本 cmd_1676 の推奨**: **案A** (誤 key 検出 → HTTP 400 + typo_hint)
- **実装担当**: 足軽 (server.py 1ファイル・約 180 LOC・9 endpoint)
- **follow-up**: 案C を cmd_1676b で別途・案G (SDK) は更に長期検討
- **35秒 hang の真因**: 別 cmd 起票推奨 (subprocess inbox_write.sh 内製化等)
- **read-only 遵守**: 本 cmd では server.py に**1行も触れていない** (本報告書のみ作成)
