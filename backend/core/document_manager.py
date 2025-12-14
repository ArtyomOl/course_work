import os
import re
import uuid
import sqlite3
from typing import List
from .text_preprocess import TextPreprocessor
from .index import Index


class Keyword:
    def __init__(self, original: str, stemmed: str):
        self.original = original
        self.stemmed = stemmed

    def __str__(self):
        return self.original

    def __repr__(self):
        return f"Keyword('{self.original}')"


class Document:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DOCUMENTS_PATH = os.path.join(BASE_DIR, 'data', 'documents')  # type: ignore
    DB_PATH = os.path.join(BASE_DIR, 'data', 'documents.db')  # type: ignore

    def __init__(self, id: str, name: str = None, path: str = None):
        Document.init_storage()
        self.id = id
        raw_name = name or (os.path.basename(path) if path else f"doc_{id[:8]}")
        if raw_name.lower().endswith(".txt"):
            raw_name = raw_name[:-4]
        self.name = raw_name
        candidate_path = path if path and os.path.exists(path) else None
        if not candidate_path:
            alt = os.path.join(Document.DOCUMENTS_PATH, f"{self.name}.txt")
            candidate_path = alt if os.path.exists(alt) else alt
        self.path = candidate_path
        self._keywords: List[Keyword] = []
        self.get_keywords()

    @staticmethod
    def _conn():
        os.makedirs(os.path.dirname(Document.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(Document.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_storage(cls):
        os.makedirs(cls.DOCUMENTS_PATH, exist_ok=True)
        conn = cls._conn()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS document_keywords (
                document_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                PRIMARY KEY (document_id, keyword),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_keywords_doc_id ON document_keywords(document_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON document_keywords(keyword)')
        conn.commit()
        conn.close()

    @classmethod
    def _row_to_doc(cls, row, cur):
        doc = dict(row)
        cur.execute('SELECT keyword FROM document_keywords WHERE document_id = ?', (doc['id'],))
        doc['keywords'] = [kw['keyword'] for kw in cur.fetchall()]
        return doc

    @classmethod
    def records(cls) -> List[dict]:
        try:
            conn = cls._conn()
            cur = conn.cursor()
            cur.execute('SELECT id, name, file_path FROM documents ORDER BY name')
            docs = [cls._row_to_doc(r, cur) for r in cur.fetchall()]
            conn.close()
            return docs
        except Exception as e:
            print(f"Ошибка при получении всех документов: {e}")
            return []

    @classmethod
    def record_by_id(cls, doc_id: str):
        try:
            conn = cls._conn()
            cur = conn.cursor()
            cur.execute('SELECT id, name, file_path FROM documents WHERE id = ?', (doc_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return None
            doc = cls._row_to_doc(row, cur)
            conn.close()
            return doc
        except Exception as e:
            print(f"Ошибка при получении документа по ID: {e}")
            return None

    @classmethod
    def record_by_name(cls, name: str):
        try:
            conn = cls._conn()
            cur = conn.cursor()
            cur.execute('SELECT id, name, file_path FROM documents WHERE name = ?', (name,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return None
            doc = cls._row_to_doc(row, cur)
            conn.close()
            return doc
        except Exception as e:
            print(f"Ошибка при получении документа по имени: {e}")
            return None

    @classmethod
    def add_record(cls, doc_id: str, name: str, file_path: str, keywords: List[str]):
        conn = cls._conn()
        cur = conn.cursor()
        cur.execute('INSERT OR REPLACE INTO documents (id, name, file_path) VALUES (?, ?, ?)',
                    (doc_id, name, file_path))
        cur.execute('DELETE FROM document_keywords WHERE document_id = ?', (doc_id,))
        for kw in keywords:
            cur.execute('INSERT INTO document_keywords (document_id, keyword) VALUES (?, ?)', (doc_id, kw))
        conn.commit()
        conn.close()

    @classmethod
    def update_record(cls, doc_id: str, name: str = None, file_path: str = None, keywords: List[str] = None):
        conn = cls._conn()
        cur = conn.cursor()
        updates, params = [], []
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if file_path is not None:
            updates.append('file_path = ?')
            params.append(file_path)
        if updates:
            params.append(doc_id)
            cur.execute(f'UPDATE documents SET {", ".join(updates)} WHERE id = ?', params)
        if keywords is not None:
            cur.execute('DELETE FROM document_keywords WHERE document_id = ?', (doc_id,))
            for kw in keywords:
                cur.execute('INSERT INTO document_keywords (document_id, keyword) VALUES (?, ?)', (doc_id, kw))
        conn.commit()
        conn.close()

    @classmethod
    def delete_record(cls, doc_id: str):
        conn = cls._conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        conn.commit()
        conn.close()

    @classmethod
    def exists_by_path(cls, file_path: str) -> bool:
        try:
            conn = cls._conn()
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) as count FROM documents WHERE file_path = ?', (file_path,))
            row = cur.fetchone()
            conn.close()
            return (row['count'] if row else 0) > 0
        except Exception as e:
            print(f"Ошибка при проверке существования документа: {e}")
            return False

    def get_text(self):
        try:
            if not os.path.exists(self.path):
                alt = os.path.join(Document.DOCUMENTS_PATH, f"{self.name}.txt")
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
            return TextPreprocessor.preprocess(text)
        except Exception as e:
            print(f"Ошибка при предобработке текста: {e}")
            return ""

    def get_keywords(self):
        if not self._keywords:
            self.load_keywords()
        return self._keywords

    def load_keywords(self):
        try:
            doc_data = Document.record_by_id(self.id)
            if doc_data:
                self._keywords = [Keyword(kw, TextPreprocessor.preprocess(kw)) for kw in doc_data.get('keywords', [])]
        except Exception as e:
            print(f"Ошибка при загрузке ключевых слов: {e}")
            self._keywords = []

    def add_to_index(self):
        try:
            txt = self.get_preprocess_text()
            if not txt:
                raise ValueError("Текст документа пуст")
            keywords_clean = Index().extract_keywords(txt, top_n=7)
            words = re.findall(r'\w+', self.get_text())
            keywords_original = []
            for kw in keywords_clean:
                for w in words:
                    if TextPreprocessor.preprocess(w) == kw:
                        keywords_original.append(w)
                        break
            if not Document.exists_by_path(self.path):
                Document.add_record(self.id, self.name, self.path, keywords_original)
            else:
                Document.update_record(self.id, keywords=keywords_original)
            Index().build_inverted_index()
        except Exception as e:
            print(f"Ошибка при добавлении документа в индекс: {e}")
            raise

    def delete(self):
        try:
            Document.delete_record(self.id)
            Index().build_inverted_index()
            if os.path.exists(self.path):
                os.remove(self.path)
        except Exception as e:
            print(f"Ошибка при удалении документа: {e}")
            raise

    def is_fit_for_filters(self, filters: list[str]):
        if not filters:
            return True
        try:
            doc_tokens = set((self.get_preprocess_text() or "").split())
        except Exception:
            doc_tokens = set()
        kw_stems = {k.stemmed for k in self.get_keywords() if getattr(k, "stemmed", None)}
        doc_vocab = doc_tokens | kw_stems
        for w in filters:
            stem = TextPreprocessor.preprocess(w)
            if not stem:
                continue
            if stem not in doc_vocab:
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
            os.makedirs(Document.DOCUMENTS_PATH, exist_ok=True)
            path = os.path.join(Document.DOCUMENTS_PATH, f"{name}.txt")
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
        Document.init_storage()
        rows = Document.records()
        return [Document(id=d['id'], name=d.get('name'), path=d['file_path']) for d in rows]

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
            doc.add_to_index()
        except Exception as e:
            print(f"Ошибка при обновлении текста документа: {e}")
            raise

    @staticmethod
    def delete_document(doc_id_or_name: str):
        try:
            doc_data = Document.record_by_id(doc_id_or_name)
            if not doc_data:
                doc_data = Document.record_by_name(doc_id_or_name)
            if not doc_data:
                raise ValueError(f"Документ '{doc_id_or_name}' не найден")
            doc = Document(id=doc_data['id'], name=doc_data['name'], path=doc_data['file_path'])
            doc.delete()
        except Exception as e:
            print(f"Ошибка при удалении документа: {e}")
            raise
