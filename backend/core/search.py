import math
from typing import List
from .query import Query
from .search_result import SearchResult
from .document_manager import Document
from .index import Index
from .search_history import SearchHistory
from . import indexer


class SearchEngine:
    def __init__(self):
        self.index = Index()
        self.history = SearchHistory()

    def _calculate_scores(self, query: Query, exclude_doc: str = None):
        try:
            scores = {}
            postings_map = self.index.fetch_postings(query.terms)
            for term, postings in postings_map.items():
                q_val = query.vector.get(term, 0.0)
                idf_val = indexer.idf(term)
                for doc_id, tf in postings:
                    if doc_id == exclude_doc:
                        continue
                    scores[doc_id] = scores.get(doc_id, 0.0) + q_val * (1 + math.log(tf)) * idf_val
            return scores
        except Exception as e:
            print(f"Ошибка при вычислении оценок: {e}")
            return {}

    def _rank(self, scores: dict, query: Query) -> List[SearchResult]:
        try:
            norm_q = math.sqrt(sum(v*v for v in query.vector.values()))
            if norm_q == 0:
                return []
            
            docs = {d.name: d for d in Document.get_all()}
            results = []
            
            for doc_id, score in scores.items():
                norm_d = self.index.fetch_doc_norm(doc_id)
                if norm_d == 0:
                    continue
                sim = score / (norm_q * norm_d)
                if sim > 0:
                    doc = docs.get(doc_id)
                    if doc:
                        results.append(SearchResult(doc, sim))
            
            results.sort(reverse=True)
            return results
        except Exception as e:
            print(f"Ошибка при ранжировании результатов: {e}")
            return []

    def search(self, query_text: str, filters: list[str]=None) -> List[SearchResult]:
        try:
            if not query_text or not query_text.strip():
                raise ValueError("Поисковый запрос не может быть пустым")
            
            self.history.add(query_text)
            query = Query(query_text)
            
            if query.is_empty():
                return []
            
            scores = self._calculate_scores(query)
            results = self._rank(scores, query)
            
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
