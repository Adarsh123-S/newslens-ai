# NewsLens AI

RAG-based multi-source news research assistant — retrieves articles from
multiple sources and generates answers with source comparison, agreement/
contradiction detection, and citations.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key (get one at console.anthropic.com):
   ```
   # Windows PowerShell:
   $env:ANTHROPIC_API_KEY="your-key-here"

   # Mac/Linux:
   export ANTHROPIC_API_KEY=your-key-here
   ```

## Project structure

```
src/
  config.py              - RSS feed sources, settings
  database.py            - SQLite storage layer
  text_cleaner.py        - HTML stripping / text normalization
  collector.py           - Phase 1: pulls articles from RSS feeds
  seed_sample_data.py    - Alternative to collector.py: loads 6 sample
                            articles for testing without live feeds
  embeddings.py          - Phase 2: real semantic search
                            (sentence-transformers + FAISS)
  retrieval_fallback.py  - Lightweight TF-IDF search (no model download
                            needed) - useful for quick testing
  rag_pipeline.py         - Phase 3: retrieval + Claude API generation,
                            with source comparison / contradiction detection
```

## Running it, in order

From inside the `src/` folder:

1. **Get articles into the database** (pick one):
   ```
   python collector.py          # pulls real articles from RSS feeds
   ```
   or, for quick testing without internet-dependent feeds:
   ```
   python seed_sample_data.py   # loads 6 sample articles
   ```

2. **Build the semantic search index** (first time, and after adding new articles):
   ```
   python embeddings.py
   ```
   Note: this downloads the `all-MiniLM-L6-v2` model (~90MB) from
   HuggingFace on first run.

3. **Ask a question**:
   ```
   python rag_pipeline.py
   ```
   This currently uses `retrieval_fallback.py` (TF-IDF) for retrieval by
   default. To use real semantic search instead, open `rag_pipeline.py`
   and change:
   ```python
   from retrieval_fallback import semantic_search
   ```
   to:
   ```python
   from embeddings import semantic_search
   ```

   To ask your own question, edit the query at the bottom of
   `rag_pipeline.py`, or import `answer_question()` into your own script:
   ```python
   from rag_pipeline import answer_question
   result = answer_question("your question here")
   print(result["answer"])
   ```

## What's still to build

- Sentiment analysis module (RoBERTa-based)
- Contradiction/timeline detection logic
- Web UI (FastAPI + frontend)

## Notes

- `config.py` has the RSS feed list — add/remove sources there.
- The database lives at `data/newslens.db` (created automatically).
- Duplicate articles (same URL) are automatically skipped on re-collection.
