#!/usr/bin/env bash
# stuck_subtask_check.sh — assigned タスクが30分以上停滞していれば家老に通達
# cron */5 * * * * で実行。dedup: 同task_idは1時間以内重複通達skip
set -euo pipefail

DB="/home/murakami/multi-agent-shogun/queue/cmds.db"
API="http://192.168.2.7:8770/api/inbox_write"
CACHE="/tmp/stuck_notified_cache.txt"
THRESHOLD_MINUTES=30
DEDUP_WINDOW=3600

touch "$CACHE"

now_epoch=$(date +%s)

# assigned タスクで timestamp が閾値以上前のものを抽出
sqlite3 "$DB" "SELECT task_id, agent, parent_cmd, timestamp FROM tasks WHERE status='assigned'" 2>/dev/null | while IFS="|" read -r task_id agent parent_cmd ts; do
    [[ -z "$task_id" ]] && continue

    # ISO8601 → epoch
    ts_epoch=$(date -d "$ts" +%s 2>/dev/null) || continue
    age_minutes=$(( (now_epoch - ts_epoch) / 60 ))

    if (( age_minutes < THRESHOLD_MINUTES )); then
        continue
    fi

    # dedup: cache 内に同task_id かつ DEDUP_WINDOW 以内の記録があれば skip
    notified=false
    if [[ -f "$CACHE" ]]; then
        while IFS=':' read -r cached_tid cached_epoch; do
            [[ -z "$cached_tid" ]] && continue
            if [[ "$cached_tid" == "$task_id" ]]; then
                if (( now_epoch - cached_epoch < DEDUP_WINDOW )); then
                    notified=true
                    break
                fi
            fi
        done < "$CACHE"
    fi
    if [[ "$notified" == "true" ]]; then
        continue
    fi

    # 通達
    msg="stuck検知: ${task_id} (agent=${agent}, age=${age_minutes}分, cmd=${parent_cmd})"
    curl -sf -X POST "$API" \
        -H 'Content-Type: application/json' \
        -d "{\"to\":\"karo\",\"from\":\"cron_stuck_check\",\"type\":\"wake_up\",\"message\":\"${msg}\"}" \
        > /dev/null 2>&1 || true

    # cache 記録
    echo "${task_id}:${now_epoch}" >> "$CACHE"
done

# cache 古いエントリ掃除 (24時間以上前)
if [[ -s "$CACHE" ]]; then
    tmp=$(mktemp)
    cutoff=$((now_epoch - 86400))
    while IFS=':' read -r cached_tid cached_epoch; do
        [[ -z "$cached_tid" ]] && continue
        if (( cached_epoch >= cutoff )); then
            echo "${cached_tid}:${cached_epoch}" >> "$tmp"
        fi
    done < "$CACHE"
    mv "$tmp" "$CACHE"
fi
