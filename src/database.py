"""
NewsLens AI - Database layer
Simple SQLite storage for Phase 1. Swap for PostgreSQL later if needed —
the schema won't need to change.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    published_at TEXT,
    raw_summary TEXT,
    cleaned_text TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
    embedded INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
"""


def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def insert_article(source, title, url, published_at, raw_summary, cleaned_text):
    """Insert an article. Silently skips duplicates (same URL)."""
    with get_conn() as conn:
        try:
            conn.execute(
                """INSERT INTO articles
                   (source, title, url, published_at, raw_summary, cleaned_text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (source, title, url, published_at, raw_summary, cleaned_text),
            )
            return True
        except sqlite3.IntegrityError:
            return False  # duplicate URL, already have it


def get_all_articles(limit=None):
    with get_conn() as conn:
        query = "SELECT * FROM articles ORDER BY published_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        return [dict(row) for row in conn.execute(query).fetchall()]


def get_unembedded_articles():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE embedded = 0"
        ).fetchall()
        return [dict(row) for row in rows]


def mark_embedded(article_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE articles SET embedded = 1 WHERE id = ?", (article_id,)
        )


def article_count():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
