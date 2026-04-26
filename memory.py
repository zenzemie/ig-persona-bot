import sqlite3
import json
from datetime import datetime

class ChatMemory:
    def __init__(self, db_path='memory.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    thread_id TEXT,
                    sender_id TEXT,
                    text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_message(self, thread_id, sender_id, text, message_id=None):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    'INSERT INTO messages (thread_id, sender_id, text, message_id) VALUES (?, ?, ?, ?)',
                    (thread_id, sender_id, text, message_id)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Message already exists
                pass

    def get_history(self, thread_id, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT sender_id, text FROM messages WHERE thread_id = ? ORDER BY timestamp DESC LIMIT ?',
                (thread_id, limit)
            )
            rows = cursor.fetchall()
            return [{"role": "assistant" if row[0] == "me" else "user", "content": row[1]} for row in reversed(rows)]

    def is_last_message_from_me(self, thread_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT sender_id FROM messages WHERE thread_id = ? ORDER BY timestamp DESC LIMIT 1',
                (thread_id,)
            )
            row = cursor.fetchone()
            return row and row[0] == "me"

    def message_exists(self, message_id):
        if not message_id:
            return False
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT 1 FROM messages WHERE message_id = ?',
                (message_id,)
            )
            return cursor.fetchone() is not None
