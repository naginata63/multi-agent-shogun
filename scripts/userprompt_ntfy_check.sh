#!/usr/bin/env bash
# UserPromptSubmit hook: 殿がメッセージを送るたびにntfy_sent.logの新着をチェック
# 将軍のみ実行。新着があればコンテキストに注入する。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 将軍のみ実行
AGENT_ID=""
if [ -n "${TMUX_PANE:-}" ]; then
    AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
fi
if [[ "$AGENT_ID" != "shogun" ]]; then
    exit 0
fi

NTFY_LOG="$SCRIPT_DIR/queue/ntfy_sent.log"
FLAGS_DIR="$SCRIPT_DIR/queue/.flags"
mkdir -p "$FLAGS_DIR"
LAST_LINE_FILE="$FLAGS_DIR/shogun_ntfy_last_line"

if [ ! -f "$NTFY_LOG" ]; then
    exit 0
fi

CURRENT=$(wc -l < "$NTFY_LOG")
LAST=$(cat "$LAST_LINE_FILE" 2>/dev/null || echo "$CURRENT")

if [ "$CURRENT" -gt "$LAST" ]; then
    NEW_COUNT=$((CURRENT - LAST))
    NEW_LINES=$(tail -n "$NEW_COUNT" "$NTFY_LOG")
    echo "【ntfy新着 ${NEW_COUNT}件】"
    echo "$NEW_LINES"
fi

# 現在の行数を記録
echo "$CURRENT" > "$LAST_LINE_FILE"

# 殿発言ごとに SQLite 側の ntfy_received/wake_up を自動既読化 (cmd_1526 watcher SQLite化対応)
timeout 2 bash -c '
unread_ids=$(curl -s -m 2 "http://localhost:8770/api/inbox_messages?agent=shogun&unread=1&limit=100&full=0" 2>/dev/null | \
    python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  ids=[m[\"id\"] for m in d.get(\"messages\",[]) if m.get(\"type\") in (\"ntfy_received\",\"wake_up\")]
  if ids: print(\",\".join(\"\\\"\"+i+\"\\\"\" for i in ids))
except: pass
" 2>/dev/null)
if [ -n "$unread_ids" ]; then
    curl -s -m 2 -X POST "http://localhost:8770/api/inbox_mark_read" \
        -H "Content-Type: application/json" \
        -d "{\"agent\":\"shogun\",\"ids\":[$unread_ids]}" >/dev/null 2>&1
fi
' 2>/dev/null

# 殿発言ごとに shogun.yaml の ntfy_received 通知を自動既読化 (累積防止・仕組み化 2026-04-28殿命)
SHOGUN_YAML="$SCRIPT_DIR/queue/inbox/shogun.yaml"
if [ -f "$SHOGUN_YAML" ]; then
    timeout 3 python3 - "$SHOGUN_YAML" <<'PY' 2>/dev/null
import sys, yaml, datetime
path = sys.argv[1]
NOW = datetime.datetime.now().isoformat(timespec='seconds')
try:
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    items = data.get('messages', data.get('inbox', []))
    if not isinstance(items, list): sys.exit(0)
    key = 'messages' if 'messages' in data else 'inbox'
    updated = 0
    for m in items:
        if not isinstance(m, dict): continue
        # ntfy_received 通知のみ自動既読化 (他typeは手動処理保持)
        if m.get('type') == 'ntfy_received' and (m.get('read') in (False, 0, None)):
            m['read'] = True
            m['read_at'] = NOW
            m['actor'] = 'auto_userprompt_hook'
            updated += 1
    if updated > 0:
        data[key] = items
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
except Exception:
    sys.exit(0)
PY
fi

# ntfy_inbox.yaml の status:pending 確認 (殿のスマホ画像/メッセージ未処理検出)
NTFY_INBOX="$SCRIPT_DIR/queue/ntfy_inbox.yaml"
if [ -f "$NTFY_INBOX" ]; then
    PENDING_OUT=$(timeout 3 python3 - "$NTFY_INBOX" <<'PY' 2>/dev/null
import sys, yaml
path = sys.argv[1]
try:
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    items = data.get("inbox", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    pendings = [d for d in items if isinstance(d, dict) and d.get("status") == "pending"]
    if not pendings: sys.exit(0)
    print(f"【ntfy_inbox.yaml status:pending {len(pendings)}件 — 画像/メッセージ未処理あり】")
    for d in pendings[-5:]:
        ts = d.get("timestamp", "?")
        msg = (d.get("message") or "")[:40]
        img = d.get("image_path", "")
        if img:
            print(f"  📷 {ts} {img}")
        else:
            print(f"  💬 {ts} {msg}")
    print(f"対応: queue/ntfy_inbox.yaml の image_path を Read で目視 → 対応 → status: processed に更新")
except Exception as e:
    pass
PY
)
    if [ -n "$PENDING_OUT" ]; then
        echo ""
        echo "$PENDING_OUT"
    fi
fi

exit 0
