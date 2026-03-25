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

# RSS feed sources — Google News RSS with targeted queries
RSS_FEEDS = [
    {
        "name": "Commodity Prices",
        "url": "https://news.google.com/rss/search?q=commodity+prices+oil+wheat+sugar+when:7d&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Oil & Energy",
        "url": "https://news.google.com/rss/search?q=crude+oil+brent+opec+energy+prices+when:7d&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Shipping & Trade",
        "url": "https://news.google.com/rss/search?q=shipping+freight+red+sea+container+trade+when:7d&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Food & Agriculture",
        "url": "https://news.google.com/rss/search?q=wheat+rice+sugar+coffee+palm+oil+food+prices+when:7d&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Middle East Economy",
        "url": "https://news.google.com/rss/search?q=middle+east+trade+turkey+egypt+lebanon+economy+when:7d&hl=en-US&gl=US&ceid=US:en",
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
    "soy oil": "Soybean Oil",
    "palm oil": "Palm Oil",
    "olive oil": "Olive Oil",
    "sugar": "Sugar (Raw)",
    "coffee": "Coffee (Arabica)",
    "arabica": "Coffee (Arabica)",
    "robusta": "Coffee (Robusta)",
    "tea": "Tea",
    "cocoa": "Cocoa",
    "chocolate": "Cocoa",
    "milk powder": "Powdered Milk",
    "dairy": "Powdered Milk",
    "butter": "Butter",
    "diesel": "Diesel",
    "crude oil": "Brent Crude Oil",
    "brent": "Brent Crude Oil",
    "oil price": "Brent Crude Oil",
    "opec": "Brent Crude Oil",
    "natural gas": "Diesel",
    "shipping": "Container Freight Rate",
    "freight": "Container Freight Rate",
    "container": "Container Freight Rate",
    "aluminum": "Aluminum",
    "aluminium": "Aluminum",
    "packaging": "Paper/Cardboard",
    "plastic": "HDPE (Plastic)",
    "red sea": "Container Freight Rate",
    "suez": "Container Freight Rate",
    "houthi": "Container Freight Rate",
    "turkish lira": "USD/TRY",
    "turkey economy": "USD/TRY",
    "egyptian pound": "USD/EGP",
    "egypt economy": "USD/EGP",
    "yuan": "USD/CNY",
    "china trade": "USD/CNY",
    "lebanon": "USD/LBP",
    "commodity": "Brent Crude Oil",
    "inflation": "Sugar (Raw)",
    "food price": "Wheat",
    "grain": "Wheat",
    "fertilizer": "Wheat",
    "soybean": "Soybean Oil",
    "tin": "Tin Plate",
}


class RSSFetcher:
    """Fetches and parses commodity-related news from RSS feeds."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = httpx.AsyncClient(
            timeout=20.0,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; FMCGIntelligenceBot/1.0; +https://market.melqard.com)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
            follow_redirects=True,
        )

    async def fetch_all_feeds(self) -> list[dict]:
        """Fetch articles from all configured RSS feeds."""
        all_articles = []
        for feed in RSS_FEEDS:
            articles = await self._fetch_feed(feed["url"], feed["name"])
            all_articles.extend(articles)
            logger.info("RSS feed fetched", source=feed["name"], articles=len(articles))
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
                published_at=self._strip_tz(article.get("published_at")),
                summary=article.get("summary"),
                matched_commodities=",".join(matched) if matched else None,
            )
            self.db.add(record)
            stored += 1

        if stored > 0:
            await self.db.commit()

        logger.info("RSS fetch complete", stored=stored, skipped=skipped, total=len(articles))
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

            # Handle both RSS 2.0 (<channel><item>) and Atom (<entry>) formats
            channel = root.find("channel")
            items = []
            if channel is not None:
                items = channel.findall("item")
            else:
                # Try Atom format
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                items = root.findall("atom:entry", ns)
                if not items:
                    items = root.findall("entry")

            for item in items:
                title = (
                    item.findtext("title", "")
                    or item.findtext("{http://www.w3.org/2005/Atom}title", "")
                )
                link = item.findtext("link", "")
                if not link:
                    # Atom: <link href="..."/>
                    link_el = item.find("{http://www.w3.org/2005/Atom}link")
                    if link_el is not None:
                        link = link_el.get("href", "")
                    else:
                        link_el = item.find("link")
                        if link_el is not None and link_el.get("href"):
                            link = link_el.get("href", "")

                pub_date_str = (
                    item.findtext("pubDate")
                    or item.findtext("{http://www.w3.org/2005/Atom}published")
                    or item.findtext("{http://www.w3.org/2005/Atom}updated")
                )
                description = (
                    item.findtext("description", "")
                    or item.findtext("{http://www.w3.org/2005/Atom}summary", "")
                    or item.findtext("{http://www.w3.org/2005/Atom}content", "")
                )

                if not title or not link:
                    continue

                pub_date = None
                if pub_date_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_str)
                    except Exception:
                        try:
                            # ISO format for Atom
                            pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                        except Exception:
                            pass

                # Strip HTML tags from description
                clean_desc = re.sub(r"<[^>]+>", "", description) if description else ""

                articles.append({
                    "title": title[:500],
                    "url": link[:1000],
                    "source": source_name,
                    "published_at": pub_date,
                    "summary": clean_desc[:1000] if clean_desc else None,
                })
        except ElementTree.ParseError as e:
            logger.warning("RSS parse error", source=source_name, error=str(e))

        return articles

    @staticmethod
    def _strip_tz(dt: datetime | None) -> datetime | None:
        """Strip timezone info for SQLAlchemy DateTime without tz."""
        if dt is None:
            return None
        return dt.replace(tzinfo=None) if dt.tzinfo else dt

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
