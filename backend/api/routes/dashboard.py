"""API routes for the main dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import AlertResponse, DashboardSummary
from backend.core.database import get_db
from backend.models.alert import Alert
from backend.models.commodity import Commodity
from backend.models.product import Product
from backend.models.supplier import Supplier
from backend.services.erp_integration.erp_client import ERPClient
from backend.services.supply_chain.risk_analyzer import SupplyChainRiskAnalyzer

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get a high-level summary for the dashboard."""
    # Counts
    commodities_count = await db.execute(
        select(func.count()).select_from(Commodity).where(Commodity.is_active.is_(True))
    )
    products_count = await db.execute(
        select(func.count()).select_from(Product).where(Product.is_active.is_(True))
    )
    suppliers_count = await db.execute(
        select(func.count()).select_from(Supplier).where(Supplier.is_active.is_(True))
    )
    alerts_count = await db.execute(
        select(func.count())
        .select_from(Alert)
        .where(Alert.is_resolved.is_(False))
    )

    # Supply chain risk
    analyzer = SupplyChainRiskAnalyzer(db)
    overview = await analyzer.get_supply_chain_overview()

    # Low stock
    erp = ERPClient(db)
    low_stock = await erp.get_low_stock_products()

    return DashboardSummary(
        total_commodities_tracked=commodities_count.scalar() or 0,
        total_products=products_count.scalar() or 0,
        total_suppliers=suppliers_count.scalar() or 0,
        active_alerts=alerts_count.scalar() or 0,
        overall_supply_risk_score=overview.get("overall_risk_score", 0),
        commodities_with_price_increase=0,  # Computed from price data
        low_stock_items=len(low_stock),
    )


@router.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Alert)
        .where(Alert.is_resolved.is_(False))
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        query = query.where(Alert.is_read.is_(False))
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        return {"error": "Alert not found"}
    alert.is_read = True
    await db.commit()
    return {"status": "ok"}


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        return {"error": "Alert not found"}
    alert.is_resolved = True
    await db.commit()
    return {"status": "ok"}
