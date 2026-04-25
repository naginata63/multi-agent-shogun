#!/usr/bin/env python3
"""sqlite_yaml_audit.py — YAML vs SQLite dual-path consistency checker.

Compares record counts and content hashes between YAML files and SQLite tables.
Exit 0 = all match. Exit 1 = discrepancies found (+ ntfy alert if --notify-on-fail).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "queue", "cmds.db")


def _hash_obj(obj):
    """Deterministic JSON hash for comparison."""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _load_yaml(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def audit_commands():
    """Compare shogun_to_karo.yaml vs commands table."""
    yaml_path = os.path.join(BASE_DIR, "queue", "shogun_to_karo.yaml")
    data = _load_yaml(yaml_path)
    yaml_cmds = data.get("commands", []) if data else []
    yaml_count = len(yaml_cmds)

    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, status, priority, purpose, timestamp FROM commands").fetchall()
    conn.close()

    db_count = len(rows)
    db_ids = {r["id"] for r in rows}
    yaml_ids = {c.get("id") for c in yaml_cmds}

    missing_in_db = yaml_ids - db_ids
    extra_in_db = db_ids - yaml_ids

    diffs = []
    if missing_in_db:
        diffs.append(f"commands: {len(missing_in_db)} in YAML but missing from SQLite: {missing_in_db}")
    if extra_in_db:
        diffs.append(f"commands: {len(extra_in_db)} in SQLite but missing from YAML: {extra_in_db}")

    # Content hash comparison for matched records
    db_map = {r["id"]: r for r in rows}
    for c in yaml_cmds:
        cid = c.get("id")
        if cid not in db_map:
            continue
        db_row = db_map[cid]
        yaml_hash = _hash_obj({"status": c.get("status"), "priority": c.get("priority"), "purpose": c.get("purpose")})
        db_hash = _hash_obj({"status": db_row["status"], "priority": db_row["priority"], "purpose": db_row["purpose"] or ""})
        if yaml_hash != db_hash:
            diffs.append(f"commands/{cid}: hash mismatch yaml={yaml_hash} db={db_hash}")

    return yaml_count, db_count, diffs


def audit_inbox():
    """Compare queue/inbox/*.yaml vs inbox_messages table."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=5)
    db_rows = conn.execute("SELECT id, agent, from_agent, type, content, read, timestamp FROM inbox_messages").fetchall()
    conn.close()
    db_count = len(db_rows)
    db_ids = {r[0] for r in db_rows}

    inbox_dir = os.path.join(BASE_DIR, "queue", "inbox")
    yaml_msgs = []
    for fn in os.listdir(inbox_dir):
        if not fn.endswith(".yaml"):
            continue
        data = _load_yaml(os.path.join(inbox_dir, fn))
        if data and data.get("messages"):
            yaml_msgs.extend(data["messages"])

    yaml_count = len(yaml_msgs)
    yaml_ids = {m.get("id") for m in yaml_msgs}

    missing_in_db = yaml_ids - db_ids
    extra_in_db = db_ids - yaml_ids

    diffs = []
    if missing_in_db:
        diffs.append(f"inbox: {len(missing_in_db)} in YAML but missing from SQLite: {missing_in_db}")
    if extra_in_db:
        diffs.append(f"inbox: {len(extra_in_db)} in SQLite but missing from YAML: {extra_in_db}")

    return yaml_count, db_count, diffs


def audit_tasks():
    """Compare queue/tasks/*.yaml vs tasks table."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=5)
    db_rows = conn.execute("SELECT task_id, agent, status, parent_cmd FROM tasks").fetchall()
    conn.close()
    db_count = len(db_rows)
    db_map = {r[0]: r for r in db_rows}

    tasks_dir = os.path.join(BASE_DIR, "queue", "tasks")
    yaml_tasks = []
    for fn in os.listdir(tasks_dir):
        if not fn.endswith(".yaml"):
            continue
        data = _load_yaml(os.path.join(tasks_dir, fn))
        if data and data.get("tasks"):
            for t in data["tasks"]:
                t["_source_file"] = fn
            yaml_tasks.extend(data["tasks"])

    yaml_count = len(yaml_tasks)
    diffs = []
    for t in yaml_tasks:
        tid = t.get("task_id")
        if tid not in db_map:
            diffs.append(f"tasks: {tid} in YAML ({t.get('_source_file')}) but missing from SQLite")
        else:
            db_row = db_map[tid]
            yaml_hash = _hash_obj({"status": t.get("status"), "agent": t.get("assigned_to") or t.get("agent"), "parent_cmd": t.get("parent_cmd")})
            db_hash = _hash_obj({"status": db_row[2], "agent": db_row[1], "parent_cmd": db_row[3]})
            if yaml_hash != db_hash:
                diffs.append(f"tasks/{tid}: hash mismatch yaml={yaml_hash} db={db_hash}")

    db_ids = {r[0] for r in db_rows}
    yaml_ids = {t.get("task_id") for t in yaml_tasks}
    extra_in_db = db_ids - yaml_ids
    if extra_in_db:
        diffs.append(f"tasks: {len(extra_in_db)} in SQLite but missing from YAML: {extra_in_db}")

    return yaml_count, db_count, diffs


def audit_reports():
    """Compare queue/reports/*.yaml vs reports table."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=5)
    db_count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    conn.close()

    reports_dir = os.path.join(BASE_DIR, "queue", "reports")
    yaml_count = 0
    for fn in os.listdir(reports_dir):
        if fn.endswith(".yaml"):
            yaml_count += 1

    diffs = []
    if yaml_count != db_count:
        diffs.append(f"reports: count mismatch yaml={yaml_count} db={db_count}")

    return yaml_count, db_count, diffs


def send_ntfy(msg):
    try:
        subprocess.run(
            ["bash", os.path.join(BASE_DIR, "scripts", "ntfy.sh"), msg],
            timeout=10, capture_output=True
        )
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="SQLite vs YAML audit")
    parser.add_argument("--notify-on-fail", action="store_true", help="Send ntfy alert on discrepancy")
    args = parser.parse_args()

    all_diffs = []
    tables = [
        ("commands", audit_commands),
        ("inbox_messages", audit_inbox),
        ("tasks", audit_tasks),
        ("reports", audit_reports),
    ]

    for table_name, audit_fn in tables:
        try:
            yaml_n, db_n, diffs = audit_fn()
            status = "OK" if not diffs else "DIFF"
            print(f"[{status}] {table_name}: yaml={yaml_n} db={db_n}")
            for d in diffs:
                print(f"  {d}")
            all_diffs.extend(diffs)
        except Exception as e:
            print(f"[ERR] {table_name}: {e}")
            all_diffs.append(f"{table_name}: audit error: {e}")

    print(f"\n=== RESULT: {len(all_diffs)} discrepancies ===")
    if all_diffs and args.notify_on_fail:
        send_ntfy(f"SQLite audit FAIL: {len(all_diffs)} discrepancies found")

    sys.exit(1 if all_diffs else 0)


if __name__ == "__main__":
    main()
