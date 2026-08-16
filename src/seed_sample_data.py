"""
NewsLens AI - Sample Data Seeder

Populates the DB with realistic sample articles so Phases 2-4
(embeddings, RAG, sentiment, contradiction detection) can be built
and demoed without live internet access.

On your own machine, you won't need this — collector.py will pull
real articles from RSS feeds instead. Run this OR collector.py, not
necessarily both.
"""

from datetime import datetime, timedelta, timezone
from database import init_db, insert_article, article_count
from text_cleaner import clean_article

# Deliberately includes overlapping topics covered differently by
# different "sources" -- useful for testing source comparison /
# contradiction detection later.
SAMPLE_ARTICLES = [
    {
        "source": "The Hindu",
        "title": "India unveils new AI regulation framework focused on transparency",
        "summary": (
            "The Ministry of Electronics and IT released a draft AI governance "
            "framework emphasizing algorithmic transparency and mandatory audits "
            "for high-risk AI systems. Officials say the rules aim to build public "
            "trust without stifling innovation in the fast-growing sector."
        ),
        "days_ago": 1,
    },
    {
        "source": "Times of India",
        "title": "Tech industry raises concerns over new AI compliance rules",
        "summary": (
            "Industry bodies have warned that the newly proposed AI regulations "
            "could impose heavy compliance costs on startups. Several founders "
            "argue the audit requirements are too broad and could slow adoption "
            "of AI tools across sectors."
        ),
        "days_ago": 1,
    },
    {
        "source": "Reuters World",
        "title": "India's AI rules draw comparisons to EU AI Act",
        "summary": (
            "Analysts note the proposed framework shares structural similarities "
            "with the EU's risk-tiered approach to AI regulation, though India's "
            "draft leaves more discretion to sector regulators rather than a "
            "single central authority."
        ),
        "days_ago": 0,
    },
    {
        "source": "TechCrunch",
        "title": "Global AI chip demand pushes Nvidia to record quarter",
        "summary": (
            "Nvidia reported record data center revenue driven by continued "
            "demand for AI training chips. The company said supply remains "
            "constrained despite expanded manufacturing capacity."
        ),
        "days_ago": 2,
    },
    {
        "source": "BBC World",
        "title": "Nvidia earnings beat expectations amid AI boom",
        "summary": (
            "Nvidia's latest results topped analyst forecasts, with data center "
            "sales more than doubling year-on-year. The chipmaker's stock rose "
            "in after-hours trading following the announcement."
        ),
        "days_ago": 2,
    },
    {
        "source": "Al Jazeera",
        "title": "Nvidia warns of export restriction impact on future growth",
        "summary": (
            "Despite strong quarterly results, Nvidia cautioned that expanded "
            "export restrictions on advanced chips to certain markets could "
            "weigh on growth in coming quarters, tempering investor optimism."
        ),
        "days_ago": 1,
    },
]


def seed():
    init_db()
    now = datetime.now(timezone.utc)
    added = 0

    for i, art in enumerate(SAMPLE_ARTICLES):
        published_at = (now - timedelta(days=art["days_ago"], hours=i)).isoformat()
        cleaned_text = clean_article(art["title"], art["summary"])
        # unique dummy URL per article
        url = f"https://example-news.local/{art['source'].lower().replace(' ', '-')}/{i}"

        inserted = insert_article(
            source=art["source"],
            title=art["title"],
            url=url,
            published_at=published_at,
            raw_summary=art["summary"],
            cleaned_text=cleaned_text,
        )
        if inserted:
            added += 1

    print(f"Seeded {added} sample articles.")
    print(f"Total articles in database: {article_count()}")


if __name__ == "__main__":
    seed()
