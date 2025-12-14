from .index import Index

_idx = Index()


def tokenize(text: str):
    return _idx.tokenize(text)


def build_inverted_index():
    return _idx.build_inverted_index()


def total_docs() -> int:
    return _idx.total_docs()


def idf(term: str) -> float:
    return _idx.idf(term)


def create_vector(text: str):
    return _idx.create_vector(text)


def extract_keywords(text: str, top_n: int = 5):
    return _idx.extract_keywords(text, top_n)


def extract_keywords_surface(text: str, top_n: int = 5):
    return _idx.extract_keywords_surface(text, top_n)

def add_document_to_index(doc_id: str, text: str):
    return _idx.build_inverted_index()


def delete_document_from_index(doc_id: str):
    return _idx.build_inverted_index()
