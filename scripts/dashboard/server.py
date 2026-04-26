#!/usr/bin/env python3
"""MCP Dashboard Web UI v2 - Port 8770
DB-driven auto-detection: R1-R7 rules, R7 syncs dashboard.md 🚨要対応."""

import glob
import http.server
import json
import os
import re
import sqlite3
import subprocess
import threading
import uuid
import yaml
from datetime import datetime, timezone, timedelta

PORT = 8770
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_SCRIPT_DIR, "..", "..", "queue", "cmds.db")  # cmd_1488 dual-path 統一 (旧: data/dashboard.db 空)
BASE_DIR = os.path.join(_SCRIPT_DIR, "..", "..")
TASKS_DIR = os.path.join(BASE_DIR, "queue", "tasks")
INBOX_DIR = os.path.join(BASE_DIR, "queue", "inbox")
SHOGUN_TO_KARO = os.path.join(BASE_DIR, "queue", "shogun_to_karo.yaml")
DASHBOARD_MD = os.path.join(BASE_DIR, "dashboard.md")

# Status values that mean "done / no longer active"
DONE_STATUSES = {"done", "cancelled", "superseded", "done_ng"}
ACTIVE_STATUSES = {"pending", "assigned", "in_progress", "blocked"}
_EXCLUDED_AGENTS_R5 = {"pending", "archive"}

# ─── Async Job Tracking ─────────────────────────────────────────────────────
_jobs = {}
_jobs_lock = threading.Lock()

# ─── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
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
        # issued_at (newer cmds use this instead of timestamp)
        m = re.search(r"^  issued_at:\s*['\"]?(.+?)['\"]?$", block, re.MULTILINE)
        if m:
            cmd["issued_at"] = m.group(1).strip().strip("'\"")
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
    """Commands を SQLite から読む (cmd_1488 dual-path read source・cmd_1494 切替)。
    キャッシュは DB mtime で判定。SQLite 失敗時は空リストを返す。"""
    global _stk_cache
    try:
        mtime = os.path.getmtime(DB_PATH)
        if mtime == _stk_cache["mtime"] and _stk_cache["data"]:
            return _stk_cache["data"]
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            cmds = []
            for r in conn.execute("SELECT * FROM commands"):
                d = {k: v for k, v in dict(r).items() if v is not None}
                for k_json, k_clean in [
                    ('acceptance_criteria_json', 'acceptance_criteria'),
                    ('depends_on_json', 'depends_on'),
                    ('notes_json', 'notes'),
                ]:
                    if d.get(k_json):
                        try:
                            d[k_clean] = json.loads(d[k_json])
                        except Exception:
                            pass
                        d.pop(k_json, None)
                d.pop('full_yaml_blob', None)
                cmds.append(d)
        finally:
            conn.close()
        _stk_cache = {"mtime": mtime, "data": cmds}
        return cmds
    except Exception:
        return []


def get_active_cmds():
    return [c for c in parse_shogun_to_karo()
            if c.get("status") not in DONE_STATUSES]


def get_recent_done(n=5):
    done = [c for c in parse_shogun_to_karo() if c.get("status") == "done"]
    done.sort(key=lambda c: c.get("timestamp") or "", reverse=True)
    return done[:n]


_JST = timezone(timedelta(hours=9))


def parse_ts(ts_str):
    """Parse timestamp string to UTC datetime. Returns None on failure.
    Naive timestamps (no tz info) are assumed to be JST (UTC+9)."""
    if not ts_str:
        return None
    try:
        s = str(ts_str).strip()
        # Has explicit offset or Z
        if "+" in s[10:] or s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        elif "T" in s:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_JST)
        else:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_JST)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def age_hours(ts_str):
    """Hours since timestamp. Returns large number if unparseable.
    Negative values (future timestamps) are clamped to 0."""
    dt = parse_ts(ts_str)
    if not dt:
        return 9999
    now = datetime.now(timezone.utc)
    return max(0, (now - dt).total_seconds() / 3600)


# ─── Auto-detection rules R1-R6 ────────────────────────────────────────────────

def detect_action_required():
    items = []
    now = datetime.now(timezone.utc)

    # R1: cmd長期停滞 (active cmd > 24h)
    for cmd in get_active_cmds():
        h = age_hours(cmd.get("timestamp") or cmd.get("issued_at", ""))
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

    # R2: ブロック報告検出 (ashigaru*/gunshi messages only, not shogun/karo)
    block_keywords = ["ブロック", "blocked", "DBSC", "認証", "殿操作", "待ち", "失敗"]
    _R2_ALLOWED_FROM_PREFIX = ("ashigaru", "gunshi")
    _R2_UNBLOCK_TYPES = {"report_done", "report_completed", "unblock", "report_received"}
    recent_msgs = read_recent_messages(hours=48)

    # First pass: find which agents have resolved their blocks
    resolved_agents = set()
    for msg in recent_msgs:
        mfrom = msg.get("from", "") or ""
        mtype = msg.get("type", "") or ""
        if mfrom.startswith(_R2_ALLOWED_FROM_PREFIX) and mtype in _R2_UNBLOCK_TYPES:
            resolved_agents.add(mfrom)

    seen_r2 = set()
    for msg in recent_msgs:
        content = msg.get("content", "") or ""
        mtype = msg.get("type", "") or ""
        mfrom = msg.get("from", "") or ""
        # Only ashigaru*/gunshi messages
        if not mfrom.startswith(_R2_ALLOWED_FROM_PREFIX):
            continue
        # Skip if agent has resolved their block
        if mfrom in resolved_agents:
            continue
        if mtype in ("report_blocked", "report_error") or any(kw in content for kw in block_keywords):
            key = (mfrom, content[:60])
            if key in seen_r2:
                continue
            seen_r2.add(key)
            items.append({
                "rule": "R2",
                "severity": "HIGH",
                "title": f"ブロック報告: {mfrom} → {msg.get('to', '?')}",
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
                "age_hours": age_hours(cmd.get("timestamp") or cmd.get("issued_at", "")),
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

    # R5: 未読メッセージ滞留 (unread inbox messages > 30min) — uses _rm_cache
    if os.path.isdir(INBOX_DIR):
        for fname in os.listdir(INBOX_DIR):
            if not fname.endswith(".yaml"):
                continue
            agent_id = fname.replace(".yaml", "")
            if agent_id in _EXCLUDED_AGENTS_R5:
                continue
            filepath = os.path.join(INBOX_DIR, fname)
            try:
                mt = os.path.getmtime(filepath)
                cached = _rm_cache.get(fname)
                if cached and cached["mtime"] == mt:
                    messages = cached["messages"]
                else:
                    with open(filepath) as f:
                        data = yaml.safe_load(f)
                    messages = data.get("messages", []) if data else []
                    _rm_cache[fname] = {"mtime": mt, "messages": messages}
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

    # R6: タスク失敗 (failed status in tasks YAML) — uses _yt_cache
    if os.path.isdir(TASKS_DIR):
        for fname in os.listdir(TASKS_DIR):
            if not fname.endswith(".yaml"):
                continue
            agent_id = fname.replace(".yaml", "")
            if agent_id in _EXCLUDED_AGENTS_R5:
                continue
            filepath = os.path.join(TASKS_DIR, fname)
            try:
                mt = os.path.getmtime(filepath)
                cached = _yt_cache.get(fname)
                if cached and cached["mtime"] == mt:
                    tasks = cached["tasks"]
                else:
                    with open(filepath) as f:
                        data = yaml.safe_load(f)
                    tasks = data.get("tasks", []) if data else []
                    _yt_cache[fname] = {"mtime": mt, "tasks": tasks}
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

    # R7: dashboard.md 🚨要対応同期
    try:
        if os.path.isfile(DASHBOARD_MD):
            with open(DASHBOARD_MD, encoding="utf-8") as f:
                md_text = f.read()
            in_section = False
            for line in md_text.splitlines():
                stripped = line.strip()
                if "要対応" in stripped and stripped.startswith("## "):
                    in_section = True
                    continue
                if in_section and stripped.startswith("## ") and "要対応" not in stripped:
                    break
                if in_section and stripped.startswith("### ⚠️"):
                    title = stripped.replace("### ⚠️", "").strip()
                    cmd_match = None
                    m = re.search(r'(cmd_\d+)', title)
                    if m:
                        cmd_match = m.group(1)
                    items.append({
                        "rule": "R7",
                        "severity": "HIGH",
                        "title": title[:100],
                        "detail": "dashboard.md 🚨要対応より",
                        "age_hours": 0,
                        "cmd_id": cmd_match,
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


# ─── YAML readers (mtime-cached to avoid re-parsing ~3MB YAMLs) ──────────────────

# Per-file caches: {fname: {"mtime": float, "tasks": list}}
_yt_cache = {}
# Per-file caches for inbox: {fname: {"mtime": float, "messages": list, "agent_id": str}}
_rm_cache = {}


def _parse_tasks_regex(filepath):
    """Fallback regex parser for task YAML when yaml.safe_load fails.
    Extracts task list items with status, task_id, parent_cmd, timestamp, description."""
    tasks = []
    try:
        with open(filepath) as f:
            text = f.read()
        # Split on "- task:" or "- task_id:" top-level items
        blocks = re.split(r'\n(?=- (?:task:|task_id:))', text)
        for block in blocks:
            if not block.strip().startswith("- "):
                continue
            t = {}
            m = re.search(r'task_id:\s*(\S+)', block)
            if m:
                t["task_id"] = m.group(1).strip()
            m = re.search(r'parent_cmd:\s*(\S+)', block)
            if m:
                t["parent_cmd"] = m.group(1).strip()
            m = re.search(r'^\s+status:\s*(\S+)', block, re.MULTILINE)
            if m:
                t["status"] = m.group(1).strip()
            m = re.search(r'timestamp:\s*[\'"]?(\S+?)[\'"]?\s*$', block, re.MULTILINE)
            if m:
                t["timestamp"] = m.group(1).strip().strip("'\"")
            desc_match = re.search(r'description:\s*\|(.*)', block, re.DOTALL)
            if desc_match:
                t["description"] = desc_match.group(1).strip()[:200]
            if t.get("task_id"):
                tasks.append(t)
    except Exception:
        pass
    return tasks


def read_yaml_tasks():
    agents = {}
    if not os.path.isdir(TASKS_DIR):
        return agents
    _EXCLUDED = {"pending.yaml", "archive"}
    for fname in os.listdir(TASKS_DIR):
        if not fname.endswith(".yaml"):
            continue
        if fname in _EXCLUDED:
            continue
        agent_id = fname.replace(".yaml", "")
        filepath = os.path.join(TASKS_DIR, fname)
        try:
            mt = os.path.getmtime(filepath)
            cached = _yt_cache.get(fname)
            if cached and cached["mtime"] == mt:
                tasks = cached["tasks"]
            else:
                with open(filepath) as f:
                    data = yaml.safe_load(f)
                tasks = data.get("tasks", []) if data else []
                _yt_cache[fname] = {"mtime": mt, "tasks": tasks}
        except Exception:
            # Fallback: regex-based parsing
            tasks = _parse_tasks_regex(filepath)
            _yt_cache[fname] = {"mtime": os.path.getmtime(filepath), "tasks": tasks}

        try:
            latest_assigned = None
            total = len(tasks)
            done = sum(1 for t in tasks if t.get("status") == "done")
            for t in reversed(tasks):
                if t.get("status") == "assigned":
                    latest_assigned = t
                    break
            # Compute elapsed_min from task timestamp, fallback to file mtime
            elapsed_min = None
            if latest_assigned:
                ts_str = latest_assigned.get("timestamp", "")
                assigned_at = parse_ts(ts_str) if ts_str else None
                if not assigned_at:
                    assigned_at = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
                elapsed_min = (datetime.now(timezone.utc) - assigned_at).total_seconds() / 60

            agents[agent_id] = {
                "agent_id": agent_id,
                "status": "busy" if latest_assigned else "idle",
                "current_task": latest_assigned.get("task_id") if latest_assigned else None,
                "current_cmd": latest_assigned.get("parent_cmd") if latest_assigned else None,
                "description": (latest_assigned.get("description", "")[:80] if latest_assigned else ""),
                "total_tasks": total,
                "done_tasks": done,
                "elapsed_min": round(elapsed_min, 1) if elapsed_min is not None else None,
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
                "elapsed_min": None,
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
        if agent_id in _EXCLUDED_AGENTS_R5:
            continue
        filepath = os.path.join(INBOX_DIR, fname)
        try:
            mt = os.path.getmtime(filepath)
            cached = _rm_cache.get(fname)
            if cached and cached["mtime"] == mt:
                raw_msgs = cached["messages"]
            else:
                with open(filepath) as f:
                    data = yaml.safe_load(f)
                raw_msgs = data.get("messages", []) if data else []
                _rm_cache[fname] = {"mtime": mt, "messages": raw_msgs}
            for m in raw_msgs[-10:]:
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
    msgs.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return msgs[:30]


# ─── Agent status detection via DB messages table ─────────────────────────────

# Agents to track
POLL_AGENTS = [
    "ashigaru1", "ashigaru2", "ashigaru3", "ashigaru4",
    "ashigaru5", "ashigaru6", "ashigaru7", "gunshi",
]

# Message types that indicate agent status (latest wins)
_BUSY_TYPES = {"task_assigned"}
_IDLE_TYPES = {"report_done", "report_completed", "report_received"}
_BLOCKED_TYPES = {"report_blocked"}
_ERROR_TYPES = {"report_error"}


def get_db_agent_status(agent_id: str, conn) -> str:
    """Determine agent status from DB messages table.

    Looks at messages involving the agent (as sender or recipient).
    The most recent status-relevant message determines current state:
      task_assigned (to agent)   → busy
      report_done/completed (from agent) → idle
      report_blocked (from agent)        → blocked
      report_error (from agent)          → error
    """
    rows = query_db(
        conn,
        """
        SELECT type, timestamp AS created_at,
               CASE WHEN agent = ? THEN 'in' ELSE 'out' END AS direction
        FROM inbox_messages
        WHERE agent = ? OR from_agent = ?
        ORDER BY timestamp DESC
        LIMIT 50
        """,
        (agent_id, agent_id, agent_id),
    )
    for row in rows:
        mtype = row.get("type", "")
        direction = row.get("direction", "")
        if direction == "in" and mtype in _BUSY_TYPES:
            return "busy"
        if direction == "out" and mtype in _IDLE_TYPES:
            return "idle"
        if direction == "out" and mtype in _BLOCKED_TYPES:
            return "blocked"
        if direction == "out" and mtype in _ERROR_TYPES:
            return "error"
    return "unknown"


# ─── Dashboard data aggregation ────────────────────────────────────────────────

def _get_dingtalk_qc_stats():
    """DingTalk音声QCのリアルタイム統計（複数ログファイル集約）"""
    import subprocess
    log_dir = os.path.join(BASE_DIR, "work", "dingtalk_qc")
    log_files = sorted(glob.glob(os.path.join(log_dir, "qc_log*.jsonl")))
    if not log_files:
        return None
    try:
        total = confirmed = skipped = error = 0
        sims = []
        vols = []
        sources = {}
        for log_path in log_files:
            file_total = 0
            with open(log_path) as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        total += 1
                        file_total += 1
                        action = d.get("action", "")
                        if "確認済み" in action: confirmed += 1
                        elif "スキップ" in action: skipped += 1
                        elif "エラー" in action: error += 1
                        sim = d.get("similarity", -1)
                        if sim >= 0: sims.append(sim)
                        vol = d.get("mean_volume_db")
                        if vol is not None: vols.append(vol)
                    except: pass
            sources[os.path.basename(log_path)] = file_total
        running = subprocess.run(["pgrep", "-f", "dingtalk_qc_loop"],
                                 capture_output=True).returncode == 0
        return {
            "total": total,
            "processed": confirmed + error,
            "target": 10000,
            "confirmed": confirmed,
            "skipped": skipped,
            "error": error,
            "avg_similarity": round(sum(sims)/len(sims), 1) if sims else 0,
            "min_similarity": round(min(sims), 1) if sims else 0,
            "avg_volume": round(sum(vols)/len(vols), 1) if vols else 0,
            "earned": (confirmed + error) * 9,
            "running": running,
            "sources": sources,
        }
    except:
        return None


def _get_advisor_proxy_stats():
    """Advisor Proxyのリアルタイム統計"""
    try:
        import urllib.request
        health = json.loads(urllib.request.urlopen("http://localhost:8780/health", timeout=2).read())
        metrics = json.loads(urllib.request.urlopen("http://localhost:8780/metrics", timeout=2).read())
        return {
            "status": "up",
            "uptime_seconds": health.get("uptime_seconds"),
            "circuit_state": health.get("circuit_state", "unknown"),
            "total_requests": metrics.get("total_requests", 0),
            "success": metrics.get("success", 0),
            "failures": metrics.get("failures", 0),
            "advisor_calls": metrics.get("advisor_calls", 0),
            "avg_response_ms": metrics.get("avg_response_ms", 0),
        }
    except Exception:
        return {"status": "down"}


def get_dashboard_data():
    conn = get_db()

    # SQLite inbox_messages (cmd_1488 dual-path)
    db_messages = query_db(conn, "SELECT * FROM inbox_messages ORDER BY timestamp DESC LIMIT 20")
    db_msg_count = query_db(conn, "SELECT COUNT(*) as c FROM inbox_messages")
    msg_count_db = db_msg_count[0]["c"] if db_msg_count else 0

    # YAML data
    yaml_agents = read_yaml_tasks()
    yaml_messages = read_recent_messages(hours=24)

    # Agent map (YAML primary)
    agent_map = {}
    for aid, a in yaml_agents.items():
        agent_map[aid] = a

    # Override status with DB-driven status
    for aid, a in agent_map.items():
        # Override status with DB messages-based detection
        db_status = get_db_agent_status(aid, conn)
        if db_status and db_status != 'unknown':
            a["status"] = db_status
        # else: keep YAML-derived status (no forced idle)
        # idle agents should not show elapsed time from old assigned tasks
        if a["status"] != "busy":
            a["elapsed_min"] = None

    conn.close()

    # Active cmds
    active_cmds = get_active_cmds()
    recent_done = get_recent_done(20)

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
    all_messages.sort(key=lambda x: x.get("timestamp") or x.get("created_at") or "", reverse=True)
    all_messages = all_messages[:30]

    # Stats
    busy_agents = sum(1 for a in agent_map.values() if a.get("status") == "busy")
    idle_agents = sum(1 for a in agent_map.values() if a.get("status") == "idle")
    total_done = sum(a.get("done_tasks", 0) for a in agent_map.values())

    # Strip total_tasks/done_tasks from per-agent API response
    for a in agent_map.values():
        a.pop("total_tasks", None)
        a.pop("done_tasks", None)

    # DingTalk QC stats
    dingtalk_qc = _get_dingtalk_qc_stats()

    # Advisor Proxy stats
    advisor_proxy = _get_advisor_proxy_stats()

    return {
        "stats": {
            "action_required_count": len(action_required),
            "busy_agents": busy_agents,
            "idle_agents": idle_agents,
            "active_cmds": len(active_cmds),
            "db_messages": msg_count_db,
            "total_done": total_done,
        },
        "dingtalk_qc": dingtalk_qc,
        "advisor_proxy": advisor_proxy,
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
  <div class="panel" id="dingtalk-panel"><h2>💰 DingTalk音声QC</h2><div id="dingtalk-qc"></div></div>
  <div class="panel" id="advisor-proxy-panel"><h2>🔮 Advisor Proxy</h2><div id="advisor-proxy"></div></div>
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

function renderDingtalkQC(qc) {
  const el = $('dingtalk-qc');
  if (!qc) { el.innerHTML = '<div class="empty">データなし</div>'; return; }
  const processed = qc.processed || (qc.confirmed + qc.error);
  const pct = (processed / qc.target * 100).toFixed(1);
  const status = qc.running ? '<span class="badge badge-busy">稼働中</span>' : '<span class="badge badge-idle">停止中</span>';
  el.innerHTML = `
    <div style="margin-bottom:8px">${status} <strong>¥${qc.earned.toLocaleString()}</strong> / ¥90,000</div>
    <div style="background:#21262d;border-radius:4px;height:20px;margin-bottom:8px">
      <div style="background:#238636;height:100%;border-radius:4px;width:${pct}%;min-width:2px;text-align:center;color:#fff;font-size:0.7em;line-height:20px">${processed}/${qc.target} (${pct}%)</div>
    </div>
    <table>
      <tr><td>✅ 確認済み</td><td>${qc.confirmed}</td></tr>
      <tr><td>🟡 スキップ</td><td>${qc.skipped}</td></tr>
      <tr><td>🔴 エラー</td><td>${qc.error}</td></tr>
      <tr><td>📊 平均類似度</td><td>${qc.avg_similarity}%</td></tr>
      <tr><td>📉 最低類似度</td><td>${qc.min_similarity}%</td></tr>
      <tr><td>🔊 平均音量</td><td>${qc.avg_volume} dB</td></tr>
    </table>
    ${qc.sources ? `<div style="margin-top:8px;font-size:0.75em;color:#8b949e">内訳: ${Object.entries(qc.sources).map(([k,v]) => `${k.replace('qc_log','').replace('.jsonl','') || 'main'}=${v}`).join(', ')}</div>` : ''}`;
}

function renderAdvisorProxy(ap) {
  const el = $('advisor-proxy');
  if (!ap) { el.innerHTML = '<div class="empty">データなし</div>'; return; }
  if (ap.status === 'down') {
    el.innerHTML = '<div style="text-align:center;padding:12px"><span class="badge badge-idle">停止中</span></div>';
    return;
  }
  const circuit = ap.circuit_state || 'unknown';
  const circuitBadge = circuit === 'closed'
    ? '<span class="badge badge-idle">closed</span>'
    : circuit === 'open'
      ? '<span class="badge badge-busy" style="background:#f85149">OPEN</span>'
      : `<span class="badge badge-error">${esc(circuit)}</span>`;
  const uptime = ap.uptime_seconds != null
    ? (ap.uptime_seconds >= 3600 ? `${Math.floor(ap.uptime_seconds/3600)}h ${Math.round((ap.uptime_seconds%3600)/60)}m` : `${Math.round(ap.uptime_seconds/60)}m`)
    : '—';
  const successRate = ap.total_requests > 0 ? ((ap.success / ap.total_requests) * 100).toFixed(1) : '—';
  el.innerHTML = `
    <table>
      <tr><td>📡 状態</td><td><span class="badge badge-busy">稼働中</span></td></tr>
      <tr><td>⏱ 稼働時間</td><td>${uptime}</td></tr>
      <tr><td>🔒 サーキット</td><td>${circuitBadge}</td></tr>
      <tr><td>📨 リクエスト</td><td>${ap.total_requests}</td></tr>
      <tr><td>✅ 成功</td><td>${ap.success} (${successRate}%)</td></tr>
      <tr><td>🔴 失敗</td><td>${ap.failures}</td></tr>
      <tr><td>🔮 Advisor呼出</td><td>${ap.advisor_calls}</td></tr>
      <tr><td>⏱ 平均応答</td><td>${Math.round(ap.avg_response_ms)}ms</td></tr>
    </table>`;
}

function renderAgents(agents) {
  if (!agents || !agents.length) { $('agents').innerHTML = '<div class="empty">No agents</div>'; return; }
  let html = '<table><tr><th>エージェント</th><th>状態</th><th>タスク</th><th>経過</th></tr>';
  agents.sort((a,b) => {
    const order = ['karo','ashigaru1','ashigaru2','ashigaru3','ashigaru4','ashigaru5','ashigaru6','ashigaru7','gunshi'];
    return order.indexOf(a.agent_id) - order.indexOf(b.agent_id);
  });
  for (const a of agents) {
    const badge = `badge-${a.status || 'offline'}`;
    const task = a.current_task || a.tmux_task || '—';
    let elapsed = '—';
    if (a.elapsed_min != null) {
      const mins = a.elapsed_min;
      if (mins < 60) {
        elapsed = `${Math.round(mins)}m`;
      } else {
        elapsed = `${Math.floor(mins / 60)}h ${Math.round(mins % 60)}m`;
      }
      if (mins > 120) {
        elapsed = `<span style="color:#f85149">${elapsed}</span>`;
      } else if (mins > 60) {
        elapsed = `<span style="color:#d29922">${elapsed}</span>`;
      }
    }
    html += `<tr>
      <td><strong>${esc(a.agent_id)}</strong></td>
      <td><span class="badge ${badge}">${esc(a.status || 'offline')}</span></td>
      <td class="truncate" title="${esc(a.description || a.current_task || '')}">${esc(task)}</td>
      <td style="white-space:nowrap">${elapsed}</td>
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
    renderDingtalkQC(d.dingtalk_qc);
    renderAdvisorProxy(d.advisor_proxy);
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


CMDS_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>📋 cmd 一覧</title>
<style>
body{margin:0;padding:12px;background:#1a1a1a;color:#eee;font-family:-apple-system,sans-serif;font-size:14px}
h1{margin:0 0 8px;font-size:1.3em}
.counts{font-size:12px;color:#888;margin-bottom:8px}
.bar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.pill{padding:4px 12px;border-radius:14px;border:1px solid #444;background:#2a2a2a;color:#eee;cursor:pointer;font-size:13px;user-select:none}
.pill.active{background:#FCC700;color:#000;border-color:#FCC700;font-weight:bold}
.q{flex:1;min-width:180px;padding:6px 10px;background:#222;color:#eee;border:1px solid #444;border-radius:4px;font-size:14px}
.cmd{margin-bottom:10px;padding:10px 12px;background:#222;border-radius:6px;border-left:3px solid #555}
.cmd.pending{border-left-color:#FCC700}
.cmd.done{border-left-color:#4CAF50}
.cmd.cancelled{border-left-color:#f55}
.cmd.superseded{border-left-color:#888}
.cmd.testing{border-left-color:#5af}
.id{font-weight:bold;font-size:1.05em;color:#fff}
.status{display:inline-block;padding:1px 8px;border-radius:8px;font-size:10px;background:#333;margin-left:6px;color:#eee;letter-spacing:0.5px}
.status.pending{background:#665b00;color:#FCC700}
.status.done{background:#1d4422;color:#7be090}
.status.cancelled{background:#5a1818;color:#ffaaaa}
.status.superseded{background:#444;color:#aaa}
.purpose{color:#bbb;margin:4px 0;line-height:1.4}
.lord{color:#FCC700;font-size:13px;margin:4px 0;border-left:2px solid #FCC700;padding-left:8px;background:rgba(252,199,0,0.05)}
.meta{color:#666;font-size:11px;margin-top:4px}
.empty{text-align:center;color:#666;padding:40px}
</style>
</head>
<body>
<h1>📋 cmd 一覧</h1>
<div class="counts" id="counts">loading…</div>
<div class="bar">
  <input type="text" class="q" id="q" placeholder="ID / purpose / lord_original / assigned_to で検索…">
  <span class="pill active" data-s="">全て</span>
  <span class="pill" data-s="pending">pending</span>
  <span class="pill" data-s="done">done</span>
  <span class="pill" data-s="cancelled">cancelled</span>
  <span class="pill" data-s="superseded">superseded</span>
</div>
<div id="list"></div>
<script>
let curStatus = '';
let curQ = '';
function escapeHtml(s){return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
async function load() {
  const params = new URLSearchParams();
  if (curStatus) params.set('status', curStatus);
  if (curQ) params.set('q', curQ);
  params.set('limit', '300');
  const r = await fetch('/api/cmd_list?' + params);
  const d = await r.json();
  const countParts = Object.entries(d.counts || {}).map(([k,v])=>`${k}:${v}`).join(' / ');
  document.getElementById('counts').textContent = `total ${d.total} / shown ${d.shown} | ${countParts}`;
  const list = document.getElementById('list');
  list.innerHTML = '';
  if (!d.cmds || d.cmds.length === 0) {
    list.innerHTML = '<div class="empty">該当なし</div>';
    return;
  }
  d.cmds.forEach(c => {
    const div = document.createElement('div');
    const status = c.status || '';
    div.className = 'cmd ' + status;
    let html = `<div><span class="id">${escapeHtml(c.id||'')}</span><span class="status ${status}">${status}</span> <span class="meta">${escapeHtml(c.priority||'')} / ${escapeHtml(c.timestamp||c.issued_at||'')}</span></div>`;
    if (c.purpose) html += `<div class="purpose">${escapeHtml(c.purpose)}</div>`;
    if (c.lord_original) html += `<div class="lord">殿: ${escapeHtml(c.lord_original)}</div>`;
    const metaItems = [];
    if (c.assigned_to) metaItems.push('→ ' + escapeHtml(c.assigned_to));
    if (c.project) metaItems.push('proj: ' + escapeHtml(c.project));
    if (c.depends_on) metaItems.push('depends: ' + escapeHtml(c.depends_on));
    if (c.cancelled_reason) metaItems.push('reason: ' + escapeHtml(c.cancelled_reason));
    if (metaItems.length) html += `<div class="meta">${metaItems.join(' | ')}</div>`;
    div.innerHTML = html;
    list.appendChild(div);
  });
}
document.querySelectorAll('.pill').forEach(p => {
  p.addEventListener('click', () => {
    document.querySelectorAll('.pill').forEach(x => x.classList.remove('active'));
    p.classList.add('active');
    curStatus = p.dataset.s;
    load();
  });
});
document.getElementById('q').addEventListener('input', e => {
  curQ = e.target.value;
  clearTimeout(window._qt);
  window._qt = setTimeout(load, 300);
});
load();
setInterval(load, 30000);
</script>
</body>
</html>"""


# ─── Async Job Workers ────────────────────────────────────────────────────────────

def _run_suggest_director_notes(job_id, payload):
    """Background worker for /api/suggest_director_notes."""
    import subprocess
    try:
        _jobs[job_id]['status'] = 'running'
        scene_desc = payload.get('scene_desc', '')
        situation = payload.get('situation', '')
        lines = payload.get('lines', [])
        char_name = payload.get('char_name', '')
        new_expression_file = payload.get('new_expression_file', '')
        director_notes = payload.get('director_notes', '')
        expr_design_path = os.path.join(BASE_DIR, 'projects/dozle_kirinuki/context/expression_design_v5.md')
        expr_design_text = ''
        if os.path.exists(expr_design_path):
            with open(expr_design_path, 'r', encoding='utf-8') as f:
                expr_design_text = f.read()[:3000]
        ref_images = payload.get('ref_images', [])
        shot_type = payload.get('shot_type', '')
        lines_text = '\n'.join(lines) if lines else '（セリフなし）'
        KOMAWARI_DESC = {
            'S1_A.png': '全面1コマ', 'S2_A.png': '上大70%+下小30%', 'S2_B.png': '上小30%+下大70%',
            'S2_C.png': '縦割り右小30%+左大70%', 'S2_D.png': '縦割り右大70%+左小30%',
            'S2_E.png': '均等縦割り', 'T1.png': '全面1コマ',
            'T2_A.png': '上下均等2段', 'T2_B.png': '左右均等2列', 'T2_C.png': '上大下小',
            'T3_A.png': '均等3段', 'T3_B.png': '上1コマ+下2コマ',
            'T3_C.png': '縦割り左大60%+右2コマ', 'T3_D.png': '縦割り右大60%+左2コマ',
            'T3_E.png': '上1コマ+下2コマ(重要側60%)', 'T3_F.png': '上2コマ(重要側60%)+下1コマ',
            'T4_A.png': '上3コマ45%+下大55%', 'T4_B.png': '上大55%+下3コマ45%',
            'T4_C.png': '上下2コマ(重要側60%交互)', 'T4_D.png': '均等4段',
            'T4_E.png': '右大コマ縦通し+左2段+下全幅', 'T4_F.png': '上全幅+右2段+左大コマ縦通し',
            'T5_A.png': '上3コマ45%+下2コマ55%', 'T5_B.png': '上2コマ55%+下3コマ45%',
            'T5_C.png': '上2+中全幅+下2',
            'T6_A.png': '均等6コマ(3段2列)', 'T6_B.png': '上2大+下4小',
            'D1_diagonal_2.png': '斜め2分割', 'D2_zigzag_3.png': 'ジグザグ斜め3分割',
            'D3_v_split.png': 'V字分割(上大+下2斜め)', 'D4_radial_4.png': '放射状4分割',
            'D5_overlay_4.png': 'ぶち抜き大コマ+小コマ3', 'D6_staircase_4.png': '階段状4コマ',
            'D7_fan_3.png': '扇状(上狭→下広)', 'D8_x_split_4.png': 'X字斜め4分割',
        }
        ref_descs = []
        for r in ref_images:
            fname = os.path.basename(r)
            if 'komawari_templates/' in r:
                desc = KOMAWARI_DESC.get(fname, 'コマ割りテンプレート')
                ref_descs.append(f'{fname}=コマ割りテンプレート（{desc}。この構図に従って描け）')
            elif 'character/selected/' in r:
                ref_descs.append(f'{fname}=キャラクターリファレンス（この外見・服装を正確に再現せよ）')
            else:
                ref_descs.append(f'{fname}=背景リファレンス（この背景を参考にせよ）')
        attachment_line = '添付画像の説明: ' + '、'.join(ref_descs) if ref_descs else ''
        prompt = f"""あなたはドズル社マイクラ漫画の演出家です。
キャラクターの表情リファレンスが変わったので、画像生成プロンプト（director_notes）を全文書き直してください。

## キャラクター設定（参考）
{expr_design_text}

## パネル情報
- シーン概要: {scene_desc}
- 状況: {situation}
- セリフ: {lines_text}
- コマ割り: {shot_type}

## 表情変更
- キャラクター: {char_name}
- 新しい表情ファイル: {new_expression_file}

## 添付リファレンス画像一覧
{attachment_line}

## 現在のdirector_notes（変更前）
{director_notes}

## 指示
上記の表情変更とリファレンス画像に合わせて、director_notesを全文書き直してください。
以下の構成で出力:
1. 最初に「添付画像の説明: 」行（上記の添付リファレンス画像一覧をそのまま使え）
2. 続けて「これらのリファレンス画像のキャラクターの外見・服装を正確に再現すること。」
3. コマ割りに応じた構図指示（上下分割なら上段・下段、左右分割なら右・左）
   ※左右分割の場合の読み順ルール: 右コマ=先に発言する人、左コマ=後に発言する人（日本の漫画は右→左に読む）
4. 各コマのキャラクターの表情・ポーズ・感情の具体的な描写（新しい表情に合わせる）
5. 背景指示（リファレンス背景に合わせる）
6. 禁止事項（武器・盾・バケツ持たせるな等）

- 日本語で、簡潔かつ具体的に
- 余計な説明や前置きは不要。director_notesテキストのみ出力してください"""
        # claude CLI 引数順序: --model を先に、-p prompt を最後に（-p直後がpromptとして解釈されるため）
        result = subprocess.run(
            ['claude', '--model', 'sonnet', '-p', prompt],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode != 0:
            raise Exception(f'Claude CLI error: {result.stderr[:200]}')
        suggested = result.stdout.strip()
        with _jobs_lock:
            _jobs[job_id]['status'] = 'done'
            _jobs[job_id]['result'] = {'status': 'ok', 'suggested': suggested}
    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]['status'] = 'error'
            _jobs[job_id]['error'] = str(e)


def _run_generate_panels(job_id, payload):
    """Background worker for /api/generate_panels_llm."""
    import subprocess
    try:
        _jobs[job_id]['status'] = 'running'
        rows = payload.get('rows', [])
        gemini_context = payload.get('gemini_context', '')
        scene_name = payload.get('scene_name', '')
        title = payload.get('title', '')
        save_path = payload.get('save_path', '')
        selected_dir = os.path.join(BASE_DIR, 'projects/dozle_kirinuki/assets/dozle_jp/character/selected')
        available_files = set()
        if os.path.isdir(selected_dir):
            available_files = {f for f in os.listdir(selected_dir) if f.endswith('.png')}
        prompt_path = os.path.join(BASE_DIR, 'projects/dozle_kirinuki/context/panel_candidate_prompt.txt')
        prompt_knowledge = ''
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                full_prompt = f.read()
            idx = full_prompt.find('# 漫画制作ナレッジ')
            prompt_knowledge = full_prompt[idx:] if idx >= 0 else full_prompt
        rows_text = '\n'.join(
            f"{row.get('timestamp', '')} {row.get('speaker', '')}: {row.get('text', '')}"
            for row in rows
        )
        rgba_files = sorted(f for f in available_files if '_rgba.png' in f)
        files_list = '\n'.join(rgba_files) if rgba_files else '（ファイルなし）'
        scene_summary = DashboardHandler._extract_scene_summary(gemini_context) if gemini_context else ''
        claude_prompt = f"""あなたはドズル社漫画ショートの構成作家です。
以下の書き起こし（殿レビュー済み）とシーン情報から、漫画パネルのJSONを生成してください。

## 書き起こし（話者+セリフ）
{rows_text}

## シーン情報（Gemini動画解析）
{scene_summary if scene_summary else '（シーン情報なし）'}

## タイトル・シーン名
タイトル: {title}
シーン: {scene_name}

## 出力形式（必須）
```json で囲んで以下の形式で出力せよ。全フィールド必須。省略するな。

{{
  "panels": [
    {{
      "id": "p1_xxx",
      "title": "P1: 話者「セリフ冒頭」",
      "characters": ["dozle"],
      "lines": ["セリフ全文"],
      "start_sec": 0,
      "duration_sec": 5,
      "shot_type": "S2",
      "is_climax": false,
      "scene_desc": "シーンの説明",
      "situation": "状況の説明",
      "director_notes": "表情コード+ポーズ+背景+禁止事項",
      "ref_images": ["assets/dozle_jp/character/selected/dozle_smile_r1_rgba.png"]
    }}
  ]
}}

### フィールド説明
- characters: メンバーキー（dozle/bon/qnly/orafu/oo_men/nekooji）。必須
- lines: セリフ。書き起こしから該当セリフをそのまま入れよ。必須
- shot_type: 1人→S2、2人→T2_B、climax→S1
- ref_images: "assets/dozle_jp/character/selected/{{キャラ}}_{{表情}}_rgba.png" 形式。下記の使用可能ファイルから選べ
- director_notes: 表情コード+ポーズ具体指示+背景+禁止事項。必須

{prompt_knowledge}

## 使用可能な表情ファイル
以下のファイルのみ使用可（存在しないファイルは絶対に使わないこと）:
{files_list}

## 共通ルール
全キャラクターの身長はだいたい同じくらいに描くこと。
【最重要】おおはらMENは必ずゴーグルを目を覆うように装着して描け。
ぼんじゅうるはサングラス必須。おんりーは丸メガネ必須。
デフォルメ・SD・ちびキャラ禁止。武器・盾・バケツ禁止。

【重要】各パネルの "characters" フィールドには必ずメンバーキーを入れること。
使用可能なキー: dozle, bon, qnly, orafu, oo_men, nekooji
セリフがないパネルも含め、全パネルに characters を設定すること。"""
        claude_bin = os.path.expanduser('~/.local/bin/claude')
        result = subprocess.run(
            [claude_bin, '-p', claude_prompt, '--model', 'claude-opus-4-6'],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            raise Exception(f'Claude CLI error: {result.stderr[:500]}')
        output_text = result.stdout.strip()
        panels_data = None
        json_match = re.search(r'```json\s*([\s\S]+?)\s*```', output_text)
        if json_match:
            try:
                panels_data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        if panels_data is None:
            try:
                panels_data = json.loads(output_text)
            except json.JSONDecodeError:
                raise Exception(f'Claude出力からJSONを抽出できませんでした。出力先頭: {output_text[:300]}')
        if isinstance(panels_data, list):
            panels_data = {'panels': panels_data}
        if 'panels' in panels_data:
            for i, panel in enumerate(panels_data['panels']):
                if not panel.get('characters'):
                    if i < len(rows):
                        speaker = rows[i].get('speaker', '不明')
                        if speaker != '不明':
                            panel['characters'] = [speaker]
        REF_PREFIX = 'projects/dozle_kirinuki/assets/dozle_jp/character/selected/'
        if 'panels' in panels_data:
            for panel in panels_data['panels']:
                new_refs = []
                for ref in panel.get('ref_images', []):
                    fname = os.path.basename(ref)
                    if fname in available_files:
                        new_refs.append(REF_PREFIX + fname)
                    else:
                        chars = panel.get('characters', [])
                        fallback = None
                        for char in chars:
                            fb_fname = f'{char}_smile_r1_rgba.png'
                            if fb_fname in available_files:
                                fallback = REF_PREFIX + fb_fname
                                break
                        if fallback:
                            new_refs.append(fallback)
                panel['ref_images'] = new_refs
        if 'meta' not in panels_data or not panels_data['meta']:
            panels_data['meta'] = {}
        meta = panels_data['meta']
        if not meta.get('scene'):
            meta['scene'] = scene_name or ''
        if not meta.get('title'):
            meta['title'] = title or '（タイトル未設定）'
        if not meta.get('panel_count'):
            meta['panel_count'] = len(panels_data.get('panels', []))
        if not meta.get('common_rules'):
            meta['common_rules'] = (
                "全キャラクターの身長はだいたい同じくらいに描くこと。極端な身長差をつけるな。"
                "【最重要】おおはらMENは必ずゴーグルを目を覆うように装着（目が隠れる位置。額に上げるな）して描け。"
                "ゴーグルなしのMENは絶対に描くな。リファレンス画像のゴーグルをそのまま再現せよ。"
                "サングラスではなくゴーグルである。ぼんじゅうるはサングラス必須。おんりーは丸メガネ必須。"
                "デフォルメ・SD・ちびキャラ禁止。等身大のアニメ風キャラクターとして描くこと。武器・盾・バケツ禁止。"
            )
        meta['generated_by'] = 'claude_opus_via_panel_review'
        if save_path:
            abs_save = os.path.realpath(os.path.join(BASE_DIR, save_path))
            if abs_save.startswith(os.path.realpath(BASE_DIR) + os.sep):
                os.makedirs(os.path.dirname(abs_save), exist_ok=True)
                with open(abs_save, 'w', encoding='utf-8') as f:
                    json.dump(panels_data, f, ensure_ascii=False, indent=2)
        panels = panels_data.get('panels', [])
        with _jobs_lock:
            _jobs[job_id]['status'] = 'done'
            _jobs[job_id]['result'] = {'status': 'ok', 'panels': panels, 'panel_count': len(panels)}
    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]['status'] = 'error'
            _jobs[job_id]['error'] = str(e)


# ─── HTTP Handler ───────────────────────────────────────────────────────────────

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    @staticmethod
    def _extract_scene_summary(gemini_text: str) -> str:
        """Gemini生テキストから【シーン一覧】セクションだけ抽出。トークン節約。"""
        lines = gemini_text.split('\n')
        result = []
        in_section = False
        for line in lines:
            if '【シーン一覧】' in line:
                in_section = True
                result.append(line)
                continue
            if in_section:
                if line.startswith('## 【') or line.startswith('# '):
                    break
                result.append(line)
        return '\n'.join(result) if result else gemini_text[:2000]

    def do_GET(self):
        if self.path.startswith('/api/dashboard') and not self.path.startswith('/api/dashboard_md') and not self.path.startswith('/api/dashboard_update'):
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                slim = qs.get('slim', ['0'])[0] == '1'
                data = get_dashboard_data()
                if slim:
                    # 家老 context 削減用 slim 版: stats + active_cmds + action_required + agents のみ
                    data = {
                        'stats': data.get('stats', {}),
                        'active_cmds': [
                            {k: c.get(k) for k in ('id', 'status', 'priority', 'purpose', 'timestamp')}
                            for c in (data.get('active_cmds') or [])
                        ],
                        'action_required': data.get('action_required', []),
                        'agents': [
                            {k: a.get(k) for k in ('agent_id', 'status', 'current_task', 'last_inbox_update')}
                            for a in (data.get('agents') or [])
                        ],
                        'source': 'sqlite_slim',
                    }
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
        elif self.path.startswith('/api/job_status'):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            job_id = qs.get('id', [''])[0]
            with _jobs_lock:
                job = _jobs.get(job_id)
            if job is None:
                body = json.dumps({'status': 'not_found'}).encode()
                self.send_response(404)
            else:
                body = json.dumps(job, default=str).encode()
                self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ('/', '/index.html'):
            body = HTML.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ('/cmds', '/cmds.html'):
            body = CMDS_HTML.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith('/api/cmd_list'):
            # cmd_1488 dual-path 完了後は SQLite が読み出しソース。
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                status_filter = qs.get('status', [None])[0]
                keyword = qs.get('q', [None])[0]
                limit = int(qs.get('limit', ['20'])[0])  # default 200→20 (家老 context 削減)
                slim = qs.get('slim', ['0'])[0] == '1'

                conn = sqlite3.connect(DB_PATH, timeout=5)
                conn.row_factory = sqlite3.Row
                try:
                    counts = {}
                    for r in conn.execute(
                        "SELECT status, COUNT(*) AS c FROM commands GROUP BY status"
                    ):
                        counts[r['status']] = r['c']
                    total = sum(counts.values())

                    sql = "SELECT * FROM commands"
                    params = []
                    where = []
                    if status_filter:
                        where.append("status = ?")
                        params.append(status_filter)
                    if keyword:
                        kw = f"%{keyword.lower()}%"
                        where.append(
                            "(LOWER(id) LIKE ? OR LOWER(COALESCE(purpose,'')) LIKE ? "
                            "OR LOWER(COALESCE(lord_original,'')) LIKE ? "
                            "OR LOWER(COALESCE(assigned_to,'')) LIKE ?)"
                        )
                        params.extend([kw, kw, kw, kw])
                    if where:
                        sql += " WHERE " + " AND ".join(where)
                    sql += " ORDER BY COALESCE(timestamp, issued_at) DESC LIMIT ?"
                    params.append(limit)

                    slim_drop = {'command_text', 'acceptance_criteria_json', 'depends_on_json',
                                 'notes_json', 'full_yaml_blob', 'north_star',
                                 'implementation_flow', 'verify_guidance'}
                    cmds = []
                    for r in conn.execute(sql, params):
                        d = {k: v for k, v in dict(r).items()
                             if v is not None and k != 'full_yaml_blob'}
                        if slim:
                            for k in list(d.keys()):
                                if k in slim_drop:
                                    d.pop(k, None)
                        else:
                            for k_json, k_clean in [
                                ('acceptance_criteria_json', 'acceptance_criteria'),
                                ('depends_on_json', 'depends_on'),
                                ('notes_json', 'notes'),
                            ]:
                                if d.get(k_json):
                                    try:
                                        d[k_clean] = json.loads(d[k_json])
                                    except Exception:
                                        pass
                                    d.pop(k_json, None)
                        cmds.append(d)
                finally:
                    conn.close()

                resp_data = {
                    'total': total,
                    'counts': counts,
                    'shown': len(cmds),
                    'cmds': cmds,
                    'source': 'sqlite_slim' if slim else 'sqlite',
                }
                body = json.dumps(resp_data, ensure_ascii=False,
                                  default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/api/cmd_detail'):
            # GET /api/cmd_detail?id=cmd_1487 → 1件分の full データ
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                cmd_id = (qs.get('id', [''])[0] or '').strip()
                if not cmd_id:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'id required'}).encode('utf-8'))
                    return

                conn = sqlite3.connect(DB_PATH, timeout=5)
                conn.row_factory = sqlite3.Row
                try:
                    r = conn.execute(
                        "SELECT * FROM commands WHERE id = ?", (cmd_id,)
                    ).fetchone()
                finally:
                    conn.close()

                if r is None:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': f'cmd not found: {cmd_id}'}, ensure_ascii=False
                    ).encode('utf-8'))
                    return

                d = {k: v for k, v in dict(r).items() if v is not None}
                for k_json, k_clean in [
                    ('acceptance_criteria_json', 'acceptance_criteria'),
                    ('depends_on_json', 'depends_on'),
                    ('notes_json', 'notes'),
                ]:
                    if d.get(k_json):
                        try:
                            d[k_clean] = json.loads(d[k_json])
                        except Exception:
                            pass
                        d.pop(k_json, None)

                body = json.dumps(d, ensure_ascii=False, indent=2,
                                  default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/api/task_list'):
            # GET /api/task_list?agent=ashigaru3&status=assigned&limit=50
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                agent = qs.get('agent', [None])[0]
                status_filter = qs.get('status', [None])[0]
                cmd_filter = qs.get('cmd', [None])[0]
                limit = int(qs.get('limit', ['50'])[0])

                conn = sqlite3.connect(DB_PATH, timeout=5)
                conn.row_factory = sqlite3.Row
                try:
                    sql = "SELECT * FROM tasks"
                    params = []
                    where = []
                    if agent:
                        where.append("agent = ?"); params.append(agent)
                    if status_filter:
                        where.append("status = ?"); params.append(status_filter)
                    if cmd_filter:
                        where.append("parent_cmd = ?"); params.append(cmd_filter)
                    if where:
                        sql += " WHERE " + " AND ".join(where)
                    sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)
                    tasks = []
                    for r in conn.execute(sql, params):
                        d = {k: v for k, v in dict(r).items()
                             if v is not None and k != 'full_yaml_blob'}
                        for k_json, k_clean in [
                            ('acceptance_criteria_json', 'acceptance_criteria'),
                            ('notes_json', 'notes'),
                            ('params_json', 'params'),
                        ]:
                            if d.get(k_json):
                                try: d[k_clean] = json.loads(d[k_json])
                                except Exception: pass
                                d.pop(k_json, None)
                        tasks.append(d)
                finally:
                    conn.close()

                body = json.dumps({'tasks': tasks, 'shown': len(tasks),
                                   'source': 'sqlite'}, ensure_ascii=False,
                                  indent=2, default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/api/inbox_messages'):
            # GET /api/inbox_messages?agent=karo&unread=1&limit=20&full=0
            # full=0 (default cmd_1495): summary cols only — 件名/from/type のみ・content 含まず
            # full=1: 全カラム返却 (本文 content 含む)
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                agent = qs.get('agent', [None])[0]
                unread = qs.get('unread', [None])[0]  # '1' で未読のみ
                limit = int(qs.get('limit', ['20'])[0])
                full = qs.get('full', ['0'])[0] == '1'

                conn = sqlite3.connect(DB_PATH, timeout=5)
                conn.row_factory = sqlite3.Row
                try:
                    cols = "*" if full else "id, agent, from_agent, type, read, timestamp"
                    sql = f"SELECT {cols} FROM inbox_messages"
                    params = []
                    where = []
                    if agent:
                        where.append("agent = ?"); params.append(agent)
                    if unread == '1':
                        where.append("read = 0")
                    if where:
                        sql += " WHERE " + " AND ".join(where)
                    sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)
                    msgs = [dict(r) for r in conn.execute(sql, params)]
                finally:
                    conn.close()

                body = json.dumps({'messages': msgs, 'shown': len(msgs),
                                   'full': full, 'source': 'sqlite'},
                                  ensure_ascii=False, indent=2, default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/dashboard_md':
            # GET /api/dashboard_md — dashboard.md の markdown 全文取得 (家老が Read 直叩き廃止)
            try:
                if not os.path.exists(DASHBOARD_MD):
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'dashboard.md not found'}).encode())
                    return
                with open(DASHBOARD_MD, 'r', encoding='utf-8') as f:
                    md = f.read()
                resp = json.dumps({
                    'content': md,
                    'bytes': len(md.encode('utf-8')),
                    'mtime': os.path.getmtime(DASHBOARD_MD),
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/api/report_detail'):
            # GET /api/report_detail?id=<report_id> — DB行 + YAML 全文を返す
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                rid = (qs.get('id', [''])[0] or '').strip()
                if not rid:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'id required'}).encode('utf-8'))
                    return
                conn = sqlite3.connect(DB_PATH, timeout=5)
                conn.row_factory = sqlite3.Row
                try:
                    r = conn.execute(
                        "SELECT * FROM reports WHERE report_id = ?", (rid,)
                    ).fetchone()
                finally:
                    conn.close()
                if r is None:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': f'report not found: {rid}'}, ensure_ascii=False
                    ).encode('utf-8'))
                    return
                d = {k: v for k, v in dict(r).items() if v is not None}
                rp = d.get('report_path')
                if rp:
                    full = rp if os.path.isabs(rp) else os.path.join(BASE_DIR, rp)
                    if os.path.isfile(full):
                        try:
                            with open(full, 'r', encoding='utf-8') as f:
                                d['content_yaml'] = f.read()
                        except Exception:
                            d['content_yaml'] = None
                body = json.dumps(d, ensure_ascii=False, indent=2,
                                  default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/api/report_list'):
            # GET /api/report_list?cmd=cmd_XXX&worker=ashigaru3&limit=20
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                cmd_filter = qs.get('cmd', [None])[0]
                worker = qs.get('worker', [None])[0]
                task_id = qs.get('task', [None])[0]
                limit = int(qs.get('limit', ['20'])[0])

                conn = sqlite3.connect(DB_PATH, timeout=5)
                conn.row_factory = sqlite3.Row
                try:
                    sql = "SELECT * FROM reports"
                    params = []
                    where = []
                    if cmd_filter:
                        where.append("parent_cmd = ?"); params.append(cmd_filter)
                    if worker:
                        where.append("worker_id = ?"); params.append(worker)
                    if task_id:
                        where.append("task_id = ?"); params.append(task_id)
                    if where:
                        sql += " WHERE " + " AND ".join(where)
                    sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)
                    reports = [dict(r) for r in conn.execute(sql, params)]
                finally:
                    conn.close()

                body = json.dumps({'reports': reports, 'shown': len(reports),
                                   'source': 'sqlite'}, ensure_ascii=False,
                                  indent=2, default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/work/'):
            # 静的ファイル配信: /work/ → projects/dozle_kirinuki/work/
            import mimetypes
            from urllib.parse import unquote, urlparse
            parsed = urlparse(self.path)
            rel = unquote(parsed.path[len('/work/'):])
            # パストラバーサル防止
            if '..' in rel:
                self.send_response(403)
                self.end_headers()
                return
            filepath = os.path.join(BASE_DIR, 'projects', 'dozle_kirinuki', 'work', rel)
            if os.path.isfile(filepath):
                body = open(filepath, 'rb').read()
                mime, _ = mimetypes.guess_type(filepath)
                self.send_response(200)
                self.send_header('Content-Type', mime or 'application/octet-stream')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path.startswith('/assets/'):
            # 静的ファイル配信: /assets/ → projects/dozle_kirinuki/assets/
            import mimetypes
            from urllib.parse import unquote, urlparse
            parsed = urlparse(self.path)
            rel = unquote(parsed.path[len('/assets/'):])
            if '..' in rel:
                self.send_response(403)
                self.end_headers()
                return
            filepath = os.path.join(BASE_DIR, 'projects', 'dozle_kirinuki', 'assets', rel)
            if os.path.isfile(filepath):
                body = open(filepath, 'rb').read()
                mime, _ = mimetypes.guess_type(filepath)
                self.send_response(200)
                self.send_header('Content-Type', mime or 'application/octet-stream')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path.startswith('/api/list_panels_json'):
            # ?dir=<相対パス> で対象ディレクトリ限定（同階層のみscan）。指定なしなら work/ 全体
            from urllib.parse import urlparse as _up, parse_qs as _pq, unquote as _uq
            import glob as _glob
            qs = _pq(_up(self.path).query)
            dir_param = (qs.get('dir', [''])[0] or '').strip()
            results = []
            if dir_param:
                if '..' in dir_param or dir_param.startswith('/'):
                    self.send_response(403); self.end_headers(); return
                target_dir = os.path.join(BASE_DIR, _uq(dir_param))
                if os.path.isdir(target_dir):
                    edited_matches = sorted(_glob.glob(os.path.join(target_dir, '*_edited.json')))
                    raw_matches = sorted(_glob.glob(os.path.join(target_dir, '*_raw.json')))
                    all_panels = sorted(_glob.glob(os.path.join(target_dir, 'panels_*.json')))
                    panels_matches = [m for m in all_panels if not m.endswith('_edited.json')]
                    for match in edited_matches + raw_matches + panels_matches:
                        rel = os.path.relpath(match, BASE_DIR)
                        results.append({'name': os.path.basename(match), 'path': rel})
            else:
                work_dir = os.path.join(BASE_DIR, 'projects', 'dozle_kirinuki', 'work')
                if os.path.isdir(work_dir):
                    edited_matches = sorted(_glob.glob(os.path.join(work_dir, '**', '*_edited.json'), recursive=True))
                    raw_matches = sorted(_glob.glob(os.path.join(work_dir, '**', '*_raw.json'), recursive=True))
                    all_panels = sorted(_glob.glob(os.path.join(work_dir, '**', 'panels_*.json'), recursive=True))
                    panels_matches = [m for m in all_panels if not m.endswith('_edited.json')]
                    for match in edited_matches + raw_matches + panels_matches:
                        rel = os.path.relpath(match, BASE_DIR)
                        parent = os.path.basename(os.path.dirname(match))
                        name = os.path.basename(match) + '  [' + parent + ']'
                        results.append({'name': name, 'path': rel})
            body = json.dumps(results, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith('/api/load_raw_candidates'):
            from urllib.parse import unquote, urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            rel_path = unquote(params.get('path', [''])[0])
            if not rel_path:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "path parameter required"}')
                return
            abs_path = os.path.realpath(os.path.join(BASE_DIR, rel_path))
            if not abs_path.startswith(os.path.realpath(BASE_DIR) + os.sep):
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "path outside project directory"}')
                return
            if not os.path.isfile(abs_path):
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "file not found"}')
                return
            try:
                with open(abs_path, encoding='utf-8') as f:
                    body = f.read().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/api/load_panels_json'):
            from urllib.parse import unquote, urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            rel_path = unquote(params.get('path', [''])[0])
            if not rel_path:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "path parameter required"}')
                return
            abs_path = os.path.realpath(os.path.join(BASE_DIR, rel_path))
            if not abs_path.startswith(os.path.realpath(BASE_DIR) + os.sep):
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "path outside project directory"}')
                return
            if not os.path.isfile(abs_path):
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "file not found"}')
                return
            try:
                with open(abs_path, encoding='utf-8') as f:
                    body = f.read().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.split('?')[0] == '/api/agent_health':
            import subprocess as _sp
            try:
                agents = ['karo', 'ashigaru1', 'ashigaru2', 'ashigaru3',
                          'ashigaru4', 'ashigaru5', 'ashigaru6', 'ashigaru7', 'gunshi']
                # Single tmux call: collect all pane agent_ids
                alive_agents = None
                try:
                    r = _sp.run(
                        ['tmux', 'list-panes', '-t', 'multiagent:0',
                         '-F', '#{pane_index}:#{@agent_id}'],
                        capture_output=True, text=True, timeout=5
                    )
                    if r.returncode == 0:
                        alive_agents = set()
                        for line in r.stdout.strip().splitlines():
                            if ':' in line:
                                aid = line.split(':', 1)[1].strip()
                                if aid:
                                    alive_agents.add(aid)
                except Exception:
                    pass  # tmux unavailable — alive_agents stays None

                agents_data = []
                for agent_id in agents:
                    info = {'agent_id': agent_id}

                    # Pane alive
                    if alive_agents is not None:
                        info['pane_alive'] = agent_id in alive_agents
                    else:
                        info['pane_alive'] = None
                        info['reason'] = 'tmux_unavailable'

                    # Inbox last update
                    inbox_path = os.path.join(INBOX_DIR, f'{agent_id}.yaml')
                    try:
                        info['last_inbox_update'] = datetime.fromtimestamp(
                            os.path.getmtime(inbox_path), tz=timezone.utc
                        ).isoformat()
                    except OSError:
                        info['last_inbox_update'] = None

                    # Task info from YAML
                    tasks_path = os.path.join(TASKS_DIR, f'{agent_id}.yaml')
                    info['last_task_status'] = None
                    info['last_task_id'] = None
                    info['current_task_summary'] = None
                    try:
                        with open(tasks_path, encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        tasks = data.get('tasks', []) if isinstance(data, dict) else []
                        if tasks:
                            last = tasks[-1]
                            if isinstance(last, dict):
                                info['last_task_status'] = last.get('status')
                                info['last_task_id'] = last.get('task_id')
                                if last.get('status') == 'assigned':
                                    summary = last.get('purpose') or last.get('description') or ''
                                    info['current_task_summary'] = str(summary)[:50]
                    except Exception:
                        pass  # keep nulls

                    agents_data.append(info)

                payload = {
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                    'agents': agents_data
                }
                body = json.dumps(payload, ensure_ascii=False, default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                # Graceful degradation: never 500
                body = json.dumps({
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                    'error': str(e), 'agents': []
                }, default=str).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        import mimetypes
        from urllib.parse import unquote, urlparse
        if self.path == '/api/save_panels_json':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))
                rel_path = payload.get('path', '')
                data = payload.get('data')
                if not rel_path or data is None:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error": "path and data are required"}')
                    return
                # セキュリティ: プロジェクトディレクトリ外へのアクセス禁止
                abs_path = os.path.realpath(os.path.join(BASE_DIR, rel_path))
                if not abs_path.startswith(os.path.realpath(BASE_DIR) + os.sep):
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error": "path outside project directory"}')
                    return
                with open(abs_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                resp = json.dumps({'status': 'ok', 'path': abs_path}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/suggest_director_notes':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))

                job_id = uuid.uuid4().hex[:8]
                with _jobs_lock:
                    _jobs[job_id] = {'status': 'queued', 'created': datetime.now().isoformat()}
                t = threading.Thread(target=_run_suggest_director_notes, args=(job_id, payload), daemon=True)
                t.start()

                resp = json.dumps({'status': 'processing', 'job_id': job_id}, ensure_ascii=False).encode('utf-8')
                self.send_response(202)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/generate_panels_llm':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))

                job_id = uuid.uuid4().hex[:8]
                with _jobs_lock:
                    _jobs[job_id] = {'status': 'queued', 'created': datetime.now().isoformat()}
                t = threading.Thread(target=_run_generate_panels, args=(job_id, payload), daemon=True)
                t.start()

                resp = json.dumps({'status': 'processing', 'job_id': job_id}, ensure_ascii=False).encode('utf-8')
                self.send_response(202)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/regenerate_partial_with_gemini':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                panels_path = body.get('panels_path', '')
                clip_path = body.get('clip_path', '')
                edited_rows = body.get('edited_rows', [])

                if not panels_path or not clip_path or not edited_rows:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error": "panels_path, clip_path, edited_rows required"}')
                    return

                # パストラバーサル防止
                abs_panels = os.path.realpath(os.path.join(BASE_DIR, panels_path))
                abs_clip = os.path.realpath(clip_path)
                if not abs_panels.startswith(os.path.realpath(BASE_DIR) + os.sep):
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error": "panels_path outside project"}')
                    return

                import tempfile
                job_id = uuid.uuid4().hex[:8]

                # edited_rowsを一時ファイルに保存
                tmp_edited = os.path.join(tempfile.gettempdir(), f'edited_rows_{job_id}.json')
                with open(tmp_edited, 'w', encoding='utf-8') as f:
                    json.dump(edited_rows, f, ensure_ascii=False)

                # 出力パス: panels_xxx_v2.json （元データ保護）
                output_path = panels_path.replace('.json', '_v2.json')

                GENERATE_PANELS_SCRIPT = os.path.join(BASE_DIR, 'projects/dozle_kirinuki/scripts/generate_panel_candidates.py')
                abs_base_panels = abs_panels

                with _jobs_lock:
                    _jobs[job_id] = {'status': 'queued', 'created': datetime.now().isoformat()}

                def _run_partial_regen(jid, clip, tmp_json, out):
                    try:
                        _jobs[jid]['status'] = 'running'
                        cmd = [
                            'python3', GENERATE_PANELS_SCRIPT,
                            '--clip', clip,
                            '--edited-rows-json', tmp_json,
                            '--respect-edits',
                            '--output', os.path.join(BASE_DIR, out),
                        ]
                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = proc.communicate(timeout=600)
                        if proc.returncode == 0:
                            with _jobs_lock:
                                _jobs[jid] = {'status': 'done', 'output': out, 'error': None}
                        else:
                            err = stderr.decode('utf-8', errors='replace')[:500]
                            with _jobs_lock:
                                _jobs[jid] = {'status': 'error', 'output': None, 'error': err}
                    except Exception as e:
                        with _jobs_lock:
                            _jobs[jid] = {'status': 'error', 'output': None, 'error': str(e)}

                t = threading.Thread(
                    target=_run_partial_regen,
                    args=(job_id, abs_clip, tmp_edited, output_path),
                    daemon=True
                )
                t.start()

                resp = json.dumps({'status': 'processing', 'job_id': job_id}, ensure_ascii=False).encode('utf-8')
                self.send_response(202)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/cmd_create':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))

                # --- Required field validation (lord_original 必須化 cmd_1474) ---
                required = ['id', 'purpose', 'lord_original']
                missing = [f for f in required if not body.get(f)]
                if missing:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': f'Missing required fields: {missing}'}).encode('utf-8'))
                    return

                cmd_id = body['id']

                # --- flock + YAML append ---
                import fcntl
                lock_path = SHOGUN_TO_KARO + '.lock'
                with open(lock_path, 'w') as lock_f:
                    fcntl.flock(lock_f, fcntl.LOCK_EX)

                    try:
                        # Read existing
                        with open(SHOGUN_TO_KARO, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)

                        commands = data.get('commands', [])

                        # Duplicate check
                        if any(c.get('id') == cmd_id for c in commands):
                            self.send_response(409)
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'error': f'Duplicate cmd id: {cmd_id}'}).encode('utf-8'))
                            return

                        # Build entry: defaults first
                        entry = {
                            'id': cmd_id,
                            'status': body.get('status', 'pending'),
                            'priority': body.get('priority', 'medium'),
                            'purpose': body['purpose'],
                            'timestamp': body.get('timestamp', datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%dT%H:%M:%S+09:00')),
                        }
                        # Pass-through: body の任意キーを entry に透過 (cmd_1474)
                        # depends_on / notes / redo_of / cancelled_at / cancelled_reason /
                        # implementation_flow / lord_original / command / project /
                        # north_star / acceptance_criteria / assigned_to / issued_at 等
                        # 全て自動で entry に反映される（API改修不要で拡張可能）
                        RESERVED = {'id', 'status', 'priority', 'purpose', 'timestamp'}
                        for k, v in body.items():
                            if k not in RESERVED and v is not None:
                                entry[k] = v

                        commands.append(entry)
                        data['commands'] = commands

                        # Write back (atomic-ish via write + flush)
                        with open(SHOGUN_TO_KARO, 'w', encoding='utf-8') as f:
                            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

                        entry_line = sum(1 for c in commands)
                    finally:
                        fcntl.flock(lock_f, fcntl.LOCK_UN)

                # === p2 dual-path: SQLite INSERT (after successful YAML write) ===
                storage_backend = os.environ.get('STORAGE_BACKEND', 'dual')
                if storage_backend != 'yaml':
                    try:
                        import sqlite3 as _sqlite3
                        _db_path = os.path.join(BASE_DIR, 'queue', 'cmds.db')
                        _conn = _sqlite3.connect(_db_path, timeout=5)
                        _conn.execute('PRAGMA busy_timeout = 5000')
                        _crit_json = json.dumps(body.get('acceptance_criteria', []), ensure_ascii=False) if body.get('acceptance_criteria') else None
                        _notes_json = json.dumps(body.get('notes', []), ensure_ascii=False) if body.get('notes') else None
                        _dep_json = json.dumps(body.get('depends_on', []), ensure_ascii=False) if body.get('depends_on') else None
                        _conn.execute('''INSERT OR IGNORE INTO commands
                            (id, status, priority, purpose, lord_original, command_text,
                             assigned_to, north_star, project, parent_cmd,
                             acceptance_criteria_json, depends_on_json, notes_json,
                             timestamp, full_yaml_blob)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (cmd_id, entry.get('status', 'pending'), entry.get('priority', 'medium'),
                             body['purpose'], body.get('lord_original'), body.get('command'),
                             body.get('assigned_to'), body.get('north_star'), body.get('project'),
                             body.get('parent_cmd'), _crit_json, _dep_json, _notes_json,
                             entry.get('timestamp'), json.dumps(entry, ensure_ascii=False)))
                        _conn.commit()
                        _conn.close()
                    except Exception as _sqe:
                        print(f"[dual_path] SQLite INSERT WARN: {_sqe}")

                # === cmd_1491: cmd_history JSON保管 + inbox自動通知 ===
                # cmd_history JSON保管 (将来audit_logテーブル代替まで・SQLite p2完了後は廃止)
                try:
                    history_dir = os.path.join(BASE_DIR, 'queue', 'cmd_history')
                    os.makedirs(history_dir, exist_ok=True)
                    history_path = os.path.join(history_dir, f'{cmd_id}_request.json')
                    with open(history_path, 'w', encoding='utf-8') as hf:
                        json.dump(body, hf, ensure_ascii=False, indent=2)
                except Exception as he:
                    print(f"[cmd_history] WARN: {he}")

                # inbox自動通知 (notify_karo=true デフォルト・kill_switch:false でskip)
                notify_karo = body.get('notify_karo', True)
                if notify_karo:
                    try:
                        import secrets
                        notify_message = body.get('notify_message') or f"{cmd_id}発令済(API)。purpose: {body['purpose'][:80]}"
                        inbox_path = os.path.join(BASE_DIR, 'queue', 'inbox', 'karo.yaml')
                        inbox_lock = inbox_path + '.lock'
                        now_jst = datetime.now(timezone(timedelta(hours=9)))
                        msg_id = f"msg_{now_jst.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
                        new_msg = {
                            'id': msg_id,
                            'from': 'shogun',
                            'type': 'cmd_new',
                            'content': notify_message,
                            'read': False,
                            'timestamp': now_jst.strftime('%Y-%m-%dT%H:%M:%S+09:00')
                        }
                        with open(inbox_lock, 'w') as ilf:
                            fcntl.flock(ilf, fcntl.LOCK_EX)
                            try:
                                with open(inbox_path, 'r', encoding='utf-8') as f:
                                    inbox_data = yaml.safe_load(f) or {'messages': []}
                                if not isinstance(inbox_data, dict):
                                    inbox_data = {'messages': []}
                                inbox_data.setdefault('messages', []).append(new_msg)
                                with open(inbox_path, 'w', encoding='utf-8') as f:
                                    yaml.dump(inbox_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
                            finally:
                                fcntl.flock(ilf, fcntl.LOCK_UN)
                    except Exception as ie:
                        print(f"[inbox_notify] WARN: {ie}")

                resp = json.dumps({'ok': True, 'cmd_id': cmd_id, 'entry_line': entry_line, 'fields': list(entry.keys()), 'notified': notify_karo}, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/inbox_write':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))

                target = body.get('to', '').strip()
                message = body.get('message', '').strip()
                msg_type = body.get('type', 'wake_up')
                from_agent = body.get('from', 'unknown')

                if not target or not message:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'to and message are required'}).encode('utf-8'))
                    return

                script_path = os.path.join(BASE_DIR, 'scripts', 'inbox_write.sh')
                result = subprocess.run(
                    ['bash', script_path, target, message, msg_type, from_agent],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode != 0:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': result.stderr.strip()[:500]}).encode('utf-8'))
                    return

                actual_msg_id = result.stdout.strip()
                now_jst = datetime.now(timezone(timedelta(hours=9)))
                resp = json.dumps({
                    'success': True,
                    'msg_id': actual_msg_id,
                    'timestamp': now_jst.strftime('%Y-%m-%dT%H:%M:%S')
                }, ensure_ascii=False).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/task_create':
            # POST /api/task_create — 家老が tasks YAML 追記 + SQLite tasks INSERT (dual-path)
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                required = ['agent', 'task_id', 'status']
                missing = [f for f in required if not body.get(f)]
                if missing:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': f'Missing required: {missing}'}, ensure_ascii=False
                    ).encode('utf-8'))
                    return

                agent = body['agent']
                task_id = body['task_id']
                yaml_path = os.path.join(TASKS_DIR, f'{agent}.yaml')
                lock_path = yaml_path + '.lock'
                now_jst = datetime.now(timezone(timedelta(hours=9))).isoformat()
                task_entry = {k: v for k, v in body.items() if v is not None}
                task_entry.setdefault('timestamp', now_jst)

                import fcntl as _fc
                with open(lock_path, 'w') as _lf:
                    _fc.flock(_lf, _fc.LOCK_EX)
                    if os.path.exists(yaml_path):
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            ydata = yaml.safe_load(f) or {}
                    else:
                        ydata = {}
                    tlist = ydata.setdefault('tasks', [])
                    if any(t.get('task_id') == task_id for t in tlist):
                        self.send_response(409)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(
                            {'error': f'task_id exists: {task_id}'}
                        ).encode('utf-8'))
                        return
                    tlist.append(task_entry)
                    with open(yaml_path, 'w', encoding='utf-8') as f:
                        yaml.safe_dump(ydata, f, allow_unicode=True,
                                       sort_keys=False, default_flow_style=False)

                # SQLite dual-path
                try:
                    _conn = sqlite3.connect(DB_PATH, timeout=5)
                    _conn.execute('''INSERT OR REPLACE INTO tasks
                        (task_id, agent, parent_cmd, status, priority, title,
                         project, description, target_path, procedure, steps,
                         acceptance_criteria_json, notes_json, params_json,
                         assigned_to, assignee, report_to, safety, redo_of,
                         timestamp, full_yaml_blob)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                        task_id, agent, body.get('parent_cmd'), body['status'],
                        body.get('priority'), body.get('title'), body.get('project'),
                        body.get('description'), body.get('target_path'),
                        body.get('procedure'), body.get('steps'),
                        json.dumps(body.get('acceptance_criteria', []), ensure_ascii=False),
                        json.dumps(body.get('notes', []), ensure_ascii=False),
                        json.dumps(body.get('params', {}), ensure_ascii=False),
                        body.get('assigned_to'), body.get('assignee'),
                        body.get('report_to'), body.get('safety'),
                        body.get('redo_of'),
                        task_entry['timestamp'],
                        yaml.safe_dump(task_entry, allow_unicode=True),
                    ))
                    _conn.commit()
                    _conn.close()
                except Exception as _e:
                    print(f"[Dashboard] WARN sqlite tasks INSERT failed: {_e}")

                resp = json.dumps({
                    'success': True, 'task_id': task_id, 'agent': agent,
                    'yaml_path': os.path.relpath(yaml_path, BASE_DIR),
                    'timestamp': task_entry['timestamp'],
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/dashboard_update':
            # POST /api/dashboard_update — dashboard.md 書き換え (家老の Edit 直叩き廃止)
            # body: {"content": "<markdown 全文>"} で全文上書き
            # body: {"section": "## 🚨要対応", "section_content": "..."} で該当 section 置換
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                section = body.get('section')
                if section is not None and 'section_content' in body:
                    # 部分置換: 既存 dashboard.md の section から次の同レベル見出しまでを置換
                    if not os.path.exists(DASHBOARD_MD):
                        self.send_response(404)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'dashboard.md not found'}).encode())
                        return
                    with open(DASHBOARD_MD, 'r', encoding='utf-8') as f:
                        text = f.read()
                    import re
                    # 同じヘッダーレベル (例: ## ) で次のヘッダーまでを匹配
                    level_match = re.match(r'^(#+)\s', section)
                    if not level_match:
                        self.send_response(400)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(
                            {'error': 'section must start with markdown header (e.g., "## 🚨要対応")'},
                            ensure_ascii=False).encode('utf-8'))
                        return
                    level = level_match.group(1)
                    pattern = re.compile(
                        re.escape(section) + r'.*?(?=\n' + re.escape(level) + r' |\Z)',
                        re.DOTALL,
                    )
                    new_block = section + '\n' + body['section_content'].rstrip('\n') + '\n'
                    if pattern.search(text):
                        new_text = pattern.sub(new_block, text, count=1)
                    else:
                        # section 不在 → 末尾に追加
                        new_text = text.rstrip('\n') + '\n\n' + new_block
                else:
                    content = body.get('content')
                    if content is None:
                        self.send_response(400)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(
                            {'error': 'content or (section + section_content) required'},
                            ensure_ascii=False).encode('utf-8'))
                        return
                    new_text = content if content.endswith('\n') else content + '\n'

                # backup + atomic replace
                import shutil
                bak = DASHBOARD_MD + '.bak'
                if os.path.exists(DASHBOARD_MD):
                    shutil.copy2(DASHBOARD_MD, bak)
                tmp = DASHBOARD_MD + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write(new_text)
                os.replace(tmp, DASHBOARD_MD)

                resp = json.dumps({
                    'success': True,
                    'mode': 'section' if section else 'full',
                    'bytes_written': len(new_text.encode('utf-8')),
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/report_create':
            # POST /api/report_create — 足軽/軍師が reports YAML 作成 + SQLite INSERT
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                required = ['report_id', 'worker_id', 'status']
                missing = [f for f in required if not body.get(f)]
                if missing:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': f'Missing required: {missing}'}, ensure_ascii=False
                    ).encode('utf-8'))
                    return

                report_id = body['report_id']
                reports_dir = os.path.join(BASE_DIR, 'queue', 'reports')
                os.makedirs(reports_dir, exist_ok=True)
                yaml_path = body.get('report_path') or os.path.join(
                    reports_dir, f'{report_id}.yaml'
                )
                # 絶対パス禁止 (パストラバーサル防止) と queue/reports/ 配下強制
                yaml_abs = os.path.realpath(yaml_path)
                if not yaml_abs.startswith(os.path.realpath(reports_dir) + os.sep):
                    yaml_path = os.path.join(reports_dir, f'{report_id}.yaml')
                    yaml_abs = os.path.realpath(yaml_path)
                if os.path.exists(yaml_abs):
                    self.send_response(409)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': f'report exists: {os.path.relpath(yaml_abs, BASE_DIR)}'}
                    ).encode('utf-8'))
                    return
                now_jst = datetime.now(timezone(timedelta(hours=9))).isoformat()
                report_entry = {k: v for k, v in body.items() if v is not None}
                report_entry.setdefault('timestamp', now_jst)

                with open(yaml_abs, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(report_entry, f, allow_unicode=True,
                                   sort_keys=False, default_flow_style=False)

                # SQLite dual-path
                try:
                    _conn = sqlite3.connect(DB_PATH, timeout=5)
                    _conn.execute('''INSERT OR REPLACE INTO reports
                        (report_id, worker_id, task_id, parent_cmd, status,
                         qa_decision, timestamp, report_path, summary)
                        VALUES (?,?,?,?,?,?,?,?,?)''', (
                        report_id, body['worker_id'], body.get('task_id'),
                        body.get('parent_cmd'), body['status'],
                        body.get('qa_decision'), report_entry['timestamp'],
                        os.path.relpath(yaml_abs, BASE_DIR),
                        body.get('summary'),
                    ))
                    _conn.commit()
                    _conn.close()
                except Exception as _e:
                    print(f"[Dashboard] WARN sqlite reports INSERT failed: {_e}")

                resp = json.dumps({
                    'success': True, 'report_id': report_id,
                    'yaml_path': os.path.relpath(yaml_abs, BASE_DIR),
                    'timestamp': report_entry['timestamp'],
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/api/inbox_mark_read':
            # POST /api/inbox_mark_read — cmd_1495 既読化 API
            # body: {"agent":"karo","ids":["msg_xxx",...]} か {"agent":"karo","all_unread":true}
            #   actor 任意 (audit_log 記録用)。SQLite primary + YAML dual-path。
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
                agent = (body.get('agent') or '').strip()
                ids = body.get('ids') or []
                all_unread = bool(body.get('all_unread', False))
                actor = body.get('actor') or agent or 'unknown'

                if not agent:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'agent required'}).encode('utf-8'))
                    return
                if not ids and not all_unread:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': 'ids or all_unread required'}).encode('utf-8'))
                    return

                now_iso = datetime.now(timezone.utc).isoformat()
                updated = 0
                conn = sqlite3.connect(DB_PATH, timeout=5)
                try:
                    if ids:
                        placeholders = ','.join('?' * len(ids))
                        sql = (f"UPDATE inbox_messages SET read=1, read_at=?, actor=? "
                               f"WHERE id IN ({placeholders}) AND agent=? AND read=0")
                        params = [now_iso, actor] + list(ids) + [agent]
                        cur = conn.execute(sql, params)
                        updated = cur.rowcount
                    else:  # all_unread
                        cur = conn.execute(
                            "UPDATE inbox_messages SET read=1, read_at=?, actor=? "
                            "WHERE agent=? AND read=0",
                            (now_iso, actor, agent)
                        )
                        updated = cur.rowcount
                    conn.commit()
                finally:
                    conn.close()

                # YAML dual-path (cmd_1494 以降 YAML は基本空・残骸対応)
                yaml_updated = 0
                try:
                    import fcntl as _fcntl
                    yaml_path = os.path.join(INBOX_DIR, f'{agent}.yaml')
                    if os.path.exists(yaml_path):
                        lock_path = yaml_path + '.lock'
                        with open(lock_path, 'w') as lf:
                            _fcntl.flock(lf, _fcntl.LOCK_EX)
                            try:
                                with open(yaml_path, 'r', encoding='utf-8') as f:
                                    ydata = yaml.safe_load(f) or {'messages': []}
                                if not isinstance(ydata, dict):
                                    ydata = {'messages': []}
                                changed = False
                                for m in ydata.get('messages', []):
                                    if not isinstance(m, dict):
                                        continue
                                    mid = m.get('id') or m.get('message_id')
                                    match = (ids and mid in ids) or all_unread
                                    if match and not m.get('read', False):
                                        m['read'] = True
                                        m['read_at'] = now_iso
                                        yaml_updated += 1
                                        changed = True
                                if changed:
                                    with open(yaml_path, 'w', encoding='utf-8') as f:
                                        yaml.dump(ydata, f, allow_unicode=True,
                                                  sort_keys=False,
                                                  default_flow_style=False)
                            finally:
                                _fcntl.flock(lf, _fcntl.LOCK_UN)
                except Exception as ye:
                    print(f"[mark_read YAML] WARN: {ye}")

                resp = json.dumps({
                    'ok': True, 'updated': updated, 'yaml_updated': yaml_updated,
                    'agent': agent,
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
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
    print("Agent status detection: DB-driven (inbox_messages table).")
    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
