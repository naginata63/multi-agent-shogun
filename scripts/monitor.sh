#!/usr/bin/env bash
# scripts/monitor.sh — Resource monitor (GPU/CPU/Memory)
# Usage: monitor.sh start | stop | status

set -euo pipefail

LOG_FILE="${MONITOR_LOG:-$(dirname "$0")/../logs/monitor.log}"
PID_FILE="${MONITOR_PID:-$(dirname "$0")/../logs/monitor.pid}"
INTERVAL=5
MAX_LOG_BYTES=$((100 * 1024 * 1024))  # 100MB

log_header() {
    echo -e "# timestamp\tgpu_util%\tgpu_vram_used_mb\tgpu_vram_total_mb\tcpu%\tmem_used_mb\tmem_total_mb\tgpu_procs"
}

collect_once() {
    local ts
    ts=$(date '+%Y-%m-%dT%H:%M:%S')

    # GPU stats via nvidia-smi
    local gpu_util gpu_vram_used gpu_vram_total gpu_procs
    if command -v nvidia-smi &>/dev/null; then
        read -r gpu_util gpu_vram_used gpu_vram_total < <(
            nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total \
                --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ' | tr ',' ' '
        )
        gpu_procs=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits 2>/dev/null | tr '\n' '|' | sed 's/|$//')
        gpu_procs="${gpu_procs:-none}"
    else
        gpu_util=N/A; gpu_vram_used=N/A; gpu_vram_total=N/A; gpu_procs=no_nvidia
    fi

    # CPU usage (1-second sample)
    local cpu_pct
    cpu_pct=$(top -bn1 | grep '^%Cpu' | awk '{print 100 - $8}' 2>/dev/null || echo N/A)

    # Memory (MB)
    local mem_used mem_total
    read -r mem_total mem_used < <(free -m | awk '/^Mem:/{print $2, $3}')

    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
        "$ts" "$gpu_util" "$gpu_vram_used" "$gpu_vram_total" \
        "$cpu_pct" "$mem_used" "$mem_total" "$gpu_procs"
}

rotate_log() {
    if [[ -f "$LOG_FILE" ]]; then
        local size
        size=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if (( size > MAX_LOG_BYTES )); then
            mv "$LOG_FILE" "${LOG_FILE}.bak"
            log_header > "$LOG_FILE"
        fi
    fi
}

monitor_loop() {
    mkdir -p "$(dirname "$LOG_FILE")"
    if [[ ! -f "$LOG_FILE" ]]; then
        log_header > "$LOG_FILE"
    fi
    while true; do
        rotate_log
        collect_once >> "$LOG_FILE"
        sleep "$INTERVAL"
    done
}

cmd_start() {
    if [[ -f "$PID_FILE" ]]; then
        local old_pid
        old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "already running (PID $old_pid)"
            exit 0
        fi
    fi
    monitor_loop &
    echo $! > "$PID_FILE"
    echo "monitor started (PID $!), log: $LOG_FILE"
}

cmd_stop() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "not running"
        exit 0
    fi
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        rm -f "$PID_FILE"
        echo "monitor stopped (PID $pid)"
    else
        echo "process $pid not found, cleaning up PID file"
        rm -f "$PID_FILE"
    fi
}

cmd_status() {
    collect_once | awk -F'\t' '{
        printf "timestamp:    %s\n", $1
        printf "gpu_util:     %s%%\n", $2
        printf "gpu_vram:     %s / %s MB\n", $3, $4
        printf "cpu:          %s%%\n", $5
        printf "memory:       %s / %s MB\n", $6, $7
        printf "gpu_procs:    %s\n", $8
    }'
}

case "${1:-}" in
    start)  cmd_start ;;
    stop)   cmd_stop ;;
    status) cmd_status ;;
    *)
        echo "Usage: $0 start|stop|status"
        exit 1
        ;;
esac
