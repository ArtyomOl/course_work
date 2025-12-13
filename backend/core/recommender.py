# backend/core/recommender.py
from typing import List
from .search import SearchEngine
from collections import Counter

class Recommender:
    def __init__(self, history):
        self.history = history
        self.engine = None

    def set_engine(self, engine: SearchEngine):
        self.engine = engine

    def get_document_recommendations(self, top_n: int = 5) -> List[str]:
        if not self.engine or not self.history.get_all():
            return []
        doc_counter = Counter()
        for query_text in self.history.get_all():
            results = self.engine.search(query_text)
            for r in results:
                doc_counter[r.document.name] += 1
        most_common = doc_counter.most_common(top_n)
        return [name for name, _ in most_common]
