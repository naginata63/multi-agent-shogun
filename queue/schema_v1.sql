-- ============================================================
-- SQLite Migration Schema v1
-- cmd_1484 / subtask_1484a
-- Based on: gunshi_design_sqlite_migration_1481.yaml
-- Verified against: actual YAML structure (2026-04-25)
-- ============================================================

-- Pragmas (run once at connection)
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
PRAGMA wal_autocheckpoint = 1000;
PRAGMA temp_store = MEMORY;
PRAGMA cache_size = -16000;

-- ============================================================
-- 1. commands (source: queue/shogun_to_karo.yaml)
-- ============================================================
CREATE TABLE IF NOT EXISTS commands (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('pending','in_progress','done','blocked','superseded','cancelled')),
    priority TEXT CHECK (priority IN ('low','medium','high','critical')) DEFAULT 'medium',
    purpose TEXT NOT NULL,
    lord_original TEXT,
    command_text TEXT,
    assigned_to TEXT,
    north_star TEXT,
    project TEXT,
    parent_cmd TEXT REFERENCES commands(id) ON DELETE SET NULL,
    acceptance_criteria_json TEXT,
    depends_on_json TEXT,
    notes_json TEXT,
    implementation_flow TEXT,
    verify_guidance TEXT,
    completion_note TEXT,
    cancelled_reason TEXT,
    redo_of TEXT,
    timestamp TEXT NOT NULL,
    issued_at TEXT,
    started_at TEXT,
    revised_at TEXT,
    completed_at TEXT,
    cancelled_at TEXT,
    created_at_unix INTEGER GENERATED ALWAYS AS (CAST(strftime('%s', timestamp) AS INTEGER)) STORED,
    full_yaml_blob TEXT
);

-- ============================================================
-- 2. inbox_messages (source: queue/inbox/*.yaml)
-- ============================================================
CREATE TABLE IF NOT EXISTS inbox_messages (
    id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    from_agent TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0 CHECK (read IN (0,1)),
    timestamp TEXT NOT NULL,
    read_at TEXT,
    actor TEXT
);

-- ============================================================
-- 3. tasks (source: queue/tasks/*.yaml)
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    parent_cmd TEXT REFERENCES commands(id) ON DELETE SET NULL,
    bloom_level TEXT,
    status TEXT NOT NULL CHECK (status IN ('assigned','in_progress','done','blocked','superseded','cancelled')),
    priority TEXT,
    title TEXT,
    project TEXT,
    description TEXT,
    target_path TEXT,
    procedure TEXT,
    steps TEXT,
    acceptance_criteria_json TEXT,
    notes_json TEXT,
    params_json TEXT,
    assigned_to TEXT,
    assignee TEXT,
    report_to TEXT,
    safety TEXT,
    result TEXT,
    redo_of TEXT,
    blocked_reason TEXT,
    blocked_at TEXT,
    completed_at TEXT,
    report_path TEXT,
    qa_decision TEXT,
    timestamp TEXT NOT NULL,
    started_at TEXT,
    full_yaml_blob TEXT
);

-- ============================================================
-- 4. reports (source: queue/reports/*.yaml)
-- ============================================================
CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    task_id TEXT REFERENCES tasks(task_id) ON DELETE SET NULL,
    parent_cmd TEXT REFERENCES commands(id) ON DELETE SET NULL,
    status TEXT NOT NULL,
    qa_decision TEXT,
    timestamp TEXT NOT NULL,
    report_path TEXT,
    summary TEXT,
    result_json TEXT,
    files_modified_json TEXT,
    notes_json TEXT,
    skill_candidate_json TEXT,
    hotfix_notes_json TEXT,
    north_star_alignment_json TEXT,
    purpose_gap TEXT,
    full_yaml_blob TEXT
);

-- ============================================================
-- 5. audit_log
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    actor TEXT,
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    before_json TEXT,
    after_json TEXT
);

-- ============================================================
-- Indexes
-- ============================================================
-- commands
CREATE INDEX IF NOT EXISTS idx_cmd_status ON commands(status);
CREATE INDEX IF NOT EXISTS idx_cmd_assigned ON commands(assigned_to);
CREATE INDEX IF NOT EXISTS idx_cmd_timestamp ON commands(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cmd_parent ON commands(parent_cmd);
CREATE INDEX IF NOT EXISTS idx_cmd_project ON commands(project);
-- inbox
CREATE INDEX IF NOT EXISTS idx_inbox_agent_unread ON inbox_messages(agent, read);
CREATE INDEX IF NOT EXISTS idx_inbox_timestamp ON inbox_messages(timestamp DESC);
-- tasks
CREATE INDEX IF NOT EXISTS idx_task_agent_status ON tasks(agent, status);
CREATE INDEX IF NOT EXISTS idx_task_parent ON tasks(parent_cmd);
CREATE INDEX IF NOT EXISTS idx_task_timestamp ON tasks(timestamp DESC);
-- reports
CREATE INDEX IF NOT EXISTS idx_report_task ON reports(task_id);
CREATE INDEX IF NOT EXISTS idx_report_parent ON reports(parent_cmd);
CREATE INDEX IF NOT EXISTS idx_report_worker ON reports(worker_id);
-- audit
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_log(table_name, record_id);

-- ============================================================
-- Triggers (audit logging for status changes)
-- ============================================================
CREATE TRIGGER IF NOT EXISTS tr_commands_au AFTER UPDATE ON commands FOR EACH ROW
BEGIN
    INSERT INTO audit_log(actor, action, table_name, record_id, before_json, after_json)
    VALUES (NULL, 'UPDATE', 'commands', NEW.id,
        json_object('status', OLD.status),
        json_object('status', NEW.status));
END;

CREATE TRIGGER IF NOT EXISTS tr_tasks_au AFTER UPDATE ON tasks FOR EACH ROW
BEGIN
    INSERT INTO audit_log(actor, action, table_name, record_id, before_json, after_json)
    VALUES (NULL, 'UPDATE', 'tasks', NEW.task_id,
        json_object('status', OLD.status),
        json_object('status', NEW.status));
END;

CREATE TRIGGER IF NOT EXISTS tr_inbox_read AFTER UPDATE ON inbox_messages FOR EACH ROW
WHEN OLD.read = 0 AND NEW.read = 1
BEGIN
    INSERT INTO audit_log(actor, action, table_name, record_id, before_json, after_json)
    VALUES (NEW.actor, 'MARK_READ', 'inbox_messages', NEW.id, NULL, NULL);
END;
