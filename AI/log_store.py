"""
log_store.py — SQLite-based log storage for AI interactions.

Stores all requests, generated code, execution results, and explanations
so they can be retrieved later (as required by AI_detail.md Section 2.2).
"""

import sqlite3
import json
import os
from datetime import datetime, timezone


DB_PATH = os.path.join(os.path.dirname(__file__), "ai_logs.db")


def _get_connection():
    """Get a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the logs table if it doesn't exist."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            thread_id TEXT,
            user_request TEXT,
            ai_explanation TEXT,
            generated_code TEXT,
            edited_code TEXT,
            execution_result TEXT,
            error_traceback TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()


def save_log(thread_id: str, user_request: str, ai_explanation: str,
             generated_code: str, status: str = "pending") -> int:
    """
    Save a new log entry. Returns the log ID.
    
    Status values: pending, approved, rejected, executed, failed, fixed
    """
    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO logs (timestamp, thread_id, user_request, ai_explanation,
                          generated_code, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            thread_id,
            user_request,
            ai_explanation,
            generated_code,
            status,
        )
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def update_log(log_id: int, **kwargs):
    """
    Update specific fields of a log entry.
    
    Supported fields: edited_code, execution_result, error_traceback, status
    """
    allowed_fields = {"edited_code", "execution_result", "error_traceback", "status"}
    fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not fields_to_update:
        return

    set_clause = ", ".join(f"{k} = ?" for k in fields_to_update)
    values = list(fields_to_update.values())
    values.append(log_id)

    conn = _get_connection()
    conn.execute(f"UPDATE logs SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_logs(limit: int = 50, offset: int = 0) -> list[dict]:
    """Retrieve log entries, newest first."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM logs ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_log_by_id(log_id: int) -> dict | None:
    """Retrieve a single log entry by ID."""
    conn = _get_connection()
    row = conn.execute("SELECT * FROM logs WHERE id = ?", (log_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_logs_by_thread(thread_id: str) -> list[dict]:
    """Retrieve all log entries for a specific thread."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM logs WHERE thread_id = ? ORDER BY id ASC",
        (thread_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_conversations() -> list[dict]:
    """Retrieve all distinct conversations with summary info."""
    conn = _get_connection()
    rows = conn.execute("""
        SELECT thread_id,
               MIN(timestamp) as first_time,
               MAX(timestamp) as last_time,
               COUNT(*) as msg_count,
               MIN(CASE WHEN user_request NOT LIKE '[Auto-fix]%' THEN user_request END) as first_request
        FROM logs
        WHERE thread_id IS NOT NULL AND thread_id != ''
        GROUP BY thread_id
        ORDER BY MAX(id) DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Initialize DB on import
init_db()
