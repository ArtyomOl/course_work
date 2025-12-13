import sqlite3
import os
import json
from typing import List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'documents.db')


def get_connection():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        raise


def init_database():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_keywords (
                document_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                PRIMARY KEY (document_id, keyword),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_doc_id ON document_keywords(document_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON document_keywords(keyword)')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        raise


def get_all_documents() -> List[dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, file_path FROM documents ORDER BY name')
        documents = []
        for row in cursor.fetchall():
            doc = dict(row)
            cursor.execute('SELECT keyword FROM document_keywords WHERE document_id = ?', (doc['id'],))
            doc['keywords'] = [kw['keyword'] for kw in cursor.fetchall()]
            documents.append(doc)
        
        conn.close()
        return documents
    except Exception as e:
        print(f"Ошибка при получении всех документов: {e}")
        return []


def get_document_by_id(doc_id: str) -> Optional[dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, file_path FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        doc = dict(row)
        cursor.execute('SELECT keyword FROM document_keywords WHERE document_id = ?', (doc_id,))
        doc['keywords'] = [kw['keyword'] for kw in cursor.fetchall()]
        
        conn.close()
        return doc
    except Exception as e:
        print(f"Ошибка при получении документа по ID: {e}")
        return None


def get_document_by_name(name: str) -> Optional[dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, file_path FROM documents WHERE name = ?', (name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        doc = dict(row)
        cursor.execute('SELECT keyword FROM document_keywords WHERE document_id = ?', (doc['id'],))
        doc['keywords'] = [kw['keyword'] for kw in cursor.fetchall()]
        
        conn.close()
        return doc
    except Exception as e:
        print(f"Ошибка при получении документа по имени: {e}")
        return None


def add_document(doc_id: str, name: str, file_path: str, keywords: List[str]):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT OR REPLACE INTO documents (id, name, file_path) VALUES (?, ?, ?)',
                       (doc_id, name, file_path))
        
        cursor.execute('DELETE FROM document_keywords WHERE document_id = ?', (doc_id,))
        
        for keyword in keywords:
            cursor.execute('INSERT INTO document_keywords (document_id, keyword) VALUES (?, ?)',
                          (doc_id, keyword))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при добавлении документа: {e}")
        raise


def update_document(doc_id: str, name: str = None, file_path: str = None, keywords: List[str] = None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if file_path is not None:
            updates.append('file_path = ?')
            params.append(file_path)
        
        if updates:
            params.append(doc_id)
            cursor.execute(f'UPDATE documents SET {", ".join(updates)} WHERE id = ?', params)
        
        if keywords is not None:
            cursor.execute('DELETE FROM document_keywords WHERE document_id = ?', (doc_id,))
            for keyword in keywords:
                cursor.execute('INSERT INTO document_keywords (document_id, keyword) VALUES (?, ?)',
                              (doc_id, keyword))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при обновлении документа: {e}")
        raise


def delete_document(doc_id: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при удалении документа: {e}")
        raise


def document_exists_by_path(file_path: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM documents WHERE file_path = ?', (file_path,))
        result = cursor.fetchone()
        exists = result['count'] > 0
        
        conn.close()
        return exists
    except Exception as e:
        print(f"Ошибка при проверке существования документа: {e}")
        return False

