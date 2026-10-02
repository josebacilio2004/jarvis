import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT
            )
        """)
        # Initialize default preferences if not exist
        cursor.execute("INSERT OR IGNORE INTO preferences (key, value) VALUES ('user_name', 'José')")
        cursor.execute("INSERT OR IGNORE INTO preferences (key, value) VALUES ('combat_mode', 'false')")
        cursor.execute("INSERT OR IGNORE INTO preferences (key, value) VALUES ('hands_free', 'false')")
        conn.commit()

def add_message(role: str, content: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, datetime.now().isoformat())
        )
        conn.commit()

def get_recent_messages(limit: int = 40):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role, content, timestamp FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        # Return in chronological order
        return [dict(r) for r in reversed(rows)]

def clear_messages():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()

def set_preference(key: str, value: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO preferences (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value))
        )
        conn.commit()

def get_preference(key: str, default=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

# === GESTIÓN DE TAREAS Y PROTOCOLOS STARK ===
def add_task(title: str, due_date: str = None) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, status, created_at, due_date) VALUES (?, 'pending', ?, ?)",
            (title.strip(), datetime.now().isoformat(), due_date)
        )
        conn.commit()
        return cursor.lastrowid

def get_tasks(status: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT id, title, status, created_at, due_date FROM tasks WHERE status = ? ORDER BY id DESC", (status,))
        else:
            cursor.execute("SELECT id, title, status, created_at, due_date FROM tasks ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def complete_task(identifier) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        if str(identifier).isdigit():
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (int(identifier),))
        else:
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE title LIKE ?", (f"%{identifier}%",))
        conn.commit()
        return cursor.rowcount > 0

def delete_task(task_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0

# Initialize tables on import
init_db()
