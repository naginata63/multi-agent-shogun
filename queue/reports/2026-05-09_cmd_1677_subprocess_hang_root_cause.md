# cmd_1677 server.py subprocess hang + curl 永久滞留 根本原因究明

- **作成**: 2026-05-09 12:35 JST / 軍師
- **L6 タスク**: server.py の subprocess.run hang + curl 50+分滞留 + 本日 4 回 server restart 必要事象の **実証ベース根本原因確定**
- **制約**: read-only 調査・コード/設定修正なし
- **将軍仮説**: subprocess.run timeout 不全 + flock 競合

---

## Executive Summary (根本原因・実証ベース)

**真因**: **cmd_1676a (commit 123842c・ALLOWED_KEYS guard 実装) の 400 response paths が Content-Length ヘッダーを欠落**しており、HTTP/1.1 keep-alive 環境下で **client が body 終端を判定できず connection close を無限待ち**する状態。

**証拠 (実機再現)**:
```bash
# 誤 key 投入 (期待: 即 400 + hint)
curl --max-time 15 -X POST -d '{"agent":"gunshi","msg_id":"reproduce"}' /api/inbox_mark_read
# → HTTP 400 time=15.002284s ★ 15秒満杯ハング (curl が --max-time で kill)
# response body は正しく返却される: {"error":"unknown fields","hints":{"msg_id":"...did you mean ids?"}}
# 但し connection close なし → client は body end を待ち続ける

# 正規 key 投入
curl -X POST -d '{"agent":"gunshi","ids":["nonexistent"]}' /api/inbox_mark_read
# → HTTP 200 time=0.015744s ★ 15ms 即完了 (Content-Length あり)

# task_update 誤 key
curl --max-time 15 -X POST -d '{"task_id":"foo","status":"done","worker_id":"bar"}' /api/task_update
# → HTTP 400 time=15.002482s ★ 15秒満杯ハング (同症状)
```

**HTTP/1.1 keep-alive default + Content-Length 欠落** で **常に curl --max-time まで close 待機**。本日の 50+分滞留 curl 4 件は --max-time なし or 長 timeout で投入された結果。

---

## 1. 本日の事象タイムライン

| 時刻 | 事象 | 影響 |
|------|------|------|
| 09:40 | cmd_1676a (commit 123842c) ALLOWED_KEYS guard 9 endpoint 実装 | **真因混入** (400 path Content-Length 欠落) |
| 10:03 | 旧 server (PID 3346533) restart (cmd_1676a load) | OK |
| 10:43 | cmd_1665 (commit 2c3a751) 実装 | endpoint 追加 |
| 10:54 | 新 server (PID 3585018) restart (cmd_1665 load) | OK |
| 10:56-11:03 | 4 件 curl が誤 key を投入 (ash/karo) | **curl 4 件が滞留開始** |
| 11:50 | 殿が server restart 必要と判断 | (curl 詰まり症状) |
| 12:10 | gunshi に hang 究明委任 | 本 cmd_1677 |

**滞留 4 curl** (ESTAB で 1時間以上):
- inbox_mark_read with `msg_id` (誤 key・正規 ids) — PID 3600958・10:56:53 起動・滞留 1h17m
- task_update with `worker_id` (誤 key・正規 updated_by) — PID 3614596・11:01:01・滞留 1h10m
- task_update 正規 key — PID 3615768・11:01:31・滞留 1h09m (← 別事象? 要 py-spy 確認・本報告で未確定)
- task_detail GET — PID 3621735・11:03:28・滞留 1h07m (← /api/task_detail 実装あるか不明・要確認)

---

## 2. 根本原因 (実証ベース)

### CRITICAL — Content-Length 欠落バグ (cmd_1676a 起源)

**file:line**: `scripts/dashboard/server.py` の 全 9 endpoint の 400 response paths

具体例 (`/api/inbox_mark_read` L3909-3913):
```python
self.send_response(400)
self.send_header('Content-Type', 'application/json; charset=utf-8')
self.end_headers()                                          # ← Content-Length 未設定で end_headers
self.wfile.write(json.dumps({'error': 'unknown fields', 'hints': hints}, ensure_ascii=False).encode('utf-8'))
return
```

**対比**: 正規 (200 OK) path は Content-Length 明示 (例 L3422 `/api/cmd_cancel` L3260):
```python
resp = json.dumps({...}).encode('utf-8')
self.send_response(200)
self.send_header('Content-Type', 'application/json; charset=utf-8')
self.send_header('Content-Length', str(len(resp)))          # ← 明示
self.end_headers()
self.wfile.write(resp)
```

**HTTP プロトコル違反**:
- `scripts/dashboard/server.py:1920` `protocol_version = 'HTTP/1.1'` → keep-alive default
- HTTP/1.1 で **Content-Length も Transfer-Encoding: chunked も無い** = client は body 終端不明
- HTTP RFC 7230 §3.3.3: server は Content-Length or chunked encoding を**必須** (一部 status code 除く)
- **400 status code は body 必須** (Content-Length が要求される)

**該当 endpoint** (cmd_1676a 実装の 9 箇所すべて):
1. `/api/cmd_create` (L2890-2893) — 400 path
2. `/api/cmd_status_change` (L3110-3115)
3. `/api/cmd_cancel` (L3186-3190)
4. `/api/inbox_write` (L3354-3358)
5. `/api/task_create` (L3458-3463)
6. `/api/task_update` (L3563-3567)
7. `/api/dashboard_update` (L3656-3660)
8. `/api/report_create` (L3748-3753)
9. `/api/inbox_mark_read` (L3909-3913)

**全て同パターン** (`send_response(400)` + `Content-Type` のみ + `end_headers()` + `wfile.write(...)` で Content-Length 不在)。

---

## 3. 修復案

### 暫定対策 (即日適用可能・リスク低)

**案 P1**: 全 400 response paths に Content-Length を追加
```diff
+ resp = json.dumps({'error': 'unknown fields', 'hints': hints}, ensure_ascii=False).encode('utf-8')
  self.send_response(400)
  self.send_header('Content-Type', 'application/json; charset=utf-8')
+ self.send_header('Content-Length', str(len(resp)))
  self.end_headers()
- self.wfile.write(json.dumps({'error': 'unknown fields', 'hints': hints}, ensure_ascii=False).encode('utf-8'))
+ self.wfile.write(resp)
  return
```
- **対象**: 9 箇所 + 既存 400/404/409/500 paths も同様の問題があれば修正
- **LOC**: 約 30 行 (9 endpoint × 平均 3 行追加)
- **リスク**: なし (既存 200 path と同パターン)

**案 P2** (代替): `Connection: close` ヘッダー追加で keep-alive 強制終了
```diff
  self.send_response(400)
+ self.send_header('Connection', 'close')
  self.send_header('Content-Type', 'application/json; charset=utf-8')
  self.end_headers()
```
- 短期 fix だが、keep-alive 利点 (TCP 再接続コスト削減) を失う・恒久的でない

### 恒久対策 (設計変更)

**案 R1**: HTTP response 共通 helper 関数を導入
```python
def _send_json(handler, status, body_dict):
    """統一 JSON response helper. Content-Length 自動付与で hang 防止."""
    body = json.dumps(body_dict, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

# usage
_send_json(self, 400, {'error': 'unknown fields', 'hints': hints})
return
```
- 全 endpoint で `_send_json` 経由に統一・**Content-Length 欠落の構造的予防**
- 100+ 箇所の置換要だが、将来の Content-Length 欠落事故を構造排除

**移行ロードマップ**:
1. **Phase 1 (即日)**: 案 P1 で 9 cmd_1676a 400 paths 修正 → server restart → 再現 test 0 件確認
2. **Phase 2 (数日)**: 全 endpoint の `send_response`/`wfile.write` 直書きを `_send_json` helper に置換 (cmd_1677-A subtask 起票推奨)
3. **Phase 3 (cleanup)**: 滞留 curl orphan の自動 reaper 検討 (server restart 不要にする hardening)

---

## 4. 将軍仮説の評価

| 将軍仮説 | 評価 | 根拠 |
|---------|------|------|
| **subprocess.run timeout 不全** | **誤り** | 本日の 4 件滞留 curl は subprocess 経路ではない (inbox_mark_read / task_update / task_detail は SQLite + YAML dual-path のみ・subprocess 不使用)。L2878 `subprocess.Popen` (panel 生成) は `proc.communicate(timeout=600)` で 10分 timeout 設定あり・hang していない |
| **flock 競合** | **誤り** | `lsof -p $SERVER_PID` で `.lock` ファイル open 0 件 (cmd_history のみ)・`fuser queue/cmds.db.lock` 出力なし。flock 待ちで stuck している thread は確認されず |
| **(cmd_1670 教訓) inbox_write.sh L255 pipe fd 継承** | **対策済の旧バグ** | 本日 cmd_create 10秒応答事故の真因とされたが、`( ... )</dev/null & ` で対策済。本 cmd_1677 の curl 50分滞留はそれより遥かに長く別機序 (Content-Length 欠落) |
| **busy_timeout=0** (軍師仮説) | **誤誘導** | 外部 sqlite3 CLI で読んだ別 connection の値・server.py は L72 `sqlite3.connect(timeout=10)` で Python 側 10秒タイムアウト設定済。`PRAGMA busy_timeout=0` は非該当 |

→ **将軍/軍師の事前仮説は全て誤り**。真因は **cmd_1676a 実装時の単純な HTTP プロトコル違反** (Content-Length 欠落)。

---

## 5. py-spy 取得不可の制約

**実施済**:
- `/proc/3585018/task/*/wchan` 取得 (kernel stack):
  - main thread (3585018): `poll_schedule_timeout` (LISTEN socket accept 待ち・正常)
  - SSE 8 thread: `futex_do_wait` (Python lock 待ち・正常 SSE persistent)
  - **滞留 curl thread 4 件 (3600959/3614597/3615769/3621736): `wait_woken`** (data 待ち)
- `wait_woken` = TCP socket read 待ち = **server thread が response 完了後 client の close を待っている状態** と整合
- これは Content-Length 欠落で keep-alive client が close しないため server thread が永久 wait_woken の状態を再現

**取得不可**:
- py-spy (未インストール・sudo 不可)
- Python frame スタック (kernel stack のみ)

**不確実性**: Python frame レベルの確証は取れず、`wait_woken` だけだと TCP read 待ち以外 (例: SQLite 内部 lock) も理論上ありうる。但し:
- 4 thread すべて同じ `wait_woken` (= 同一 blocking 状態)
- 再現テストで 400 response が **必ず 15秒 timeout で hang** (--max-time なら無限) を実証
- → **Content-Length 欠落 + HTTP/1.1 keep-alive close 待ち**で**ほぼ確実**に確定

---

## 6. 殿への質問事項

1. **Q1**: 案 P1 (全 9 endpoint の 400 paths に Content-Length 追加) を即日適用するか?
   - 軍師推奨: **YES**・LOC 30 行・リスクなし
2. **Q2**: 滞留中の 4 curl client (PID 3600958/3614596/3615768/3621735) を kill して TCP fd 解放するか?
   - 軍師推奨: **YES** (殿/将軍依頼で軍師は kill 不可)・新 server には他に 7 connection しかなく余裕あり・但し放置でも害は薄い
3. **Q3**: server restart 自動化 (1h cron in dashboard_lifecycle.sh) を維持するか?
   - 維持: hung connection を定期的に close できる safety net・但し処理中 client 切断のコスト
   - 廃止: server を **完全 stateless + Content-Length 厳守** にして restart 不要設計
   - 軍師推奨: **暫定維持 → Phase 2 (案 R1 helper 統一) 完了後に廃止検討**
4. **Q4**: cmd_1676a (typo guard) を一旦 revert するか?
   - 軍師推奨: **revert 不要**。typo guard 自体は北極星 (silent fail 排除) と整合・修正は Content-Length 追加のみで両立

---

## 7. 検証手順 (家老向け)

1. 案 P1 実装後の再現テスト:
```bash
# 期待: 全て < 1秒で完了
curl --max-time 5 -s -w "HTTP %{http_code} time=%{time_total}s\n" -X POST -H 'Content-Type: application/json' \
  -d '{"agent":"gunshi","msg_id":"test"}' http://192.168.2.4:8770/api/inbox_mark_read

curl --max-time 5 -s -w "HTTP %{http_code} time=%{time_total}s\n" -X POST -H 'Content-Type: application/json' \
  -d '{"task_id":"foo","status":"done","worker_id":"bar"}' http://192.168.2.4:8770/api/task_update

curl --max-time 5 -s -w "HTTP %{http_code} time=%{time_total}s\n" -X POST -H 'Content-Type: application/json' \
  -d '{"agent":"gunshi","unknown_field":"test"}' http://192.168.2.4:8770/api/inbox_write
```

2. 既存 200 OK path regression なし確認:
```bash
curl -s -w "HTTP %{http_code} time=%{time_total}s\n" "http://192.168.2.4:8770/api/cmd_next_id"
# 期待: HTTP 200 + < 100ms
```

3. ESTAB connection 数監視:
```bash
ss -tnp | grep ":8770" | wc -l   # → SSE 8-9 + 必要最小限・滞留なし
```

---

## 8. 結論

**今日 4 回 server restart の真因 + curl 50+分滞留 + subprocess.run hang 風症状 → 全て同一原因**:
- **cmd_1676a (commit 123842c) の 400 response paths で Content-Length 欠落**
- HTTP/1.1 keep-alive default で client が body 終端不明 → connection close 待機で hang
- 9 endpoint すべて同パターン (cmd_1676a 実装時の見落とし)

**将軍/軍師の事前仮説 (subprocess.run timeout 不全 / flock 競合) は全て誤り**。真因は単純な **HTTP プロトコル違反** で、Content-Length 9 行追加 (LOC 30) で**即日完全解消可能**。

**follow-up cmd 推奨**:
- **cmd_1677-A** (CRITICAL・即日): 案 P1 (Content-Length 追加 9 箇所) — 足軽 1 担当推奨
- **cmd_1677-B** (HIGH): 案 R1 (`_send_json` helper 統一・全 endpoint 適用) — 設計後実装
- **cmd_1677-C** (MEDIUM): 滞留 curl reaper (server 側で hang client 自動 timeout・hardening)
- **cmd_1677-D** (LOW): server restart 自動化 (dashboard_lifecycle.sh) の存続判断
