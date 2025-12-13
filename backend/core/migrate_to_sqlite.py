"""
Скрипт для миграции данных из JSON в SQLite
"""
import json
import os
from .database import init_database, add_document

DATA_PATH = r'D:\Python projects\COURSE_WORK\data\documents_metadata.json'


def migrate():
    """Мигрирует данные из JSON в SQLite"""
    # Инициализируем базу данных
    init_database()
    
    # Читаем данные из JSON
    if not os.path.exists(DATA_PATH):
        print(f"Файл {DATA_PATH} не найден. Миграция не требуется.")
        return
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = data.get('documents', [])
    
    if not documents:
        print("Нет документов для миграции.")
        return
    
    # Мигрируем каждый документ
    migrated_count = 0
    for doc in documents:
        doc_id = doc.get('id')
        name = doc.get('name')
        file_path = doc.get('file_path')
        keywords = doc.get('keywords', [])
        
        if not doc_id or not name or not file_path:
            print(f"Пропущен документ с неполными данными: {doc}")
            continue
        
        add_document(doc_id, name, file_path, keywords)
        migrated_count += 1
        print(f"Мигрирован документ: {name} (ID: {doc_id})")
    
    print(f"\nМиграция завершена. Мигрировано документов: {migrated_count}")


if __name__ == '__main__':
    migrate()

