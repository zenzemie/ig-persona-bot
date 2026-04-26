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
                    thread_id TEXT,
                    sender_id TEXT,
                    text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_message(self, thread_id, sender_id, text):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO messages (thread_id, sender_id, text) VALUES (?, ?, ?)',
                (thread_id, sender_id, text)
            )
            conn.commit()

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
