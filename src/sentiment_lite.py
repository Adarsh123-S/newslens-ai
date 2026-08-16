"""
NewsLens AI - Sentiment Analysis (Deployment version)

Uses VADER instead of RoBERTa for the deployed web app -- RoBERTa +
torch/transformers needs 400-500MB+ RAM just to load, which exceeds
free hosting tier limits (e.g. Render's 512MB cap) and will crash
the app. VADER is lightweight (a few MB, no model download, instant
startup) and gives reasonable positive/neutral/negative labels.

For local development, sentiment.py (RoBERTa-based) is more accurate
and has no memory constraints -- use that instead when running locally.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from database import get_all_articles

_analyzer = None


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def analyze_sentiment(text: str) -> dict:
    """
    Returns {"label": "positive"|"neutral"|"negative", "score": float}
    VADER's compound score ranges -1 (most negative) to +1 (most positive).
    """
    analyzer = get_analyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {"label": label, "score": round(abs(compound), 3)}


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