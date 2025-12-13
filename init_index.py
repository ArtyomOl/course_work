import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.core.indexer import build_inverted_index
from backend.core.database import init_database
from backend.core.document_manager import Document

def initialize():
    print("Инициализация системы...")
    
    print("1. Инициализация базы данных...")
    try:
        init_database()
        print("   ✓ База данных инициализирована")
    except Exception as e:
        print(f"   ✗ Ошибка при инициализации БД: {e}")
        return False
    
    print("2. Построение индекса документов...")
    try:
        build_inverted_index()
        print("   ✓ Индекс построен")
    except Exception as e:
        print(f"   ✗ Ошибка при построении индекса: {e}")
        return False
    
    print("3. Добавление документов в базу данных...")
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        docs_path = os.path.join(base_dir, 'data', 'documents')
        
        if not os.path.exists(docs_path):
            print(f"   ! Папка с документами не найдена: {docs_path}")
            return True
        
        files = [f for f in os.listdir(docs_path) if f.endswith('.txt')]
        
        for filename in files:
            try:
                doc_name = filename[:-4]
                file_path = os.path.join(docs_path, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if text.strip():
                    doc = Document.create_new(doc_name, text)
                    print(f"   ✓ Добавлен: {doc_name}")
            except FileExistsError:
                print(f"   - Пропущен (уже существует): {doc_name}")
            except Exception as e:
                print(f"   ✗ Ошибка при добавлении {filename}: {e}")
        
        print(f"   ✓ Обработано файлов: {len(files)}")
    except Exception as e:
        print(f"   ✗ Ошибка при добавлении документов: {e}")
        return False
    
    print("\n✓ Инициализация завершена успешно!")
    return True

if __name__ == '__main__':
    success = initialize()
    sys.exit(0 if success else 1)