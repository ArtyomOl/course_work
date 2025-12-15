from collections import defaultdict


class Recommender:
    def __init__(self, history):
        self.history = history
        self.engine = None

    def set_engine(self, engine):
        self.engine = engine

    def get_document_recommendations(self, top_n=5):
        if not self.engine:
            return []
        
        queries = self.history.get_all()
        if not queries:
            return []
        
        scores = defaultdict(float)
        weight = 1.0
        
        for query in queries:
            results = self.engine.search(query, add_to_history=False)[:10]
            for rank, result in enumerate(results, 1):
                scores[result.document.name] += weight * (1.0 / rank)
            weight *= 0.9
        
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [name for name, score in sorted_docs[:top_n]]
