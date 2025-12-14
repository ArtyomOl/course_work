from .text_preprocess import TextPreprocessor
from .index import Index


class Query:
    def __init__(self, text: str):
        self.original = text.strip()
        self.processed = TextPreprocessor.preprocess(text)
        self.vector = Index().compute_query_vector(self.processed)
        self.terms = list(self.vector.keys())

    def is_empty(self) -> bool:
        return not self.processed or not self.vector
