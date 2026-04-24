#!/bin/bash
# YouTube解析ダッシュボード自動起動セットアップスクリプト
# cmd_891: PC起動時にHTTPサーバー+ブラウザを自動起動
#
# 実行方法: bash scripts/setup_youtube_dashboard_autostart.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="$REPO_DIR/projects/dozle_kirinuki/analytics/dashboard"
SERVICE_DIR="$HOME/.config/systemd/user"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "=== YouTube Dashboard Autostart Setup ==="

# 1. systemdユーザーサービス作成
mkdir -p "$SERVICE_DIR"
cat > "$SERVICE_DIR/youtube-dashboard.service" << EOF
[Unit]
Description=YouTube Analytics Dashboard HTTP Server
After=default.target

[Service]
Type=simple
WorkingDirectory=$DASHBOARD_DIR
ExecStartPre=/bin/bash -c '! ss -tlnp | grep -q ":8080 "'
ExecStart=/usr/bin/python3 -m http.server 8080
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
echo "✓ systemdサービスファイル作成: $SERVICE_DIR/youtube-dashboard.service"

# 2. XDG autostartエントリ作成
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/youtube-dashboard-browser.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=YouTube Dashboard Browser
Exec=bash -c 'sleep 3 && xdg-open http://localhost:8080'
X-GNOME-Autostart-enabled=true
EOF
echo "✓ XDG autostartファイル作成: $AUTOSTART_DIR/youtube-dashboard-browser.desktop"

# 3. サービス有効化・起動
systemctl --user daemon-reload
systemctl --user enable --now youtube-dashboard.service
echo "✓ サービス有効化・起動完了"

# 4. 検証
sleep 2
HTTP_STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080)
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ HTTP 200 確認: http://localhost:8080"
else
    echo "✗ HTTP status: $HTTP_STATUS (期待: 200)"
    exit 1
fi

echo ""
echo "=== セットアップ完了 ==="
echo "次回PC起動時から自動的にダッシュボードが開きます"
echo "手動確認: http://localhost:8080"
