"""Background task scheduler for periodic data syncing and analysis."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.core.config import settings
from backend.core.database import async_session
from backend.core.logging import logger
from backend.services.erp_integration.erp_client import ERPClient
from backend.services.market_data.commodity_tracker import CommodityTracker
from backend.services.pos_integration.pos_client import POSClient
from backend.services.supply_chain.risk_analyzer import SupplyChainRiskAnalyzer

scheduler = AsyncIOScheduler()


async def sync_erp_products():
    """Periodically sync products from ERP."""
    async with async_session() as db:
        client = ERPClient(db)
        try:
            result = await client.sync_products()
            logger.info("Scheduled ERP product sync", **result)
        finally:
            await client.close()


async def sync_erp_inventory():
    """Periodically sync inventory from ERP."""
    async with async_session() as db:
        client = ERPClient(db)
        try:
            result = await client.sync_inventory()
            logger.info("Scheduled ERP inventory sync", **result)
        finally:
            await client.close()


async def sync_pos_sales():
    """Periodically sync sales from POS."""
    async with async_session() as db:
        client = POSClient(db)
        try:
            result = await client.sync_recent_sales()
            logger.info("Scheduled POS sales sync", **result)
        finally:
            await client.close()


async def fetch_commodity_prices():
    """Periodically fetch global commodity prices."""
    async with async_session() as db:
        tracker = CommodityTracker(db)
        try:
            await tracker.fetch_world_bank_prices()
            logger.info("Scheduled commodity price fetch complete")
        finally:
            await tracker.close()


async def run_supply_chain_assessments():
    """Periodically reassess supplier risks."""
    async with async_session() as db:
        from sqlalchemy import select

        from backend.models.supplier import Supplier

        result = await db.execute(
            select(Supplier).where(Supplier.is_active.is_(True))
        )
        suppliers = result.scalars().all()
        analyzer = SupplyChainRiskAnalyzer(db)

        for supplier in suppliers:
            try:
                await analyzer.assess_supplier_risk(supplier.id)
            except Exception as e:
                logger.error(
                    "Risk assessment failed",
                    supplier_id=supplier.id,
                    error=str(e),
                )


def setup_scheduler():
    """Configure and start the background scheduler."""
    scheduler.add_job(
        sync_erp_products,
        trigger=IntervalTrigger(minutes=settings.erp_sync_interval_minutes),
        id="sync_erp_products",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_erp_inventory,
        trigger=IntervalTrigger(minutes=settings.erp_sync_interval_minutes),
        id="sync_erp_inventory",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_pos_sales,
        trigger=IntervalTrigger(minutes=settings.pos_sync_interval_minutes),
        id="sync_pos_sales",
        replace_existing=True,
    )
    scheduler.add_job(
        fetch_commodity_prices,
        trigger=IntervalTrigger(hours=6),
        id="fetch_commodity_prices",
        replace_existing=True,
    )
    scheduler.add_job(
        run_supply_chain_assessments,
        trigger=IntervalTrigger(hours=24),
        id="run_supply_chain_assessments",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Background scheduler started")
