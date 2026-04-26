# MCPダッシュボードにAdvisor Proxyパネル追加手順 (cmd_1366)

## 重要：着手前にgit pullせよ
cmd_1364が同じserver.pyを修正済みである。競合を避けるため必ず最新を取得すること：
```bash
cd /home/murakami/multi-agent-shogun && git pull origin main
```

## 対象ファイル
`scripts/dashboard/server.py`（既存ファイルへの修正のみ）

## 修正手順

1. `git pull origin main` を実行してcmd_1364の変更を取り込む
2. `scripts/dashboard/server.py` を読む
3. `_get_advisor_proxy_stats()` 関数を新設（`_get_dingtalk_qc_stats()`の近くに追加）：
   ```python
   def _get_advisor_proxy_stats():
       try:
           import urllib.request
           health = json.loads(urllib.request.urlopen("http://localhost:8780/health", timeout=2).read())
           metrics = json.loads(urllib.request.urlopen("http://localhost:8780/metrics", timeout=2).read())
           return {
               "status": "up",
               "uptime_seconds": health.get("uptime_seconds"),
               "circuit_state": health.get("circuit_state", "unknown"),
               "total_requests": metrics.get("total_requests", 0),
               "success": metrics.get("success", 0),
               "failures": metrics.get("failures", 0),
               "advisor_calls": metrics.get("advisor_calls", 0),
               "avg_response_ms": metrics.get("avg_response_ms", 0),
           }
       except Exception:
           return {"status": "down"}
   ```
4. `_build_dashboard_data()` に `"advisor_proxy": _get_advisor_proxy_stats()` を追加
5. フロントHTMLにAdvisor Proxyパネルを追加（DingTalkパネルの近くに配置）：
   - 稼働状態・uptime・リクエスト数・advisor呼出数・サーキット状態を表示
   - サーキットがopenの場合は赤色警告

## テスト

```bash
curl http://192.168.2.7:8770/api/dashboard | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('advisor_proxy',{}), indent=2))"
```
- `advisor_proxy` キーが存在すること
- プロキシ停止中なら `{"status": "down"}` であること

## 完了処理

```bash
git add scripts/dashboard/server.py
git commit -m "feat(cmd_1366): MCPダッシュボードにAdvisor Proxyパネル追加"
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽4号、subtask_1366a完了。advisor_proxyキー確認結果を報告。" report_completed ashigaru4
```
