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
        
        # 1. Messages table with user_id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Preferences table with composite primary key (user_id, key)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT DEFAULT 'default',
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (user_id, key)
            )
        """)
        
        # 3. Tasks table with user_id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT
            )
        """)
        
        # Safe migrations: Check if user_id column exists in existing tables
        for table in ["messages", "tasks"]:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT DEFAULT 'default'")
        
        cursor.execute("PRAGMA table_info(preferences)")
        p_cols = [row["name"] for row in cursor.fetchall()]
        if "user_id" not in p_cols:
            # Recreate preferences table preserving old data
            cursor.execute("CREATE TABLE preferences_new (user_id TEXT DEFAULT 'default', key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY (user_id, key))")
            cursor.execute("INSERT OR IGNORE INTO preferences_new (user_id, key, value) SELECT 'default', key, value FROM preferences")
            cursor.execute("DROP TABLE preferences")
            cursor.execute("ALTER TABLE preferences_new RENAME TO preferences")

        # Default preferences for default admin user
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'user_name', 'José')")
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'combat_mode', 'false')")
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'hands_free', 'false')")
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'role', 'admin')")
        conn.commit()

# === MULTI-USER MESSAGES ===
def add_message(user_id: str, role: str, content: str):
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (uid, role, content, datetime.now().isoformat())
        )
        conn.commit()

def get_recent_messages(user_id: str = "default", limit: int = 40):
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, role, content, timestamp FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (uid, limit)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in reversed(rows)]

def clear_messages(user_id: str = "default"):
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (uid,))
        conn.commit()

# === MULTI-USER PREFERENCES ===
def set_preference(user_id: str, key: str, value: str):
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO preferences (user_id, key, value) VALUES (?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value",
            (uid, key, str(value))
        )
        conn.commit()

def get_preference(user_id: str, key: str, default=None):
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE user_id = ? AND key = ?", (uid, key))
        row = cursor.fetchone()
        return row["value"] if row else default

# === MULTI-USER TAREAS Y PROTOCOLOS STARK ===
def add_task(user_id: str, title: str, due_date: str = None) -> int:
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_id, title, status, created_at, due_date) VALUES (?, ?, 'pending', ?, ?)",
            (uid, title.strip(), datetime.now().isoformat(), due_date)
        )
        conn.commit()
        return cursor.lastrowid

def get_tasks(user_id: str = "default", status: str = None):
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT id, user_id, title, status, created_at, due_date FROM tasks WHERE user_id = ? AND status = ? ORDER BY id DESC", (uid, status))
        else:
            cursor.execute("SELECT id, user_id, title, status, created_at, due_date FROM tasks WHERE user_id = ? ORDER BY id DESC", (uid,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def complete_task(user_id: str, identifier) -> bool:
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        if str(identifier).isdigit():
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE user_id = ? AND id = ?", (uid, int(identifier)))
        else:
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE user_id = ? AND title LIKE ?", (uid, f"%{identifier}%"))
        conn.commit()
        return cursor.rowcount > 0

def delete_task(user_id: str, task_id: int) -> bool:
    uid = user_id or "default"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ? AND id = ?", (uid, task_id))
        conn.commit()
        return cursor.rowcount > 0

# Initialize on import
init_db()
