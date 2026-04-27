"""Canonical inbox message types (cmd_1514).

14 canonical types as constants. Nothing else passes the CHECK constraint.
"""

# ─── Task lifecycle ───────────────────────────────────────────────────────────
TASK_ASSIGNED = "task_assigned"
CLEAR_COMMAND = "clear_command"
CMD_NEW = "cmd_new"
CMD_REVISED = "cmd_revised"
CMD_CORRECTION = "cmd_correction"
CMD_SPEC_CONFIRMED = "cmd_spec_confirmed"

# ─── Reports ──────────────────────────────────────────────────────────────────
REPORT_RECEIVED = "report_received"
REPORT_COMPLETED = "report_completed"
REPORT_BLOCKED = "report_blocked"
REPORT_ERROR = "report_error"

# ─── QC ───────────────────────────────────────────────────────────────────────
QC_REQUEST = "qc_request"
QC_RESULT = "qc_result"
QC_DONE = "qc_done"

# ─── System ───────────────────────────────────────────────────────────────────
WAKE_UP = "wake_up"

# All valid types (for CHECK constraint)
CANONICAL_TYPES = frozenset({
    TASK_ASSIGNED,
    CLEAR_COMMAND,
    CMD_NEW,
    CMD_REVISED,
    CMD_CORRECTION,
    CMD_SPEC_CONFIRMED,
    REPORT_RECEIVED,
    REPORT_COMPLETED,
    REPORT_BLOCKED,
    REPORT_ERROR,
    QC_REQUEST,
    QC_RESULT,
    QC_DONE,
    WAKE_UP,
})

# Agent status detection
BUSY_TYPES = frozenset({TASK_ASSIGNED})
IDLE_TYPES = frozenset({REPORT_COMPLETED, REPORT_RECEIVED})
BLOCKED_TYPES = frozenset({REPORT_BLOCKED})
ERROR_TYPES = frozenset({REPORT_ERROR})

# Migration map: old type -> canonical type
MIGRATION_MAP = {
    "report_done": REPORT_COMPLETED,
    "task_completion_notice": REPORT_COMPLETED,
    "recovery_done": REPORT_COMPLETED,
    "session_check": WAKE_UP,
    "cmd_simplify": CMD_CORRECTION,
    "approval_request": CMD_SPEC_CONFIRMED,
    "nightly_audit": REPORT_COMPLETED,
    "lord_judgement": CMD_SPEC_CONFIRMED,
}

# Test-only types to quarantine
TEST_TYPES = frozenset({"test", "_test", "cmd_test", "qc_test"})
