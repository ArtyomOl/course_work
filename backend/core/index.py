import os
import re
import math
import sqlite3
import pickle
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
from . import text_preprocess as tp


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'documents')
INDEX_DB = os.path.join(BASE_DIR, 'backend', 'core', 'index', 'inverted_index.db')


class Index:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        os.makedirs(os.path.dirname(INDEX_DB), exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(INDEX_DB)

    def _ensure_schema(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS index_table (term TEXT PRIMARY KEY, postings BLOB)')
        cur.execute('CREATE TABLE IF NOT EXISTS term_meta (term TEXT PRIMARY KEY, df INTEGER, idf REAL)')
        cur.execute('CREATE TABLE IF NOT EXISTS doc_meta (filename TEXT PRIMARY KEY, norm REAL)')
        cur.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value INTEGER)')
        conn.commit()
        conn.close()

    def tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', tp.preprocess_text(text))

    def build_inverted_index(self):
        try:
            self._ensure_schema()
            os.makedirs(DATA_PATH, exist_ok=True)
            docs = [f for f in os.listdir(DATA_PATH) if f.endswith('.txt')]

            term_docs: Dict[str, set] = defaultdict(set)
            doc_freqs: Dict[str, Counter] = {}

            for f in docs:
                path = os.path.join(DATA_PATH, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        tokens = self.tokenize(file.read())
                    freqs = Counter(tokens)
                    name = f[:-4]
                    doc_freqs[name] = freqs
                    for t in freqs:
                        term_docs[t].add(name)
                except Exception as e:
                    print(f"Ошибка при обработке файла {f}: {e}")
                    continue

            total = len(doc_freqs)
            if total == 0:
                conn = self._connect()
                cur = conn.cursor()
                cur.execute('DELETE FROM index_table')
                cur.execute('DELETE FROM term_meta')
                cur.execute('DELETE FROM doc_meta')
                cur.execute('INSERT OR REPLACE INTO metadata VALUES ("total_docs", ?)', (0,))
                conn.commit()
                conn.close()
                return

            conn = self._connect()
            cur = conn.cursor()

            for t, dset in term_docs.items():
                df = len(dset)
                idf = math.log((total + 1) / (df + 1)) + 1
                cur.execute('INSERT OR REPLACE INTO term_meta VALUES (?, ?, ?)', (t, df, idf))
                cur.execute('INSERT OR REPLACE INTO index_table VALUES (?, ?)',
                            (t, pickle.dumps([(n, doc_freqs[n][t]) for n in dset])))

            for n, freqs in doc_freqs.items():
                norm = math.sqrt(sum(((1 + math.log(tf)) * (math.log((total + 1) / (len(term_docs[t]) + 1)) + 1)) ** 2 for t, tf in freqs.items()))
                cur.execute('INSERT OR REPLACE INTO doc_meta VALUES (?, ?)', (n, norm))

            cur.execute('INSERT OR REPLACE INTO metadata VALUES ("total_docs", ?)', (total,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при построении индекса: {e}")
            raise

    def total_docs(self) -> int:
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT value FROM metadata WHERE key="total_docs"')
            row = cur.fetchone()
            conn.close()
            return int(row[0]) if row else 0
        except Exception as e:
            print(f"Ошибка при получении количества документов: {e}")
            return 0

    def idf(self, term: str) -> float:
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT idf FROM term_meta WHERE term=?', (term,))
            row = cur.fetchone()
            conn.close()
            total = self.total_docs()
            return float(row[0]) if row else math.log((total + 1) / 1) + 1
        except Exception as e:
            print(f"Ошибка при вычислении IDF для термина {term}: {e}")
            return 1.0

    def create_vector(self, text: str) -> Dict[str, float]:
        tokens = self.tokenize(text)
        if not tokens:
            return {}
        f = Counter(tokens)
        return {t: (1 + math.log(tf)) * self.idf(t) for t, tf in f.items()}

    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        vec = self.create_vector(text)
        if not vec:
            return []
        return [w for w, _ in sorted(vec.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    def extract_keywords_surface(self, text: str, top_n: int = 5) -> List[str]:
        try:
            stems = self.extract_keywords(text, top_n)
            if not stems:
                return []
            words = re.findall(r'[A-Za-zА-Яа-яЁё]+', text or '')
            variants: Dict[str, Dict[str, int]] = defaultdict(dict)
            for w in words:
                lw = w.lower().replace('ё', 'е')
                if len(lw) <= 2 or lw in tp.TextPreprocessor.STOP_WORDS:
                    continue
                st = tp.TextPreprocessor.stem(lw)
                if not st:
                    continue
                if st not in variants:
                    variants[st] = {}
                variants[st][lw] = variants[st].get(lw, 0) + 1

            def choose_form(stem: str) -> str:
                forms = variants.get(stem)
                if not forms:
                    return stem
                sorted_forms = sorted(forms.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))
                return sorted_forms[0][0]

            return [choose_form(s) for s in stems]
        except Exception:
            return self.extract_keywords(text, top_n)
    def fetch_postings(self, terms: List[str]) -> Dict[str, List[Tuple[str, int]]]:
        try:
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
        except Exception as e:
            print(f"Ошибка при получении постингов: {e}")
            return {}

    def fetch_doc_norm(self, doc_id: str) -> float:
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS doc_meta (filename TEXT PRIMARY KEY, norm REAL)')
            cur.execute('SELECT norm FROM doc_meta WHERE filename = ?', (doc_id,))
            row = cur.fetchone()
            conn.close()
            return float(row[0]) if row else 0.0
        except Exception as e:
            print(f"Ошибка при получении нормы документа: {e}")
            return 0.0

    def compute_query_vector(self, query: str) -> Dict[str, float]:
        return self.create_vector(query)
