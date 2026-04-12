#!/usr/bin/env python3
"""MCP Dashboard Web UI v2 - Port 8770
DB-driven auto-detection: R1-R7 rules, R7 syncs dashboard.md 🚨要対応."""

import http.server
import json
import os
import re
import sqlite3
import yaml
from datetime import datetime, timezone, timedelta

PORT = 8770
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_SCRIPT_DIR, "..", "..", "data", "dashboard.db")
BASE_DIR = os.path.join(_SCRIPT_DIR, "..", "..")
TASKS_DIR = os.path.join(BASE_DIR, "queue", "tasks")
INBOX_DIR = os.path.join(BASE_DIR, "queue", "inbox")
SHOGUN_TO_KARO = os.path.join(BASE_DIR, "queue", "shogun_to_karo.yaml")
DASHBOARD_MD = os.path.join(BASE_DIR, "dashboard.md")

# Status values that mean "done / no longer active"
DONE_STATUSES = {"done", "cancelled", "superseded", "done_ng"}
ACTIVE_STATUSES = {"pending", "assigned", "in_progress", "blocked"}
_EXCLUDED_AGENTS_R5 = {"pending", "archive"}

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
        SELECT type, created_at,
               CASE WHEN to_agent = ? THEN 'in' ELSE 'out' END AS direction
        FROM messages
        WHERE to_agent = ? OR from_agent = ?
        ORDER BY created_at DESC
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
    """DingTalk音声QCのリアルタイム統計"""
    log_path = os.path.join(BASE_DIR, "work", "dingtalk_qc", "qc_log.jsonl")
    if not os.path.isfile(log_path):
        return None
    try:
        total = confirmed = skipped = error = 0
        sims = []
        vols = []
        with open(log_path) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    total += 1
                    action = d.get("action", "")
                    if "確認済み" in action: confirmed += 1
                    elif "スキップ" in action: skipped += 1
                    elif "エラー" in action: error += 1
                    sim = d.get("similarity", -1)
                    if sim >= 0: sims.append(sim)
                    vol = d.get("mean_volume_db")
                    if vol is not None: vols.append(vol)
                except: pass
        import subprocess
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
            "earned": total * 9,
            "running": running,
        }
    except:
        return None


def get_dashboard_data():
    conn = get_db()

    # SQLite messages (Phase 4 DB)
    db_messages = query_db(conn, "SELECT * FROM messages ORDER BY created_at DESC LIMIT 20")
    db_msg_count = query_db(conn, "SELECT COUNT(*) as c FROM messages")
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
        elif self.path == '/api/list_panels_json':
            import glob as _glob
            work_dir = os.path.join(BASE_DIR, 'projects', 'dozle_kirinuki', 'work')
            results = []
            if os.path.isdir(work_dir):
                panels_matches = sorted(_glob.glob(os.path.join(work_dir, '**', 'panels_*.json'), recursive=True))
                raw_matches = sorted(_glob.glob(os.path.join(work_dir, '**', '*_raw.json'), recursive=True))
                for match in panels_matches + raw_matches:
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

                scene_desc = payload.get('scene_desc', '')
                situation = payload.get('situation', '')
                lines = payload.get('lines', [])
                char_name = payload.get('char_name', '')
                new_expression_file = payload.get('new_expression_file', '')
                director_notes = payload.get('director_notes', '')

                # expression_design_v5.md を読み込む（キャラクター性格情報）
                expr_design_path = os.path.join(BASE_DIR, 'projects/dozle_kirinuki/context/expression_design_v5.md')
                expr_design_text = ''
                if os.path.exists(expr_design_path):
                    with open(expr_design_path, 'r', encoding='utf-8') as f:
                        expr_design_text = f.read()[:3000]  # 最初の3000文字のみ（コスト節約）

                ref_images = payload.get('ref_images', [])
                shot_type = payload.get('shot_type', '')

                lines_text = '\n'.join(lines) if lines else '（セリフなし）'

                # ref_imagesからファイル名説明を自動生成
                KOMAWARI_DESC = {
                    'S1_A.png': '全面1コマ',
                    'S2_A.png': '上大70%+下小30%', 'S2_B.png': '上小30%+下大70%',
                    'S2_C.png': '縦割り右小30%+左大70%', 'S2_D.png': '縦割り右大70%+左小30%',
                    'S2_E.png': '均等縦割り',
                    'T1.png': '全面1コマ',
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

                import subprocess
                result = subprocess.run(
                    ['claude', '-p', '--model', 'sonnet', prompt],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    raise Exception(f'Claude CLI error: {result.stderr[:200]}')
                suggested = result.stdout.strip()

                resp = json.dumps({'status': 'ok', 'suggested': suggested}, ensure_ascii=False).encode('utf-8')
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
    print("Agent status detection: DB-driven (messages table).")
    server = http.server.HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
