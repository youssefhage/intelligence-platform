"""API routes for report generation."""

import io

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db, get_redis

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/weekly")
async def generate_weekly_report(db: AsyncSession = Depends(get_db)):
    """Generate the weekly intelligence report as HTML."""
    from backend.services.reports.weekly_report import WeeklyReportGenerator

    try:
        redis = await get_redis()
    except Exception:
        redis = None

    generator = WeeklyReportGenerator(db, redis)
    html = await generator.generate_html()
    return HTMLResponse(content=html)
