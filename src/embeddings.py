"""
NewsLens AI - Embeddings (Phase 2)

Uses sentence-transformers (all-MiniLM-L6-v2) + FAISS for real semantic
search. This is the version you should run on your own machine, where
HuggingFace and the model weights are reachable.

Requires: pip install sentence-transformers faiss-cpu numpy
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from database import get_all_articles, get_unembedded_articles, mark_embedded

MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_PATH = "data/faiss.index"
ID_MAP_PATH = "data/faiss_ids.npy"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def build_index():
    """Embed all unembedded articles and add them to a FAISS index."""
    articles = get_unembedded_articles()
    if not articles:
        print("No new articles to embed.")
        return

    texts = [a["cleaned_text"] for a in articles]
    ids = [a["id"] for a in articles]
    vectors = embed_texts(texts).astype("float32")

    dim = vectors.shape[1]
    try:
        index = faiss.read_index(INDEX_PATH)
        existing_ids = list(np.load(ID_MAP_PATH))
    except Exception:
        index = faiss.IndexFlatIP(dim)  # cosine similarity via normalized vectors
        existing_ids = []

    index.add(vectors)
    existing_ids.extend(ids)

    faiss.write_index(index, INDEX_PATH)
    np.save(ID_MAP_PATH, np.array(existing_ids))

    for aid in ids:
        mark_embedded(aid)

    print(f"Embedded and indexed {len(articles)} articles.")


def semantic_search(query: str, top_k: int = 5):
    """Return top_k articles most semantically similar to the query."""
    index = faiss.read_index(INDEX_PATH)
    id_map = np.load(ID_MAP_PATH)

    query_vec = embed_texts([query]).astype("float32")
    scores, indices = index.search(query_vec, top_k)

    all_articles = {a["id"]: a for a in get_all_articles()}
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        article_id = int(id_map[idx])
        article = all_articles.get(article_id)
        if article:
            results.append({**article, "score": float(score)})
    return results


if __name__ == "__main__":
    build_index()
