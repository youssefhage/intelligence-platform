"""API routes for news feed and geopolitical overlay."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.news import NewsArticle
from backend.services.news.geopolitical_overlay import GeopoliticalOverlay

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/feed")
async def get_news_feed(
    limit: int = 30,
    commodity: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get recent news articles, optionally filtered by commodity."""
    query = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit)
    if commodity:
        query = query.where(NewsArticle.matched_commodities.contains(commodity))
    result = await db.execute(query)
    articles = result.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "source": a.source,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "summary": a.summary,
            "matched_commodities": a.matched_commodities.split(",") if a.matched_commodities else [],
            "sentiment": a.sentiment,
            "impact_score": a.impact_score,
        }
        for a in articles
    ]


@router.post("/fetch")
async def trigger_news_fetch(db: AsyncSession = Depends(get_db)):
    """Manually trigger RSS feed fetch."""
    import traceback
    from backend.services.news.rss_fetcher import RSSFetcher

    fetcher = RSSFetcher(db)
    try:
        result = await fetcher.fetch_and_store()
        return result
    except Exception as e:
        traceback.print_exc()
        return {"stored": 0, "skipped": 0, "total_fetched": 0, "error": str(e)}
    finally:
        await fetcher.close()


@router.get("/geopolitical/scenarios")
async def get_geopolitical_scenarios():
    """List available geopolitical scenario types."""
    overlay = GeopoliticalOverlay()
    return overlay.get_scenario_types()


@router.get("/geopolitical/scenario/{scenario_id}")
async def run_geopolitical_scenario(scenario_id: str):
    """Run a specific geopolitical scenario and see commodity impacts."""
    overlay = GeopoliticalOverlay()
    return overlay.run_scenario(scenario_id)


@router.get("/geopolitical/supply-routes")
async def get_supply_routes():
    """Get supply route data for map visualization."""
    overlay = GeopoliticalOverlay()
    return overlay.get_supply_routes()


@router.post("/geopolitical/route-risk")
async def assess_route_risk(active_scenarios: list[str]):
    """Assess supply route risks based on active geopolitical scenarios."""
    overlay = GeopoliticalOverlay()
    return overlay.assess_route_risk(active_scenarios)
