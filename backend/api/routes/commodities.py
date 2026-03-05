"""API routes for commodity tracking and price management."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import (
    CommodityCreate,
    CommodityPriceRecord,
    CommodityResponse,
)
from backend.core.database import get_db
from backend.models.commodity import Commodity
from backend.services.market_data.commodity_tracker import CommodityTracker
from backend.services.market_data.price_forecaster import PriceForecaster

router = APIRouter(prefix="/commodities", tags=["commodities"])


@router.get("/", response_model=list[CommodityResponse])
async def list_commodities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Commodity).where(Commodity.is_active.is_(True))
    )
    return result.scalars().all()


@router.post("/", response_model=CommodityResponse)
async def create_commodity(
    data: CommodityCreate, db: AsyncSession = Depends(get_db)
):
    commodity = Commodity(**data.model_dump())
    db.add(commodity)
    await db.commit()
    await db.refresh(commodity)
    return commodity


@router.get("/prices/latest")
async def get_latest_prices(db: AsyncSession = Depends(get_db)):
    tracker = CommodityTracker(db)
    return await tracker.get_latest_prices()


@router.post("/prices")
async def record_price(
    data: CommodityPriceRecord, db: AsyncSession = Depends(get_db)
):
    tracker = CommodityTracker(db)
    price = await tracker.record_price(
        commodity_id=data.commodity_id,
        price_usd=data.price_usd,
        source=data.source,
        recorded_at=data.recorded_at,
        notes=data.notes,
    )
    return {"id": price.id, "commodity_id": price.commodity_id, "price_usd": price.price_usd}


@router.get("/{commodity_id}/history")
async def get_price_history(
    commodity_id: int, days: int = 90, db: AsyncSession = Depends(get_db)
):
    tracker = CommodityTracker(db)
    prices = await tracker.get_price_history(commodity_id, days)
    return [
        {
            "id": p.id,
            "price_usd": p.price_usd,
            "price_lbp": p.price_lbp,
            "source": p.source,
            "recorded_at": p.recorded_at.isoformat(),
        }
        for p in prices
    ]


@router.get("/{commodity_id}/forecast")
async def get_forecast(
    commodity_id: int,
    horizon_days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    forecaster = PriceForecaster(db)
    return await forecaster.forecast_prices(commodity_id, horizon_days)


@router.get("/{commodity_id}/anomalies")
async def get_anomalies(
    commodity_id: int, db: AsyncSession = Depends(get_db)
):
    forecaster = PriceForecaster(db)
    return await forecaster.detect_price_anomalies(commodity_id)


@router.post("/initialize")
async def initialize_commodities(db: AsyncSession = Depends(get_db)):
    tracker = CommodityTracker(db)
    commodities = await tracker.initialize_commodities()
    return {"initialized": len(commodities)}
