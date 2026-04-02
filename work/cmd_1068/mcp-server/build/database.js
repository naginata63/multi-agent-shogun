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
exports.updateAgentStatus = updateAgentStatus;
exports.getAllAgentStatuses = getAllAgentStatuses;
exports.getReports = getReports;
exports.saveAgentState = saveAgentState;
exports.getAgentState = getAgentState;
exports.getDashboard = getDashboard;
exports.clearAllData = clearAllData;
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

    CREATE TABLE IF NOT EXISTS agent_status (
      agent_id    TEXT PRIMARY KEY,
      status      TEXT NOT NULL DEFAULT 'idle',
      current_task TEXT,
      updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS agent_state (
      agent_id    TEXT NOT NULL,
      key         TEXT NOT NULL,
      value       TEXT NOT NULL,
      updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (agent_id, key)
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
// ============================================================
// Phase 2: 追加機能
// ============================================================
function updateAgentStatus(agent_id, status, current_task) {
    const db = getDb();
    const valid = ["idle", "busy", "error", "offline"];
    if (!valid.includes(status)) {
        return { success: false, error: `Invalid status: ${status}` };
    }
    db.prepare(`
    INSERT INTO agent_status (agent_id, status, current_task, updated_at)
    VALUES (?, ?, ?, datetime('now'))
    ON CONFLICT(agent_id) DO UPDATE SET
      status = excluded.status,
      current_task = excluded.current_task,
      updated_at = datetime('now')
  `).run(agent_id, status, current_task ?? null);
    return { success: true, agent_id, status };
}
function getAllAgentStatuses() {
    const db = getDb();
    const agents = db
        .prepare("SELECT * FROM agent_status ORDER BY agent_id ASC")
        .all();
    return { agents };
}
function getReports(parentCmd) {
    const db = getDb();
    if (parentCmd) {
        const reports = db
            .prepare(`SELECT r.* FROM reports r JOIN tasks t ON r.task_id = t.task_id
         WHERE t.parent_cmd = ? ORDER BY r.created_at ASC`)
            .all(parentCmd);
        return { reports };
    }
    const reports = db
        .prepare("SELECT * FROM reports ORDER BY created_at ASC")
        .all();
    return { reports };
}
function saveAgentState(agent_id, key, value) {
    const db = getDb();
    db.prepare(`
    INSERT INTO agent_state (agent_id, key, value, updated_at)
    VALUES (?, ?, ?, datetime('now'))
    ON CONFLICT(agent_id, key) DO UPDATE SET
      value = excluded.value,
      updated_at = datetime('now')
  `).run(agent_id, key, value);
    return { success: true, agent_id, key };
}
function getAgentState(agent_id) {
    const db = getDb();
    const states = db
        .prepare("SELECT key, value FROM agent_state WHERE agent_id = ? ORDER BY key ASC")
        .all(agent_id);
    const stateMap = {};
    for (const s of states) {
        stateMap[s.key] = s.value;
    }
    return { agent_id, state: stateMap };
}
function getDashboard() {
    const db = getDb();
    const stats = getStats();
    const agents = db
        .prepare("SELECT * FROM agent_status ORDER BY agent_id ASC")
        .all();
    const recentTasks = db
        .prepare("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 20")
        .all();
    const recentMessages = db
        .prepare("SELECT * FROM messages ORDER BY created_at DESC LIMIT 20")
        .all();
    return {
        stats,
        agents,
        recent_tasks: recentTasks,
        recent_messages: recentMessages,
        timestamp: new Date().toISOString(),
    };
}
function clearAllData() {
    const db = getDb();
    db.exec(`
    DELETE FROM agent_state;
    DELETE FROM agent_status;
    DELETE FROM reports;
    DELETE FROM messages;
    DELETE FROM tasks;
  `);
    return { success: true, message: "All data cleared" };
}
