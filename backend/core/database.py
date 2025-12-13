import sqlite3
import os
import json
from typing import List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'documents.db')


def get_connection():
    """Создает и возвращает соединение с базой данных"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Инициализирует структуру базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица документов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            file_path TEXT NOT NULL
        )
    ''')
    
    # Таблица ключевых слов (many-to-many связь)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_keywords (
            document_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            PRIMARY KEY (document_id, keyword),
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    ''')
    
    # Индексы для ускорения поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_doc_id ON document_keywords(document_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON document_keywords(keyword)')
    
    conn.commit()
    conn.close()


def get_all_documents() -> List[dict]:
    """Получить все документы с их ключевыми словами"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, file_path FROM documents ORDER BY name')
    documents = []
    for row in cursor.fetchall():
        doc = dict(row)
        # Получаем ключевые слова для документа
        cursor.execute('SELECT keyword FROM document_keywords WHERE document_id = ?', (doc['id'],))
        doc['keywords'] = [kw['keyword'] for kw in cursor.fetchall()]
        documents.append(doc)
    
    conn.close()
    return documents


def get_document_by_id(doc_id: str) -> Optional[dict]:
    """Получить документ по ID"""
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


def get_document_by_name(name: str) -> Optional[dict]:
    """Получить документ по имени"""
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


def add_document(doc_id: str, name: str, file_path: str, keywords: List[str]):
    """Добавить новый документ"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('INSERT OR REPLACE INTO documents (id, name, file_path) VALUES (?, ?, ?)',
                   (doc_id, name, file_path))
    
    # Удаляем старые ключевые слова
    cursor.execute('DELETE FROM document_keywords WHERE document_id = ?', (doc_id,))
    
    # Добавляем новые ключевые слова
    for keyword in keywords:
        cursor.execute('INSERT INTO document_keywords (document_id, keyword) VALUES (?, ?)',
                      (doc_id, keyword))
    
    conn.commit()
    conn.close()


def update_document(doc_id: str, name: str = None, file_path: str = None, keywords: List[str] = None):
    """Обновить документ"""
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


def delete_document(doc_id: str):
    """Удалить документ (каскадное удаление ключевых слов)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    
    conn.commit()
    conn.close()


def document_exists_by_path(file_path: str) -> bool:
    """Проверить, существует ли документ с таким путем"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM documents WHERE file_path = ?', (file_path,))
    result = cursor.fetchone()
    exists = result['count'] > 0
    
    conn.close()
    return exists

