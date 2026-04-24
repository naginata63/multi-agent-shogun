#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# silent_fail_watcher.sh — ログ内 ERROR/WARN/FALLBACK/COST/BILLING を即検知し ntfy 通知
# Usage: bash scripts/silent_fail_watcher.sh
#
# 設計思想 (cmd_1443_p04 H4):
#   - Gemini 22K円課金事故型 silent fail を即時検知し殿へ ntfy
#   - inotifywait でログ追記検知 → 位置管理で追記分のみ grep → level 判定
#   - ERROR/COST/BILLING → 即時 ntfy (60s dedup)
#   - WARN/FALLBACK → バッファ → 300s 集約 ntfy
#
# 監視対象 (*.log のみ):
#   - /home/murakami/multi-agent-shogun/logs/*.log (logs/daily/ 除外)
#   - /home/murakami/multi-agent-shogun/projects/*/logs/*.log
#
# 自己フィードバック防止 (除外):
#   - logs/silent_fail_watcher.log (自分)
#   - queue/ntfy_sent.log (ntfy 出力ログ)
#   - logs/daily/*.md (ntfy 日報)
#   - *_backup.log / *_test.log
# ═══════════════════════════════════════════════════════════════

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/silent_fail_watcher.log"
PID_FILE="$SCRIPT_DIR/logs/silent_fail_watcher.pid"
STATE_DIR="$SCRIPT_DIR/queue/.flags/silent_fail"
DEDUP_DIR="$STATE_DIR/dedup"
WARN_BUFFER="$STATE_DIR/warn_buffer.log"
OFFSET_DIR="$STATE_DIR/offsets"

mkdir -p "$DEDUP_DIR" "$OFFSET_DIR" "$(dirname "$LOG_FILE")"
: > "$WARN_BUFFER" 2>/dev/null || true

# PID 記録・二重起動防止
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[$(date)] silent_fail_watcher already running (pid=$OLD_PID)" >> "$LOG_FILE"
        exit 0
    fi
fi
echo $$ > "$PID_FILE"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

log "silent_fail_watcher starting (pid=$$)"

# ── 設定 ──
DEDUP_WINDOW_SEC="${DEDUP_WINDOW_SEC:-60}"
WARN_FLUSH_SEC="${WARN_FLUSH_SEC:-300}"
ERROR_REGEX='(^|[^A-Za-z])(ERROR|Error|error|FAIL|Fail|fail|FATAL|Fatal|CRITICAL|Critical|COST|Cost|BILLING|Billing|billing)([^A-Za-z]|$)'
WARN_REGEX='(^|[^A-Za-z])(WARN|Warn|warn|WARNING|Warning|FALLBACK|Fallback|fallback)([^A-Za-z]|$)'
# COST/BILLING は ERROR 扱い (最優先即通知)

# ── 除外パターン ──
# 自己フィードバックループ防止: silent_fail_watcher 自体のログと ntfy 出力系を除外。
# 殿判断: 広すぎる除外 (例: *_test.log) は正規ログ取りこぼしの恐れがあるので追加しない。
is_excluded() {
    local f="$1"
    case "$f" in
        */silent_fail_watcher.log) return 0 ;;
        */silent_fail_watcher_stdout.log) return 0 ;;
        */silent_fail_watcher_stderr.log) return 0 ;;
        */ntfy_sent.log) return 0 ;;
        */logs/daily/*) return 0 ;;
        *)  return 1 ;;
    esac
}

# ── 行レベル除外パターン (cmd_1451 + cmd_1457 noise 一掃) ──
# 以下の行は ERROR/WARN に分類されても通知対象外 (self-healing / 既知 false-positive):
#   - inbox_watcher*.log "nudge text still visible" → retry 機構が正常動作中 (1-2 attempt で収束)
#   - semantic_update.log "[quota] batch N hit 429" → 60s backoff で self-healing 中
#   - semantic_update.log "WARN: .../gunshi.yaml: while parsing ..." → YAML 修正後消えるが再発保険
#   - advisor_proxy*.log "Advisor context" → advisor呼出時のcontextダンプ(INFO)
#   - advisor_proxy*.log "Advisor response" → advisor応答本文(INFO)
#   - advisor_proxy*.log "[System prompt excerpt]" → system prompt断片(INFO)
#   - advisor_proxy*.log "x-anthropic-billing-header" → billing header(INFO)
# cmd_1448 scope (C01-C10 = cron_health_check.log 内の embedding 404 / rsync code 23 等) は除外しない
is_noise_line() {
    local line="$1"
    case "$line" in
        *"nudge text still visible"*) return 0 ;;
        *"[quota] batch "*"hit 429 quota"*) return 0 ;;
        *"while parsing a block mapping"*) return 0 ;;
        *"expected <block end>, but found <block sequence start>"*) return 0 ;;
        *"Advisor context"*) return 0 ;;
        *"Advisor response"*) return 0 ;;
        *"[System prompt excerpt]"*) return 0 ;;
        *"x-anthropic-billing-header"*) return 0 ;;
        *) return 1 ;;
    esac
}

# ── 監視対象ディレクトリ列挙 ──
# 監視対象 (タスク YAML 仕様 3ディレクトリ):
#   (1) logs/ (ルート)
#   (2) work/ + work/*/ (cmd_* サブディレクトリ含む・*.log のみ処理)
#   (3) projects/*/logs/
enum_watch_dirs() {
    # (1) ルート logs/
    echo "$SCRIPT_DIR/logs"
    # (2) work/ 本体 + 直下サブディレクトリ (再帰なし・*.log 処理のみ)
    if [ -d "$SCRIPT_DIR/work" ]; then
        echo "$SCRIPT_DIR/work"
        while IFS= read -r -d '' d; do
            echo "$d"
        done < <(find "$SCRIPT_DIR/work" -maxdepth 1 -mindepth 1 -type d -print0 2>/dev/null)
    fi
    # (3) projects/*/logs/
    while IFS= read -r -d '' d; do
        echo "$d"
    done < <(find "$SCRIPT_DIR/projects" -maxdepth 2 -type d -name logs -print0 2>/dev/null)
}

# ── オフセットファイル ──
offset_file_for() {
    local path="$1"
    local key
    key=$(echo -n "$path" | md5sum | cut -d' ' -f1)
    echo "$OFFSET_DIR/$key"
}

# ── 起動時: 既存ログは末尾 (現在のサイズ) に初期化して既存内容を flood 防止 ──
init_offsets() {
    local count=0
    local watch_dir logfile size
    while IFS= read -r watch_dir; do
        [ -d "$watch_dir" ] || continue
        while IFS= read -r -d '' logfile; do
            is_excluded "$logfile" && continue
            [ -f "$logfile" ] || continue
            size=$(stat -c '%s' "$logfile" 2>/dev/null || echo 0)
            echo "$size" > "$(offset_file_for "$logfile")"
            count=$((count + 1))
        done < <(find "$watch_dir" -maxdepth 1 -type f -name '*.log' -print0 2>/dev/null)
    done < <(enum_watch_dirs)
    log "initialized offsets for $count log files"
}

# ── dedup: 同一ライン 60s 以内は 1 回だけ通知 ──
should_notify() {
    local line="$1"
    local key
    key=$(echo -n "$line" | md5sum | cut -d' ' -f1)
    local state_file="$DEDUP_DIR/$key"
    local now
    now=$(date +%s)
    if [ -f "$state_file" ]; then
        local last
        last=$(cat "$state_file" 2>/dev/null || echo 0)
        if [ $((now - last)) -lt "$DEDUP_WINDOW_SEC" ]; then
            return 1
        fi
    fi
    echo "$now" > "$state_file"
    return 0
}

# ── dedup キャッシュ掃除 (5 分以上古いエントリ削除) ──
cleanup_dedup() {
    find "$DEDUP_DIR" -type f -mmin +5 -delete 2>/dev/null
}

# ── level 判定 ──
classify_line() {
    local line="$1"
    if echo "$line" | grep -qE "$ERROR_REGEX"; then
        echo "ERROR"
        return
    fi
    if echo "$line" | grep -qE "$WARN_REGEX"; then
        echo "WARN"
        return
    fi
    echo "NONE"
}

# ── 新規追記行を読む ──
read_new_lines() {
    local path="$1"
    local offset_file
    offset_file=$(offset_file_for "$path")
    local prev_offset=0
    [ -f "$offset_file" ] && prev_offset=$(cat "$offset_file" 2>/dev/null || echo 0)
    local cur_size
    cur_size=$(stat -c '%s' "$path" 2>/dev/null || echo 0)
    if [ "$cur_size" -lt "$prev_offset" ]; then
        # rotated / truncated → reset
        prev_offset=0
    fi
    if [ "$cur_size" -le "$prev_offset" ]; then
        return 0
    fi
    # 追記分のみ読む
    tail -c "+$((prev_offset + 1))" "$path" 2>/dev/null || true
    echo "$cur_size" > "$offset_file"
}

# ── ntfy 送信 (safe wrapper: 自己ログに書かない) ──
# SILENT_FAIL_DRY_RUN=1 で ntfy.sh を呼ばず log のみ (動作確認用)
notify_ntfy() {
    local msg="$1"
    if [ "${SILENT_FAIL_DRY_RUN:-0}" = "1" ]; then
        log "DRY_RUN ntfy: $msg"
        return 0
    fi
    bash "$SCRIPT_DIR/scripts/ntfy.sh" "$msg" 2>/dev/null || log "ntfy failed: $msg"
}

# ── WARN バッファ flush ──
flush_warn_buffer() {
    [ -s "$WARN_BUFFER" ] || return 0
    local count
    count=$(wc -l < "$WARN_BUFFER" 2>/dev/null || echo 0)
    [ "$count" -eq 0 ] && return 0
    local sample
    sample=$(head -3 "$WARN_BUFFER" | cut -c 1-120 | tr '\n' '|')
    notify_ntfy "⚠️ [silent_fail] WARN/FALLBACK ${count}件 直近5分: ${sample}"
    : > "$WARN_BUFFER"
    log "flushed $count warn entries"
}

# ── 1 行の処理 ──
process_line() {
    local source_file="$1"
    local line="$2"
    [ -z "$line" ] && return 0
    # cmd_1451: 行レベルの noise exclusion (self-healing / 既知 false-positive)
    is_noise_line "$line" && return 0
    local level
    level=$(classify_line "$line")
    case "$level" in
        ERROR)
            if should_notify "$line"; then
                local short
                short=$(echo "$line" | cut -c 1-200)
                notify_ntfy "🚨 [silent_fail] ERROR $(basename "$source_file"): $short"
                log "ERROR notified: $(basename "$source_file"): $short"
            fi
            ;;
        WARN)
            # WARN はバッファ蓄積のみ (dedup も軽め: 同一行は1回のみ保存)
            if should_notify "$line"; then
                local short
                short=$(echo "$line" | cut -c 1-200)
                echo "$(basename "$source_file"): $short" >> "$WARN_BUFFER"
            fi
            ;;
    esac
}

# ── ファイル変更イベント処理 ──
handle_file_event() {
    local path="$1"
    is_excluded "$path" && return 0
    case "$path" in
        *.log) ;;
        *)    return 0 ;;
    esac
    [ -f "$path" ] || return 0
    local new_content
    new_content=$(read_new_lines "$path")
    [ -z "$new_content" ] && return 0
    while IFS= read -r line; do
        process_line "$path" "$line"
    done <<< "$new_content"
}

# ── メインループ ──
# 設計: 別プロセスで warn_flusher を動かすと SIGTERM 時に sleep が
#       trap に先んじて block し、kill が効かない問題があるため、
#       main ループで read -t の timeout を使い定期 flush を実行する。
main() {
    init_offsets

    cleanup() {
        log "shutting down"
        [ -n "${INOTIFY_PID:-}" ] && kill "$INOTIFY_PID" 2>/dev/null || true
        flush_warn_buffer
        rm -f "$PID_FILE" "$STATE_DIR/inotify.fifo"
    }
    trap 'cleanup; exit 0' TERM INT
    trap 'cleanup' EXIT

    # 監視対象ディレクトリ列挙 (配列化)
    local watch_dirs=()
    local d
    while IFS= read -r d; do
        [ -d "$d" ] && watch_dirs+=("$d")
    done < <(enum_watch_dirs)
    log "watching dirs: ${watch_dirs[*]}"

    # inotifywait を FIFO 経由で起動 (pid 捕捉可能)
    local fifo="$STATE_DIR/inotify.fifo"
    rm -f "$fifo"
    mkfifo "$fifo"
    inotifywait -m -e modify,close_write,create,moved_to --format '%w %e %f' "${watch_dirs[@]}" >"$fifo" 2>>"$LOG_FILE" &
    INOTIFY_PID=$!
    log "inotifywait started (pid=$INOTIFY_PID)"

    # FIFO を fd 3 で開き read -t で timeout flush を実行
    exec 3<"$fifo"
    local last_flush
    last_flush=$(date +%s)

    while true; do
        local ev_line=""
        # read -t でタイムアウト付きで FIFO を読む
        # タイムアウト間隔は WARN_FLUSH_SEC を上限に設定 (最低 1 秒)
        local read_timeout="$WARN_FLUSH_SEC"
        [ "$read_timeout" -lt 1 ] && read_timeout=1
        if IFS= read -r -t "$read_timeout" -u 3 ev_line; then
            if [ -n "$ev_line" ]; then
                local ev_dir ev_file full_path
                ev_dir=$(echo "$ev_line" | awk '{print $1}')
                ev_file=$(echo "$ev_line" | awk '{for(i=3;i<=NF;i++) printf $i" "; print ""}' | sed 's/ $//')
                if [ -n "$ev_file" ]; then
                    full_path="${ev_dir}${ev_file}"
                    case "$full_path" in
                        *.log) handle_file_event "$full_path" ;;
                    esac
                fi
            fi
        fi
        # 定期 flush
        local now
        now=$(date +%s)
        if [ $((now - last_flush)) -ge "$WARN_FLUSH_SEC" ]; then
            flush_warn_buffer
            cleanup_dedup
            last_flush=$now
        fi
        # inotifywait が死んでいたら終了
        if ! kill -0 "$INOTIFY_PID" 2>/dev/null; then
            log "inotifywait died, exiting"
            return 1
        fi
    done
}

main "$@"
