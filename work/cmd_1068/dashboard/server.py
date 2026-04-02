#!/usr/bin/env python3
"""MCP Dashboard Web UI - Port 8770
Reads SQLite + YAML files to display agent dashboard."""

import http.server
import json
import os
import re
import sqlite3
import yaml
from datetime import datetime

PORT = 8770
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "experiment.db")
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..")
TASKS_DIR = os.path.join(BASE_DIR, "queue", "tasks")
INBOX_DIR = os.path.join(BASE_DIR, "queue", "inbox")


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


def read_yaml_tasks():
    """Read agent task YAMLs for status."""
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
            # Find latest assigned task
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
                "description": (latest_assigned.get("description", "")[:100] if latest_assigned else ""),
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


def read_recent_messages():
    """Read recent messages from inbox YAMLs."""
    msgs = []
    if not os.path.isdir(INBOX_DIR):
        return msgs
    for fname in os.listdir(INBOX_DIR):
        if not fname.endswith(".yaml"):
            continue
        agent_id = fname.replace(".yaml", "")
        filepath = os.path.join(INBOX_DIR, agent_id + ".yaml")
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
            messages = data.get("messages", []) if data else []
            for m in messages[-5:]:  # last 5 per agent
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
    return msgs[:20]


def get_dashboard_data():
    conn = get_db()

    # SQLite messages
    db_messages = query_db(conn, "SELECT * FROM messages ORDER BY created_at DESC LIMIT 20")
    db_tasks = query_db(conn, "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 20")
    db_agents = query_db(conn, "SELECT * FROM agent_status ORDER BY agent_id ASC")
    db_reports = query_db(conn, "SELECT * FROM reports ORDER BY created_at DESC LIMIT 10")

    # Stats from SQLite
    stats_rows = query_db(conn, "SELECT COUNT(*) as c FROM messages")
    msg_count = stats_rows[0]["c"] if stats_rows else 0
    task_rows = query_db(conn, "SELECT COUNT(*) as c FROM tasks")
    task_count = task_rows[0]["c"] if task_rows else 0
    done_rows = query_db(conn, "SELECT COUNT(*) as c FROM tasks WHERE status='done'")
    done_count = done_rows[0]["c"] if done_rows else 0
    report_rows = query_db(conn, "SELECT COUNT(*) as c FROM reports")
    report_count = report_rows[0]["c"] if report_rows else 0

    conn.close()

    # YAML data
    yaml_agents = read_yaml_tasks()
    yaml_messages = read_recent_messages()

    # Merge: YAML agents take priority (they're always up-to-date)
    agent_map = {}
    for a in db_agents:
        agent_map[a["agent_id"]] = a
    for aid, a in yaml_agents.items():
        agent_map[aid] = {**agent_map.get(aid, {}), **a}

    # Merge messages: combine DB and YAML, dedupe by content+timestamp
    all_messages = []
    seen = set()
    for m in db_messages + yaml_messages:
        key = (m.get("content", "")[:50], m.get("timestamp", ""))
        if key not in seen:
            seen.add(key)
            all_messages.append(m)
    all_messages.sort(key=lambda x: x.get("timestamp", "") or x.get("created_at", ""), reverse=True)
    all_messages = all_messages[:30]

    return {
        "stats": {
            "message_count": msg_count + len(yaml_messages),
            "task_count": task_count,
            "done_count": done_count,
            "report_count": report_count,
            "yaml_agents": len(yaml_agents),
        },
        "agents": list(agent_map.values()),
        "tasks": db_tasks[:20],
        "messages": all_messages[:30],
        "reports": db_reports[:10],
        "timestamp": datetime.now().isoformat(),
    }


HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Shogun MCP Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'JetBrains Mono', 'Fira Code', monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }
h1 { color: #58a6ff; margin-bottom: 5px; font-size: 1.4em; }
.header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; border-bottom: 1px solid #21262d; padding-bottom: 10px; }
.header .ts { color: #8b949e; font-size: 0.85em; }
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
.stat-card { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 14px; text-align: center; }
.stat-card .num { font-size: 1.8em; color: #58a6ff; font-weight: bold; }
.stat-card .label { font-size: 0.75em; color: #8b949e; margin-top: 4px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.panel { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 16px; }
.panel h2 { color: #f0883e; font-size: 1em; margin-bottom: 12px; border-bottom: 1px solid #21262d; padding-bottom: 6px; }
.full { grid-column: 1 / -1; }
table { width: 100%; border-collapse: collapse; font-size: 0.82em; }
th { text-align: left; color: #8b949e; padding: 6px 8px; border-bottom: 1px solid #21262d; }
td { padding: 6px 8px; border-bottom: 1px solid #161b22; }
tr:hover { background: #1c2128; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: bold; }
.badge-busy { background: #da3633; color: #fff; }
.badge-idle { background: #238636; color: #fff; }
.badge-error { background: #d29922; color: #000; }
.badge-offline { background: #484f58; color: #fff; }
.badge-unread { background: #58a6ff; color: #000; }
.truncate { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.msg-to { color: #58a6ff; }
.msg-from { color: #f0883e; }
.msg-type { color: #8b949e; font-size: 0.75em; }
.empty { color: #484f58; font-style: italic; padding: 20px; text-align: center; }
@media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="header">
  <h1>Shogun MCP Dashboard</h1>
  <span class="ts" id="ts"></span>
</div>
<div class="stats-row" id="stats"></div>
<div class="grid">
  <div class="panel"><h2>Agent Status</h2><div id="agents"></div></div>
  <div class="panel"><h2>Recent Tasks (SQLite)</h2><div id="tasks"></div></div>
  <div class="panel full"><h2>Recent Messages</h2><div id="messages"></div></div>
</div>
<script>
const escapeHtml = (s) => s ? s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;') : '';

function renderStats(d) {
  const s = d.stats;
  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="num">${s.yaml_agents}</div><div class="label">Agents</div></div>
    <div class="stat-card"><div class="num">${s.message_count}</div><div class="label">Messages</div></div>
    <div class="stat-card"><div class="num">${s.task_count}</div><div class="label">Tasks</div></div>
    <div class="stat-card"><div class="num">${s.done_count}</div><div class="label">Completed</div></div>
    <div class="stat-card"><div class="num">${s.report_count}</div><div class="label">Reports</div></div>
  `;
}

function renderAgents(agents) {
  if (!agents || !agents.length) { document.getElementById('agents').innerHTML = '<div class="empty">No agents</div>'; return; }
  let html = '<table><tr><th>Agent</th><th>Status</th><th>Task</th><th>Done/Total</th></tr>';
  agents.sort((a,b) => (a.agent_id||'').localeCompare(b.agent_id||''));
  for (const a of agents) {
    const badge = `badge-${a.status||'offline'}`;
    const task = a.current_task || '-';
    html += `<tr>
      <td><strong>${escapeHtml(a.agent_id)}</strong></td>
      <td><span class="badge ${badge}">${escapeHtml(a.status)}</span></td>
      <td class="truncate" title="${escapeHtml(a.current_task||'')}">${escapeHtml(task)}</td>
      <td>${a.done_tasks||0}/${a.total_tasks||0}</td>
    </tr>`;
  }
  html += '</table>';
  document.getElementById('agents').innerHTML = html;
}

function renderTasks(tasks) {
  if (!tasks || !tasks.length) { document.getElementById('tasks').innerHTML = '<div class="empty">No tasks in SQLite</div>'; return; }
  let html = '<table><tr><th>ID</th><th>Assignee</th><th>Status</th><th>Updated</th></tr>';
  for (const t of tasks) {
    const badge = `badge-${t.status === 'done' ? 'idle' : t.status === 'failed' ? 'error' : 'busy'}`;
    html += `<tr>
      <td>${escapeHtml(t.task_id)}</td>
      <td>${escapeHtml(t.assignee)}</td>
      <td><span class="badge ${badge}">${escapeHtml(t.status)}</span></td>
      <td>${escapeHtml((t.updated_at||'').slice(0,16))}</td>
    </tr>`;
  }
  html += '</table>';
  document.getElementById('tasks').innerHTML = html;
}

function renderMessages(msgs) {
  if (!msgs || !msgs.length) { document.getElementById('messages').innerHTML = '<div class="empty">No messages</div>'; return; }
  let html = '<table><tr><th>Time</th><th>From</th><th>To</th><th>Type</th><th>Content</th></tr>';
  for (const m of msgs.slice(0, 20)) {
    const ts = (m.timestamp || m.created_at || '').slice(0, 16).replace('T', ' ');
    const readBadge = m.read ? '' : ' <span class="badge badge-unread">NEW</span>';
    html += `<tr>
      <td style="white-space:nowrap">${escapeHtml(ts)}</td>
      <td class="msg-from">${escapeHtml(m.from_agent || m.from)}</td>
      <td class="msg-to">${escapeHtml(m.to_agent || m.to)}</td>
      <td class="msg-type">${escapeHtml(m.type)}${readBadge}</td>
      <td class="truncate" style="max-width:500px" title="${escapeHtml(m.content||'')}">${escapeHtml((m.content||'').slice(0,120))}</td>
    </tr>`;
  }
  html += '</table>';
  document.getElementById('messages').innerHTML = html;
}

async function refresh() {
  try {
    const r = await fetch('/api/dashboard');
    const d = await r.json();
    document.getElementById('ts').textContent = 'Updated: ' + d.timestamp;
    renderStats(d);
    renderAgents(d.agents);
    renderTasks(d.tasks);
    renderMessages(d.messages);
  } catch(e) { console.error(e); }
}
refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/dashboard':
            data = get_dashboard_data()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[Dashboard] {args[0]}")


if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    print(f"MCP Dashboard running on http://0.0.0.0:{PORT}/")
    print(f"DB: {os.path.abspath(DB_PATH)}")
    print(f"Tasks: {TASKS_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
