# advisor_proxy.py request_id ログ追加手順

## 対象ファイル
`scripts/advisor_proxy.py`

## 修正内容

1. `import uuid` を既存importに追加
2. `handle_request` 関数冒頭に `req_id = uuid.uuid4().hex[:8]` を追加
3. 既存の `logger.info("Passthrough %s %s", method, path)` → `logger.info("[%s] Passthrough %s %s", req_id, method, path)`
4. 既存の `logger.info("Messages request — model=%s stream=%s", ...)` → `logger.info("[%s] Messages request — model=%s stream=%s", req_id, ...)`
5. 既存の `logger.info("Advisor tool_use detected (loop %d/%d), id=%s", ...)` → `logger.info("[%s] Advisor tool_use detected (loop %d/%d), id=%s", req_id, ...)`
6. 既存ロジック（POST処理、advisor検出ループ等）は一切変更しない

## テスト

- プロキシ起動中なら: `curl http://localhost:8780/health` で正常応答確認
- `tail -5 logs/advisor_proxy.log` でログに `[xxxxxxxx]` 形式のreq_idが含まれるか確認
- プロキシ未起動の場合は「コード変更のみ完了、起動後確認が必要」と明記すること

## 完了処理

```bash
git add scripts/advisor_proxy.py
git commit -m "feat(cmd_1362): handle_requestにrequest_idログ追加"
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽2号、subtask_1362a完了。commit番号と動作確認結果を報告。" report_completed ashigaru2
```
