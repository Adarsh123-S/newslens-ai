"""
NewsLens AI - RAG Pipeline (Phase 3) + Sentiment

Combines retrieval (semantic search over articles), sentiment scoring,
and an LLM call to generate an answer that explicitly compares sources,
flags contradictions/agreements, and reports sentiment per source.

Uses retrieval_fallback.py here. Swap to embeddings.py on your own
machine for real semantic search.

Uses Google Gemini's free-tier API for generation, and the local
RoBERTa model (sentiment.py) for sentiment scoring.
"""

import json
import os
import urllib.request
import urllib.error

from retrieval_fallback import semantic_search
from sentiment_lite import analyze_sentiment

MODEL = "gemini-3.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
API_KEY = os.environ.get("GOOGLE_API_KEY")


def build_context(articles: list[dict]) -> str:
    """Format retrieved articles + their sentiment into a labeled context block."""
    blocks = []
    for i, a in enumerate(articles, start=1):
        sentiment = analyze_sentiment(a["cleaned_text"])
        blocks.append(
            f"[Source {i}: {a['source']}]\n"
            f"Title: {a['title']}\n"
            f"Published: {a['published_at']}\n"
            f"Sentiment: {sentiment['label']} (confidence {sentiment['score']})\n"
            f"Content: {a['cleaned_text']}\n"
        )
    return "\n".join(blocks)


def ask_llm(query: str, context: str) -> str:
    system_prompt = (
        "You are NewsLens AI, a multi-source news research assistant. "
        "You are given a user question and several news articles retrieved "
        "from different sources, each with a pre-computed sentiment label "
        "(positive/neutral/negative) and confidence score. Answer the "
        "question using ONLY the provided articles. Structure your response "
        "with these sections:\n\n"
        "## Summary\n(2-3 sentence direct answer)\n\n"
        "## Source Comparison\n(what each source reports, referencing them as "
        "'Source N: <name>')\n\n"
        "## Agreements\n(facts multiple sources confirm)\n\n"
        "## Contradictions / Differences\n(where sources disagree or emphasize "
        "different things -- if none, say so explicitly)\n\n"
        "## Sentiment Breakdown\n(list each source's sentiment label and briefly "
        "explain WHY it leans that way based on its content -- not just "
        "restating the label)\n\n"
        "## Sources Used\n(list source names)\n\n"
        "Do not use outside knowledge. If the articles don't contain enough "
        "information, say so."
    )

    user_message = f"Question: {query}\n\nRetrieved articles:\n\n{context}"

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 2000
        }
    }

    if not API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable not set. "
            "Get a free key from aistudio.google.com/apikey and run:\n"
            "  $env:GOOGLE_API_KEY=\"your-key-here\"   (PowerShell)"
        )

    req = urllib.request.Request(
        f"{API_URL}?key={API_KEY}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"API request failed ({e.code}): {error_body}") from None

    try:
        candidate = data["candidates"][0]
        parts = candidate["content"]["parts"]
        return "\n".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError):
        return f"Unexpected response format: {json.dumps(data, indent=2)}"


def answer_question(query: str, top_k: int = 5) -> dict:
    articles = semantic_search(query, top_k=top_k)
    if not articles:
        return {
            "query": query,
            "answer": "No relevant articles found in the database for this query.",
            "sources": [],
        }

    context = build_context(articles)
    answer = ask_llm(query, context)

    return {
        "query": query,
        "answer": answer,
        "sources": [{"source": a["source"], "title": a["title"], "url": a["url"]} for a in articles],
    }


if __name__ == "__main__":
    result = answer_question("How are different sources reporting on India's AI regulation?")
    print(f"Q: {result['query']}\n")
    print(result["answer"])
    print("\n--- Sources ---")
    for s in result["sources"]:
        print(f"- {s['source']}: {s['title']}")