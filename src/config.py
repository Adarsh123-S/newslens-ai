"""
NewsLens AI - Configuration
Add or remove RSS feeds here. Mix of sources is what enables
'source comparison' features later in the RAG pipeline.
"""

RSS_FEEDS = {
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Times of India (Top Stories)": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Guardian (World)": "https://www.theguardian.com/world/rss",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}

DB_PATH = "data/newslens.db"

# How many articles to pull per feed per run
MAX_ARTICLES_PER_FEED = 20
