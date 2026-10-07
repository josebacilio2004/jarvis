import os
import sqlite3
from datetime import datetime

# Environment-based Connection Strings
MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

DB_TYPE = "sqlite"
mongo_db = None
pg_conn_url = None

# 1. Try MongoDB
if MONGODB_URI:
    try:
        from pymongo import MongoClient, DESCENDING
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        client.admin.command('ping')
        db_name = os.getenv("MONGODB_DB_NAME", "jarvis_os")
        mongo_db = client[db_name]
        DB_TYPE = "mongodb"
        print(f"[Database] Engine: MongoDB (Connected to '{db_name}')")
    except Exception as e:
        print(f"[Database] MongoDB connection failed, attempting fallback: {e}")

# 2. Try PostgreSQL (e.g. Render Postgres)
if DB_TYPE == "sqlite" and DATABASE_URL:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        pg_conn_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        DB_TYPE = "postgres"
        print("[Database] Engine: PostgreSQL (Connected to Remote DB)")
    except Exception as e:
        print(f"[Database] PostgreSQL connection failed, falling back to SQLite: {e}")

# 3. Default to SQLite
if DB_TYPE == "sqlite":
    DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis.db")
    print(f"[Database] Engine: SQLite (Local: {os.path.basename(DB_PATH)})")

    def get_sqlite_conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    if DB_TYPE == "mongodb":
        # Create indexes
        mongo_db.messages.create_index([("user_id", 1), ("_id", -1)])
        mongo_db.preferences.create_index([("user_id", 1), ("key", 1)], unique=True)
        mongo_db.tasks.create_index([("user_id", 1), ("id", -1)])
        mongo_db.calendar_events.create_index([("user_id", 1), ("date", 1), ("time", 1)])
        
        # Ensure default preferences
        for k, v in [("user_name", "José"), ("combat_mode", "false"), ("hands_free", "false"), ("role", "admin")]:
            mongo_db.preferences.update_one(
                {"user_id": "default", "key": k},
                {"$setOnInsert": {"value": v}},
                upsert=True
            )
        return

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(100) DEFAULT 'default',
                        role VARCHAR(20) NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS preferences (
                        user_id VARCHAR(100) DEFAULT 'default',
                        key VARCHAR(100) NOT NULL,
                        value TEXT NOT NULL,
                        PRIMARY KEY (user_id, key)
                    );
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(100) DEFAULT 'default',
                        title TEXT NOT NULL,
                        status VARCHAR(30) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        due_date TEXT
                    );
                    CREATE TABLE IF NOT EXISTS calendar_events (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(100) DEFAULT 'default',
                        title TEXT NOT NULL,
                        date VARCHAR(20) NOT NULL,
                        time VARCHAR(20) NOT NULL,
                        duration_minutes INTEGER DEFAULT 60,
                        description TEXT,
                        location TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    INSERT INTO preferences (user_id, key, value) VALUES 
                    ('default', 'user_name', 'José'),
                    ('default', 'combat_mode', 'false'),
                    ('default', 'hands_free', 'false'),
                    ('default', 'role', 'admin')
                    ON CONFLICT (user_id, key) DO NOTHING;
                """)
            conn.commit()
        return

    # SQLite
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT DEFAULT 'default',
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (user_id, key)
            )
        """)
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                description TEXT,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'user_name', 'José')")
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'combat_mode', 'false')")
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'hands_free', 'false')")
        cursor.execute("INSERT OR IGNORE INTO preferences (user_id, key, value) VALUES ('default', 'role', 'admin')")
        conn.commit()

# === MULTI-USER MESSAGES ===
def add_message(user_id: str, role: str, content: str):
    uid = user_id or "default"
    now_iso = datetime.now().isoformat()
    if DB_TYPE == "mongodb":
        mongo_db.messages.insert_one({
            "user_id": uid,
            "role": role,
            "content": content,
            "timestamp": now_iso
        })
        return

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (user_id, role, content, timestamp) VALUES (%s, %s, %s, %s)",
                    (uid, role, content, now_iso)
                )
            conn.commit()
        return

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (uid, role, content, now_iso)
        )
        conn.commit()

def get_recent_messages(user_id: str = "default", limit: int = 40):
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        from pymongo import DESCENDING
        docs = list(mongo_db.messages.find({"user_id": uid}).sort("_id", DESCENDING).limit(limit))
        res = []
        for d in reversed(docs):
            res.append({
                "id": str(d.get("_id")),
                "user_id": d.get("user_id"),
                "role": d.get("role"),
                "content": d.get("content"),
                "timestamp": d.get("timestamp")
            })
        return res

    if DB_TYPE == "postgres":
        import psycopg2
        from psycopg2.extras import RealDictCursor
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, user_id, role, content, timestamp::text FROM messages WHERE user_id = %s ORDER BY id DESC LIMIT %s",
                    (uid, limit)
                )
                rows = cur.fetchall()
                return list(reversed(rows))

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, role, content, timestamp FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (uid, limit)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in reversed(rows)]

def clear_messages(user_id: str = "default"):
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        mongo_db.messages.delete_many({"user_id": uid})
        return

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM messages WHERE user_id = %s", (uid,))
            conn.commit()
        return

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (uid,))
        conn.commit()

# === MULTI-USER PREFERENCES ===
def set_preference(user_id: str, key: str, value: str):
    uid = user_id or "default"
    val = str(value)
    if DB_TYPE == "mongodb":
        mongo_db.preferences.update_one(
            {"user_id": uid, "key": key},
            {"$set": {"value": val}},
            upsert=True
        )
        return

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO preferences (user_id, key, value) VALUES (%s, %s, %s) ON CONFLICT (user_id, key) DO UPDATE SET value = EXCLUDED.value",
                    (uid, key, val)
                )
            conn.commit()
        return

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO preferences (user_id, key, value) VALUES (?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value",
            (uid, key, val)
        )
        conn.commit()

def get_preference(user_id: str, key: str, default=None):
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        doc = mongo_db.preferences.find_one({"user_id": uid, "key": key})
        return doc["value"] if doc and "value" in doc else default

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM preferences WHERE user_id = %s AND key = %s", (uid, key))
                row = cur.fetchone()
                return row[0] if row else default

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE user_id = ? AND key = ?", (uid, key))
        row = cursor.fetchone()
        return row["value"] if row else default

# === MULTI-USER TAREAS Y PROTOCOLOS STARK ===
def add_task(user_id: str, title: str, due_date: str = None) -> int:
    uid = user_id or "default"
    now_iso = datetime.now().isoformat()
    if DB_TYPE == "mongodb":
        # Generate numeric auto-id from counter or timestamp
        last = mongo_db.tasks.find_one({"user_id": uid}, sort=[("id", -1)])
        next_id = (last.get("id", 0) + 1) if last and isinstance(last.get("id"), int) else int(datetime.now().timestamp() % 1000000)
        mongo_db.tasks.insert_one({
            "id": next_id,
            "user_id": uid,
            "title": title.strip(),
            "status": "pending",
            "created_at": now_iso,
            "due_date": due_date
        })
        return next_id

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (user_id, title, status, created_at, due_date) VALUES (%s, %s, 'pending', %s, %s) RETURNING id",
                    (uid, title.strip(), now_iso, due_date)
                )
                tid = cur.fetchone()[0]
            conn.commit()
            return tid

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_id, title, status, created_at, due_date) VALUES (?, ?, 'pending', ?, ?)",
            (uid, title.strip(), now_iso, due_date)
        )
        conn.commit()
        return cursor.lastrowid

def get_tasks(user_id: str = "default", status: str = None):
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        from pymongo import DESCENDING
        query = {"user_id": uid}
        if status:
            query["status"] = status
        docs = list(mongo_db.tasks.find(query).sort("id", DESCENDING))
        res = []
        for d in docs:
            res.append({
                "id": d.get("id"),
                "user_id": d.get("user_id"),
                "title": d.get("title"),
                "status": d.get("status"),
                "created_at": d.get("created_at"),
                "due_date": d.get("due_date")
            })
        return res

    if DB_TYPE == "postgres":
        import psycopg2
        from psycopg2.extras import RealDictCursor
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if status:
                    cur.execute(
                        "SELECT id, user_id, title, status, created_at::text, due_date FROM tasks WHERE user_id = %s AND status = %s ORDER BY id DESC",
                        (uid, status)
                    )
                else:
                    cur.execute(
                        "SELECT id, user_id, title, status, created_at::text, due_date FROM tasks WHERE user_id = %s ORDER BY id DESC",
                        (uid,)
                    )
                return cur.fetchall()

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT id, user_id, title, status, created_at, due_date FROM tasks WHERE user_id = ? AND status = ? ORDER BY id DESC", (uid, status))
        else:
            cursor.execute("SELECT id, user_id, title, status, created_at, due_date FROM tasks WHERE user_id = ? ORDER BY id DESC", (uid,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def complete_task(user_id: str, identifier) -> bool:
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        if str(identifier).isdigit():
            res = mongo_db.tasks.update_one({"user_id": uid, "id": int(identifier)}, {"$set": {"status": "completed"}})
        else:
            import re
            res = mongo_db.tasks.update_one({"user_id": uid, "title": re.compile(str(identifier), re.IGNORECASE)}, {"$set": {"status": "completed"}})
        return res.modified_count > 0

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                if str(identifier).isdigit():
                    cur.execute("UPDATE tasks SET status = 'completed' WHERE user_id = %s AND id = %s", (uid, int(identifier)))
                else:
                    cur.execute("UPDATE tasks SET status = 'completed' WHERE user_id = %s AND title ILIKE %s", (uid, f"%{identifier}%"))
                affected = cur.rowcount > 0
            conn.commit()
            return affected

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        if str(identifier).isdigit():
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE user_id = ? AND id = ?", (uid, int(identifier)))
        else:
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE user_id = ? AND title LIKE ?", (uid, f"%{identifier}%"))
        conn.commit()
        return cursor.rowcount > 0

def delete_task(user_id: str, task_id: int) -> bool:
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        res = mongo_db.tasks.delete_one({"user_id": uid, "id": int(task_id)})
        return res.deleted_count > 0

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE user_id = %s AND id = %s", (uid, int(task_id)))
                affected = cur.rowcount > 0
            conn.commit()
            return affected

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ? AND id = ?", (uid, task_id))
        conn.commit()
        return cursor.rowcount > 0

# === CALENDAR EVENTS ===
def add_calendar_event(user_id: str, title: str, date: str, time: str, duration_minutes: int = 60, description: str = "", location: str = "") -> int:
    uid = user_id or "default"
    now_iso = datetime.now().isoformat()
    if DB_TYPE == "mongodb":
        last = mongo_db.calendar_events.find_one(sort=[("id", -1)])
        next_id = (last["id"] + 1) if last and "id" in last else 1
        mongo_db.calendar_events.insert_one({
            "id": next_id,
            "user_id": uid,
            "title": title,
            "date": date,
            "time": time,
            "duration_minutes": duration_minutes,
            "description": description,
            "location": location,
            "created_at": now_iso
        })
        return next_id

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO calendar_events (user_id, title, date, time, duration_minutes, description, location) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;",
                    (uid, title, date, time, duration_minutes, description, location)
                )
                new_id = cur.fetchone()[0]
            conn.commit()
            return new_id

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO calendar_events (user_id, title, date, time, duration_minutes, description, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, title, date, time, duration_minutes, description, location)
        )
        conn.commit()
        return cursor.lastrowid

def get_calendar_events(user_id: str, date_filter: str = None) -> list:
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        query = {"user_id": uid}
        if date_filter:
            query["date"] = date_filter
        docs = list(mongo_db.calendar_events.find(query, {"_id": 0}).sort([("date", 1), ("time", 1)]))
        return docs

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if date_filter:
                    cur.execute("SELECT id, user_id, title, date, time, duration_minutes, description, location, created_at FROM calendar_events WHERE user_id = %s AND date = %s ORDER BY time ASC", (uid, date_filter))
                else:
                    cur.execute("SELECT id, user_id, title, date, time, duration_minutes, description, location, created_at FROM calendar_events WHERE user_id = %s ORDER BY date ASC, time ASC", (uid,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        if date_filter:
            cursor.execute("SELECT id, user_id, title, date, time, duration_minutes, description, location, created_at FROM calendar_events WHERE user_id = ? AND date = ? ORDER BY time ASC", (uid, date_filter))
        else:
            cursor.execute("SELECT id, user_id, title, date, time, duration_minutes, description, location, created_at FROM calendar_events WHERE user_id = ? ORDER BY date ASC, time ASC", (uid,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def delete_calendar_event(user_id: str, event_id: int) -> bool:
    uid = user_id or "default"
    if DB_TYPE == "mongodb":
        res = mongo_db.calendar_events.delete_one({"user_id": uid, "id": int(event_id)})
        return res.deleted_count > 0

    if DB_TYPE == "postgres":
        import psycopg2
        with psycopg2.connect(pg_conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM calendar_events WHERE user_id = %s AND id = %s", (uid, int(event_id)))
                affected = cur.rowcount > 0
            conn.commit()
            return affected

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM calendar_events WHERE user_id = ? AND id = ?", (uid, event_id))
        conn.commit()
        return cursor.rowcount > 0

# Initialize on import
init_db()
