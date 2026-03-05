"""API routes for AI-powered intelligence and insights."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import InsightResponse
from backend.core.database import get_db
from backend.models.alert import Alert
from backend.models.insight import MarketInsight
from backend.services.ai_engine.intelligence_engine import IntelligenceEngine
from backend.services.erp_integration.erp_client import ERPClient
from backend.services.market_data.commodity_tracker import CommodityTracker
from backend.services.pos_integration.pos_client import POSClient
from backend.services.supply_chain.risk_analyzer import SupplyChainRiskAnalyzer

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/insights", response_model=list[InsightResponse])
async def list_insights(
    limit: int = 20, category: str | None = None, db: AsyncSession = Depends(get_db)
):
    query = select(MarketInsight).order_by(MarketInsight.created_at.desc()).limit(limit)
    if category:
        query = query.where(MarketInsight.category == category)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/analyze-market")
async def analyze_market(db: AsyncSession = Depends(get_db)):
    """Trigger comprehensive market analysis."""
    tracker = CommodityTracker(db)
    risk_analyzer = SupplyChainRiskAnalyzer(db)
    engine = IntelligenceEngine(db)

    commodity_data = await tracker.get_latest_prices()
    supply_chain_data = await risk_analyzer.get_supply_chain_overview()

    insight = await engine.analyze_market_conditions(commodity_data, supply_chain_data)
    return {
        "id": insight.id,
        "title": insight.title,
        "summary": insight.summary,
        "detailed_analysis": insight.detailed_analysis,
        "recommended_actions": insight.recommended_actions,
    }


@router.post("/daily-briefing")
async def generate_daily_briefing(db: AsyncSession = Depends(get_db)):
    """Generate the daily intelligence briefing."""
    tracker = CommodityTracker(db)
    risk_analyzer = SupplyChainRiskAnalyzer(db)
    erp = ERPClient(db)
    pos = POSClient(db)
    engine = IntelligenceEngine(db)

    commodity_prices = await tracker.get_latest_prices()
    supply_chain = await risk_analyzer.get_supply_chain_overview()
    low_stock = await erp.get_low_stock_products()
    top_selling = await pos.get_top_selling_products()

    # Get recent alerts
    alert_result = await db.execute(
        select(Alert)
        .where(Alert.is_resolved.is_(False))
        .order_by(Alert.created_at.desc())
        .limit(10)
    )
    alerts = alert_result.scalars().all()
    recent_alerts = [
        {
            "type": a.alert_type.value,
            "severity": a.severity.value,
            "title": a.title,
            "message": a.message,
        }
        for a in alerts
    ]

    insight = await engine.generate_daily_briefing(
        commodity_prices, supply_chain, low_stock, top_selling, recent_alerts
    )

    return {
        "id": insight.id,
        "title": insight.title,
        "summary": insight.summary,
        "detailed_analysis": insight.detailed_analysis,
        "recommended_actions": insight.recommended_actions,
    }


@router.post("/pricing-analysis/{product_id}")
async def analyze_pricing(product_id: int, db: AsyncSession = Depends(get_db)):
    """Analyze pricing opportunity for a specific product."""
    from backend.models.product import Product
    from backend.services.market_data.price_forecaster import PriceForecaster

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return {"error": "Product not found"}

    product_data = {
        "name": product.name,
        "category": product.category,
        "current_cost_usd": product.current_cost_usd,
        "current_sell_price_usd": product.current_sell_price_usd,
        "margin_percent": product.margin_percent,
    }

    # Try to get commodity forecast
    commodity_forecast = {}
    if product.primary_commodity:
        from backend.models.commodity import Commodity

        comm_result = await db.execute(
            select(Commodity).where(Commodity.name == product.primary_commodity)
        )
        commodity = comm_result.scalar_one_or_none()
        if commodity:
            forecaster = PriceForecaster(db)
            commodity_forecast = await forecaster.forecast_prices(commodity.id)

    pos = POSClient(db)
    sales_velocity = await pos.get_sales_velocity(product_id)

    engine = IntelligenceEngine(db)
    insight = await engine.analyze_pricing_opportunity(
        product_data, commodity_forecast, sales_velocity
    )

    return {
        "id": insight.id,
        "title": insight.title,
        "summary": insight.summary,
        "detailed_analysis": insight.detailed_analysis,
        "recommended_actions": insight.recommended_actions,
    }
