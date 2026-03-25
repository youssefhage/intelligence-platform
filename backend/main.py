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

    # Migrate category column from enum to varchar for flexibility
    try:
        from sqlalchemy import text as sa_text
        async with engine.begin() as conn:
            # Check if column is still enum type and convert to varchar
            result = await conn.execute(sa_text("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'commodities' AND column_name = 'category'
            """))
            row = result.scalar_one_or_none()
            if row and row == "USER-DEFINED":
                await conn.execute(sa_text("""
                    ALTER TABLE commodities
                    ALTER COLUMN category TYPE VARCHAR(50)
                    USING category::TEXT
                """))
                print("Migrated category column from enum to varchar")
            else:
                print(f"Category column type: {row}")
    except Exception as e:
        print(f"Category migration note: {e}")

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
