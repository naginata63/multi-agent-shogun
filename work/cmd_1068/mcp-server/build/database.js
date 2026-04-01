"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getDb = getDb;
exports.createTask = createTask;
exports.getAssignedTasks = getAssignedTasks;
exports.updateTaskStatus = updateTaskStatus;
exports.sendMessage = sendMessage;
exports.getUnreadMessages = getUnreadMessages;
exports.submitReport = submitReport;
exports.getStats = getStats;
const better_sqlite3_1 = __importDefault(require("better-sqlite3"));
const path_1 = __importDefault(require("path"));
const DB_PATH = path_1.default.join(__dirname, "../../experiment.db");
let db;
function getDb() {
    if (!db) {
        db = new better_sqlite3_1.default(DB_PATH);
        db.pragma("journal_mode = WAL");
        db.pragma("foreign_keys = ON");
        initSchema(db);
    }
    return db;
}
function initSchema(db) {
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
function createTask(task_id, assignee, description, parent_cmd) {
    const db = getDb();
    const stmt = db.prepare(`
    INSERT INTO tasks (task_id, assignee, description, parent_cmd)
    VALUES (?, ?, ?, ?)
  `);
    stmt.run(task_id, assignee, description, parent_cmd);
    const task = db.prepare("SELECT * FROM tasks WHERE task_id = ?").get(task_id);
    return { success: true, task };
}
function getAssignedTasks(agent_id) {
    const db = getDb();
    const tasks = db
        .prepare("SELECT * FROM tasks WHERE assignee = ? AND status = 'assigned' ORDER BY created_at ASC")
        .all(agent_id);
    return { tasks };
}
function updateTaskStatus(task_id, status) {
    const db = getDb();
    const valid = ["assigned", "in_progress", "done", "failed"];
    if (!valid.includes(status)) {
        return { success: false, error: `Invalid status: ${status}` };
    }
    const stmt = db.prepare("UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE task_id = ?");
    const info = stmt.run(status, task_id);
    return { success: info.changes > 0, task_id, status };
}
function sendMessage(to, content, type, from) {
    const db = getDb();
    const stmt = db.prepare(`
    INSERT INTO messages (to_agent, from_agent, content, type)
    VALUES (?, ?, ?, ?)
  `);
    const info = stmt.run(to, from, content, type);
    return { success: true, message_id: info.lastInsertRowid };
}
function getUnreadMessages(agent_id) {
    const db = getDb();
    const messages = db
        .prepare("SELECT * FROM messages WHERE to_agent = ? AND read = 0 ORDER BY created_at ASC")
        .all(agent_id);
    // mark as read
    db.prepare("UPDATE messages SET read = 1 WHERE to_agent = ? AND read = 0").run(agent_id);
    return { messages };
}
function submitReport(worker_id, task_id, result) {
    const db = getDb();
    const stmt = db.prepare(`
    INSERT INTO reports (worker_id, task_id, result)
    VALUES (?, ?, ?)
  `);
    const info = stmt.run(worker_id, task_id, result);
    // mark task as done
    db.prepare("UPDATE tasks SET status = 'done', updated_at = datetime('now') WHERE task_id = ?").run(task_id);
    return { success: true, report_id: info.lastInsertRowid };
}
function getStats() {
    const db = getDb();
    const task_count = db.prepare("SELECT COUNT(*) as c FROM tasks").get().c;
    const done_count = db
        .prepare("SELECT COUNT(*) as c FROM tasks WHERE status = 'done'")
        .get().c;
    const message_count = db.prepare("SELECT COUNT(*) as c FROM messages").get().c;
    const report_count = db.prepare("SELECT COUNT(*) as c FROM reports").get().c;
    return { task_count, done_count, message_count, report_count };
}
