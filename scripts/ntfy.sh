#!/usr/bin/env bash
# SayTask通知 — ntfy.sh経由でスマホにプッシュ通知
# FR-066: ntfy認証対応 (Bearer token / Basic auth)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS="$SCRIPT_DIR/config/settings.yaml"

# ntfy_auth.sh読み込み
# shellcheck source=../lib/ntfy_auth.sh
source "$SCRIPT_DIR/lib/ntfy_auth.sh"

TOPIC=$(grep 'ntfy_topic:' "$SETTINGS" | awk '{print $2}' | tr -d '"')
if [ -z "$TOPIC" ]; then
  echo "ntfy_topic not configured in settings.yaml" >&2
  exit 1
fi

# 認証引数を取得（設定がなければ空 = 後方互換）
AUTH_ARGS=()
while IFS= read -r line; do
    [ -n "$line" ] && AUTH_ARGS+=("$line")
done < <(ntfy_get_auth_args "$SCRIPT_DIR/config/ntfy_auth.env")

# shellcheck disable=SC2086
curl -s "${AUTH_ARGS[@]}" -H "Tags: outbound" -d "$1" "https://ntfy.sh/$TOPIC" > /dev/null

# 送信ログ記録
echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$SCRIPT_DIR/queue/ntfy_sent.log"

# 日報自動追記
DAILY_DIR="$SCRIPT_DIR/logs/daily"
mkdir -p "$DAILY_DIR" 2>/dev/null
echo "- [$(date '+%H:%M')] $1" >> "$DAILY_DIR/$(date '+%Y-%m-%d').md"

# デスクトップ通知（PCの前にいる殿向け）
notify-send -u normal -t 10000 "🤖 将軍システム" "$1" 2>/dev/null &

# VOICEVOX音声通知（voicevox_enabled: true の場合のみ）
VOICEVOX_ENABLED=$(grep 'voicevox_enabled:' "$SETTINGS" | awk '{print $2}' | tr -d '"')
if [ "$VOICEVOX_ENABLED" = "true" ]; then
  bash "$SCRIPT_DIR/scripts/ntfy_voice.sh" "$1" &
fi
