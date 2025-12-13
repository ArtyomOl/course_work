from .document_manager import Document


class SearchResult:
    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score

    def __lt__(self, other):
        return self.score < other.score

    def __repr__(self):
        return f"SearchResult(doc={self.document.name}, score={self.score:.4f})"
