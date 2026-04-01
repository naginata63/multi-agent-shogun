import Database from "better-sqlite3";
import path from "path";
import fs from "fs";

const DB_PATH = path.join(__dirname, "../../experiment.db");

let db: Database.Database;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma("journal_mode = WAL");
    db.pragma("foreign_keys = ON");
    initSchema(db);
  }
  return db;
}

function initSchema(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS tasks (
      task_id     TEXT PRIMARY KEY,
      assignee    TEXT NOT NULL,
      description TEXT NOT NULL,
      parent_cmd  TEXT,
      status      TEXT NOT NULL DEFAULT 'assigned',
      created_at  TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS messages (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      to_agent    TEXT NOT NULL,
      from_agent  TEXT NOT NULL,
      content     TEXT NOT NULL,
      type        TEXT NOT NULL DEFAULT 'task_assigned',
      read        INTEGER NOT NULL DEFAULT 0,
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS reports (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      worker_id   TEXT NOT NULL,
      task_id     TEXT NOT NULL,
      result      TEXT NOT NULL,
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `);
}

export function createTask(
  task_id: string,
  assignee: string,
  description: string,
  parent_cmd: string
): object {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT INTO tasks (task_id, assignee, description, parent_cmd)
    VALUES (?, ?, ?, ?)
  `);
  stmt.run(task_id, assignee, description, parent_cmd);
  const task = db.prepare("SELECT * FROM tasks WHERE task_id = ?").get(task_id);
  return { success: true, task };
}

export function getAssignedTasks(agent_id: string): object {
  const db = getDb();
  const tasks = db
    .prepare(
      "SELECT * FROM tasks WHERE assignee = ? AND status = 'assigned' ORDER BY created_at ASC"
    )
    .all(agent_id);
  return { tasks };
}

export function updateTaskStatus(task_id: string, status: string): object {
  const db = getDb();
  const valid = ["assigned", "in_progress", "done", "failed"];
  if (!valid.includes(status)) {
    return { success: false, error: `Invalid status: ${status}` };
  }
  const stmt = db.prepare(
    "UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE task_id = ?"
  );
  const info = stmt.run(status, task_id);
  return { success: info.changes > 0, task_id, status };
}

export function sendMessage(
  to: string,
  content: string,
  type: string,
  from: string
): object {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT INTO messages (to_agent, from_agent, content, type)
    VALUES (?, ?, ?, ?)
  `);
  const info = stmt.run(to, from, content, type);
  return { success: true, message_id: info.lastInsertRowid };
}

export function getUnreadMessages(agent_id: string): object {
  const db = getDb();
  const messages = db
    .prepare(
      "SELECT * FROM messages WHERE to_agent = ? AND read = 0 ORDER BY created_at ASC"
    )
    .all(agent_id);
  // mark as read
  db.prepare("UPDATE messages SET read = 1 WHERE to_agent = ? AND read = 0").run(
    agent_id
  );
  return { messages };
}

export function submitReport(
  worker_id: string,
  task_id: string,
  result: string
): object {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT INTO reports (worker_id, task_id, result)
    VALUES (?, ?, ?)
  `);
  const info = stmt.run(worker_id, task_id, result);
  // mark task as done
  db.prepare(
    "UPDATE tasks SET status = 'done', updated_at = datetime('now') WHERE task_id = ?"
  ).run(task_id);
  return { success: true, report_id: info.lastInsertRowid };
}

export function getStats(): object {
  const db = getDb();
  const task_count = (
    db.prepare("SELECT COUNT(*) as c FROM tasks").get() as { c: number }
  ).c;
  const done_count = (
    db
      .prepare("SELECT COUNT(*) as c FROM tasks WHERE status = 'done'")
      .get() as { c: number }
  ).c;
  const message_count = (
    db.prepare("SELECT COUNT(*) as c FROM messages").get() as { c: number }
  ).c;
  const report_count = (
    db.prepare("SELECT COUNT(*) as c FROM reports").get() as { c: number }
  ).c;
  return { task_count, done_count, message_count, report_count };
}
