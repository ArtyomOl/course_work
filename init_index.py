import os
import sys
import uuid
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.core.document_manager import Document
from backend.core.index import Index
from backend.core.text_preprocess import TextPreprocessor


def initialize():
    try:
        print("Инициализация системы...")
        Document.init_storage()
        print("База данных готова")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        docs_path = os.path.join(base_dir, 'data', 'documents')
        if not os.path.exists(docs_path):
            print(f"Папка с документами не найдена: {docs_path}")
            return True
        files = [f for f in os.listdir(docs_path) if f.endswith('.txt')]
        added = 0
        for filename in files:
            try:
                doc_name = filename[:-4]
                file_path = os.path.join(docs_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                if not text.strip():
                    continue
                if Document.record_by_name(doc_name):
                    print(f"Пропущен: {doc_name}")
                    continue
                processed = TextPreprocessor.preprocess(text)
                idx = Index()
                clean = idx.extract_keywords(processed, top_n=7)
                words = re.findall(r'\w+', text)
                original = []
                for kw in clean:
                    found = next((w for w in words if TextPreprocessor.preprocess(w) == kw), None)
                    if found and found not in original:
                        original.append(found)
                doc_id = str(uuid.uuid4())
                Document.add_record(doc_id, doc_name, file_path, original)
                print(f"Добавлен: {doc_name}")
                added += 1
            except Exception as e:
                print(f"Ошибка при обработке {filename}: {e}")
                continue
        Index().build_inverted_index()
        print(f"Готово. Добавлено: {added}, всего файлов: {len(files)}")
        return True
    except Exception as e:
        print(f"Сбой инициализации: {e}")
        return False


if __name__ == '__main__':
    ok = initialize()
    sys.exit(0 if ok else 1)