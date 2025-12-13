from . import text_preprocess as tp
from .index import Index


class Query:
    def __init__(self, text: str):
        self.original = text.strip()
        self.processed = tp.preprocess_text(text)
        self.vector = Index().compute_query_vector(self.processed)
        self.terms = list(self.vector.keys())

    def is_empty(self) -> bool:
        return not self.processed or not self.vector
