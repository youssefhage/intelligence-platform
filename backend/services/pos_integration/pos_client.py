"""POS system integration for real-time sales data."""

from datetime import datetime, timedelta

import httpx
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.inventory import SalesRecord
from backend.models.product import Product

logger = structlog.get_logger()


class POSClient:
    """Pulls sales transaction data from the POS system."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.http_client = httpx.AsyncClient(
            base_url=settings.pos_base_url,
            headers={
                "Authorization": f"Bearer {settings.pos_api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def sync_recent_sales(self, hours: int = 1) -> dict:
        """Pull recent sales transactions from POS."""
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        try:
            response = await self.http_client.get(
                "/transactions", params={"since": since}
            )
            response.raise_for_status()
            transactions = response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error("POS sales sync failed", error=str(e))
            return {"synced": 0, "errors": [str(e)]}

        synced = 0
        for txn in transactions:
            # Check if already recorded
            existing = await self.db.execute(
                select(SalesRecord).where(
                    SalesRecord.pos_transaction_id == str(txn["transaction_id"])
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Find matching product
            result = await self.db.execute(
                select(Product).where(
                    Product.erp_product_id == str(txn.get("product_id", ""))
                )
            )
            product = result.scalar_one_or_none()

            record = SalesRecord(
                product_id=product.id if product else 0,
                pos_transaction_id=str(txn["transaction_id"]),
                quantity_sold=txn.get("quantity", 0),
                unit_price_usd=txn.get("unit_price", 0),
                total_usd=txn.get("total", 0),
                customer_type=txn.get("customer_type"),
                channel=txn.get("channel", "pos"),
                sold_at=datetime.fromisoformat(txn["timestamp"]),
            )
            self.db.add(record)
            synced += 1

        await self.db.commit()
        logger.info("POS sales sync completed", synced=synced)
        return {"synced": synced, "errors": []}

    async def get_sales_velocity(
        self, product_id: int, days: int = 30
    ) -> dict:
        """Calculate sales velocity metrics for a product."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(
                func.sum(SalesRecord.quantity_sold),
                func.sum(SalesRecord.total_usd),
                func.count(SalesRecord.id),
            )
            .where(SalesRecord.product_id == product_id)
            .where(SalesRecord.sold_at >= since)
        )
        row = result.one()
        total_qty = row[0] or 0
        total_revenue = row[1] or 0
        txn_count = row[2] or 0

        return {
            "product_id": product_id,
            "period_days": days,
            "total_quantity_sold": float(total_qty),
            "total_revenue_usd": round(float(total_revenue), 2),
            "transaction_count": txn_count,
            "avg_daily_quantity": round(float(total_qty) / max(days, 1), 2),
            "avg_daily_revenue_usd": round(float(total_revenue) / max(days, 1), 2),
        }

    async def get_top_selling_products(
        self, days: int = 7, limit: int = 20
    ) -> list[dict]:
        """Get top selling products by revenue."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(
                SalesRecord.product_id,
                func.sum(SalesRecord.total_usd).label("revenue"),
                func.sum(SalesRecord.quantity_sold).label("quantity"),
            )
            .where(SalesRecord.sold_at >= since)
            .group_by(SalesRecord.product_id)
            .order_by(func.sum(SalesRecord.total_usd).desc())
            .limit(limit)
        )
        rows = result.all()

        top_products = []
        for row in rows:
            prod_result = await self.db.execute(
                select(Product).where(Product.id == row.product_id)
            )
            product = prod_result.scalar_one_or_none()
            top_products.append(
                {
                    "product_id": row.product_id,
                    "product_name": product.name if product else "Unknown",
                    "category": product.category if product else None,
                    "revenue_usd": round(float(row.revenue), 2),
                    "quantity_sold": float(row.quantity),
                    "margin_percent": product.margin_percent if product else None,
                }
            )

        return top_products

    async def close(self):
        await self.http_client.aclose()
