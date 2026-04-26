# advisor_proxy.py リトライ・サーキットブレーカー・メトリクス実装手順

## 対象ファイル
`scripts/advisor_proxy.py`（既存ファイルへの追記のみ。新規.py禁止）

## 実装前にadvisor()を呼べ（step 3.8）
設計方針を確認してから実装に入ること。advisor()が利用不可の場合は以下の設計方針で進めよ。

## 設計方針（推奨）

### 1. CircuitBreakerクラスで状態管理
グローバル変数よりクラスの方が保守性が高い。以下の構造を推奨：

```python
import asyncio, time, threading

class CircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._lock = threading.Lock()

    def record_success(self): ...
    def record_failure(self): ...
    def can_request(self) -> bool: ...  # half_open後30秒経過チェックも含む

circuit_breaker = CircuitBreaker()
```

### 2. Metricsはdataclassかシンプルなクラス
```python
import threading
class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.total_requests = 0
        self.success = 0
        self.failures = 0
        self.advisor_calls = 0
        self._response_times = []  # 直近100件のみ保持

    def avg_response_ms(self) -> float: ...

metrics = Metrics()
```

### 3. リトライとサーキットブレーカーの相互作用
- サーキットOPEN中はリトライをスキップして即座に503返却
- リトライはZ.AI upstream呼び出し部分を関数化して再利用

## 実装ステップ

1. `scripts/advisor_proxy.py` を全て読む
2. import追加: `import threading`, `import asyncio`（既にある場合はスキップ）
3. `CircuitBreaker`クラスを定数定義セクション（`PROXY_PORT`等の後）に追加
4. `Metrics`クラスをその直後に追加
5. `handle_request`関数を修正:
   - 関数冒頭でサーキット確認（`if not circuit_breaker.can_request()`→503返却）
   - upstream呼び出しをヘルパー関数（`async def _upstream_post(...)`）に切り出し
   - リトライループ（最大2回、backoff 1s→2s、5xx/タイムアウトのみ）
   - metrics更新（total/success/failure/response_time）
6. `handle_health`にcircuit_state追加:
   ```python
   {"status": "ok", "uptime_seconds": ..., "circuit_state": circuit_breaker.state}
   ```
7. `handle_metrics`関数を新規追加:
   ```python
   async def handle_metrics(request):
       return web.json_response({
           "total_requests": metrics.total_requests,
           "success": metrics.success,
           "failures": metrics.failures,
           "advisor_calls": metrics.advisor_calls,
           "avg_response_ms": metrics.avg_response_ms(),
           "circuit_state": circuit_breaker.state,
       })
   ```
8. `main()`のrouter設定に`app.router.add_get("/metrics", handle_metrics)`を追加

## テスト

- `curl http://localhost:8780/health` → circuit_stateフィールド確認
- `curl http://localhost:8780/metrics` → 全フィールド確認
- プロキシ未起動の場合は「コード変更のみ完了」と明記

## 完了処理

```bash
git add scripts/advisor_proxy.py
git commit -m "feat(cmd_1363): advisor_proxyにリトライ・サーキットブレーカー・メトリクス追加"
```

実装完了前にadvisor()を呼んで成果物レビュー（step 4.8）。

```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽3号、subtask_1363a完了。commit番号と動作確認結果を報告。" report_completed ashigaru3
```
