"""
NewsLens AI - Sentiment Analysis (Phase 2b)

Uses a pretrained RoBERTa model fine-tuned for sentiment classification
(cardiffnlp/twitter-roberta-base-sentiment-latest) to score each article
as positive / neutral / negative. No training needed -- pretrained model,
downloaded automatically on first run (~500MB, one-time).

Adds a sentiment analysis layer to articles already in the database,
and can be plugged into rag_pipeline.py to show sentiment alongside
source comparison.
"""

from transformers import pipeline

from database import get_all_articles

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        print("Loading sentiment model (first run downloads ~500MB)...")
        _classifier = pipeline("sentiment-analysis", model=MODEL_NAME)
    return _classifier


def analyze_sentiment(text: str) -> dict:
    """
    Returns {"label": "positive"|"neutral"|"negative", "score": float}
    Truncates long text since the model has a token limit.
    """
    classifier = get_classifier()
    truncated = text[:512]  # rough safety truncation before tokenization
    result = classifier(truncated)[0]
    return {"label": result["label"].lower(), "score": round(result["score"], 3)}


def analyze_all_articles():
    """Run sentiment on every article currently in the database and print results."""
    articles = get_all_articles()
    if not articles:
        print("No articles in database. Run seed_sample_data.py or collector.py first.")
        return []

    results = []
    for a in articles:
        sentiment = analyze_sentiment(a["cleaned_text"])
        results.append({**a, "sentiment": sentiment})
        print(f"[{sentiment['label']:>8} {sentiment['score']:.2f}] {a['source']}: {a['title']}")

    return results


if __name__ == "__main__":
    analyze_all_articles()