#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# ntfy Input Listener
# Streams messages from ntfy topic, writes to inbox YAML, wakes shogun.
# NOT polling — uses ntfy's streaming endpoint (long-lived HTTP connection).
# FR-066: ntfy認証対応 (Bearer token / Basic auth)
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS="$SCRIPT_DIR/config/settings.yaml"
TOPIC=$(grep 'ntfy_topic:' "$SETTINGS" | awk '{print $2}' | tr -d '"')
INBOX="$SCRIPT_DIR/queue/ntfy_inbox.yaml"
LOCKFILE="${INBOX}.lock"
CORRUPT_DIR="$SCRIPT_DIR/logs/ntfy_inbox_corrupt"

# ntfy_auth.sh読み込み
# shellcheck source=../lib/ntfy_auth.sh
source "$SCRIPT_DIR/lib/ntfy_auth.sh"

if [ -z "$TOPIC" ]; then
    echo "[ntfy_listener] ntfy_topic not configured in settings.yaml" >&2
    exit 1
fi

# トピック名セキュリティ検証
ntfy_validate_topic "$TOPIC" || true

# Initialize inbox if not exists
if [ ! -f "$INBOX" ]; then
    echo "inbox:" > "$INBOX"
fi

# 認証引数を取得（設定がなければ空 = 後方互換）
AUTH_ARGS=()
while IFS= read -r line; do
    [ -n "$line" ] && AUTH_ARGS+=("$line")
done < <(ntfy_get_auth_args "$SCRIPT_DIR/config/ntfy_auth.env")

# JSON field extractor (python3 — jq not available)
parse_json() {
    "$SCRIPT_DIR/.venv/bin/python3" -c "import sys,json; print(json.load(sys.stdin).get('$1',''))" 2>/dev/null
}

parse_tags() {
    "$SCRIPT_DIR/.venv/bin/python3" -c "import sys,json; print(','.join(json.load(sys.stdin).get('tags',[])))" 2>/dev/null
}

parse_attachment_url() {
    "$SCRIPT_DIR/.venv/bin/python3" -c "
import sys,json
data = json.load(sys.stdin)
att = data.get('attachment', {})
if att and att.get('url'):
    print(att['url'])
" 2>/dev/null
}

parse_attachment_name() {
    "$SCRIPT_DIR/.venv/bin/python3" -c "
import sys,json
data = json.load(sys.stdin)
att = data.get('attachment', {})
print(att.get('name', ''))
" 2>/dev/null
}

parse_attachment_size() {
    "$SCRIPT_DIR/.venv/bin/python3" -c "
import sys,json
data = json.load(sys.stdin)
att = data.get('attachment', {})
print(att.get('size', 0))
" 2>/dev/null
}

validate_attachment() {
    local name="$1"
    local size="$2"

    # 拡張子チェック（画像のみ許可）
    local ext="${name##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    case "$ext" in
        jpg|jpeg|png|gif|webp|heic|heif|pdf) ;;
        *) echo "[ntfy] 拒否: 非許可拡張子 .$ext" >&2; return 1 ;;
    esac

    # サイズチェック（15MB上限 = ntfyの制限に合わせる）
    local max_size=15728640  # 15 * 1024 * 1024
    if [ "$size" -gt "$max_size" ] 2>/dev/null; then
        echo "[ntfy] 拒否: サイズ超過 ${size}bytes > 15MB" >&2
        return 1
    fi

    return 0
}

download_attachment() {
    local url="$1"
    local name="$2"
    local msg_id="$3"

    # 保存先ディレクトリ（settings.yamlから読む、デフォルト: screenshots/ntfy/）
    local save_dir
    save_dir=$(grep 'ntfy_image_dir:' "$SETTINGS" | awk '{print $2}' | tr -d '"')
    if [ -z "$save_dir" ]; then
        save_dir="$SCRIPT_DIR/screenshots/ntfy"
    else
        # 相対パスなら絶対パスに変換
        [[ "$save_dir" = /* ]] || save_dir="$SCRIPT_DIR/$save_dir"
    fi
    mkdir -p "$save_dir"

    # ファイル名: {msg_id}_{元ファイル名}（衝突回避）
    # ファイル名のサニタイズ: /, .., スペースを除去
    local safe_name
    safe_name=$(echo "$name" | sed 's/[^a-zA-Z0-9._-]/_/g')
    local dest="$save_dir/${msg_id}_${safe_name}"

    # ダウンロード（認証引数付き、タイムアウト30秒）
    if curl -sS -o "$dest" --max-time 30 "${AUTH_ARGS[@]}" "$url" 2>/dev/null; then
        # ファイル存在＆サイズ > 0 確認
        if [ -s "$dest" ]; then
            echo "$dest"
            return 0
        fi
    fi

    # 失敗時: ファイル削除
    rm -f "$dest" 2>/dev/null
    return 1
}

append_ntfy_inbox() {
    local msg_id="$1"
    local ts="$2"
    local msg="$3"
    local image_path="${4:-}"  # 新規引数（オプション）

    (
        if command -v flock &>/dev/null; then
            flock -w 5 200 || exit 1
        else
            _ld="${LOCKFILE}.d"; _i=0
            while ! mkdir "$_ld" 2>/dev/null; do sleep 0.1; _i=$((_i+1)); [ $_i -ge 50 ] && exit 1; done
            trap "rmdir '$_ld' 2>/dev/null" EXIT
        fi
        NTFY_INBOX_PATH="$INBOX" \
        NTFY_CORRUPT_DIR="$CORRUPT_DIR" \
        MSG_ID="$msg_id" \
        MSG_TS="$ts" \
        MSG_TEXT="$msg" \
        IMAGE_PATH="$image_path" \
        "$SCRIPT_DIR/.venv/bin/python3" - << 'PY'
import datetime
import os
import shutil
import sys
import tempfile
import yaml

path = os.environ["NTFY_INBOX_PATH"]
corrupt_dir = os.environ.get("NTFY_CORRUPT_DIR", "")
entry = {
    "id": os.environ.get("MSG_ID", ""),
    "timestamp": os.environ.get("MSG_TS", ""),
    "message": os.environ.get("MSG_TEXT", ""),
    "status": "pending",
}
# 添付画像パスがあれば追加
image_path = os.environ.get("IMAGE_PATH", "")
if image_path:
    entry["image_path"] = image_path

data = {}
parse_error = False

if os.path.exists(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        if isinstance(loaded, dict):
            data = loaded
        elif loaded is None:
            data = {}
        else:
            parse_error = True
    except Exception:
        parse_error = True

if parse_error and os.path.exists(path):
    try:
        if corrupt_dir:
            os.makedirs(corrupt_dir, exist_ok=True)
            backup = os.path.join(
                corrupt_dir,
                f"ntfy_inbox_corrupt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
            )
            shutil.copy2(path, backup)
    except Exception:
        pass
    data = {}

items = data.get("inbox")
if not isinstance(items, list):
    items = []

# 重複チェック: 同一msg_idが既に存在する場合はスキップ
msg_id = os.environ.get("MSG_ID", "")
if msg_id and any(item.get("id", "") == msg_id for item in items):
    sys.exit(0)  # 既存エントリ — スキップ

items.append(entry)
data["inbox"] = items

tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
try:
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
    os.replace(tmp_path, path)
except Exception as e:
    try:
        os.unlink(tmp_path)
    except Exception:
        pass
    print(f"[ntfy_listener] failed to write inbox: {e}", file=sys.stderr)
    sys.exit(1)
PY
    ) 200>"$LOCKFILE"
}

AUTH_LABEL="none"; [ -n "${NTFY_TOKEN:-}" ] && AUTH_LABEL="token"; [ -n "${NTFY_USER:-}" ] && AUTH_LABEL="basic"
echo "[$(date)] ntfy listener started — topic: $TOPIC (auth: $AUTH_LABEL)" >&2

while true; do
    # Stream new messages (long-lived connection, blocks until message arrives)
    # since=<unix_ts>: 接続開始時刻以降のメッセージのみ受信（再接続時の過去メッセージ重複を防止）
    SINCE_TS=$(date +%s)
    curl -s --no-buffer "${AUTH_ARGS[@]}" "https://ntfy.sh/$TOPIC/json?since=${SINCE_TS}" 2>/dev/null | while IFS= read -r line; do
        # Skip keepalive pings and non-message events
        EVENT=$(echo "$line" | parse_json event)
        [ "$EVENT" != "message" ] && continue

        # Skip outbound messages (sent by our own scripts/ntfy.sh)
        TAGS=$(echo "$line" | parse_tags)
        echo "$TAGS" | grep -q "outbound" && continue

        # Extract message content
        MSG=$(echo "$line" | parse_json message)
        [ -z "$MSG" ] && continue

        MSG_ID=$(echo "$line" | parse_json id)
        TIMESTAMP=$(date "+%Y-%m-%dT%H:%M:%S%:z")

        echo "[$(date)] Received: $MSG" >&2

        # --- 添付ファイル処理 ---
        ATT_URL=$(echo "$line" | parse_attachment_url)
        ATT_NAME=$(echo "$line" | parse_attachment_name)
        ATT_SIZE=$(echo "$line" | parse_attachment_size)
        IMAGE_PATH=""

        if [ -n "$ATT_URL" ]; then
            if ! validate_attachment "$ATT_NAME" "$ATT_SIZE"; then
                echo "[$(date)] [ntfy_listener] WARNING: attachment rejected: name=$ATT_NAME size=$ATT_SIZE" >&2
            else
                IMAGE_PATH=$(download_attachment "$ATT_URL" "$ATT_NAME" "$MSG_ID")
                if [ -z "$IMAGE_PATH" ]; then
                    echo "[$(date)] [ntfy_listener] WARNING: attachment download failed: $ATT_URL" >&2
                else
                    echo "[$(date)] Attachment saved: $IMAGE_PATH" >&2
                fi
            fi
        fi

        # Append to inbox YAML (flock + atomic write; multiline-safe)
        if ! append_ntfy_inbox "$MSG_ID" "$TIMESTAMP" "$MSG" "$IMAGE_PATH"; then
            echo "[$(date)] [ntfy_listener] WARNING: failed to append ntfy_inbox entry" >&2
            continue
        fi

        # Auto-reply removed — shogun replies directly after processing.

        # shogunへのinbox: 殿のスマホからのメッセージのみ起こす
        # 家老のntfy通知（絵文字で始まる）は起こさない（Session Startで読む）
        IS_AGENT_MSG=false
        case "$MSG" in
            ✅*|🎬*|🐑*|🌟*|🎤*|📊*|🚨*|📰*|🖼️*|🔍*|❌*|🌐*|📋*) IS_AGENT_MSG=true ;;
        esac
        if [ "$IS_AGENT_MSG" = false ]; then
            bash "$SCRIPT_DIR/scripts/inbox_write.sh" shogun \
                "ntfyから新しいメッセージ受信。queue/ntfy_inbox.yaml を確認し処理せよ。" \
                ntfy_received ntfy_listener
        fi
    done

    # Connection dropped — reconnect after brief pause
    echo "[$(date)] Connection lost, reconnecting in 5s..." >&2
    sleep 5
done
