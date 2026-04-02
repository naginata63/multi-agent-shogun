#!/usr/bin/env python3
"""
MCP Phase 3: ファイルベース inbox と MCP SQLite DB の比較スクリプト
Usage: python3 scripts/mcp_file_compare.py [--notify]

差分があれば ntfy で通知（--notify 時のみ）。
cron で定期実行を想定。
"""
import argparse
import glob
import os
import sqlite3
import sys
import yaml

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_DB = os.path.join(SCRIPT_DIR, "work", "cmd_1068", "experiment.db")
INBOX_DIR = os.path.join(SCRIPT_DIR, "queue", "inbox")


def get_mcp_messages():
    """MCP SQLite DB から全メッセージを取得"""
    if not os.path.exists(MCP_DB):
        return []
    conn = sqlite3.connect(MCP_DB, timeout=3)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT to_agent, from_agent, content, type, file_msg_id, "
        "file_timestamp, created_at FROM messages ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_file_messages():
    """全 inbox YAML からメッセージを取得"""
    all_msgs = []
    for path in glob.glob(os.path.join(INBOX_DIR, "*.yaml")):
        agent = os.path.basename(path).replace(".yaml", "")
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        for m in data.get("messages", []):
            all_msgs.append({
                "agent": agent,
                "id": m.get("id", ""),
                "from": m.get("from", ""),
                "content": m.get("content", ""),
                "type": m.get("type", ""),
                "timestamp": m.get("timestamp", ""),
                "read": m.get("read", False),
            })
    return all_msgs


def compare():
    mcp_msgs = get_mcp_messages()
    file_msgs = get_file_messages()

    # file_msg_id で照合
    file_ids = {m["id"] for m in file_msgs if m["id"]}
    mcp_file_ids = {m["file_msg_id"] for m in mcp_msgs if m.get("file_msg_id")}

    only_in_file = file_ids - mcp_file_ids
    only_in_mcp = mcp_file_ids - file_ids

    stats = {
        "file_count": len(file_msgs),
        "mcp_count": len(mcp_msgs),
        "only_in_file": len(only_in_file),
        "only_in_mcp": len(only_in_mcp),
        "matched": len(file_ids & mcp_file_ids),
    }

    # 詳細
    if only_in_file:
        stats["only_in_file_ids"] = sorted(only_in_file)
    if only_in_mcp:
        stats["only_in_mcp_ids"] = sorted(only_in_mcp)

    return stats


def main():
    parser = argparse.ArgumentParser(description="MCP dual-write comparison")
    parser.add_argument("--notify", action="store_true", help="ntfy通知")
    parser.add_argument("--json", action="store_true", help="JSON出力")
    args = parser.parse_args()

    stats = compare()

    if args.json:
        import json
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(f"=== MCP Dual-Write Comparison ===")
        print(f"File inbox: {stats['file_count']} msgs")
        print(f"MCP SQLite: {stats['mcp_count']} msgs")
        print(f"Matched:    {stats['matched']}")
        print(f"Only file:  {stats['only_in_file']}")
        print(f"Only MCP:   {stats['only_in_mcp']}")
        if stats["only_in_file"]:
            print(f"  Missing from MCP: {stats.get('only_in_file_ids', [])[:5]}...")
        if stats["only_in_mcp"]:
            print(f"  Missing from file: {stats.get('only_in_mcp_ids', [])[:5]}...")

    if args.notify and (stats["only_in_file"] > 5 or stats["only_in_mcp"] > 5):
        fo = stats["only_in_file"]
        mo = stats["only_in_mcp"]
        msg = f"MCP dual-write差分検知: file-only={fo} mcp-only={mo}"
        os.system(f'bash {SCRIPT_DIR}/scripts/ntfy.sh "{msg}"')

    # 差分が大きい場合はexit 1
    if stats["only_in_file"] > 10 or stats["only_in_mcp"] > 10:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
