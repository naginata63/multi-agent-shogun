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

# === cmd完了時: 自動done更新 ===
# メッセージが「✅ cmd_XXXX完了」パターンの場合、
# shogun_to_karo.yamlの該当cmd status → done に更新
# pending/in_progress両方を対象（自動in_progressが効いていないケースに対応）
_update_cmd_done() {
    local msg="$1"
    # Match "✅ cmd_XXXX完了" pattern
    echo "$msg" | grep -qP '✅ cmd_\d+完了' || return 0

    local cmd_id
    cmd_id=$(echo "$msg" | grep -oP 'cmd_\d+' | head -1)
    [ -z "$cmd_id" ] && return 0

    local yaml_file="$SCRIPT_DIR/queue/shogun_to_karo.yaml"
    [ ! -f "$yaml_file" ] && return 0

    local lock_file="${yaml_file}.lock"
    local tmp_file="${yaml_file}.tmp.$$"

    (
        flock -w 5 200 || exit 0

        if awk -v cmd="$cmd_id" '
            /- id: / { in_block = ($0 ~ "- id: " cmd) }
            in_block && /^  status: (pending|in_progress)$/ {
                sub(/status: (pending|in_progress)/, "status: done")
                in_block = 0
                updated = 1
            }
            { print }
            END { exit (updated ? 0 : 1) }
        ' "$yaml_file" > "$tmp_file"; then
            mv "$tmp_file" "$yaml_file"
        else
            rm -f "$tmp_file"
        fi
    ) 200>"$lock_file" 2>/dev/null

    return 0
}
_update_cmd_done "$1"

# === done cmd自動アーカイブ（100件超で古いdone退避） ===
_archive_old_done_cmds() {
    local YAML="$SCRIPT_DIR/queue/shogun_to_karo.yaml"
    local ARCHIVE_DIR="$SCRIPT_DIR/queue/archive"
    local THRESHOLD=100
    local KEEP_RECENT=50

    [ ! -f "$YAML" ] && return 0

    # done件数カウント
    local DONE_COUNT
    DONE_COUNT=$(grep -c "status: done" "$YAML" 2>/dev/null || echo 0)
    if [ "$DONE_COUNT" -le "$THRESHOLD" ]; then
        return 0
    fi

    local ARCHIVE_FILE="${ARCHIVE_DIR}/shogun_to_karo_$(date +%Y%m%d).yaml"
    mkdir -p "$ARCHIVE_DIR"

    # PythonでYAMLアーカイブ処理（flock排他制御）
    (
        flock -w 5 201 || exit 0

        python3 -c "
import sys
THRESHOLD = $THRESHOLD
KEEP_RECENT = $KEEP_RECENT
yaml_file = '$YAML'
archive_file = '$ARCHIVE_FILE'

with open(yaml_file) as f:
    lines = f.readlines()

# done行の位置を特定
done_indices = []
cmd_start = None
for i, line in enumerate(lines):
    if line.strip().startswith('- id: cmd_'):
        cmd_start = i
    if cmd_start is not None and 'status: done' in line and line.strip().startswith('status:'):
        done_indices.append(cmd_start)
        cmd_start = None

# 古いdone（直近KEEP_RECENT件以外）をアーカイブ
to_archive = done_indices[:-KEEP_RECENT] if len(done_indices) > KEEP_RECENT else []
if not to_archive:
    sys.exit(0)

# アーカイブファイルに書き込み
with open(archive_file, 'w') as af:
    af.write('# Archived done cmds - $(date)\\n')
    for idx in to_archive:
        end = idx + 1
        while end < len(lines) and not lines[end].strip().startswith('- id:'):
            end += 1
        for line in lines[idx:end]:
            af.write(line)

# 元ファイルから削除（逆順で）
for idx in reversed(to_archive):
    end = idx + 1
    while end < len(lines) and not lines[end].strip().startswith('- id:'):
        end += 1
    del lines[idx:end]

with open(yaml_file, 'w') as f:
    f.writelines(lines)

print(f'Archived {len(to_archive)} done cmds. Kept {min(len(done_indices), KEEP_RECENT)} recent.')
"
    ) 201>"${YAML}.lock2" 2>/dev/null

    return 0
}
_archive_old_done_cmds

# 送信ログ記録
NTFY_LOG="$SCRIPT_DIR/queue/ntfy_sent.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$NTFY_LOG"

# ログローテーション（500行超で古い行を切り捨て、直近300行を残す）
if [ -f "$NTFY_LOG" ]; then
    LINE_COUNT=$(wc -l < "$NTFY_LOG")
    if [ "$LINE_COUNT" -gt 500 ]; then
        ARCHIVE_DIR="$SCRIPT_DIR/queue/archive"
        mkdir -p "$ARCHIVE_DIR" 2>/dev/null
        cp "$NTFY_LOG" "$ARCHIVE_DIR/ntfy_sent_$(date +%Y%m%d).log" 2>/dev/null
        tail -300 "$NTFY_LOG" > "${NTFY_LOG}.tmp" && mv "${NTFY_LOG}.tmp" "$NTFY_LOG"
    fi
fi

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
