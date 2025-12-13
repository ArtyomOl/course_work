import os, re, math, sqlite3, pickle
from collections import Counter, defaultdict
from . import text_preprocess as tp

DATA_PATH = r'D:\Python projects\COURSE_WORK\data\documents'
INDEX_DB = r'D:\Python projects\COURSE_WORK\backend\core\index\inverted_index.db'

def tokenize(text):
    return re.findall(r'\w+', tp.preprocess_text(text))

def connect_db():
    os.makedirs(os.path.dirname(INDEX_DB), exist_ok=True)
    conn = sqlite3.connect(INDEX_DB)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS index_table (term TEXT PRIMARY KEY, postings BLOB)')
    cur.execute('CREATE TABLE IF NOT EXISTS term_meta (term TEXT PRIMARY KEY, df INTEGER, idf REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS doc_meta (filename TEXT PRIMARY KEY, norm REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value INTEGER)')
    conn.commit()
    return conn, cur

def build_inverted_index():
    conn, cur = connect_db()
    os.makedirs(DATA_PATH, exist_ok=True)
    docs = [f for f in os.listdir(DATA_PATH) if f.endswith('.txt')]
    term_docs, doc_freqs = defaultdict(set), {}
    for f in docs:
        path = os.path.join(DATA_PATH, f)
        print(path)
        with open(path, 'r', encoding='utf-8') as file:
            tokens = tokenize(file.read())
        freqs = Counter(tokens)
        name = f[:-4]
        doc_freqs[name] = freqs
        for t in freqs:
            term_docs[t].add(name)
    total = len(doc_freqs)
    for t, dset in term_docs.items():
        df = len(dset)
        idf = math.log((total + 1) / (df + 1)) + 1
        cur.execute('INSERT OR REPLACE INTO term_meta VALUES (?, ?, ?)', (t, df, idf))
        cur.execute('INSERT OR REPLACE INTO index_table VALUES (?, ?)',
                    (t, pickle.dumps([(n, doc_freqs[n][t]) for n in dset])))
    for n, freqs in doc_freqs.items():
        norm = math.sqrt(sum(((1 + math.log(tf)) * (math.log((total + 1) / (len(term_docs[t]) + 1)) + 1))**2 for t, tf in freqs.items()))
        cur.execute('INSERT OR REPLACE INTO doc_meta VALUES (?, ?)', (n, norm))
    cur.execute('INSERT OR REPLACE INTO metadata VALUES ("total_docs", ?)', (total,))
    conn.commit()
    conn.close()

def add_document_to_index(doc_id, text):
    file_path = os.path.join(DATA_PATH, f"{doc_id}.txt")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    build_inverted_index()

def delete_document_from_index(doc_id):
    file_path = os.path.join(DATA_PATH, f"{doc_id}.txt")
    if os.path.exists(file_path):
        os.remove(file_path)
    build_inverted_index()

def total_docs():
    conn, cur = connect_db()
    cur.execute('SELECT value FROM metadata WHERE key="total_docs"')
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def idf(term):
    conn, cur = connect_db()
    cur.execute('SELECT idf FROM term_meta WHERE term=?', (term,))
    row = cur.fetchone()
    conn.close()
    total = total_docs()
    return row[0] if row else math.log((total + 1) / 1) + 1

def create_vector(text):
    tokens = tokenize(text)
    if not tokens: return {}
    f = Counter(tokens)
    return {t: (1 + math.log(tf)) * idf(t) for t, tf in f.items()}

def extract_keywords(text, top_n=5):
    vec = create_vector(text)
    if not vec: return []
    return [w for w, _ in sorted(vec.items(), key=lambda x: x[1], reverse=True)[:top_n]]

if __name__ == '__main__':
    build_inverted_index()
