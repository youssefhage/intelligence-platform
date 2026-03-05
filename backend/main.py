"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import (
    analytics,
    commodities,
    dashboard,
    intelligence,
    notifications,
    suppliers,
    sync,
    webhooks,
)
from backend.core.config import settings
from backend.core.database import Base, engine, async_session
from backend.core.logging import setup_logging
from backend.models import (  # noqa: F401 - ensure all models registered with Base
    Commodity, CommodityPrice, Product, ProductPriceHistory,
    Supplier, SupplierRiskAssessment, Alert, InventorySnapshot,
    SalesRecord, MarketInsight,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Create tables using SQLAlchemy metadata (works even without alembic migrations)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables ensured")
    except Exception as e:
        print(f"Table creation warning: {e}")

    # Also try alembic stamp if tables were just created
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

    # Seed data if empty
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
                print(f"Database has {count} commodities, skipping seed")
    except Exception as e:
        print(f"Seed skipped: {e}")

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


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "FMCG Intelligence Platform",
        "environment": settings.app_env,
    }
