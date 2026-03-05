"""Webhook handlers for real-time ERP/POS event processing."""

import json
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.alert import Alert, AlertSeverity, AlertType
from backend.models.inventory import InventorySnapshot, SalesRecord
from backend.models.product import Product, ProductPriceHistory

logger = structlog.get_logger()


class WebhookEventType:
    # ERP events
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_CREATED = "product.created"
    INVENTORY_CHANGED = "inventory.changed"
    PURCHASE_ORDER_CREATED = "purchase_order.created"
    PURCHASE_ORDER_RECEIVED = "purchase_order.received"
    COST_PRICE_CHANGED = "cost_price.changed"

    # POS events
    SALE_COMPLETED = "sale.completed"
    REFUND_PROCESSED = "refund.processed"
    DAILY_CLOSE = "daily.close"


class ERPWebhookHandler:
    """Processes real-time webhook events from the ERP system."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_event(self, event_type: str, payload: dict) -> dict:
        """Route and process an incoming ERP webhook event."""
        handlers = {
            WebhookEventType.PRODUCT_UPDATED: self._handle_product_update,
            WebhookEventType.PRODUCT_CREATED: self._handle_product_create,
            WebhookEventType.INVENTORY_CHANGED: self._handle_inventory_change,
            WebhookEventType.COST_PRICE_CHANGED: self._handle_cost_change,
            WebhookEventType.PURCHASE_ORDER_RECEIVED: self._handle_po_received,
        }

        handler = handlers.get(event_type)
        if not handler:
            logger.warning("Unknown ERP webhook event", event_type=event_type)
            return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}

        try:
            result = await handler(payload)
            logger.info("ERP webhook processed", event_type=event_type, result=result)
            return {"status": "processed", "event_type": event_type, **result}
        except Exception as e:
            logger.error("ERP webhook handler failed", event_type=event_type, error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_product_update(self, payload: dict) -> dict:
        """Handle product data updates from ERP."""
        erp_id = str(payload["product_id"])
        result = await self.db.execute(
            select(Product).where(Product.erp_product_id == erp_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            return {"action": "skipped", "reason": "product not found"}

        updated_fields = []
        for field in ("name", "sku", "category", "brand", "unit"):
            if field in payload and getattr(product, field) != payload[field]:
                setattr(product, field, payload[field])
                updated_fields.append(field)

        if "sell_price" in payload:
            product.current_sell_price_usd = payload["sell_price"]
            updated_fields.append("sell_price")

        await self.db.commit()
        return {"action": "updated", "fields": updated_fields}

    async def _handle_product_create(self, payload: dict) -> dict:
        """Handle new product creation from ERP."""
        erp_id = str(payload["product_id"])

        # Check if already exists
        existing = await self.db.execute(
            select(Product).where(Product.erp_product_id == erp_id)
        )
        if existing.scalar_one_or_none():
            return {"action": "skipped", "reason": "already exists"}

        cost = payload.get("cost_price", 0)
        sell = payload.get("sell_price", 0)
        margin = ((sell - cost) / cost * 100) if cost > 0 else 0

        product = Product(
            erp_product_id=erp_id,
            name=payload.get("name", ""),
            sku=payload.get("sku"),
            category=payload.get("category"),
            brand=payload.get("brand"),
            unit=payload.get("unit"),
            current_cost_usd=cost,
            current_sell_price_usd=sell,
            margin_percent=round(margin, 2),
            supplier_name=payload.get("supplier"),
        )
        self.db.add(product)
        await self.db.commit()
        return {"action": "created", "product_name": product.name}

    async def _handle_inventory_change(self, payload: dict) -> dict:
        """Handle real-time inventory level changes."""
        erp_id = str(payload["product_id"])
        result = await self.db.execute(
            select(Product).where(Product.erp_product_id == erp_id)
        )
        product = result.scalar_one_or_none()

        snapshot = InventorySnapshot(
            product_id=product.id if product else 0,
            erp_product_id=erp_id,
            quantity_on_hand=payload.get("qty_on_hand", 0),
            quantity_reserved=payload.get("qty_reserved", 0),
            quantity_on_order=payload.get("qty_on_order", 0),
            warehouse_location=payload.get("warehouse"),
            reorder_point=payload.get("reorder_point"),
            days_of_stock=payload.get("days_of_stock"),
            snapshot_at=datetime.utcnow(),
        )
        self.db.add(snapshot)

        # Check for low stock alert
        days_of_stock = payload.get("days_of_stock")
        if days_of_stock is not None and days_of_stock <= 7:
            product_name = product.name if product else f"Product {erp_id}"
            alert = Alert(
                alert_type=AlertType.INVENTORY_LOW,
                severity=(
                    AlertSeverity.CRITICAL if days_of_stock <= 3 else AlertSeverity.WARNING
                ),
                title=f"Low stock: {product_name}",
                message=(
                    f"{product_name} has only {days_of_stock:.1f} days of stock remaining "
                    f"({payload.get('qty_on_hand', 0)} units on hand)."
                ),
                related_entity_type="product",
                related_entity_id=product.id if product else None,
                action_recommended=(
                    f"Place urgent reorder for {product_name}. "
                    f"Current reorder point: {payload.get('reorder_point', 'N/A')}."
                ),
            )
            self.db.add(alert)

        await self.db.commit()
        return {"action": "recorded", "days_of_stock": days_of_stock}

    async def _handle_cost_change(self, payload: dict) -> dict:
        """Handle cost price changes — critical for margin monitoring."""
        erp_id = str(payload["product_id"])
        result = await self.db.execute(
            select(Product).where(Product.erp_product_id == erp_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            return {"action": "skipped", "reason": "product not found"}

        old_cost = product.current_cost_usd or 0
        new_cost = payload.get("new_cost", 0)

        if old_cost > 0:
            cost_change_pct = ((new_cost - old_cost) / old_cost) * 100
        else:
            cost_change_pct = 0

        # Record price history
        margin = (
            ((product.current_sell_price_usd - new_cost) / new_cost * 100)
            if new_cost > 0 and product.current_sell_price_usd
            else 0
        )
        history = ProductPriceHistory(
            product_id=product.id,
            cost_usd=new_cost,
            sell_price_usd=product.current_sell_price_usd,
            margin_percent=round(margin, 2),
            source="erp_webhook",
            recorded_at=datetime.utcnow(),
            notes=f"Cost changed from ${old_cost:.2f} to ${new_cost:.2f} ({cost_change_pct:+.1f}%)",
        )
        self.db.add(history)

        product.current_cost_usd = new_cost
        product.margin_percent = round(margin, 2)

        # Alert if margin is being squeezed
        if margin < 5:
            alert = Alert(
                alert_type=AlertType.MARGIN_EROSION,
                severity=AlertSeverity.CRITICAL if margin < 0 else AlertSeverity.WARNING,
                title=f"Margin alert: {product.name}",
                message=(
                    f"{product.name} margin dropped to {margin:.1f}% after cost increase "
                    f"of {cost_change_pct:+.1f}%. Sell price: ${product.current_sell_price_usd:.2f}, "
                    f"New cost: ${new_cost:.2f}."
                ),
                related_entity_type="product",
                related_entity_id=product.id,
                action_recommended=(
                    f"Increase sell price of {product.name} to maintain margins, "
                    f"or find alternative supplier with lower cost."
                ),
            )
            self.db.add(alert)

        await self.db.commit()
        return {
            "action": "cost_updated",
            "old_cost": old_cost,
            "new_cost": new_cost,
            "new_margin": round(margin, 2),
        }

    async def _handle_po_received(self, payload: dict) -> dict:
        """Handle purchase order receipt — updates inventory and tracks lead times."""
        items_received = payload.get("items", [])
        for item in items_received:
            erp_id = str(item.get("product_id", ""))
            result = await self.db.execute(
                select(Product).where(Product.erp_product_id == erp_id)
            )
            product = result.scalar_one_or_none()
            if not product:
                continue

            snapshot = InventorySnapshot(
                product_id=product.id,
                erp_product_id=erp_id,
                quantity_on_hand=item.get("new_qty_on_hand", 0),
                quantity_reserved=item.get("qty_reserved", 0),
                quantity_on_order=max(
                    0, item.get("qty_on_order", 0) - item.get("qty_received", 0)
                ),
                warehouse_location=item.get("warehouse"),
                snapshot_at=datetime.utcnow(),
            )
            self.db.add(snapshot)

        await self.db.commit()
        return {"action": "po_received", "items_count": len(items_received)}


class POSWebhookHandler:
    """Processes real-time webhook events from the POS system."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_event(self, event_type: str, payload: dict) -> dict:
        """Route and process an incoming POS webhook event."""
        handlers = {
            WebhookEventType.SALE_COMPLETED: self._handle_sale,
            WebhookEventType.REFUND_PROCESSED: self._handle_refund,
            WebhookEventType.DAILY_CLOSE: self._handle_daily_close,
        }

        handler = handlers.get(event_type)
        if not handler:
            logger.warning("Unknown POS webhook event", event_type=event_type)
            return {"status": "ignored"}

        try:
            result = await handler(payload)
            logger.info("POS webhook processed", event_type=event_type)
            return {"status": "processed", **result}
        except Exception as e:
            logger.error("POS webhook handler failed", event_type=event_type, error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_sale(self, payload: dict) -> dict:
        """Record a completed sale transaction."""
        txn_id = str(payload.get("transaction_id", ""))

        # Check for duplicate
        existing = await self.db.execute(
            select(SalesRecord).where(SalesRecord.pos_transaction_id == txn_id)
        )
        if existing.scalar_one_or_none():
            return {"action": "skipped", "reason": "duplicate"}

        items = payload.get("items", [])
        recorded = 0
        for item in items:
            erp_id = str(item.get("product_id", ""))
            result = await self.db.execute(
                select(Product).where(Product.erp_product_id == erp_id)
            )
            product = result.scalar_one_or_none()

            record = SalesRecord(
                product_id=product.id if product else 0,
                pos_transaction_id=txn_id,
                quantity_sold=item.get("quantity", 0),
                unit_price_usd=item.get("unit_price", 0),
                total_usd=item.get("total", 0),
                customer_type=payload.get("customer_type"),
                channel=payload.get("channel", "pos"),
                sold_at=datetime.fromisoformat(
                    payload.get("timestamp", datetime.utcnow().isoformat())
                ),
            )
            self.db.add(record)
            recorded += 1

        await self.db.commit()
        return {"action": "recorded", "items": recorded}

    async def _handle_refund(self, payload: dict) -> dict:
        """Record a refund transaction as a negative sale."""
        items = payload.get("items", [])
        recorded = 0
        for item in items:
            erp_id = str(item.get("product_id", ""))
            result = await self.db.execute(
                select(Product).where(Product.erp_product_id == erp_id)
            )
            product = result.scalar_one_or_none()

            record = SalesRecord(
                product_id=product.id if product else 0,
                pos_transaction_id=str(payload.get("refund_id", "")),
                quantity_sold=-abs(item.get("quantity", 0)),
                unit_price_usd=item.get("unit_price", 0),
                total_usd=-abs(item.get("total", 0)),
                customer_type=payload.get("customer_type"),
                channel="refund",
                sold_at=datetime.utcnow(),
                notes=f"Refund for transaction {payload.get('original_transaction_id', '')}",
            )
            self.db.add(record)
            recorded += 1

        await self.db.commit()
        return {"action": "refund_recorded", "items": recorded}

    async def _handle_daily_close(self, payload: dict) -> dict:
        """Process end-of-day POS summary."""
        return {
            "action": "daily_close_received",
            "total_sales": payload.get("total_sales_usd", 0),
            "transaction_count": payload.get("transaction_count", 0),
        }
