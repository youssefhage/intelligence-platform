"""Margin erosion detection and pricing intelligence."""

import json
from datetime import datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.alert import Alert, AlertSeverity, AlertType
from backend.models.insight import InsightCategory, MarketInsight
from backend.models.inventory import SalesRecord
from backend.models.product import Product, ProductPriceHistory

logger = structlog.get_logger()


class MarginAnalyzer:
    """Detects margin erosion and identifies pricing opportunities."""

    # Margin thresholds for wholesale FMCG in Lebanon
    CRITICAL_MARGIN_THRESHOLD = 3.0  # Below this is unsustainable
    WARNING_MARGIN_THRESHOLD = 8.0   # Below this needs attention
    TARGET_MARGIN_MIN = 12.0         # Healthy minimum margin

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_full_analysis(self) -> dict:
        """Run complete margin analysis across all active products."""
        products_result = await self.db.execute(
            select(Product).where(Product.is_active.is_(True))
        )
        products = products_result.scalars().all()

        eroding = []
        negative = []
        healthy = []
        opportunities = []

        for product in products:
            analysis = await self._analyze_product_margin(product)

            if analysis["status"] == "negative":
                negative.append(analysis)
            elif analysis["status"] == "critical":
                eroding.append(analysis)
            elif analysis["status"] == "warning":
                eroding.append(analysis)
            else:
                healthy.append(analysis)

            if analysis.get("opportunity"):
                opportunities.append(analysis)

        # Create alerts for critical items
        for item in negative + [e for e in eroding if e["status"] == "critical"]:
            await self._create_margin_alert(item)

        # Store insight
        if eroding or negative:
            await self._store_margin_insight(eroding, negative, opportunities)

        summary = {
            "total_products_analyzed": len(products),
            "negative_margin_count": len(negative),
            "eroding_margin_count": len(eroding),
            "healthy_count": len(healthy),
            "opportunities_count": len(opportunities),
            "negative_margin_products": negative,
            "eroding_margin_products": eroding[:20],
            "pricing_opportunities": opportunities[:10],
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Margin analysis complete",
            total=len(products),
            negative=len(negative),
            eroding=len(eroding),
        )
        return summary

    async def _analyze_product_margin(self, product: Product) -> dict:
        """Analyze margin health for a single product."""
        current_margin = product.margin_percent or 0
        cost = product.current_cost_usd or 0
        sell = product.current_sell_price_usd or 0

        # Get margin trend (last 30 days of cost history)
        history_result = await self.db.execute(
            select(ProductPriceHistory)
            .where(ProductPriceHistory.product_id == product.id)
            .where(
                ProductPriceHistory.recorded_at
                >= datetime.utcnow() - timedelta(days=30)
            )
            .order_by(ProductPriceHistory.recorded_at.asc())
        )
        history = history_result.scalars().all()

        margin_trend = "stable"
        margin_change_30d = 0.0
        if len(history) >= 2:
            first_margin = history[0].margin_percent or 0
            last_margin = history[-1].margin_percent or 0
            margin_change_30d = last_margin - first_margin
            if margin_change_30d < -3:
                margin_trend = "declining_fast"
            elif margin_change_30d < -1:
                margin_trend = "declining"
            elif margin_change_30d > 3:
                margin_trend = "improving"

        # Get sales velocity to understand impact
        since = datetime.utcnow() - timedelta(days=30)
        sales_result = await self.db.execute(
            select(
                func.sum(SalesRecord.total_usd),
                func.sum(SalesRecord.quantity_sold),
            )
            .where(SalesRecord.product_id == product.id)
            .where(SalesRecord.sold_at >= since)
        )
        sales_row = sales_result.one()
        monthly_revenue = float(sales_row[0] or 0)
        monthly_qty = float(sales_row[1] or 0)

        # Determine status
        if current_margin < 0:
            status = "negative"
        elif current_margin < self.CRITICAL_MARGIN_THRESHOLD:
            status = "critical"
        elif current_margin < self.WARNING_MARGIN_THRESHOLD:
            status = "warning"
        else:
            status = "healthy"

        # Identify pricing opportunity
        opportunity = None
        if current_margin < self.TARGET_MARGIN_MIN and sell > 0 and cost > 0:
            target_sell = cost * (1 + self.TARGET_MARGIN_MIN / 100)
            price_increase_needed = target_sell - sell
            opportunity = {
                "current_sell": round(sell, 2),
                "suggested_sell": round(target_sell, 2),
                "increase_needed": round(price_increase_needed, 2),
                "increase_pct": round((price_increase_needed / sell) * 100, 2),
                "monthly_revenue_impact": round(
                    monthly_qty * price_increase_needed, 2
                ),
            }

        return {
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category,
            "sku": product.sku,
            "current_cost_usd": round(cost, 2),
            "current_sell_usd": round(sell, 2),
            "current_margin_pct": round(current_margin, 2),
            "margin_trend": margin_trend,
            "margin_change_30d": round(margin_change_30d, 2),
            "monthly_revenue_usd": round(monthly_revenue, 2),
            "monthly_quantity": round(monthly_qty, 1),
            "status": status,
            "opportunity": opportunity,
        }

    async def _create_margin_alert(self, analysis: dict):
        """Create alert for margin erosion."""
        is_negative = analysis["current_margin_pct"] < 0
        alert = Alert(
            alert_type=AlertType.MARGIN_EROSION,
            severity=AlertSeverity.CRITICAL if is_negative else AlertSeverity.WARNING,
            title=(
                f"{'Negative' if is_negative else 'Critical'} margin: "
                f"{analysis['product_name']}"
            ),
            message=(
                f"{analysis['product_name']} (SKU: {analysis['sku']}) has a margin of "
                f"{analysis['current_margin_pct']}% (cost: ${analysis['current_cost_usd']}, "
                f"sell: ${analysis['current_sell_usd']}). "
                f"Margin trend: {analysis['margin_trend']} "
                f"({analysis['margin_change_30d']:+.1f}% over 30 days)."
            ),
            related_entity_type="product",
            related_entity_id=analysis["product_id"],
            action_recommended=(
                f"Increase sell price to at least "
                f"${analysis['opportunity']['suggested_sell']:.2f} "
                f"(+{analysis['opportunity']['increase_pct']:.1f}%)"
                if analysis.get("opportunity")
                else "Review cost structure and consider alternative suppliers."
            ),
        )
        self.db.add(alert)
        await self.db.commit()

    async def _store_margin_insight(
        self,
        eroding: list[dict],
        negative: list[dict],
        opportunities: list[dict],
    ):
        """Store margin analysis as a market insight."""
        total_revenue_at_risk = sum(p["monthly_revenue_usd"] for p in negative + eroding)
        total_opportunity = sum(
            p["opportunity"]["monthly_revenue_impact"]
            for p in opportunities
            if p.get("opportunity")
        )

        insight = MarketInsight(
            category=InsightCategory.PRICING,
            title=f"Margin Analysis: {len(negative)} negative, {len(eroding)} eroding",
            summary=(
                f"{len(negative)} products have negative margins and {len(eroding)} are "
                f"below warning threshold. Total monthly revenue at risk: "
                f"${total_revenue_at_risk:,.2f}. Potential monthly revenue uplift from "
                f"price corrections: ${total_opportunity:,.2f}."
            ),
            detailed_analysis=json.dumps(
                {
                    "negative_margin_products": negative[:10],
                    "eroding_products": eroding[:10],
                    "top_opportunities": opportunities[:10],
                    "total_revenue_at_risk": total_revenue_at_risk,
                    "total_opportunity_value": total_opportunity,
                },
            ),
            data_sources=json.dumps(["product_catalog", "price_history", "sales_data"]),
            recommended_actions=json.dumps(
                [
                    f"Immediately adjust pricing on {len(negative)} negative-margin products",
                    f"Review {len(eroding)} products with eroding margins within this week",
                    f"Potential monthly revenue uplift: ${total_opportunity:,.2f}",
                ]
            ),
            confidence_score=0.9,
            generated_by="margin_analyzer",
            created_at=datetime.utcnow(),
        )
        self.db.add(insight)
        await self.db.commit()


class AutoReorderEngine:
    """Generates automatic reorder suggestions based on stock levels and demand."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_reorder_suggestions(self) -> list[dict]:
        """Generate reorder suggestions for products running low on stock."""
        from backend.models.inventory import InventorySnapshot

        # Get latest inventory snapshots
        subquery = (
            select(
                InventorySnapshot.product_id,
                func.max(InventorySnapshot.snapshot_at).label("latest"),
            )
            .group_by(InventorySnapshot.product_id)
            .subquery()
        )

        result = await self.db.execute(
            select(InventorySnapshot)
            .join(
                subquery,
                (InventorySnapshot.product_id == subquery.c.product_id)
                & (InventorySnapshot.snapshot_at == subquery.c.latest),
            )
        )
        snapshots = result.scalars().all()

        suggestions = []
        for snapshot in snapshots:
            if snapshot.days_of_stock is None:
                continue

            # Get product details
            prod_result = await self.db.execute(
                select(Product).where(Product.id == snapshot.product_id)
            )
            product = prod_result.scalar_one_or_none()
            if not product or not product.is_active:
                continue

            # Calculate sales velocity
            since = datetime.utcnow() - timedelta(days=30)
            sales_result = await self.db.execute(
                select(func.sum(SalesRecord.quantity_sold))
                .where(SalesRecord.product_id == product.id)
                .where(SalesRecord.sold_at >= since)
            )
            monthly_sales = float(sales_result.scalar() or 0)
            daily_avg = monthly_sales / 30

            if daily_avg <= 0:
                continue

            # Determine if reorder is needed
            lead_time_days = 14  # Default lead time
            safety_stock_days = 7
            reorder_point = daily_avg * (lead_time_days + safety_stock_days)
            economic_order_qty = daily_avg * 30  # 1 month supply

            needs_reorder = (
                snapshot.days_of_stock <= (lead_time_days + safety_stock_days)
                and snapshot.quantity_on_order < economic_order_qty * 0.5
            )

            if needs_reorder:
                order_qty = max(
                    economic_order_qty - snapshot.quantity_on_order,
                    0,
                )
                if order_qty <= 0:
                    continue

                urgency = "critical" if snapshot.days_of_stock <= 3 else (
                    "urgent" if snapshot.days_of_stock <= 7 else "normal"
                )

                suggestions.append(
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "sku": product.sku,
                        "category": product.category,
                        "supplier": product.supplier_name,
                        "current_stock": snapshot.quantity_on_hand,
                        "days_of_stock": round(snapshot.days_of_stock, 1),
                        "daily_avg_sales": round(daily_avg, 2),
                        "on_order": snapshot.quantity_on_order,
                        "suggested_order_qty": round(order_qty, 0),
                        "estimated_cost_usd": round(
                            order_qty * (product.current_cost_usd or 0), 2
                        ),
                        "urgency": urgency,
                        "reorder_point": round(reorder_point, 0),
                        "lead_time_days": lead_time_days,
                    }
                )

        # Sort by urgency
        urgency_order = {"critical": 0, "urgent": 1, "normal": 2}
        suggestions.sort(key=lambda s: urgency_order.get(s["urgency"], 99))

        # Create alerts for critical items
        for s in suggestions:
            if s["urgency"] == "critical":
                alert = Alert(
                    alert_type=AlertType.INVENTORY_LOW,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Reorder needed: {s['product_name']}",
                    message=(
                        f"{s['product_name']} has only {s['days_of_stock']} days of stock. "
                        f"Suggested order: {s['suggested_order_qty']:.0f} units "
                        f"(est. ${s['estimated_cost_usd']:,.2f})."
                    ),
                    related_entity_type="product",
                    related_entity_id=s["product_id"],
                    action_recommended=(
                        f"Place order for {s['suggested_order_qty']:.0f} units from "
                        f"{s['supplier'] or 'preferred supplier'}."
                    ),
                )
                self.db.add(alert)

        await self.db.commit()

        logger.info(
            "Reorder suggestions generated",
            total=len(suggestions),
            critical=len([s for s in suggestions if s["urgency"] == "critical"]),
        )
        return suggestions
