import os
import math
import sqlite3
import datetime
from typing import List
from .document_manager import Document
from .index import Index
from .text_preprocess import TextPreprocessor, preprocess_query


class SearchResult:
    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score

    def __lt__(self, other):
        return self.score < other.score

    def __repr__(self):
        return f"SearchResult(doc={self.document.name}, score={self.score:.4f})"


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
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._db_path = os.path.join(base_dir, 'backend', 'core', 'index', 'search_history.db')
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self._db_path)

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
                cur.execute('INSERT INTO history (query, timestamp) VALUES (?, ?)', (query, datetime.datetime.now().isoformat()))
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


class Query:
    def __init__(self, text: str):
        self.original = text.strip()
        self.processed = preprocess_query(text)
        self.vector = Index().compute_query_vector(self.processed)
        self.terms = list(self.vector.keys())

    def is_empty(self) -> bool:
        return not self.processed or not self.vector


class SearchEngine:
    def __init__(self):
        self.index = Index()
        self.history = SearchHistory()

    def _calculate_scores(self, query: Query, exclude_doc: str = None):
        try:
            scores = {}
            postings_map = self.index.fetch_postings(query.terms)
            if not postings_map:
                return scores
            idf_cache = {t: self.index.idf(t) for t in postings_map.keys()}
            for term, postings in postings_map.items():
                q_val = query.vector.get(term)
                if not q_val:
                    continue
                idf_val = idf_cache.get(term, 1.0)
                for doc_id, tf in postings:
                    if doc_id == exclude_doc or tf <= 0:
                        continue
                    scores[doc_id] = scores.get(doc_id, 0.0) + q_val * (1 + math.log(tf)) * idf_val
            return scores
        except Exception as e:
            print(f"Ошибка при вычислении оценок: {e}")
            return {}

    def _rank(self, scores: dict, query: Query) -> List[SearchResult]:
        try:
            norm_q = math.sqrt(sum(v * v for v in query.vector.values()))
            if norm_q == 0:
                return []
            docs = {d.name: d for d in Document.get_all()}
            q_terms = set(query.terms)
            q_tokens = query.processed.split()
            q_bigrams = set(f"{q_tokens[i]} {q_tokens[i+1]}" for i in range(len(q_tokens) - 1)) if len(q_tokens) > 1 else set()
            results = []
            for doc_id, score in scores.items():
                norm_d = self.index.fetch_doc_norm(doc_id)
                if norm_d == 0:
                    continue
                sim = score / (norm_q * norm_d)
                if sim <= 0:
                    continue
                doc = docs.get(doc_id)
                if not doc:
                    continue
                try:
                    title_tokens = set(TextPreprocessor.preprocess(doc.name).split())
                except Exception:
                    title_tokens = set()
                if q_terms and title_tokens and q_terms.intersection(title_tokens):
                    sim *= 1.15
                try:
                    doc_pp = doc.get_preprocess_text()
                    if doc_pp and any(bg in doc_pp for bg in q_bigrams):
                        sim *= 1.10
                except Exception:
                    pass
                results.append(SearchResult(doc, sim))
            results.sort(reverse=True)
            return results
        except Exception as e:
            print(f"Ошибка при ранжировании результатов: {e}")
            return []

    def search(self, query_text: str, filters: list[str] = None, add_to_history: bool = True) -> List[SearchResult]:
        try:
            if not query_text or not query_text.strip():
                raise ValueError("Поисковый запрос не может быть пустым")
            if add_to_history:
                self.history.add(query_text)
            query = Query(query_text)
            if query.is_empty():
                return []
            scores = self._calculate_scores(query)
            results = self._rank(scores, query)
            threshold = 0.1
            results = [r for r in results if r.score >= threshold]
            if filters:
                results = [r for r in results if r.document.is_fit_for_filters(filters)]
            return results
        except Exception as e:
            print(f"Ошибка при поиске: {e}")
            raise

    def get_similar_documents(self, doc_id: str, top_n: int = 5) -> List[SearchResult]:
        try:
            doc = next((d for d in Document.get_all() if d.name == doc_id), None)
            if not doc:
                return []
            text = doc.get_preprocess_text()
            if not text:
                return []
            query = Query(text)
            if query.is_empty():
                return []
            scores = self._calculate_scores(query, exclude_doc=doc_id)
            return self._rank(scores, query)[:top_n]
        except Exception as e:
            print(f"Ошибка при поиске похожих документов: {e}")
            return []
