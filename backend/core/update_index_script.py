import json
import os
import requests
import time
from text_preprocess import preprocess_text
from indexer import upload_df  # твоя функция обновления индекса

INDEX_PATH = r'D:\Python projects\COURSE_WORK\core\index\index.json'
WIKI_API = "https://ru.wikipedia.org/w/api.php"

# Заголовок, чтобы не получить 403
HEADERS = {
    "User-Agent": "WikiIndexer/1.0 (your_email@example.com)"
}


def get_random_wikipedia_article():
    """
    Возвращает случайную статью (текст) с Википедии.
    Использует MediaWiki API — стабильный и не блокируется.
    """
    try:
        params = {
            "action": "query",
            "format": "json",
            "generator": "random",
            "grnnamespace": 0,  # только основные статьи
            "prop": "extracts",
            "explaintext": True,
            "grnlimit": 1
        }
        response = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"[Ошибка {response.status_code}] {response.text[:200]}")
            return None

        data = response.json()
        if "query" not in data:
            return None

        page = next(iter(data["query"]["pages"].values()))
        return page.get("extract", "")
    except Exception as e:
        print(f"[Ошибка] {e}")
        return None


def ensure_index_exists():
    if not os.path.exists(INDEX_PATH):
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump({"count": 0, "frequency": {}}, f, ensure_ascii=False, indent=4)


def increment_doc_count():
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    meta['count'] = meta.get('count', 0) + 1
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)


def train_index_on_random_wiki_articles(num_articles=500):
    ensure_index_exists()
    processed = 0

    print(f"📘 Начинаем обучение на {num_articles} случайных статьях Википедии...\n")

    for i in range(num_articles):
        raw_text = get_random_wikipedia_article()
        if not raw_text:
            time.sleep(1)
            continue

        clean_text = preprocess_text(raw_text)
        words = clean_text.split()

        if len(words) < 10:
            continue

        upload_df(words)
        increment_doc_count()
        processed += 1

        if (i + 1) % 20 == 0:
            print(f"→ Обработано {processed} статей")

        # Не спешим, чтобы не получить 429 или 403
        time.sleep(1)

    print(f"\n✅ Индексирование завершено. Всего добавлено {processed} статей.")

    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    print(f"📦 В индексе {len(meta['frequency'])} уникальных слов из {meta['count']} документов.")


if __name__ == "__main__":
    train_index_on_random_wiki_articles(num_articles=1000)
