"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import (
    analytics,
    commodities,
    dashboard,
    intelligence,
    landed_cost,
    news,
    notifications,
    reports,
    suppliers,
    sync,
    webhooks,
)
from backend.core.config import settings
from backend.core.database import Base, engine, async_session
from backend.core.logging import setup_logging
from backend.models import (  # noqa: F401 - ensure all models registered with Base
    Commodity, CommodityPrice, Product, ProductPriceHistory,
    Supplier, SupplierRiskAssessment, Alert, AlertThreshold,
    InventorySnapshot, SalesRecord, MarketInsight,
    CurrencyRate, NewsArticle, LandedCostCalculation, DutyRate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import traceback

    try:
        setup_logging()
    except Exception as e:
        print(f"Logging setup warning: {e}")

    # Ensure PostgreSQL enum types have all values before creating/altering tables
    # ALTER TYPE ... ADD VALUE must run outside a transaction block
    try:
        from sqlalchemy import text as sa_text
        from sqlalchemy.ext.asyncio import create_async_engine as _cae
        raw_engine = _cae(
            str(engine.url),
            isolation_level="AUTOCOMMIT",
        )
        async with raw_engine.connect() as conn:
            for val in ["beverage", "packaging", "cleaning", "shipping", "currency", "other"]:
                try:
                    await conn.execute(
                        sa_text(f"ALTER TYPE commoditycategory ADD VALUE IF NOT EXISTS '{val}'")
                    )
                except Exception:
                    pass
        await raw_engine.dispose()
        print("Enum types updated")
    except Exception as e:
        print(f"Enum update note: {e}")

    # Create tables using SQLAlchemy metadata (works even without alembic migrations)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables ensured")
    except Exception as e:
        print(f"Table creation warning: {e}")
        traceback.print_exc()

    # Also try alembic for any pending migrations
    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print("Alembic migrations applied")
        else:
            print(f"Alembic note: {result.stderr[:200]}")
    except Exception as e:
        print(f"Alembic skipped: {e}")

    # Seed data if empty, then ensure all commodities exist
    try:
        from sqlalchemy import text
        async with async_session() as db:
            row = await db.execute(text("SELECT COUNT(*) FROM commodities"))
            count = row.scalar()
            if count == 0:
                from backend.seed_data import seed_commodities_and_prices, seed_suppliers
                await seed_commodities_and_prices(db)
                await seed_suppliers(db)
                print("Database seeded successfully")
            else:
                # Ensure any new commodities from DEFAULT_COMMODITIES are added
                from backend.services.market_data.commodity_tracker import CommodityTracker
                tracker = CommodityTracker(db)
                all_commodities = await tracker.ensure_all_commodities()
                print(f"Database has {len(all_commodities)} commodities (ensured all defaults)")
    except Exception as e:
        print(f"Seed skipped: {e}")
        traceback.print_exc()

    yield


app = FastAPI(
    title="FMCG Intelligence Platform",
    description=(
        "AI-enabled market intelligence for wholesale FMCG operations in Lebanon. "
        "Monitors commodity prices, supply chain risks, and provides actionable insights."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(dashboard.router, prefix="/api")
app.include_router(commodities.router, prefix="/api")
app.include_router(suppliers.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(landed_cost.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "FMCG Intelligence Platform",
        "environment": settings.app_env,
    }
