"""
NewsLens AI - Text cleaning
RSS summaries often contain HTML tags, escaped entities, and tracking
cruft. This strips it down to plain readable text before storage/embedding.
"""

import re
import html
from bs4 import BeautifulSoup


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and decode entities."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")
    text = soup.get_text(separator=" ")
    text = html.unescape(text)
    return normalize_whitespace(text)


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_article(title: str, raw_summary: str) -> str:
    """
    Produce the text that will eventually be chunked + embedded.
    Combines title + cleaned summary since RSS feeds rarely give full body text.
    """
    cleaned_summary = clean_html(raw_summary)
    title = normalize_whitespace(title or "")
    return f"{title}. {cleaned_summary}".strip()
