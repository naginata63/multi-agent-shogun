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
