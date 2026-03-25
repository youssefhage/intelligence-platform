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
    """Periodically fetch global commodity prices from multiple sources."""
    async with async_session() as db:
        from backend.services.market_data.real_connectors import EnhancedCommodityTracker

        tracker = EnhancedCommodityTracker(db)
        try:
            result = await tracker.fetch_all_prices()
            await tracker.check_price_alerts()
            logger.info("Scheduled multi-source commodity price fetch complete", **result)
        except Exception as e:
            logger.error("Commodity price fetch failed, falling back", error=str(e))
            # Fallback to basic tracker
            basic_tracker = CommodityTracker(db)
            try:
                await basic_tracker.fetch_world_bank_prices()
            finally:
                await basic_tracker.close()
        finally:
            await tracker.close()


async def update_currency_rates():
    """Periodically fetch USD/LBP exchange rates."""
    async with async_session() as db:
        from backend.services.market_data.currency_tracker import CurrencyTracker

        tracker = CurrencyTracker(db)
        try:
            await tracker.fetch_current_rates()
            await tracker.check_rate_movement()
            logger.info("Currency rates updated")
        except Exception as e:
            logger.error("Currency rate update failed", error=str(e))
        finally:
            await tracker.close()


async def fetch_news():
    """Periodically fetch commodity-related news from RSS feeds."""
    async with async_session() as db:
        from backend.services.news.rss_fetcher import RSSFetcher

        fetcher = RSSFetcher(db)
        try:
            result = await fetcher.fetch_and_store()
            logger.info("Scheduled news fetch complete", **result)
        except Exception as e:
            logger.error("News fetch failed", error=str(e))
        finally:
            await fetcher.close()


async def fetch_forex_rates():
    """Periodically fetch multi-currency exchange rates (TRY, EGP, CNY, LBP)."""
    async with async_session() as db:
        from backend.services.market_data.forex_connector import ForexConnector

        connector = ForexConnector(db)
        try:
            rates = await connector.fetch_and_persist()
            logger.info("Forex rates fetched and persisted", pairs=len(rates))
        except Exception as e:
            logger.error("Forex rate fetch failed", error=str(e))
        finally:
            await connector.close()


async def check_port_status():
    """Periodically check Lebanese port operational status."""
    async with async_session() as db:
        from backend.services.market_data.port_tracker import PortTracker

        tracker = PortTracker(db)
        try:
            await tracker.check_port_status()
            logger.info("Port status check complete")
        except Exception as e:
            logger.error("Port status check failed", error=str(e))
        finally:
            await tracker.close()


async def run_margin_analysis():
    """Periodically analyze product margins for erosion."""
    async with async_session() as db:
        from backend.services.ai_engine.margin_analyzer import MarginAnalyzer

        analyzer = MarginAnalyzer(db)
        try:
            result = await analyzer.run_full_analysis()
            logger.info(
                "Margin analysis complete",
                negative=result["negative_margin_count"],
                eroding=result["eroding_margin_count"],
            )
        except Exception as e:
            logger.error("Margin analysis failed", error=str(e))


async def generate_reorder_suggestions():
    """Periodically generate auto-reorder suggestions."""
    async with async_session() as db:
        from backend.services.ai_engine.margin_analyzer import AutoReorderEngine

        engine = AutoReorderEngine(db)
        try:
            suggestions = await engine.generate_reorder_suggestions()
            logger.info("Reorder suggestions generated", count=len(suggestions))
        except Exception as e:
            logger.error("Reorder suggestion generation failed", error=str(e))


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
    scheduler.add_job(
        update_currency_rates,
        trigger=IntervalTrigger(hours=4),
        id="update_currency_rates",
        replace_existing=True,
    )
    scheduler.add_job(
        check_port_status,
        trigger=IntervalTrigger(hours=12),
        id="check_port_status",
        replace_existing=True,
    )
    scheduler.add_job(
        run_margin_analysis,
        trigger=IntervalTrigger(hours=12),
        id="run_margin_analysis",
        replace_existing=True,
    )
    scheduler.add_job(
        generate_reorder_suggestions,
        trigger=IntervalTrigger(hours=8),
        id="generate_reorder_suggestions",
        replace_existing=True,
    )
    scheduler.add_job(
        fetch_forex_rates,
        trigger=IntervalTrigger(hours=4),
        id="fetch_forex_rates",
        replace_existing=True,
    )
    scheduler.add_job(
        fetch_news,
        trigger=IntervalTrigger(hours=2),
        id="fetch_news",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Background scheduler started")
