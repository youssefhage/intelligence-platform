"""API routes for analytics: margin analysis, demand forecasting, competitors, scenarios."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.ai_engine.competitor_monitor import CompetitorMonitor
from backend.services.ai_engine.demand_forecaster import DemandForecaster
from backend.services.ai_engine.margin_analyzer import AutoReorderEngine, MarginAnalyzer
from backend.services.ai_engine.scenario_engine import ScenarioEngine
from backend.services.market_data.currency_tracker import CurrencyTracker
from backend.services.market_data.port_tracker import PortTracker

router = APIRouter(prefix="/analytics", tags=["analytics"])


# --- Margin Analysis ---
@router.get("/margin/analysis")
async def run_margin_analysis(db: AsyncSession = Depends(get_db)):
    """Run full margin erosion analysis across all products."""
    analyzer = MarginAnalyzer(db)
    return await analyzer.run_full_analysis()


# --- Demand Forecasting ---
@router.get("/demand/product/{product_id}")
async def forecast_product_demand(
    product_id: int, horizon_days: int = 30, db: AsyncSession = Depends(get_db)
):
    """Forecast demand for a specific product."""
    forecaster = DemandForecaster(db)
    return await forecaster.forecast_product_demand(product_id, horizon_days)


@router.get("/demand/category/{category}")
async def forecast_category_demand(
    category: str, horizon_days: int = 30, db: AsyncSession = Depends(get_db)
):
    """Forecast aggregate demand for a product category."""
    forecaster = DemandForecaster(db)
    return await forecaster.forecast_category_demand(category, horizon_days)


# --- Competitor Monitoring ---
class CompetitorPriceInput(BaseModel):
    competitor_name: str
    product_name: str
    price_usd: float
    source: str = "manual_survey"
    sku_match: str | None = None
    notes: str = ""


class BulkCompetitorPriceInput(BaseModel):
    observations: list[CompetitorPriceInput]


@router.post("/competitors/prices")
async def record_competitor_price(
    data: CompetitorPriceInput, db: AsyncSession = Depends(get_db)
):
    """Record a single competitor price observation."""
    monitor = CompetitorMonitor(db)
    return await monitor.record_price_observation(
        competitor_name=data.competitor_name,
        product_name=data.product_name,
        price_usd=data.price_usd,
        source=data.source,
        sku_match=data.sku_match,
        notes=data.notes,
    )


@router.post("/competitors/prices/bulk")
async def record_bulk_competitor_prices(
    data: BulkCompetitorPriceInput, db: AsyncSession = Depends(get_db)
):
    """Record multiple competitor price observations."""
    monitor = CompetitorMonitor(db)
    return await monitor.record_bulk_prices(
        [obs.model_dump() for obs in data.observations]
    )


@router.get("/competitors/position")
async def get_competitive_position(
    product_id: int | None = None, db: AsyncSession = Depends(get_db)
):
    """Analyze competitive position for a product or entire portfolio."""
    monitor = CompetitorMonitor(db)
    return await monitor.analyze_competitive_position(product_id)


# --- What-If Scenarios ---
class ScenarioInput(BaseModel):
    scenario_type: str
    parameters: dict


@router.post("/scenarios/run")
async def run_scenario(data: ScenarioInput, db: AsyncSession = Depends(get_db)):
    """Run a what-if scenario analysis."""
    engine = ScenarioEngine(db)
    return await engine.run_scenario(data.scenario_type, data.parameters)


@router.get("/scenarios/types")
async def list_scenario_types():
    """List available scenario types with descriptions."""
    return {
        "scenario_types": [
            {
                "type": "commodity_price_shock",
                "description": "Model impact of commodity price increase/decrease",
                "example_params": {
                    "commodity_name": "Wheat",
                    "price_change_pct": 20,
                },
            },
            {
                "type": "currency_devaluation",
                "description": "Model impact of LBP devaluation",
                "example_params": {"devaluation_pct": 15},
            },
            {
                "type": "supply_disruption",
                "description": "Model impact of supplier disruption",
                "example_params": {
                    "supplier_name": "Supplier Name",
                    "duration_days": 30,
                },
            },
            {
                "type": "demand_surge",
                "description": "Model impact of unexpected demand increase",
                "example_params": {
                    "surge_pct": 30,
                    "category": "rice",
                    "duration_days": 14,
                },
            },
            {
                "type": "competitor_price_cut",
                "description": "Model impact of competitor cutting prices",
                "example_params": {
                    "competitor_name": "Competitor",
                    "price_cut_pct": 10,
                    "category": "cooking_oil",
                },
            },
            {
                "type": "tariff_change",
                "description": "Model impact of tariff/duty changes",
                "example_params": {
                    "commodity_name": "Sugar",
                    "tariff_change_pct": 5,
                },
            },
        ]
    }


# --- Currency ---
@router.get("/currency/rates")
async def get_currency_rates(db: AsyncSession = Depends(get_db)):
    """Get current USD/LBP exchange rates from multiple sources."""
    tracker = CurrencyTracker(db)
    result = await tracker.get_rate_summary()
    await tracker.close()
    return result


# --- Port & Shipping ---
@router.get("/ports/status")
async def get_port_status(db: AsyncSession = Depends(get_db)):
    """Get current Lebanese port operational status."""
    tracker = PortTracker(db)
    statuses = await tracker.check_port_status()
    await tracker.close()
    return {"ports": statuses}


@router.get("/ports/routes")
async def get_shipping_routes(db: AsyncSession = Depends(get_db)):
    """Get status of key shipping routes to Lebanon."""
    tracker = PortTracker(db)
    await tracker.check_port_status()  # Populate port statuses first
    routes = await tracker.get_shipping_routes_status()
    await tracker.close()
    return routes


@router.get("/ports/timeline")
async def get_import_timeline(
    origin_region: str,
    commodity_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Estimate import timeline from origin to warehouse."""
    tracker = PortTracker(db)
    await tracker.check_port_status()
    timeline = await tracker.get_import_timeline_estimate(origin_region, commodity_name)
    await tracker.close()
    return timeline


# --- Auto-Reorder ---
@router.get("/reorder/suggestions")
async def get_reorder_suggestions(db: AsyncSession = Depends(get_db)):
    """Generate automatic reorder suggestions based on stock and demand."""
    engine = AutoReorderEngine(db)
    return await engine.generate_reorder_suggestions()
