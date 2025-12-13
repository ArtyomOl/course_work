import sqlite3
import datetime
import os
from typing import List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HISTORY_DB = os.path.join(BASE_DIR, 'backend', 'core', 'index', 'search_history.db')


class SearchHistory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        os.makedirs(os.path.dirname(HISTORY_DB), exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(HISTORY_DB)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT UNIQUE, timestamp TEXT)')
        conn.commit()
        conn.close()

    def add(self, query: str):
        try:
            if not query or not query.strip():
                return
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT id FROM history WHERE query = ?', (query,))
            if not cur.fetchone():
                cur.execute('INSERT INTO history (query, timestamp) VALUES (?, ?)',
                            (query, datetime.datetime.now().isoformat()))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при добавлении запроса в историю: {e}")

    def get_all(self) -> List[str]:
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT query FROM history ORDER BY id DESC')
            data = [row[0] for row in cur.fetchall()]
            conn.close()
            return data
        except Exception as e:
            print(f"Ошибка при получении истории: {e}")
            return []

    def clear(self):
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('DELETE FROM history')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при очистке истории: {e}")
