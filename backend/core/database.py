from typing import List, Optional
from .document_manager import Document


def init_database():
    Document.init_storage()


def get_all_documents() -> List[dict]:
    return Document.records()


def get_document_by_id(doc_id: str) -> Optional[dict]:
    return Document.record_by_id(doc_id)


def get_document_by_name(name: str) -> Optional[dict]:
    return Document.record_by_name(name)


def add_document(doc_id: str, name: str, file_path: str, keywords: List[str]):
    Document.add_record(doc_id, name, file_path, keywords)


def update_document(doc_id: str, name: str = None, file_path: str = None, keywords: List[str] = None):
    Document.update_record(doc_id, name=name, file_path=file_path, keywords=keywords)


def delete_document(doc_id: str):
    Document.delete_record(doc_id)


def document_exists_by_path(file_path: str) -> bool:
    return Document.exists_by_path(file_path)
