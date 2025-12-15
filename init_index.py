import os
import sys
import uuid
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.core.document_manager import Document
from backend.core.index import Index
from backend.core.text_preprocess import TextPreprocessor


def initialize():
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
    
    index = Index()
    preprocessor = TextPreprocessor()
    
    for filename in files:
        doc_name = filename[:-4]
        file_path = os.path.join(docs_path, filename)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            continue
        
        if Document.get_by_name(doc_name):
            print(f"Пропущен: {doc_name}")
            continue
        
        processed = preprocessor.preprocess(text)
        keywords_stems = index.extract_keywords(processed, top_n=7)
        
        words = re.findall(r'\w+', text)
        keywords_original = []
        for stem in keywords_stems:
            for w in words:
                if preprocessor.preprocess(w) == stem:
                    keywords_original.append(w)
                    break
        
        doc_id = str(uuid.uuid4())
        doc = Document(doc_id, doc_name, file_path)
        doc.save_to_db(keywords_original)
        
        print(f"Добавлен: {doc_name}")
        added += 1
    
    index.build_index()
    print(f"Готово. Добавлено: {added}, всего файлов: {len(files)}")
    return True


if __name__ == '__main__':
    ok = initialize()
    sys.exit(0 if ok else 1)