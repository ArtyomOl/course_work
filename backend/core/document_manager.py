import os, uuid, re
from typing import List
from . import indexer, text_preprocess as tp
from .database import (
    init_database, get_all_documents, get_document_by_id, get_document_by_name,
    add_document, update_document, delete_document, document_exists_by_path
)

DOCUMENTS_PATH = r'D:\Python projects\COURSE_WORK\data\documents\\'


class Keyword:
    def __init__(self, original: str, stemmed: str):
        self.original = original
        self.stemmed = stemmed

    def __str__(self): return self.original
    def __repr__(self): return f"Keyword('{self.original}')"


class Document:
    def __init__(self, id: str, name: str = None, path: str = None):
        init_database()  # Убеждаемся, что БД инициализирована
        self.id = id
        self.name = name or os.path.basename(path) if path else f"doc_{id[:8]}"
        self.path = path or os.path.join(DOCUMENTS_PATH, f"{self.name}.txt")
        self._keywords: List[Keyword] = []

        self.get_keywords()

    def get_text(self): 
        with open(self.path, 'r', encoding='utf-8') as f: return f.read()

    def get_preprocess_text(self):
        with open(self.path, 'r', encoding='utf-8') as f: return tp.preprocess_text(f.read())

    def get_keywords(self):
        if not self._keywords:
            self.load_keywords()
        return self._keywords

    def load_keywords(self):
        doc_data = get_document_by_id(self.id)
        if doc_data:
            self._keywords = [Keyword(kw, tp.preprocess_text(kw)) for kw in doc_data.get('keywords', [])]

    def add_to_index(self):
        if not document_exists_by_path(self.path):
            txt = self.get_preprocess_text()
            keywords_clean = indexer.extract_keywords(txt, top_n=7)
            words = re.findall(r'\w+', self.get_text())
            keywords_original = []
            for kw in keywords_clean:
                for w in words:
                    if tp.preprocess_text(w) == kw:
                        keywords_original.append(w)
                        break
            add_document(self.id, self.name, self.path, keywords_original)
        else:
            # Обновляем ключевые слова, если документ уже существует
            txt = self.get_preprocess_text()
            keywords_clean = indexer.extract_keywords(txt, top_n=7)
            words = re.findall(r'\w+', self.get_text())
            keywords_original = []
            for kw in keywords_clean:
                for w in words:
                    if tp.preprocess_text(w) == kw:
                        keywords_original.append(w)
                        break
            update_document(self.id, keywords=keywords_original)
        indexer.add_document_to_index(self.id, self.get_preprocess_text())

    def delete(self):
        delete_document(self.id)
        indexer.delete_document_from_index(self.id)
        if os.path.exists(self.path): os.remove(self.path)

    def is_fit_for_filters(self, filters: list[str]):
        if not filters:
            return True
        for w in filters:
            if tp.preprocess_text(w) not in [k.stemmed for k in self._keywords]:
                return False
        return True

    @staticmethod
    def create_new(name: str, text: str):
        os.makedirs(DOCUMENTS_PATH, exist_ok=True)
        path = os.path.join(DOCUMENTS_PATH, f"{name}.txt")
        with open(path, "w", encoding="utf-8") as f: f.write(text)
        doc = Document(id=str(uuid.uuid4()), name=name, path=path)
        doc.add_to_index()
        return doc

    @staticmethod
    def get_all():
        init_database()  # Убеждаемся, что БД инициализирована
        docs = get_all_documents()
        return [Document(id=d['id'], name=d.get('name'), path=d['file_path']) for d in docs]

    @staticmethod
    def update_text(doc_id: str, new_text: str):
        doc = next((d for d in Document.get_all() if d.id == doc_id), None)
        if not doc: raise ValueError("Документ не найден")
        with open(doc.path, 'w', encoding='utf-8') as f: f.write(new_text)
        indexer.delete_document_from_index(doc_id)
        indexer.add_document_to_index(doc_id, tp.preprocess_text(new_text))
        doc.add_to_index()

    @staticmethod
    def delete_document(doc_id_or_name: str):
        # Пробуем найти по ID, если не найдено - по имени
        doc_data = get_document_by_id(doc_id_or_name)
        if not doc_data:
            doc_data = get_document_by_name(doc_id_or_name)
        if doc_data:
            doc = Document(id=doc_data['id'], name=doc_data['name'], path=doc_data['file_path'])
            doc.delete()
