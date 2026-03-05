"""ERP system integration client for syncing inventory and product data."""

from datetime import datetime

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.inventory import InventorySnapshot
from backend.models.product import Product, ProductPriceHistory

logger = structlog.get_logger()


class ERPClient:
    """Integrates with the existing ERP system to pull product and inventory data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.http_client = httpx.AsyncClient(
            base_url=settings.erp_base_url,
            headers={
                "Authorization": f"Bearer {settings.erp_api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def sync_products(self) -> dict:
        """Pull latest product catalog from ERP and sync to local database."""
        try:
            response = await self.http_client.get("/products", params={"active": True})
            response.raise_for_status()
            erp_products = response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error("ERP product sync failed", error=str(e))
            return {"synced": 0, "errors": [str(e)]}

        synced = 0
        errors = []

        for erp_product in erp_products:
            try:
                await self._upsert_product(erp_product)
                synced += 1
            except Exception as e:
                errors.append(f"Product {erp_product.get('id')}: {e}")

        await self.db.commit()
        logger.info("ERP product sync completed", synced=synced, errors=len(errors))
        return {"synced": synced, "errors": errors}

    async def _upsert_product(self, erp_data: dict):
        """Insert or update a product from ERP data."""
        erp_id = str(erp_data["id"])
        result = await self.db.execute(
            select(Product).where(Product.erp_product_id == erp_id)
        )
        product = result.scalar_one_or_none()

        cost = erp_data.get("cost_price", 0)
        sell = erp_data.get("sell_price", 0)
        margin = ((sell - cost) / cost * 100) if cost > 0 else 0

        if product:
            # Track price change
            if product.current_cost_usd != cost:
                history = ProductPriceHistory(
                    product_id=product.id,
                    cost_usd=cost,
                    sell_price_usd=sell,
                    margin_percent=round(margin, 2),
                    source="erp_sync",
                    recorded_at=datetime.utcnow(),
                )
                self.db.add(history)

            product.name = erp_data.get("name", product.name)
            product.sku = erp_data.get("sku", product.sku)
            product.category = erp_data.get("category", product.category)
            product.brand = erp_data.get("brand", product.brand)
            product.current_cost_usd = cost
            product.current_sell_price_usd = sell
            product.margin_percent = round(margin, 2)
        else:
            product = Product(
                erp_product_id=erp_id,
                name=erp_data.get("name", ""),
                sku=erp_data.get("sku"),
                category=erp_data.get("category"),
                brand=erp_data.get("brand"),
                unit=erp_data.get("unit"),
                current_cost_usd=cost,
                current_sell_price_usd=sell,
                margin_percent=round(margin, 2),
                supplier_name=erp_data.get("supplier"),
            )
            self.db.add(product)

    async def sync_inventory(self) -> dict:
        """Pull current inventory levels from ERP."""
        try:
            response = await self.http_client.get("/inventory/snapshot")
            response.raise_for_status()
            inventory_data = response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error("ERP inventory sync failed", error=str(e))
            return {"synced": 0, "errors": [str(e)]}

        synced = 0
        now = datetime.utcnow()

        for item in inventory_data:
            erp_id = str(item["product_id"])
            result = await self.db.execute(
                select(Product).where(Product.erp_product_id == erp_id)
            )
            product = result.scalar_one_or_none()

            snapshot = InventorySnapshot(
                product_id=product.id if product else 0,
                erp_product_id=erp_id,
                quantity_on_hand=item.get("qty_on_hand", 0),
                quantity_reserved=item.get("qty_reserved", 0),
                quantity_on_order=item.get("qty_on_order", 0),
                warehouse_location=item.get("warehouse"),
                reorder_point=item.get("reorder_point"),
                days_of_stock=item.get("days_of_stock"),
                snapshot_at=now,
            )
            self.db.add(snapshot)
            synced += 1

        await self.db.commit()
        logger.info("ERP inventory sync completed", synced=synced)
        return {"synced": synced, "errors": []}

    async def get_low_stock_products(self, threshold_days: float = 14) -> list[dict]:
        """Identify products running low on stock."""
        result = await self.db.execute(
            select(InventorySnapshot)
            .where(InventorySnapshot.days_of_stock is not None)
            .where(InventorySnapshot.days_of_stock <= threshold_days)
            .order_by(InventorySnapshot.days_of_stock.asc())
        )
        snapshots = result.scalars().all()

        low_stock = []
        for snap in snapshots:
            prod_result = await self.db.execute(
                select(Product).where(Product.id == snap.product_id)
            )
            product = prod_result.scalar_one_or_none()
            low_stock.append(
                {
                    "product_id": snap.product_id,
                    "product_name": product.name if product else "Unknown",
                    "quantity_on_hand": snap.quantity_on_hand,
                    "days_of_stock": snap.days_of_stock,
                    "reorder_point": snap.reorder_point,
                    "warehouse": snap.warehouse_location,
                }
            )

        return low_stock

    async def close(self):
        await self.http_client.aclose()
