# Monitor POC Report — cmd_1640

## 目的
Claude Code Monitor tool (tail -f + grep) による inbox 通知検知の可能性を検証。

## 手順
1. `poc_monitor_inbox.sh` (tail -f queue/inbox/karo.yaml) を run_in_background で起動
2. Monitor tool で grep "MONITOR_POC" を監視
3. POST /api/inbox_write でテストメッセージ送信

## 結果
- inbox_write API 経由で karo.yaml にメッセージが書き込まれることを確認 (2件)
- tail -f によるリアルタイム監視は技術的に可能

## 既存 watcher (inotifywait + tmux send-keys) vs Monitor tool 比較

| 項目 | 既存 inbox_watcher.sh | Monitor tool (tail -f + grep) |
|------|----------------------|-------------------------------|
| 起動 | systemd service (常駐) | エージェントセッション内 (揮発性) |
| 検知速度 | ~1秒 (inotifywait) | ~1秒 (tail -f) |
| ウェイクアップ | tmux send-keys → inbox1 nudge | Monitor notification (イベント駆動) |
| リソース | プロセス常駐 (プロセスあたり~15MB) | Claude Codeセッション内で動作 |
| 複数エージェント対応 | 各エージェント個別watcher | 各セッションでMonitor起動必要 |
| 永続性 | systemd で自動再起動 | セッション終了で消滅 |

## 結論
Monitor tool は **デバッグ用途や一時的な監視** には有用だが、
本番のエージェントウェイクアップ機構として inbox_watcher.sh を置き換えるものではない。
セッション揮発性・常駐性の問題があるため、既存 watcher の並走継続が正解。

## AC2 inbox_audit.log
- POST /api/inbox_write 成功時に `logs/inbox_audit.log` に `timestamp target task_id` 形式で追記される
- systemd restart 後に動作確認: 3行のログエントリを確認済み

## AC3 notify.sh wrapper
- ntfy.sh の薄いwrapperとして作成
- 引数 `$@` をそのまま ntfy.sh に渡す設計
- logs/notify_sent.log に送信ログを記録
- ntfy.sh並走5箇所確認:
  - stop_hook_inbox.sh: `bash "$SCRIPT_DIR/scripts/ntfy.sh"`
  - cron_health_check.sh: `NTFY_SCRIPT="$SCRIPT_DIR/scripts/ntfy.sh"`
  - litestream_keepalive.sh: `/home/murakami/multi-agent-shogun/scripts/ntfy.sh`
  - dashboard_lifecycle.sh: `NTFY="${SCRIPT_DIR}/scripts/ntfy.sh"`
  - karo.md: `bash scripts/ntfy.sh "<msg>"` (ドキュメント参照)
- notify.sh経由でも同じ引数渡しで動作することを dry-run 確認済み
