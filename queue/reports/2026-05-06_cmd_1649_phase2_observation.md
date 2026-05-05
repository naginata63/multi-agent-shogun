# cmd_1649 Phase 2 SSE 24h 観察 報告書 (中間・前提条件未充足)

- **報告者**: 軍師 (gunshi)
- **task_id**: subtask_1649_sse_observation
- **parent_cmd**: cmd_1649
- **作成日**: 2026-05-06 05:50 JST
- **判定**: ⚠️ **BLOCKED** — 前提条件 (ENABLE_SSE_INBOX=true) が満たされておらず、24h 観察を開始できない
- **次アクション**: 家老による server.py 再起動 (環境変数 ENABLE_SSE_INBOX=true を設定して起動) を依頼

---

## 1. 検知した問題: ENABLE_SSE_INBOX=false で server.py が稼働中

### 1.1 診断手順

```bash
# 1) HTTP レスポンスヘッダー確認
$ curl -s -N -o /tmp/sse_test.out -D /tmp/sse_headers.out \
    "http://192.168.2.4:8770/api/inbox_stream?agent=gunshi"
$ cat /tmp/sse_headers.out
HTTP/1.1 404 Not Found
Server: BaseHTTP/0.6 Python/3.12.3
Content-Type: application/json

$ cat /tmp/sse_test.out
{"error": "SSE inbox disabled"}
```

→ `/api/inbox_stream` が **404 を返却**・body は `{"error": "SSE inbox disabled"}`。
→ server.py 内の L2473-2478 (`if not ENABLE_SSE_INBOX:` → 404 応答) のパスが実行されている。

### 1.2 server.py プロセス環境変数の確認

```bash
$ ps -o pid,etime,cmd -e | grep "dashboard/server.py"
537355 19:06 /usr/bin/python3 /home/murakami/multi-agent-shogun/scripts/dashboard/server.py

$ cat /proc/537355/environ | tr '\0' '\n' | grep -i "ENABLE\|SSE"
(empty — 該当なし)
```

→ PID 537355 (server.py) の環境変数に **ENABLE_SSE_INBOX が設定されていない**。
→ server.py L43: `ENABLE_SSE_INBOX = os.environ.get('ENABLE_SSE_INBOX', 'false').lower() == 'true'` → **default の `false` で稼働中**。

### 1.3 サーバ起動時刻と SSE コードの commit 時刻

| 観点 | 時刻 | 備考 |
|------|------|------|
| ash1 SSE 実装 commit (be80269) | 2026-05-06 05:21 | cmd_1648 Phase 1 完了 |
| server.py PID 537355 起動時刻 | 2026-05-06 05:25 | ash1 commit より 4 分後 |
| 軍師 cmd_1648 QC PASS | 2026-05-06 05:30 | feature flag = false で実装は確認済 |
| cmd_1649 タスク受信 | 2026-05-06 05:39 | 家老から起票 |
| cmd_1649 観察試行 | 2026-05-06 05:43 | 5 件テスト inbox_write |

→ server.py には SSE コードが含まれているが、**ENABLE_SSE_INBOX 環境変数が設定されないまま 5:25 に起動された** ため feature flag が false のまま。

---

## 2. 部分実施結果 (5 件テスト inbox_write の動作確認)

### 2.1 テスト実施

```
Test 1: msg_20260506_054333_469abe7a (test_1649_01)
Test 2: msg_20260506_054334_0cc58681 (test_1649_02)
Test 3: msg_20260506_054335_d9191912 (test_1649_03)
Test 4: msg_20260506_054336_d01ab27f (test_1649_04)
Test 5: msg_20260506_054338_743021c9 (test_1649_05)
```

### 2.2 結果

| 観点 | 状態 | 評価 |
|------|------|------|
| `/api/inbox_write` 応答 | 5/5 全件 success=true | ✅ inbox_write 経路は動作中 |
| `inbox_audit.log` | 5/5 全件記録 | ✅ 監査ログ機構正常 |
| inbox YAML 配信 | 5/5 全件 read=0 で gunshi の inbox に到達 | ✅ 既存経路 (inbox_watcher.sh + bash inbox_write.sh) 正常 |
| **SSE Monitor stdout** | **0/5 件 — 何も配信されない** | ❌ feature flag false のため期待通りの 0 件 |

**結論**: 既存経路は完全動作・SSE 経路は feature flag false のため未稼働。

---

## 3. SSE Monitor 起動・停止 履歴

### 3.1 起動

```python
Monitor(
    command='curl -N --no-buffer "http://192.168.2.4:8770/api/inbox_stream?agent=gunshi" 2>&1 | grep --line-buffered "^data:"',
    description='SSE inbox stream for gunshi (cmd_1649 Phase2 24h obs・data lines only)',
    persistent=true,
    timeout_ms=86400000
)
→ task_id: b2wsufvlh, status: running
```

### 3.2 観察期間

- 開始: 2026-05-06 05:42
- 停止: 2026-05-06 05:50 (8 分)
- 受信 event: **0 件**

### 3.3 停止理由

ENABLE_SSE_INBOX=false の状態で観察しても無意味であるため、`TaskStop` で停止。
server.py 再起動 (ENABLE_SSE_INBOX=true で起動) 後に観察を再開する設計。

---

## 4. 前提条件充足のための要請事項 (家老向け)

### 4.1 必要なアクション

server.py を **`ENABLE_SSE_INBOX=true`** 環境変数を設定して再起動する。

### 4.2 推奨手順 (家老が選択)

#### オプション A: 一時的環境変数で再起動 (テスト用)

```bash
# 既存 server.py を停止
pkill -f "scripts/dashboard/server.py"

# 環境変数を設定して起動
ENABLE_SSE_INBOX=true python3 /home/murakami/multi-agent-shogun/scripts/dashboard/server.py &
```

#### オプション B: dashboard_lifecycle.sh / 起動スクリプトに環境変数を永続化 (本番運用向け)

`scripts/dashboard_lifecycle.sh` または server.py 起動箇所で `export ENABLE_SSE_INBOX=true` を追加。

```bash
# 例: 起動スクリプトの先頭に追加
export ENABLE_SSE_INBOX=true
```

#### オプション C: systemd unit 化 (将来的・cmd_1651 候補)

cmd_1646 §3 で軍師が推奨した systemd unit 内の `Environment=ENABLE_SSE_INBOX=true` で永続化。

### 4.3 再起動後の確認

家老が再起動後に以下を実行 → 200 が返れば軍師に観察再開指示:

```bash
$ timeout 5 curl -s -o /dev/null -w '%{http_code}\n' "http://192.168.2.4:8770/api/inbox_stream?agent=gunshi"
# 期待: タイムアウト 5 秒で接続維持 (SSE active) → 軍師観察再開可能
# 異常: 404 (まだ feature flag false) or 500 (実装エラー)
```

---

## 5. 既存システムへの影響 (本タスク中の確認)

| 観点 | 状態 |
|------|------|
| inbox_watcher.sh (10 プロセス) | ✅ 健在・nudge 正常動作 |
| 既存 /api/inbox_write | ✅ 正常 (5/5 success) |
| inbox_audit.log | ✅ 5 件記録 |
| 軍師 inbox (5 テストメッセージ) | ✅ 既読化済 |
| poc_monitor_inbox.sh (cmd_1640) | ✅ 不変 |

→ **既存運用への影響ゼロ**。観察試行で副作用なし。

---

## 6. Phase 3 推奨判断 (現時点・暫定)

**現時点では Phase 3 起票推奨不可**。

理由:
1. Phase 2 観察開始すらできていない (前提条件未充足)
2. 24h データが 0 件
3. SSE 接続安定性・取りこぼし率が未測定

**前提条件充足後の手順**:
1. 家老が server.py 再起動 (ENABLE_SSE_INBOX=true) を実施
2. 軍師に再起動完了を inbox 通知
3. 軍師が SSE Monitor 再起動 → 5 件テスト → 24h 観察
4. 24h 後に取りこぼし 0 件確認 → Phase 3 (cmd_1650) 起票判断

---

## 7. 受入条件 充足検証 (本タスク・部分実施)

| # | 受入条件 | 結果 | 状態 |
|---|---------|------|------|
| 1 | ENABLE_SSE_INBOX=true で server.py 起動済を確認してから開始 | ❌ FAIL | feature flag false で稼働中・本書 §1 で記録 |
| 2 | 軍師セッション内で SSE Monitor 起動済 | ⚠️ 起動したが SSE 未配信 | §3 で記録・8 分間で 0 件受信 |
| 3 | 既存 inbox_watcher.sh は並走稼働継続 | ✅ | §5 で確認 |
| 4 | 24 時間観察完了 | ❌ FAIL | 観察開始不可・前提条件未充足 |
| 5 | queue/reports/2026-05-06_cmd_1649_phase2_observation.md 作成 | ✅ | 本書 |
| 6 | テスト用 inbox_write を 5-10 回発行・SSE Monitor + 既存 watcher 両方の反応確認 | ⚠️ 部分実施 | 5 件発行・既存経路のみ正常応答 |
| 7 | SSE 接続断絶 + 自動再接続の挙動記録 | ❌ FAIL | SSE 自体が disabled |
| 8 | Phase 3 起票判断資料 | ⚠️ 暫定 | §6 で記録・前提条件充足後に再評価 |
| 9 | git commit 済 | ⏳ 本書 commit 後 | — |

---

## 8. north_star_alignment

```yaml
north_star_alignment:
  status: misaligned (一時的)
  reason: "Phase 2 観察開始の前提条件 (ENABLE_SSE_INBOX=true) が未充足。家老の server.py 再起動 (環境変数設定) が必要。本中間報告で問題を即座に escalate し、家老の対応を待つ運用は cmd_1646 で軍師が指摘した『段階的展開・feature flag 運用』と整合している。"
  risks_to_north_star:
    - "家老の対応が遅れると cmd_1648 (Phase 1) と cmd_1650 (Phase 3) の間が長期化し、ロードマップが滞る。早期 escalate が必須。"
    - "ENABLE_SSE_INBOX=true の永続化方法が未確定 (一時的 env vs systemd unit)。Phase 4 (cmd_1651) で systemd 化を確実に実施する必要あり。"
    - "Phase 2 観察を再開する際に、test inbox_write のような外部投入で SSE 経路と watcher 経路の二重通知が発生する可能性。両者の整合性は cmd_1646 軸 6 (rollback) の rollback 設計で対応可能。"
```

---

## 9. 最終判定

```
status: blocked (waiting for karo's server.py restart)
acceptance_criteria_met: 1/9 (報告書作成のみ・他は前提条件未充足のため判定不能)
blocking_issue: ENABLE_SSE_INBOX=false で server.py 稼働中 (PID 537355・5:25 起動)
artifacts:
  - queue/reports/2026-05-06_cmd_1649_phase2_observation.md (本書・中間報告)
followup_actions:
  - 家老が server.py を ENABLE_SSE_INBOX=true で再起動
  - 軍師に再起動完了を inbox 通知
  - 軍師が SSE Monitor 再起動 + 5 件テスト + 24h 観察開始
  - 24h 後に Phase 3 (cmd_1650) 起票判断
```

**本タスクは前提条件未充足で BLOCKED。家老の server.py 再起動 (ENABLE_SSE_INBOX=true) を仰ぎたし。**
