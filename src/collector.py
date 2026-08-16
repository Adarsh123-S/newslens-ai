"""
NewsLens AI - Article Collector (Phase 1)

Pulls articles from RSS feeds defined in config.py, cleans them,
and stores them in SQLite. This is the top of the pipeline:

  RSS Feeds -> Collector -> Clean -> Store -> (Phase 2: Embed)
"""

import feedparser
from datetime import datetime, timezone

from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED
from database import init_db, insert_article, article_count
from text_cleaner import clean_article, clean_html


def parse_published_date(entry) -> str:
    """Return an ISO date string, falling back to 'now' if the feed omits one."""
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            return datetime(*val[:6], tzinfo=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def collect_from_feed(source_name: str, feed_url: str) -> tuple[int, int]:
    """Fetch one feed. Returns (new_articles, total_seen)."""
    print(f"  Fetching: {source_name} ...")
    parsed = feedparser.parse(feed_url)

    if parsed.bozo and not parsed.entries:
        print(f"    ⚠️  Could not parse feed ({parsed.bozo_exception})")
        return 0, 0

    new_count = 0
    entries = parsed.entries[:MAX_ARTICLES_PER_FEED]

    for entry in entries:
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        if not title or not url:
            continue

        raw_summary = entry.get("summary", "") or entry.get("description", "")
        cleaned_text = clean_article(title, raw_summary)
        published_at = parse_published_date(entry)

        inserted = insert_article(
            source=source_name,
            title=title,
            url=url,
            published_at=published_at,
            raw_summary=clean_html(raw_summary),
            cleaned_text=cleaned_text,
        )
        if inserted:
            new_count += 1

    return new_count, len(entries)


def collect_all():
    init_db()
    print(f"NewsLens AI — Collecting from {len(RSS_FEEDS)} sources\n")

    total_new = 0
    for source_name, feed_url in RSS_FEEDS.items():
        new_count, seen = collect_from_feed(source_name, feed_url)
        total_new += new_count
        print(f"    ✅ {new_count} new / {seen} seen\n")

    print(f"Done. {total_new} new articles added this run.")
    print(f"Total articles in database: {article_count()}")


if __name__ == "__main__":
    collect_all()
