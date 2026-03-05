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
from backend.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
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
