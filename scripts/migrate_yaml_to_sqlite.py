#!/usr/bin/env python3
"""Migrate YAML queue files to SQLite database.

Usage:
    python3 scripts/migrate_yaml_to_sqlite.py --dry-run --verbose --output-db /tmp/dryrun_output.sql
    python3 scripts/migrate_yaml_to_sqlite.py --output-db queue/cmds.db

Reads: queue/shogun_to_karo.yaml, queue/inbox/*.yaml, queue/tasks/*.yaml, queue/reports/*.yaml
Writes: SQLite DB (or SQL dump in dry-run mode)
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
QUEUE_DIR = os.path.join(REPO_ROOT, "queue")


def parse_args():
    p = argparse.ArgumentParser(description="Migrate YAML queue to SQLite")
    p.add_argument("--dry-run", action="store_true", help="No DB write; output SQL to file")
    p.add_argument("--verbose", action="store_true", help="Detailed logging")
    p.add_argument("--output-db", required=True, help="Output DB path or SQL file (dry-run)")
    return p.parse_args()


def log(msg, verbose_only=False):
    if not verbose_only:
        print(msg, flush=True)


def load_yaml(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        log(f"WARN: YAML parse error in {path}: {e}")
        return None


def json_or_null(obj):
    if obj is None:
        return "NULL"
    return json.dumps(obj, ensure_ascii=False)


def sql_escape(val):
    if val is None:
        return "NULL"
    s = str(val).replace("'", "''")
    return f"'{s}'"


# ── commands ──────────────────────────────────────────────

def migrate_commands(data, stats):
    """Parse shogun_to_karo.yaml (list of command dicts)."""
    items = data if isinstance(data, list) else data.get("commands", [])
    rows = []
    for cmd in items:
        if not isinstance(cmd, dict):
            stats["commands_skip"] += 1
            continue
        cid = cmd.get("id")
        if not cid:
            stats["commands_skip"] += 1
            continue
        row = {
            "id": cid,
            "status": cmd.get("status", "pending"),
            "priority": cmd.get("priority"),
            "purpose": cmd.get("purpose", ""),
            "lord_original": cmd.get("lord_original"),
            "command_text": cmd.get("command"),
            "assigned_to": cmd.get("assigned_to"),
            "north_star": cmd.get("north_star"),
            "project": cmd.get("project"),
            "parent_cmd": cmd.get("parent_cmd"),
            "acceptance_criteria_json": json_or_null(cmd.get("acceptance_criteria")),
            "depends_on_json": json_or_null(cmd.get("depends_on")),
            "notes_json": json_or_null(cmd.get("notes")),
            "implementation_flow": cmd.get("implementation_flow"),
            "verify_guidance": cmd.get("verify_guidance"),
            "completion_note": cmd.get("completion_note"),
            "cancelled_reason": cmd.get("cancelled_reason"),
            "redo_of": cmd.get("redo_of"),
            "timestamp": cmd.get("timestamp", ""),
            "issued_at": cmd.get("issued_at"),
            "started_at": cmd.get("started_at"),
            "revised_at": cmd.get("revised_at"),
            "completed_at": cmd.get("completed_at"),
            "cancelled_at": cmd.get("cancelled_at"),
            "full_yaml_blob": None,
        }
        rows.append(row)
        stats["commands_ok"] += 1
    return rows


# ── inbox_messages ────────────────────────────────────────

def migrate_inbox(agent_name, data, stats):
    """Parse queue/inbox/{agent}.yaml."""
    messages = data.get("messages", []) if isinstance(data, dict) else data
    rows = []
    for msg in messages:
        if not isinstance(msg, dict):
            stats["inbox_skip"] += 1
            continue
        mid = msg.get("id")
        if not mid:
            stats["inbox_skip"] += 1
            continue
        row = {
            "id": mid,
            "agent": agent_name,
            "from_agent": msg.get("from", ""),
            "type": msg.get("type", ""),
            "content": msg.get("content", ""),
            "read": 1 if msg.get("read") else 0,
            "timestamp": msg.get("timestamp", ""),
            "read_at": msg.get("read_at"),
            "actor": msg.get("actor"),
        }
        rows.append(row)
        stats["inbox_ok"] += 1
    return rows


# ── tasks ─────────────────────────────────────────────────

def migrate_tasks(agent_name, data, stats):
    """Parse queue/tasks/{agent}.yaml."""
    task_list = data.get("tasks", []) if isinstance(data, dict) else data
    rows = []
    for item in task_list:
        if not isinstance(item, dict):
            stats["tasks_skip"] += 1
            continue
        t = item.get("task", item)
        tid = t.get("task_id")
        if not tid:
            stats["tasks_skip"] += 1
            continue
        row = {
            "task_id": tid,
            "agent": agent_name,
            "parent_cmd": t.get("parent_cmd"),
            "bloom_level": t.get("bloom_level"),
            "status": t.get("status", "assigned"),
            "priority": t.get("priority"),
            "title": t.get("title"),
            "project": t.get("project"),
            "description": t.get("description"),
            "target_path": t.get("target_path"),
            "procedure": t.get("procedure"),
            "steps": t.get("steps"),
            "acceptance_criteria_json": json_or_null(t.get("acceptance_criteria")),
            "notes_json": json_or_null(t.get("notes")),
            "params_json": json_or_null(t.get("params")),
            "assigned_to": t.get("assigned_to"),
            "assignee": t.get("assignee"),
            "report_to": t.get("report_to"),
            "safety": t.get("safety"),
            "result": t.get("result"),
            "redo_of": t.get("redo_of"),
            "blocked_reason": t.get("blocked_reason"),
            "blocked_at": t.get("blocked_at"),
            "completed_at": t.get("completed_at"),
            "report_path": t.get("report_path"),
            "qa_decision": t.get("qa_decision"),
            "timestamp": t.get("timestamp", ""),
            "started_at": t.get("started_at"),
            "full_yaml_blob": None,
        }
        rows.append(row)
        stats["tasks_ok"] += 1
    return rows


# ── reports ───────────────────────────────────────────────

def migrate_reports(path, data, stats):
    """Parse queue/reports/*.yaml."""
    if not isinstance(data, dict):
        stats["reports_skip"] += 1
        return []
    rid = data.get("report_id") or os.path.splitext(os.path.basename(path))[0]
    row = {
        "report_id": rid,
        "worker_id": data.get("worker_id", ""),
        "task_id": data.get("task_id"),
        "parent_cmd": data.get("parent_cmd"),
        "status": data.get("status", "done"),
        "qa_decision": data.get("qa_decision"),
        "timestamp": data.get("timestamp", ""),
        "report_path": path,
        "summary": None,
        "result_json": json_or_null(data.get("result")),
        "files_modified_json": json_or_null(data.get("files_modified")),
        "notes_json": json_or_null(data.get("notes")),
        "skill_candidate_json": json_or_null(data.get("skill_candidate")),
        "hotfix_notes_json": json_or_null(data.get("hotfix_notes")),
        "north_star_alignment_json": json_or_null(data.get("north_star_alignment")),
        "purpose_gap": data.get("purpose_gap"),
        "full_yaml_blob": None,
    }
    stats["reports_ok"] += 1
    return [row]


# ── SQL generation helpers ────────────────────────────────

def generate_insert(table, row):
    cols = []
    vals = []
    for k, v in row.items():
        cols.append(k)
        vals.append(sql_escape(v))
    col_str = ", ".join(cols)
    val_str = ", ".join(vals)
    return f"INSERT OR IGNORE INTO {table} ({col_str}) VALUES ({val_str});"


def main():
    args = parse_args()
    stats = {
        "commands_ok": 0, "commands_skip": 0,
        "inbox_ok": 0, "inbox_skip": 0,
        "tasks_ok": 0, "tasks_skip": 0,
        "reports_ok": 0, "reports_skip": 0,
        "schema_mismatch": 0,
    }
    all_sql = []

    log(f"=== SQLite Migration {'(DRY-RUN)' if args.dry_run else ''} ===")
    log(f"Output: {args.output_db}")

    # ── Read schema ──
    schema_path = os.path.join(QUEUE_DIR, "schema_v1.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # ── Commands ──
    cmd_path = os.path.join(QUEUE_DIR, "shogun_to_karo.yaml")
    log(f"\n--- Reading {cmd_path} ---")
    cmd_data = load_yaml(cmd_path)
    cmd_rows = migrate_commands(cmd_data, stats)
    log(f"Commands: {stats['commands_ok']} ok, {stats['commands_skip']} skipped")
    for row in cmd_rows:
        all_sql.append(generate_insert("commands", row))

    # ── Inbox ──
    inbox_glob = os.path.join(QUEUE_DIR, "inbox", "*.yaml")
    for fpath in sorted(glob.glob(inbox_glob)):
        agent = os.path.splitext(os.path.basename(fpath))[0]
        log(f"\n--- Reading {fpath} ({agent}) ---", verbose_only=True)
        inbox_data = load_yaml(fpath)
        inbox_rows = migrate_inbox(agent, inbox_data, stats)
        for row in inbox_rows:
            all_sql.append(generate_insert("inbox_messages", row))
    log(f"Inbox: {stats['inbox_ok']} ok, {stats['inbox_skip']} skipped")

    # ── Tasks ──
    tasks_glob = os.path.join(QUEUE_DIR, "tasks", "*.yaml")
    for fpath in sorted(glob.glob(tasks_glob)):
        agent = os.path.splitext(os.path.basename(fpath))[0]
        log(f"\n--- Reading {fpath} ({agent}) ---", verbose_only=True)
        task_data = load_yaml(fpath)
        if task_data is None:
            stats["tasks_skip"] += 1
            log(f"WARN: Skipping {fpath} (YAML parse error)")
            continue
        task_rows = migrate_tasks(agent, task_data, stats)
        for row in task_rows:
            all_sql.append(generate_insert("tasks", row))
    log(f"Tasks: {stats['tasks_ok']} ok, {stats['tasks_skip']} skipped")

    # ── Reports ──
    reports_glob = os.path.join(QUEUE_DIR, "reports", "*.yaml")
    report_files = sorted(glob.glob(reports_glob))
    log(f"\n--- Reading {len(report_files)} report files ---")
    for fpath in report_files:
        report_data = load_yaml(fpath)
        if report_data is None:
            stats["reports_skip"] += 1
            log(f"WARN: Skipping {fpath} (YAML parse error)")
            continue
        report_rows = migrate_reports(fpath, report_data, stats)
        for row in report_rows:
            all_sql.append(generate_insert("reports", row))
    log(f"Reports: {stats['reports_ok']} ok, {stats['reports_skip']} skipped")

    # ── Output ──
    if args.dry_run:
        with open(args.output_db, "w", encoding="utf-8") as f:
            f.write("-- Migration dry-run output\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")
            f.write(schema_sql)
            f.write("\n\n-- Disable FK during migration (orphan refs from archived data)\n")
            f.write("PRAGMA foreign_keys = OFF;\n\n")
            f.write("-- Data inserts\n")
            for stmt in all_sql:
                f.write(stmt + "\n")
            f.write("\n-- Re-enable FK after migration\n")
            f.write("PRAGMA foreign_keys = ON;\n")
        log(f"\nDry-run SQL written to: {args.output_db}")
    else:
        import sqlite3
        conn = sqlite3.connect(args.output_db)
        conn.executescript(schema_sql)
        conn.execute("PRAGMA foreign_keys = OFF")
        for stmt in all_sql:
            try:
                conn.execute(stmt)
            except Exception as e:
                stats["schema_mismatch"] += 1
                log(f"ERROR: {e}")
                log(f"  SQL: {stmt[:120]}...")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        conn.close()
        log(f"\nDatabase written to: {args.output_db}")

    # ── Summary ──
    total_ok = stats["commands_ok"] + stats["inbox_ok"] + stats["tasks_ok"] + stats["reports_ok"]
    total_skip = stats["commands_skip"] + stats["inbox_skip"] + stats["tasks_skip"] + stats["reports_skip"]
    log(f"\n=== SUMMARY ===")
    log(f"Commands: {stats['commands_ok']} inserted, {stats['commands_skip']} skipped")
    log(f"Inbox:    {stats['inbox_ok']} inserted, {stats['inbox_skip']} skipped")
    log(f"Tasks:    {stats['tasks_ok']} inserted, {stats['tasks_skip']} skipped")
    log(f"Reports:  {stats['reports_ok']} inserted, {stats['reports_skip']} skipped")
    log(f"Total:    {total_ok} inserted, {total_skip} skipped, {stats['schema_mismatch']} schema mismatches")
    log(f"SQL statements: {len(all_sql)}")

    return 0 if stats["schema_mismatch"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
