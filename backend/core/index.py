import math
import sqlite3
import pickle
import os
from typing import Dict, List, Tuple
from . import text_preprocess as tp
from . import indexer


INDEX_DB = r'D:\Python projects\COURSE_WORK\backend\core\index\inverted_index.db'


class Index:
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
        os.makedirs(os.path.dirname(INDEX_DB), exist_ok=True)

    def _connect(self):
        return sqlite3.connect(INDEX_DB)

    def fetch_postings(self, terms: List[str]) -> Dict[str, List[Tuple[str, int]]]:
        if not terms:
            return {}
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS index_table (term TEXT PRIMARY KEY, postings BLOB)')
        placeholders = ','.join('?' for _ in terms)
        sql = f'SELECT term, postings FROM index_table WHERE term IN ({placeholders})'
        cur.execute(sql, terms)
        rows = cur.fetchall()
        conn.close()
        return {term: pickle.loads(blob) for term, blob in rows}

    def fetch_doc_norm(self, doc_id: str) -> float:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS doc_meta (filename TEXT PRIMARY KEY, norm REAL)')
        cur.execute('SELECT norm FROM doc_meta WHERE filename = ?', (doc_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0.0

    def compute_query_vector(self, query: str) -> Dict[str, float]:
        return indexer.create_vector(query)
