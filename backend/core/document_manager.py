import os, uuid, re
from typing import List
from . import indexer, text_preprocess as tp
from .database import (
    init_database, get_all_documents, get_document_by_id, get_document_by_name,
    add_document, update_document, delete_document, document_exists_by_path
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCUMENTS_PATH = os.path.join(BASE_DIR, 'data', 'documents')


class Keyword:
    def __init__(self, original: str, stemmed: str):
        self.original = original
        self.stemmed = stemmed

    def __str__(self): return self.original
    def __repr__(self): return f"Keyword('{self.original}')"


class Document:
    def __init__(self, id: str, name: str = None, path: str = None):
        init_database()
        self.id = id

        raw_name = name or (os.path.basename(path) if path else f"doc_{id[:8]}")
        if raw_name.lower().endswith(".txt"):
            raw_name = raw_name[:-4]
        self.name = raw_name

        candidate_path = path if path and os.path.exists(path) else None
        if not candidate_path:
            alt = os.path.join(DOCUMENTS_PATH, f"{self.name}.txt")
            candidate_path = alt if os.path.exists(alt) else alt
        self.path = candidate_path

        self._keywords: List[Keyword] = []
        self.get_keywords()

    def get_text(self):
        try:
            if not os.path.exists(self.path):
                alt = os.path.join(DOCUMENTS_PATH, f"{self.name}.txt")
                if os.path.exists(alt):
                    self.path = alt
                else:
                    raise FileNotFoundError(f"Файл не найден: {self.path}")
            with open(self.path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка при чтении файла {self.path}: {e}")
            return ""

    def get_preprocess_text(self):
        try:
            text = self.get_text()
            return tp.preprocess_text(text)
        except Exception as e:
            print(f"Ошибка при предобработке текста: {e}")
            return ""

    def get_keywords(self):
        if not self._keywords:
            self.load_keywords()
        return self._keywords

    def load_keywords(self):
        try:
            doc_data = get_document_by_id(self.id)
            if doc_data:
                self._keywords = [Keyword(kw, tp.preprocess_text(kw)) for kw in doc_data.get('keywords', [])]
        except Exception as e:
            print(f"Ошибка при загрузке ключевых слов: {e}")
            self._keywords = []

    def add_to_index(self):
        try:
            txt = self.get_preprocess_text()
            if not txt:
                raise ValueError("Текст документа пуст")
            
            keywords_clean = indexer.extract_keywords(txt, top_n=7)
            words = re.findall(r'\w+', self.get_text())
            keywords_original = []
            for kw in keywords_clean:
                for w in words:
                    if tp.preprocess_text(w) == kw:
                        keywords_original.append(w)
                        break
            
            if not document_exists_by_path(self.path):
                add_document(self.id, self.name, self.path, keywords_original)
            else:
                update_document(self.id, keywords=keywords_original)
            
            indexer.add_document_to_index(self.id, txt)
        except Exception as e:
            print(f"Ошибка при добавлении документа в индекс: {e}")
            raise

    def delete(self):
        try:
            delete_document(self.id)
            indexer.delete_document_from_index(self.id)
            if os.path.exists(self.path):
                os.remove(self.path)
        except Exception as e:
            print(f"Ошибка при удалении документа: {e}")
            raise

    def is_fit_for_filters(self, filters: list[str]):
        if not filters:
            return True
        for w in filters:
            if tp.preprocess_text(w) not in [k.stemmed for k in self._keywords]:
                return False
        return True

    @staticmethod
    def create_new(name: str, text: str):
        try:
            if not name or not name.strip():
                raise ValueError("Имя документа не может быть пустым")
            if not text or not text.strip():
                raise ValueError("Текст документа не может быть пустым")
            
            invalid_chars = r'[<>:"/\\|?*]'
            if re.search(invalid_chars, name):
                raise ValueError("Имя документа содержит недопустимые символы")
            
            os.makedirs(DOCUMENTS_PATH, exist_ok=True)
            path = os.path.join(DOCUMENTS_PATH, f"{name}.txt")
            
            if os.path.exists(path):
                raise FileExistsError(f"Документ с именем '{name}' уже существует")
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            
            doc = Document(id=str(uuid.uuid4()), name=name, path=path)
            doc.add_to_index()
            return doc
        except Exception as e:
            print(f"Ошибка при создании документа: {e}")
            raise

    @staticmethod
    def get_all():
        init_database()  # Убеждаемся, что БД инициализирована
        docs = get_all_documents()
        return [Document(id=d['id'], name=d.get('name'), path=d['file_path']) for d in docs]

    @staticmethod
    def update_text(doc_id: str, new_text: str):
        try:
            if not new_text or not new_text.strip():
                raise ValueError("Текст документа не может быть пустым")
            
            doc = next((d for d in Document.get_all() if d.id == doc_id or d.name == doc_id), None)
            if not doc:
                raise ValueError(f"Документ с ID '{doc_id}' не найден")
            
            with open(doc.path, 'w', encoding='utf-8') as f:
                f.write(new_text)
            
            indexer.delete_document_from_index(doc.id)
            indexer.add_document_to_index(doc.id, tp.preprocess_text(new_text))
            doc.add_to_index()
        except Exception as e:
            print(f"Ошибка при обновлении текста документа: {e}")
            raise

    @staticmethod
    def delete_document(doc_id_or_name: str):
        try:
            doc_data = get_document_by_id(doc_id_or_name)
            if not doc_data:
                doc_data = get_document_by_name(doc_id_or_name)
            
            if not doc_data:
                raise ValueError(f"Документ '{doc_id_or_name}' не найден")
            
            doc = Document(id=doc_data['id'], name=doc_data['name'], path=doc_data['file_path'])
            doc.delete()
        except Exception as e:
            print(f"Ошибка при удалении документа: {e}")
            raise
