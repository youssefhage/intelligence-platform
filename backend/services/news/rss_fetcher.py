"""RSS feed fetcher for commodity-related news."""

import re
from datetime import datetime
from xml.etree import ElementTree

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.news import NewsArticle

logger = structlog.get_logger()

# RSS feed sources
RSS_FEEDS = [
    {
        "name": "Google News - Commodities",
        "url": "https://news.google.com/rss/search?q=commodities+prices+oil+wheat+sugar",
    },
    {
        "name": "Google News - Shipping",
        "url": "https://news.google.com/rss/search?q=shipping+freight+supply+chain+disruption",
    },
    {
        "name": "Google News - Middle East Trade",
        "url": "https://news.google.com/rss/search?q=middle+east+trade+import+Lebanon",
    },
]

# Keywords for matching commodities
COMMODITY_KEYWORDS = {
    "rice": "Rice (Long Grain)",
    "wheat": "Wheat",
    "maize": "Maize",
    "corn": "Maize",
    "sunflower oil": "Sunflower Oil",
    "soybean oil": "Soybean Oil",
    "palm oil": "Palm Oil",
    "olive oil": "Olive Oil",
    "sugar": "Sugar (Raw)",
    "coffee": "Coffee (Arabica)",
    "tea": "Tea",
    "cocoa": "Cocoa",
    "milk powder": "Powdered Milk",
    "butter": "Butter",
    "diesel": "Diesel",
    "crude oil": "Brent Crude Oil",
    "brent": "Brent Crude Oil",
    "shipping": "Container Freight Rate",
    "freight": "Container Freight Rate",
    "aluminum": "Aluminum",
    "packaging": "Paper/Cardboard",
    "plastic": "HDPE (Plastic)",
    "red sea": "Container Freight Rate",
    "suez": "Container Freight Rate",
    "turkish lira": "USD/TRY",
    "egyptian pound": "USD/EGP",
    "yuan": "USD/CNY",
}


class RSSFetcher:
    """Fetches and parses commodity-related news from RSS feeds."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = httpx.AsyncClient(timeout=15.0)

    async def fetch_all_feeds(self) -> list[dict]:
        """Fetch articles from all configured RSS feeds."""
        all_articles = []
        for feed in RSS_FEEDS:
            articles = await self._fetch_feed(feed["url"], feed["name"])
            all_articles.extend(articles)
        return all_articles

    async def fetch_and_store(self) -> dict:
        """Fetch articles and store new ones in the database."""
        articles = await self.fetch_all_feeds()
        stored = 0
        skipped = 0

        for article in articles:
            # Check if article already exists by URL
            result = await self.db.execute(
                select(NewsArticle).where(NewsArticle.url == article["url"]).limit(1)
            )
            if result.scalar_one_or_none():
                skipped += 1
                continue

            # Match commodities
            matched = self._match_commodities(article["title"] + " " + (article.get("summary") or ""))

            record = NewsArticle(
                title=article["title"],
                url=article["url"],
                source=article["source"],
                published_at=article.get("published_at"),
                summary=article.get("summary"),
                matched_commodities=",".join(matched) if matched else None,
            )
            self.db.add(record)
            stored += 1

        if stored > 0:
            await self.db.commit()

        logger.info("RSS fetch complete", stored=stored, skipped=skipped)
        return {"stored": stored, "skipped": skipped, "total_fetched": len(articles)}

    async def _fetch_feed(self, url: str, source_name: str) -> list[dict]:
        """Fetch and parse a single RSS feed."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return self._parse_rss(response.text, source_name)
        except Exception as e:
            logger.warning("RSS feed fetch failed", source=source_name, error=str(e))
            return []

    def _parse_rss(self, xml_text: str, source_name: str) -> list[dict]:
        """Parse RSS XML into article dicts."""
        articles = []
        try:
            root = ElementTree.fromstring(xml_text)
            channel = root.find("channel")
            if channel is None:
                return articles

            for item in channel.findall("item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date_str = item.findtext("pubDate")
                description = item.findtext("description", "")

                if not title or not link:
                    continue

                pub_date = None
                if pub_date_str:
                    try:
                        # RFC 822 format common in RSS
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_str)
                    except Exception:
                        pass

                articles.append({
                    "title": title[:500],
                    "url": link[:1000],
                    "source": source_name,
                    "published_at": pub_date,
                    "summary": description[:1000] if description else None,
                })
        except ElementTree.ParseError as e:
            logger.warning("RSS parse error", source=source_name, error=str(e))

        return articles

    def _match_commodities(self, text: str) -> list[str]:
        """Find commodity matches in article text."""
        text_lower = text.lower()
        matched = set()
        for keyword, commodity_name in COMMODITY_KEYWORDS.items():
            if keyword in text_lower:
                matched.add(commodity_name)
        return list(matched)

    async def close(self):
        await self.client.aclose()
