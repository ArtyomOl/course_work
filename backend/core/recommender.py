from typing import List
from collections import defaultdict
from .search import SearchEngine

class Recommender:
    def __init__(self, history):
        self.history = history
        self.engine = None

    def set_engine(self, engine: SearchEngine):
        self.engine = engine

    def get_document_recommendations(self, top_n: int = 5) -> List[str]:
        if not self.engine:
            return []
        queries = self.history.get_all()
        if not queries:
            return []
        scores = defaultdict(float)
        decay = 0.9
        weight = 1.0
        for q in queries:
            try:
                results = self.engine.search(q, add_to_history=False)[:10]
                for rank, r in enumerate(results, 1):
                    scores[r.document.name] += weight * (1.0 / rank)
                weight *= decay
            except Exception:
                continue
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [name for name, _ in ranked]
