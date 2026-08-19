# 📰 NewsLens AI

**A multi-source news research assistant that retrieves, compares, and synthesizes live news coverage across outlets — surfacing agreements, contradictions, and sentiment differences between sources.**

🔗 **Live demo:** [newslens-ai-ju3i.onrender.com](https://newslens-ai-ju3i.onrender.com)

---

## What it does

Ask a question about current events (e.g. *"How are different sources reporting on India's AI regulation?"*), and NewsLens AI:

1. **Retrieves** the most relevant articles from a live-updating database of real news, pulled hourly from multiple RSS feeds
2. **Scores sentiment** (positive / neutral / negative) for each retrieved article
3. **Synthesizes** an answer using an LLM, explicitly structured to show:
   - A direct summary
   - What each source individually reports
   - Where sources **agree**
   - Where sources **contradict or diverge**
   - A sentiment breakdown per source, with reasoning — not just a label
   - The list of sources used

This isn't just a news aggregator — it's designed to make **bias and framing differences across outlets visible**, rather than presenting a single flattened answer.

---

## Architecture

```
RSS Feeds (6 sources)
      │
      ▼
 Collector ──► Clean & dedupe ──► SQLite database
      │                                │
      │         (auto-refreshes hourly + on-demand)
      ▼
 Retrieval (TF-IDF + cosine similarity,
 relative relevance filtering)
      │
      ▼
 Sentiment scoring (per retrieved article)
      │
      ▼
 LLM synthesis (Gemini) ──► Structured comparative answer
      │
      ▼
 FastAPI web UI
```

**Pipeline phases:**
- **Phase 1 — Collection:** `collector.py` pulls and cleans articles from RSS feeds defined in `config.py`, storing them in SQLite (`database.py`, `text_cleaner.py`)
- **Phase 2 — Retrieval:** `retrieval_fallback.py` ranks articles against a query using TF-IDF vectorization and cosine similarity, with a *relative* relevance cutoff (an article must score within a threshold of the top match, rather than against a fixed number) so results adapt per-query instead of relying on a single hardcoded score
- **Phase 3 — RAG synthesis:** `rag_pipeline.py` builds a labeled context block (article + source + sentiment) and prompts an LLM to produce a structured, source-comparative answer — with retry/backoff handling for transient API failures
- **Phase 4 — Web app:** `app.py` (FastAPI) serves the UI, exposes `/ask` and `/refresh` endpoints, and runs a background scheduler that re-collects fresh articles every hour

---

## Key engineering decisions

- **Two sentiment models, chosen per environment.** Locally, sentiment analysis uses a RoBERTa transformer model (`sentiment.py`) for higher accuracy. In production, it swaps to VADER (`sentiment_lite.py`) — a lightweight, rule-based analyzer — because RoBERTa + PyTorch/Transformers requires 400–500MB+ of RAM just to load, which exceeds free-tier hosting memory limits (e.g. Render's 512MB cap) and would crash the app on deploy.
- **Retry logic with exponential backoff** around the LLM API call, since free-tier LLM APIs occasionally return `503` (overloaded) or `429` (rate-limited) — these are now retried automatically instead of failing the whole request.
- **Relative, not absolute, relevance filtering.** An early version of retrieval used a fixed similarity threshold, which proved brittle — too low let irrelevant articles slip in (e.g. matching on incidental word overlap), too high sometimes filtered out every result. Switching to a threshold relative to the top-scoring match for each query made retrieval far more robust across different question types.
- **Automatic + manual data freshness.** Articles refresh automatically every hour via a background scheduler, with a manual "Refresh News" button in the UI for on-demand updates.
- **Graceful degradation everywhere.** A broken or malformed RSS feed doesn't crash collection — it's logged and skipped. A query with no relevant articles returns a clear message instead of a hallucinated answer.

---

## Tech stack

| Layer | Tools |
|---|---|
| Collection | `feedparser`, `BeautifulSoup4`, `lxml` |
| Storage | SQLite |
| Retrieval | `scikit-learn` (TF-IDF + cosine similarity) |
| Sentiment | `vaderSentiment` (prod) / RoBERTa via `transformers` + `torch` (local) |
| Generation | Google Gemini API |
| Backend | FastAPI, `uvicorn`, `APScheduler` |
| Deployment | Render |

---

## Running locally

```bash
git clone https://github.com/Adarsh123-S/newslens-ai.git
cd newslens-ai/src
pip install -r requirements.txt

# Set your Gemini API key (free tier: aistudio.google.com/apikey)
export GOOGLE_API_KEY="your-key-here"     # macOS/Linux
$env:GOOGLE_API_KEY="your-key-here"       # PowerShell

# Collect articles
python collector.py

# Run the app
uvicorn app:app --reload
```

Then open `http://127.0.0.1:8000`.

---

## Possible future improvements

- Real semantic embeddings (`sentence-transformers`) for retrieval, in place of TF-IDF — held back for the hosted demo due to memory constraints, but noted in `embeddings.py` for local use
- Additional/more resilient RSS sources
- Persistent storage beyond SQLite for multi-instance deployment
- Caching layer to reduce redundant LLM calls for repeated questions

---

*Built as an end-to-end exploration of RAG pipelines, multi-source retrieval, and deploying LLM-backed apps under real hosting constraints.*