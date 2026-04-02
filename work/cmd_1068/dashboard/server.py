#!/usr/bin/env python3
"""MCP Dashboard Web UI v2 - Port 8770
DB-driven auto-detection: R1-R6 rules, no dashboard.md dependency."""

import http.server
import json
import os
import re
import sqlite3
import subprocess
import threading
import time
import yaml
from datetime import datetime, timezone, timedelta

PORT = 8770
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "experiment.db")
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
TASKS_DIR = os.path.join(BASE_DIR, "queue", "tasks")
INBOX_DIR = os.path.join(BASE_DIR, "queue", "inbox")
SHOGUN_TO_KARO = os.path.join(BASE_DIR, "queue", "shogun_to_karo.yaml")

# Status values that mean "done / no longer active"
DONE_STATUSES = {"done", "cancelled", "superseded", "done_ng"}
ACTIVE_STATUSES = {"pending", "assigned", "in_progress", "blocked"}

# Pane map for tmux @current_task
PANE_MAP = {
    "karo": "0.0", "ashigaru1": "0.1", "ashigaru2": "0.2",
    "ashigaru3": "0.3", "ashigaru4": "0.4", "ashigaru5": "0.5",
    "ashigaru6": "0.6", "ashigaru7": "0.7", "gunshi": "0.8",
}


# ─── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_db(conn, sql, params=()):
    try:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.OperationalError:
        return []


# ─── shogun_to_karo.yaml parser ────────────────────────────────────────────────

_stk_cache = {"mtime": 0, "data": []}


def _parse_stk_regex(text):
    """Fallback regex parser for shogun_to_karo.yaml when YAML parse fails."""
    cmds = []
    # Split on top-level list items (lines starting with "- id:")
    blocks = re.split(r'\n(?=- id: )', text)
    for block in blocks:
        if not block.strip().startswith("- id:"):
            continue
        cmd = {}
        # id
        m = re.search(r'^- id:\s*(.+)$', block, re.MULTILINE)
        if m:
            cmd["id"] = m.group(1).strip()
        # status
        m = re.search(r'^  status:\s*(.+)$', block, re.MULTILINE)
        if m:
            cmd["status"] = m.group(1).strip()
        # timestamp
        m = re.search(r"^  timestamp:\s*['\"]?(.+?)['\"]?$", block, re.MULTILINE)
        if m:
            cmd["timestamp"] = m.group(1).strip().strip("'\"")
        # purpose (first line only)
        m = re.search(r'^  purpose:\s*(.+)$', block, re.MULTILINE)
        if m:
            cmd["purpose"] = m.group(1).strip()
        # acceptance_criteria (simple list extraction)
        ac = re.findall(r'^  - (.+)$', block, re.MULTILINE)
        if ac:
            cmd["acceptance_criteria"] = ac
        if cmd.get("id"):
            cmds.append(cmd)
    return cmds


def parse_shogun_to_karo():
    global _stk_cache
    try:
        mtime = os.path.getmtime(SHOGUN_TO_KARO)
        if mtime == _stk_cache["mtime"] and _stk_cache["data"]:
            return _stk_cache["data"]
        with open(SHOGUN_TO_KARO) as f:
            text = f.read()
        try:
            raw = yaml.safe_load(text)
            cmds = raw.get("commands", []) if isinstance(raw, dict) else []
        except yaml.YAMLError:
            # Fallback: regex-based parsing
            cmds = _parse_stk_regex(text)
        _stk_cache = {"mtime": mtime, "data": cmds}
        return cmds
    except Exception:
        return []


def get_active_cmds():
    return [c for c in parse_shogun_to_karo()
            if c.get("status") not in DONE_STATUSES]


def get_recent_done(n=5):
    done = [c for c in parse_shogun_to_karo() if c.get("status") == "done"]
    done.sort(key=lambda c: c.get("timestamp", ""), reverse=True)
    return done[:n]


def parse_ts(ts_str):
    """Parse timestamp string to UTC datetime. Returns None on failure."""
    if not ts_str:
        return None
    try:
        # Handle +09:00 offset
        s = str(ts_str).strip()
        # Try ISO format
        if "+" in s[10:] or (s.endswith("Z")):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        elif "T" in s:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def age_hours(ts_str):
    """Hours since timestamp. Returns large number if unparseable."""
    dt = parse_ts(ts_str)
    if not dt:
        return 9999
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds() / 3600


# ─── Auto-detection rules R1-R6 ────────────────────────────────────────────────

def detect_action_required():
    items = []
    now = datetime.now(timezone.utc)

    # R1: cmd長期停滞 (active cmd > 24h)
    for cmd in get_active_cmds():
        h = age_hours(cmd.get("timestamp", ""))
        if h > 24:
            days = int(h // 24)
            items.append({
                "rule": "R1",
                "severity": "HIGH",
                "title": f"{cmd.get('id','?')} 停滞 ({days}日{int(h%24)}h)",
                "detail": (cmd.get("purpose", "") or "")[:120],
                "age_hours": h,
                "cmd_id": cmd.get("id"),
            })

    # R2: ブロック報告検出 (inbox YAML report_blocked / content keywords)
    block_keywords = ["ブロック", "blocked", "DBSC", "認証", "殿操作", "待ち", "失敗"]
    recent_msgs = read_recent_messages(hours=48)
    seen_r2 = set()
    for msg in recent_msgs:
        content = msg.get("content", "") or ""
        mtype = msg.get("type", "") or ""
        if mtype in ("report_blocked", "report_error") or any(kw in content for kw in block_keywords):
            key = content[:60]
            if key in seen_r2:
                continue
            seen_r2.add(key)
            items.append({
                "rule": "R2",
                "severity": "HIGH",
                "title": f"ブロック報告: {msg.get('from', '?')} → {msg.get('to', '?')}",
                "detail": content[:120],
                "age_hours": age_hours(msg.get("timestamp", "")),
                "cmd_id": None,
            })

    # R3: 殿選定待ちフラグ (acceptance_criteria contains keywords)
    selection_kws = ["殿", "選定", "レビュー", "承認", "確認待ち", "殿判断", "殿選択"]
    for cmd in get_active_cmds():
        criteria = cmd.get("acceptance_criteria", []) or []
        if isinstance(criteria, list):
            criteria_text = " ".join(str(c) for c in criteria)
        else:
            criteria_text = str(criteria)
        if any(kw in criteria_text for kw in selection_kws):
            items.append({
                "rule": "R3",
                "severity": "HIGH",
                "title": f"{cmd.get('id','?')} 殿選定待ち",
                "detail": (cmd.get("purpose", "") or "")[:120],
                "age_hours": age_hours(cmd.get("timestamp", "")),
                "cmd_id": cmd.get("id"),
            })

    # R4: 足軽長時間idle (has assigned task but idle > 2h)
    yaml_agents = read_yaml_tasks()
    for aid, a in yaml_agents.items():
        if aid in ("karo", "gunshi"):
            continue
        if a.get("status") == "idle":
            # Check if there's a recent assigned task in tasks YAML that should be running
            # (This is a simplified check - idle agent with assigned task)
            pass  # Will check tasks YAML for assigned status

    # R5: 未読メッセージ滞留 (unread inbox messages > 30min)
    if os.path.isdir(INBOX_DIR):
        for fname in os.listdir(INBOX_DIR):
            if not fname.endswith(".yaml"):
                continue
            agent_id = fname.replace(".yaml", "")
            filepath = os.path.join(INBOX_DIR, fname)
            try:
                with open(filepath) as f:
                    data = yaml.safe_load(f)
                messages = data.get("messages", []) if data else []
                for m in messages:
                    if m.get("read", True):
                        continue
                    h = age_hours(m.get("timestamp", ""))
                    if h > 0.5:  # 30min
                        items.append({
                            "rule": "R5",
                            "severity": "MEDIUM",
                            "title": f"未読メッセージ滞留: {agent_id} ({int(h*60)}分放置)",
                            "detail": (m.get("content", "") or "")[:120],
                            "age_hours": h,
                            "cmd_id": None,
                        })
            except Exception:
                pass

    # R6: タスク失敗 (failed status in tasks YAML)
    if os.path.isdir(TASKS_DIR):
        for fname in os.listdir(TASKS_DIR):
            if not fname.endswith(".yaml"):
                continue
            agent_id = fname.replace(".yaml", "")
            filepath = os.path.join(TASKS_DIR, fname)
            try:
                with open(filepath) as f:
                    data = yaml.safe_load(f)
                tasks = data.get("tasks", []) if data else []
                for t in tasks:
                    if t.get("status") == "failed":
                        items.append({
                            "rule": "R6",
                            "severity": "HIGH",
                            "title": f"タスク失敗: {t.get('task_id','?')} ({agent_id})",
                            "detail": (t.get("description", "") or "")[:120],
                            "age_hours": age_hours(t.get("timestamp", "")),
                            "cmd_id": t.get("parent_cmd"),
                        })
            except Exception:
                pass

    # Dedup: R1 and R3 for same cmd_id, prefer R3
    seen_cmds = set()
    deduped = []
    # Sort: HIGH first, then by age
    items.sort(key=lambda x: (
        0 if x.get("severity") == "HIGH" else 1,
        -(x.get("age_hours") or 0)
    ))
    for item in items:
        cmd_id = item.get("cmd_id")
        rule = item.get("rule")
        if cmd_id:
            key = (cmd_id, rule)
            # For R1 and R3 on the same cmd_id, skip R1 if R3 exists
            if cmd_id in seen_cmds and rule == "R1":
                continue
            seen_cmds.add(cmd_id)
        deduped.append(item)

    return deduped[:20]  # Cap at 20 items


# ─── YAML readers ───────────────────────────────────────────────────────────────

def read_yaml_tasks():
    agents = {}
    if not os.path.isdir(TASKS_DIR):
        return agents
    for fname in os.listdir(TASKS_DIR):
        if not fname.endswith(".yaml"):
            continue
        agent_id = fname.replace(".yaml", "")
        filepath = os.path.join(TASKS_DIR, fname)
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
            tasks = data.get("tasks", []) if data else []
            latest_assigned = None
            total = len(tasks)
            done = sum(1 for t in tasks if t.get("status") == "done")
            for t in reversed(tasks):
                if t.get("status") == "assigned":
                    latest_assigned = t
                    break
            agents[agent_id] = {
                "agent_id": agent_id,
                "status": "busy" if latest_assigned else "idle",
                "current_task": latest_assigned.get("task_id") if latest_assigned else None,
                "current_cmd": latest_assigned.get("parent_cmd") if latest_assigned else None,
                "description": (latest_assigned.get("description", "")[:80] if latest_assigned else ""),
                "total_tasks": total,
                "done_tasks": done,
            }
        except Exception:
            agents[agent_id] = {
                "agent_id": agent_id,
                "status": "error",
                "current_task": None,
                "current_cmd": None,
                "description": "YAML parse error",
                "total_tasks": 0,
                "done_tasks": 0,
            }
    return agents


def read_recent_messages(hours=48):
    msgs = []
    if not os.path.isdir(INBOX_DIR):
        return msgs
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    for fname in os.listdir(INBOX_DIR):
        if not fname.endswith(".yaml"):
            continue
        agent_id = fname.replace(".yaml", "")
        filepath = os.path.join(INBOX_DIR, fname)
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
            messages = data.get("messages", []) if data else []
            for m in messages[-10:]:
                ts = parse_ts(m.get("timestamp", ""))
                if ts and ts < cutoff:
                    continue
                msgs.append({
                    "to": agent_id,
                    "from": m.get("from", "?"),
                    "content": m.get("content", "")[:200],
                    "type": m.get("type", ""),
                    "timestamp": m.get("timestamp", ""),
                    "read": m.get("read", False),
                })
        except Exception:
            pass
    msgs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return msgs[:30]


def get_tmux_task(agent_id):
    pane = PANE_MAP.get(agent_id)
    if not pane:
        return None
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-t", f"multiagent:{pane}", "-p", "#{@current_task}"],
            capture_output=True, text=True, timeout=3
        )
        return result.stdout.strip() or None
    except Exception:
        return None


# ─── Agent status polling via tmux capture-pane ────────────────────────────────

# Cache: agent_id -> {"status": str, "updated_at": float}
_pane_status_cache: dict = {}
_pane_status_lock = threading.Lock()

# Agents to poll (exclude karo from auto-status since it's always managing)
POLL_AGENTS = [
    "ashigaru1", "ashigaru2", "ashigaru3", "ashigaru4",
    "ashigaru5", "ashigaru6", "ashigaru7", "gunshi",
]


def determine_status_from_pane(output: str) -> str:
    """Determine agent status from tmux capture-pane output using pattern matching only."""
    lines = output.splitlines()
    recent = lines[-30:] if len(lines) > 30 else lines

    # Scan from bottom to top
    for line in reversed(recent):
        stripped = line.strip()
        if not stripped:
            continue
        # Skip lines that are just the ❯ prompt (input cursor, always present)
        if stripped == '❯' or (stripped.startswith('❯') and len(stripped) <= 3):
            continue

        # ✻ = idle (Claude Code idle state indicator)
        if stripped.startswith('✻'):
            return 'idle'

        # ✢ · ● = busy (Claude Code spinner characters during processing)
        if any(stripped.startswith(c) for c in ('✢', '·', '●')):
            return 'busy'

        # Text patterns indicating busy
        lower = stripped.lower()
        if any(kw in lower for kw in ('running', 'thinking', 'thought for', 'running hooks')):
            return 'busy'

        # Error patterns
        if any(kw in stripped for kw in ('ERROR', 'FAIL', 'Error:', 'Failed')):
            return 'error'

        # Blocked patterns
        if any(kw in stripped for kw in ('ブロック', 'blocked', 'BLOCKED')):
            return 'blocked'

    return 'unknown'


def capture_pane_status(agent_id: str) -> str:
    """Run tmux capture-pane for the given agent and return detected status."""
    pane = PANE_MAP.get(agent_id)
    if not pane:
        return 'unknown'
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", f"multiagent:{pane}", "-p", "-S", "-30"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return 'unknown'
        return determine_status_from_pane(result.stdout)
    except Exception:
        return 'unknown'


def poll_all_pane_statuses():
    """Poll all agent panes and update the cache."""
    new_cache = {}
    for agent_id in POLL_AGENTS:
        status = capture_pane_status(agent_id)
        new_cache[agent_id] = {"status": status, "updated_at": time.time()}
    with _pane_status_lock:
        _pane_status_cache.update(new_cache)


def _poller_loop():
    """Background thread: poll every 10 seconds."""
    while True:
        try:
            poll_all_pane_statuses()
        except Exception:
            pass
        time.sleep(10)


def start_status_poller():
    """Start the background pane-status polling thread."""
    # Initial poll so cache is populated immediately
    try:
        poll_all_pane_statuses()
    except Exception:
        pass
    t = threading.Thread(target=_poller_loop, daemon=True)
    t.start()


def get_cached_pane_status(agent_id: str):
    """Return cached pane status for agent, or None if not available."""
    with _pane_status_lock:
        entry = _pane_status_cache.get(agent_id)
    if entry is None:
        return None
    # Expire cache after 30 seconds to avoid stale data
    if time.time() - entry["updated_at"] > 30:
        return None
    return entry["status"]


# ─── Dashboard data aggregation ────────────────────────────────────────────────

def get_dashboard_data():
    conn = get_db()

    # SQLite messages (Phase 4 DB)
    db_messages = query_db(conn, "SELECT * FROM messages ORDER BY created_at DESC LIMIT 20")
    db_msg_count = query_db(conn, "SELECT COUNT(*) as c FROM messages")
    msg_count_db = db_msg_count[0]["c"] if db_msg_count else 0

    conn.close()

    # YAML data
    yaml_agents = read_yaml_tasks()
    yaml_messages = read_recent_messages(hours=24)

    # Agent map (YAML primary)
    agent_map = {}
    for aid, a in yaml_agents.items():
        agent_map[aid] = a

    # Add tmux @current_task to agent info, and override status with pane-detected status
    for aid, a in agent_map.items():
        tmux_task = get_tmux_task(aid)
        if tmux_task:
            a["tmux_task"] = tmux_task
        # Override status with real-time pane status (pattern matching, not YAML)
        pane_status = get_cached_pane_status(aid)
        if pane_status and pane_status != 'unknown':
            a["status"] = pane_status

    # Active cmds
    active_cmds = get_active_cmds()
    recent_done = get_recent_done(5)

    # 🚨 Auto-detect action required
    action_required = detect_action_required()

    # Merge messages
    all_messages = []
    seen = set()
    for m in db_messages + yaml_messages:
        key = (m.get("content", "")[:50], m.get("timestamp", "") or m.get("created_at", ""))
        if key not in seen:
            seen.add(key)
            all_messages.append(m)
    all_messages.sort(key=lambda x: x.get("timestamp", "") or x.get("created_at", ""), reverse=True)
    all_messages = all_messages[:30]

    # Stats
    busy_agents = sum(1 for a in agent_map.values() if a.get("status") == "busy")
    idle_agents = sum(1 for a in agent_map.values() if a.get("status") == "idle")
    total_done = sum(a.get("done_tasks", 0) for a in agent_map.values())

    return {
        "stats": {
            "action_required_count": len(action_required),
            "busy_agents": busy_agents,
            "idle_agents": idle_agents,
            "active_cmds": len(active_cmds),
            "db_messages": msg_count_db,
            "total_done": total_done,
        },
        "action_required": action_required,
        "agents": list(agent_map.values()),
        "active_cmds": [
            {
                "id": c.get("id"),
                "status": c.get("status"),
                "purpose": (c.get("purpose", "") or "")[:120],
                "timestamp": c.get("timestamp", ""),
                "age_hours": round(age_hours(c.get("timestamp", "")), 1),
            }
            for c in active_cmds[:15]
        ],
        "recent_done": [
            {
                "id": c.get("id"),
                "purpose": (c.get("purpose", "") or "")[:100],
                "timestamp": c.get("timestamp", ""),
            }
            for c in recent_done
        ],
        "messages": all_messages[:30],
        "timestamp": datetime.now().isoformat(),
    }


# ─── HTML ───────────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚔️ 戦況ダッシュボード</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; background: #0d1117; color: #c9d1d9; padding: 16px; }
h1 { color: #58a6ff; font-size: 1.3em; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid #21262d; padding-bottom: 10px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.ts { color: #8b949e; font-size: 0.82em; }
button { background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 0.82em; font-family: inherit; }
button:hover { background: #30363d; }

/* Stats */
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 16px; }
.stat-card { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 12px; text-align: center; }
.stat-card .num { font-size: 1.6em; font-weight: bold; }
.stat-card .label { font-size: 0.72em; color: #8b949e; margin-top: 3px; }
.num-danger { color: #f85149; }
.num-ok { color: #3fb950; }
.num-info { color: #58a6ff; }
.num-warn { color: #d29922; }

/* 🚨 Action Required */
.action-panel { background: #161b22; border: 1px solid #f85149; border-radius: 8px; padding: 14px; margin-bottom: 16px; }
.action-panel h2 { color: #f85149; font-size: 1em; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
.action-panel h2 .count { background: #f85149; color: #fff; border-radius: 12px; padding: 1px 8px; font-size: 0.8em; }
.action-item { border: 1px solid #30363d; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; background: #0d1117; }
.action-item:last-child { margin-bottom: 0; }
.action-item.high { border-left: 3px solid #f85149; }
.action-item.medium { border-left: 3px solid #d29922; }
.action-item .rule-badge { display: inline-block; background: #21262d; color: #8b949e; border-radius: 4px; padding: 1px 6px; font-size: 0.72em; margin-right: 6px; }
.action-item .title { font-weight: bold; font-size: 0.9em; }
.action-item .detail { color: #8b949e; font-size: 0.78em; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.action-empty { color: #3fb950; text-align: center; padding: 16px; font-size: 0.85em; }

/* Main grid */
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px; }
.panel { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 14px; }
.panel h2 { color: #f0883e; font-size: 0.95em; margin-bottom: 10px; border-bottom: 1px solid #21262d; padding-bottom: 6px; }
.full { grid-column: 1 / -1; }

table { width: 100%; border-collapse: collapse; font-size: 0.8em; }
th { text-align: left; color: #8b949e; padding: 5px 8px; border-bottom: 1px solid #21262d; white-space: nowrap; }
td { padding: 5px 8px; border-bottom: 1px solid #0d1117; vertical-align: top; }
tr:hover td { background: #1c2128; }
.truncate { max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.badge { display: inline-block; padding: 1px 7px; border-radius: 10px; font-size: 0.72em; font-weight: bold; white-space: nowrap; }
.badge-busy { background: #da3633; color: #fff; }
.badge-idle { background: #238636; color: #fff; }
.badge-error { background: #d29922; color: #000; }
.badge-offline { background: #484f58; color: #fff; }
.badge-unread { background: #58a6ff; color: #000; }
.badge-pending { background: #21262d; color: #8b949e; border: 1px solid #30363d; }
.badge-in_progress { background: #1f6feb; color: #fff; }
.badge-assigned { background: #388bfd; color: #fff; }
.badge-blocked { background: #da3633; color: #fff; }
.badge-done_ng { background: #d29922; color: #000; }

.age-warn { color: #d29922; }
.age-danger { color: #f85149; }
.msg-from { color: #f0883e; }
.msg-to { color: #58a6ff; }
.empty { color: #484f58; font-style: italic; padding: 16px; text-align: center; font-size: 0.82em; }

@media (max-width: 768px) { .grid2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="header">
  <h1>⚔️ 戦況ダッシュボード</h1>
  <div class="header-right">
    <span class="ts" id="ts">—</span>
    <button onclick="refresh()">🔄 更新</button>
  </div>
</div>

<div class="stats-row" id="stats"></div>

<div class="action-panel" id="action-panel">
  <h2>🚨 要対応（自動検出）<span class="count" id="action-count">0</span></h2>
  <div id="action-items"><div class="action-empty">✅ 要対応なし</div></div>
</div>

<div class="grid2">
  <div class="panel"><h2>🏯 足軽・軍師 状態</h2><div id="agents"></div></div>
  <div class="panel"><h2>📋 進行中 cmd</h2><div id="active-cmds"></div></div>
  <div class="panel full"><h2>✅ 最近の完了 + 📨 最新メッセージ</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div><div style="font-size:0.8em;color:#8b949e;margin-bottom:6px">最近の完了（直近5件）</div><div id="recent-done"></div></div>
      <div><div style="font-size:0.8em;color:#8b949e;margin-bottom:6px">最新メッセージ</div><div id="messages"></div></div>
    </div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
const esc = s => s ? String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;') : '';

function ageBadge(h) {
  if (!h && h !== 0) return '';
  if (h > 48) return `<span class="age-danger">${Math.round(h/24)}d</span>`;
  if (h > 24) return `<span class="age-danger">${Math.round(h)}h</span>`;
  if (h > 4) return `<span class="age-warn">${Math.round(h)}h</span>`;
  return `<span style="color:#8b949e">${Math.round(h)}h</span>`;
}

function renderStats(s) {
  $('stats').innerHTML = `
    <div class="stat-card"><div class="num ${s.action_required_count > 0 ? 'num-danger' : 'num-ok'}">${s.action_required_count}</div><div class="label">🚨 要対応</div></div>
    <div class="stat-card"><div class="num num-info">${s.busy_agents}</div><div class="label">⚙️ 稼働中</div></div>
    <div class="stat-card"><div class="num num-ok">${s.idle_agents}</div><div class="label">💤 空き</div></div>
    <div class="stat-card"><div class="num num-warn">${s.active_cmds}</div><div class="label">📋 進行中cmd</div></div>
    <div class="stat-card"><div class="num num-ok">${s.total_done}</div><div class="label">✅ 完了タスク</div></div>
    <div class="stat-card"><div class="num num-info">${s.db_messages}</div><div class="label">💬 DB通算</div></div>
  `;
}

function renderActionRequired(items) {
  const count = items ? items.length : 0;
  $('action-count').textContent = count;
  const panel = document.getElementById('action-panel');
  panel.style.borderColor = count > 0 ? '#f85149' : '#238636';

  if (!count) {
    $('action-items').innerHTML = '<div class="action-empty">✅ 要対応なし — システム正常</div>';
    return;
  }
  let html = '';
  for (const item of items) {
    const sev = (item.severity || 'MEDIUM').toLowerCase();
    html += `<div class="action-item ${sev}">
      <span class="rule-badge">${esc(item.rule)}</span>
      <span class="title">${esc(item.title)}</span>
      <span style="float:right;font-size:0.75em;color:#8b949e">${ageBadge(item.age_hours)}</span>
      ${item.detail ? `<div class="detail">${esc(item.detail)}</div>` : ''}
    </div>`;
  }
  $('action-items').innerHTML = html;
}

function renderAgents(agents) {
  if (!agents || !agents.length) { $('agents').innerHTML = '<div class="empty">No agents</div>'; return; }
  let html = '<table><tr><th>エージェント</th><th>状態</th><th>タスク</th><th>完/計</th></tr>';
  agents.sort((a,b) => {
    const order = ['karo','ashigaru1','ashigaru2','ashigaru3','ashigaru4','ashigaru5','ashigaru6','ashigaru7','gunshi'];
    return order.indexOf(a.agent_id) - order.indexOf(b.agent_id);
  });
  for (const a of agents) {
    const badge = `badge-${a.status || 'offline'}`;
    const task = a.current_task || a.tmux_task || '—';
    html += `<tr>
      <td><strong>${esc(a.agent_id)}</strong></td>
      <td><span class="badge ${badge}">${esc(a.status || 'offline')}</span></td>
      <td class="truncate" title="${esc(a.description || a.current_task || '')}">${esc(task)}</td>
      <td style="white-space:nowrap">${a.done_tasks || 0}/${a.total_tasks || 0}</td>
    </tr>`;
  }
  html += '</table>';
  $('agents').innerHTML = html;
}

function renderActiveCmds(cmds) {
  if (!cmds || !cmds.length) { $('active-cmds').innerHTML = '<div class="empty">進行中cmdなし</div>'; return; }
  let html = '<table><tr><th>ID</th><th>状態</th><th>経過</th><th>目的</th></tr>';
  for (const c of cmds) {
    const badge = `badge-${c.status || 'pending'}`;
    html += `<tr>
      <td style="white-space:nowrap"><strong>${esc(c.id)}</strong></td>
      <td><span class="badge ${badge}">${esc(c.status)}</span></td>
      <td style="white-space:nowrap">${ageBadge(c.age_hours)}</td>
      <td class="truncate" style="max-width:200px" title="${esc(c.purpose)}">${esc(c.purpose)}</td>
    </tr>`;
  }
  html += '</table>';
  $('active-cmds').innerHTML = html;
}

function renderRecentDone(done) {
  if (!done || !done.length) { $('recent-done').innerHTML = '<div class="empty">なし</div>'; return; }
  let html = '<table><tr><th>ID</th><th>目的</th></tr>';
  for (const c of done) {
    const ts = (c.timestamp || '').slice(5, 16).replace('T', ' ');
    html += `<tr>
      <td style="white-space:nowrap"><span style="color:#3fb950">${esc(c.id)}</span><br><span style="color:#8b949e;font-size:0.72em">${esc(ts)}</span></td>
      <td class="truncate" style="max-width:250px" title="${esc(c.purpose)}">${esc(c.purpose)}</td>
    </tr>`;
  }
  html += '</table>';
  $('recent-done').innerHTML = html;
}

function renderMessages(msgs) {
  if (!msgs || !msgs.length) { $('messages').innerHTML = '<div class="empty">なし</div>'; return; }
  let html = '<table><tr><th>時刻</th><th>From→To</th><th>内容</th></tr>';
  for (const m of msgs.slice(0, 15)) {
    const ts = (m.timestamp || m.created_at || '').slice(5, 16).replace('T', ' ');
    const readBadge = m.read ? '' : ' <span class="badge badge-unread">NEW</span>';
    html += `<tr>
      <td style="white-space:nowrap;font-size:0.75em">${esc(ts)}</td>
      <td style="white-space:nowrap"><span class="msg-from">${esc(m.from_agent || m.from)}</span><br><span class="msg-to">${esc(m.to_agent || m.to)}</span></td>
      <td class="truncate" style="max-width:300px" title="${esc(m.content||'')}">${esc((m.content||'').slice(0,100))}${readBadge}</td>
    </tr>`;
  }
  html += '</table>';
  $('messages').innerHTML = html;
}

async function refresh() {
  try {
    const r = await fetch('/api/dashboard');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    const now = new Date(d.timestamp);
    $('ts').textContent = '最終更新: ' + now.toLocaleTimeString('ja-JP');
    renderStats(d.stats);
    renderActionRequired(d.action_required);
    renderAgents(d.agents);
    renderActiveCmds(d.active_cmds);
    renderRecentDone(d.recent_done);
    renderMessages(d.messages);
  } catch(e) {
    $('ts').textContent = '⚠️ 取得失敗: ' + e.message;
    console.error(e);
  }
}

refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""


# ─── HTTP Handler ───────────────────────────────────────────────────────────────

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/dashboard':
            try:
                data = get_dashboard_data()
                body = json.dumps(data, default=str).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        elif self.path in ('/', '/index.html'):
            body = HTML.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[Dashboard] {args[0]}")


if __name__ == '__main__':
    print(f"MCP Dashboard v2 starting on http://0.0.0.0:{PORT}/")
    print(f"DB: {os.path.abspath(DB_PATH)}")
    print(f"Tasks: {TASKS_DIR}")
    print(f"shogun_to_karo: {SHOGUN_TO_KARO}")
    print("Starting agent status poller (10s interval, tmux capture-pane)...")
    start_status_poller()
    server = http.server.HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
