# GenAI Daily Report Viewer

生成AIトレンドレポートをブラウザで閲覧するローカルWebサーバー。

## セットアップ

1. 依存インストール:
   不要（Python 3.8+ 標準ライブラリのみ使用。pip3 install -r requirements.txt は不要）

2. 起動（直接）:
   bash scripts/start_viewer.sh --direct
   → http://localhost:8580 でアクセス

3. systemd常駐化（推奨）:
   sudo cp genai_viewer/genai-viewer.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable genai-viewer
   sudo systemctl start genai-viewer

4. Tailscale経由アクセス:
   http://<tailscale-ip>:8580

5. cron + viewer 組み合わせ:
   # 毎朝7時にレポート生成（Viewerが自動で最新を表示）
   0 7 * * * cd /home/murakami/multi-agent-shogun && bash scripts/genai_daily_report.sh >> logs/genai_daily.log 2>&1

## ログ確認
tail -f logs/genai_viewer.log

## 停止
bash scripts/stop_viewer.sh --direct

## フィードバック機能 (P5)

### /api/feedback エンドポイント

POST `/api/feedback` でフィードバックを記録する。

```json
{
  "article_title": "記事タイトル",
  "date": "2026-03-30",
  "reaction": "up"
}
```

`reaction` は `"up"` または `"down"`。記録先: `queue/genai_feedback.yaml`

### ntfy アクションボタン連携

`scripts/genai_ntfy_top3.sh` から ntfy 通知にフィードバックボタン（👍/👎）を追加する方法:

```bash
VIEWER_URL="http://<tailscale-ip>:8580"
ARTICLE_TITLE="記事タイトル"
DATE="2026-03-30"

curl -s https://ntfy.sh/your-topic \
  -d "📄 ${ARTICLE_TITLE}" \
  -H "Actions: http, 👍, ${VIEWER_URL}/api/feedback, body={\"article_title\":\"${ARTICLE_TITLE}\",\"date\":\"${DATE}\",\"reaction\":\"up\"}, method=POST, headers.Content-Type=application/json; http, 👎, ${VIEWER_URL}/api/feedback, body={\"article_title\":\"${ARTICLE_TITLE}\",\"date\":\"${DATE}\",\"reaction\":\"down\"}, method=POST, headers.Content-Type=application/json"
```

ntfy Actionsのフォーマット詳細: https://docs.ntfy.sh/publish/#action-buttons
