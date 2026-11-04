import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import DATABASE_PATH

@contextmanager
def connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def now():
    return datetime.now(timezone.utc).isoformat()

def init_db():
    with connection() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL, stored_name TEXT NOT NULL, file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
            extracted_text TEXT, result_json TEXT, validation_json TEXT, error_message TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_documents_sha ON documents(sha256);
        CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
        CREATE TABLE IF NOT EXISTS processing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, document_id INTEGER NOT NULL,
            event TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        ''')

def add_history(db, document_id, event, details=None):
    db.execute("INSERT INTO processing_history(document_id,event,details,created_at) VALUES(?,?,?,?)",
               (document_id, event, json.dumps(details or {}, ensure_ascii=False), now()))

def document_dict(row):
    item = dict(row)
    for key in ("result_json", "validation_json"):
        raw = item.pop(key, None)
        item[key.replace("_json", "")] = json.loads(raw) if raw else None
    return item
