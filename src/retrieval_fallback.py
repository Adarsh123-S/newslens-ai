"""
NewsLens AI - Retrieval Fallback (sandbox demo only)

sentence-transformers needs HuggingFace access to download model weights,
which this sandbox environment doesn't have. This module gives a
same-interface substitute using TF-IDF + cosine similarity (scikit-learn),
purely so we can demo the RAG pipeline end-to-end right now.

On your own machine: use embeddings.py instead (real semantic embeddings).
This file is a stand-in, not the production approach.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import get_all_articles

# An article must score at least this fraction of the TOP-scoring article's
# score to be considered relevant. This adapts per-query instead of relying
# on a fixed number, which doesn't work well since TF-IDF scores shift
# depending on the question and the current article database.
RELATIVE_RELEVANCE_CUTOFF = 0.35

# Absolute floor -- even the "best" match must clear this to avoid returning
# results for completely unrelated queries where nothing scores well.
ABSOLUTE_FLOOR = 0.04


def semantic_search(query: str, top_k: int = 5):
    """TF-IDF based 'semantic-ish' search. Good enough for demo purposes."""
    articles = get_all_articles()
    if not articles:
        return []

    texts = [f"{a['title']} {a['title']} {a['cleaned_text']}" for a in articles]

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(texts + [query])

    query_vec = tfidf_matrix[-1]
    doc_vecs = tfidf_matrix[:-1]

    scores = cosine_similarity(query_vec, doc_vecs)[0]

    ranked = sorted(zip(articles, scores), key=lambda x: x[1], reverse=True)

    if not ranked or ranked[0][1] < ABSOLUTE_FLOOR:
        return []  # nothing even remotely relevant

    top_score = ranked[0][1]
    cutoff = top_score * RELATIVE_RELEVANCE_CUTOFF

    results = [
        {**a, "score": float(s)}
        for a, s in ranked[:top_k]
        if s >= cutoff
    ]
    return results


if __name__ == "__main__":
    results = semantic_search("AI regulation in India")
    for r in results:
        print(f"[{r['score']:.3f}] {r['source']}: {r['title']}")