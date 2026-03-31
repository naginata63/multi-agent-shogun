#!/usr/bin/env bash
# Full reset helper for hung shutsujin environment.
# Usage:
#   bash scripts/reset_shutsujin.sh
#   bash scripts/reset_shutsujin.sh --keep-state
#   bash scripts/reset_shutsujin.sh --no-restart

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

RESTART=true
CLEAN_START=true

usage() {
    cat <<'EOF'
Usage: scripts/reset_shutsujin.sh [options]

Options:
  --keep-state   Restart without queue/dashboard reset (equivalent to shutsujin_departure.sh)
  --no-restart   Stop/cleanup only (do not relaunch shutsujin)
  -h, --help     Show this help
EOF
}

log() {
    printf '[reset] %s\n' "$1"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep-state)
            CLEAN_START=false
            shift
            ;;
        --no-restart)
            RESTART=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n\n' "$1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

log "Stopping watcher/listener processes..."
pkill -f "scripts/inbox_watcher.sh" 2>/dev/null || true
pkill -f "scripts/watcher_supervisor.sh" 2>/dev/null || true
pkill -f "scripts/ntfy_listener.sh" 2>/dev/null || true
pkill -f "inotifywait.*queue/inbox" 2>/dev/null || true
pkill -f "fswatch.*queue/inbox" 2>/dev/null || true

log "Killing tmux sessions..."
tmux kill-session -t multiagent 2>/dev/null || true
tmux kill-session -t shogun 2>/dev/null || true

log "Clearing stale runtime flags/locks..."
rm -f /tmp/shogun_idle_*
rm -f /tmp/agent_idle_*
rm -f "$SCRIPT_DIR/queue/.slim_yaml.lock"

if [[ "$RESTART" != true ]]; then
    log "Reset complete (no restart)."
    exit 0
fi

if [[ "$CLEAN_START" == true ]]; then
    log "Relaunching with clean state..."
    exec bash "$SCRIPT_DIR/shutsujin_departure.sh" --clean
fi

log "Relaunching with existing state..."
exec bash "$SCRIPT_DIR/shutsujin_departure.sh"
