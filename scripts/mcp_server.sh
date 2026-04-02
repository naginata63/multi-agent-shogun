#!/usr/bin/env bash
# MCP Server startup/stop script (Phase 3 production)
# Usage: bash scripts/mcp_server.sh start|stop|status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_DIR="$SCRIPT_DIR/work/cmd_1068/mcp-server"
PIDFILE="$SCRIPT_DIR/work/cmd_1068/mcp-server.pid"
LOGFILE="$SCRIPT_DIR/logs/mcp_server.log"

mkdir -p "$SCRIPT_DIR/logs"

case "${1:-status}" in
    start)
        if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
            echo "MCP server already running (PID $(cat "$PIDFILE"))"
            exit 0
        fi
        echo "Starting MCP server..."
        cd "$MCP_DIR"
        nohup node build/index.js >> "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
        sleep 1
        if kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
            echo "MCP server started (PID $(cat "$PIDFILE"))"
        else
            echo "ERROR: MCP server failed to start. Check $LOGFILE"
            rm -f "$PIDFILE"
            exit 1
        fi
        ;;
    stop)
        if [ -f "$PIDFILE" ]; then
            PID=$(cat "$PIDFILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                echo "MCP server stopped (PID $PID)"
            fi
            rm -f "$PIDFILE"
        else
            echo "MCP server not running (no PID file)"
        fi
        ;;
    status)
        if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
            echo "MCP server running (PID $(cat "$PIDFILE"))"
        else
            echo "MCP server not running"
            rm -f "$PIDFILE" 2>/dev/null
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
