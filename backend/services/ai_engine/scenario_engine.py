"""What-if scenario modeling engine for business impact analysis."""

import json
from datetime import datetime

import anthropic
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.commodity import Commodity, CommodityPrice
from backend.models.insight import InsightCategory, MarketInsight
from backend.models.inventory import SalesRecord
from backend.models.product import Product

logger = structlog.get_logger()


class ScenarioType:
    COMMODITY_PRICE_SHOCK = "commodity_price_shock"
    CURRENCY_DEVALUATION = "currency_devaluation"
    SUPPLY_DISRUPTION = "supply_disruption"
    DEMAND_SURGE = "demand_surge"
    COMPETITOR_PRICE_CUT = "competitor_price_cut"
    TARIFF_CHANGE = "tariff_change"


class ScenarioEngine:
    """Models business impact of hypothetical market scenarios.

    Enables leadership to ask 'what if' questions like:
    - What if wheat prices increase by 20%?
    - What if our main Turkish supplier is disrupted?
    - What if LBP devalues by another 15%?
    - What if Ramadan demand is 30% higher than expected?
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def run_scenario(
        self,
        scenario_type: str,
        parameters: dict,
    ) -> dict:
        """Execute a what-if scenario analysis."""
        handlers = {
            ScenarioType.COMMODITY_PRICE_SHOCK: self._commodity_shock,
            ScenarioType.CURRENCY_DEVALUATION: self._currency_devaluation,
            ScenarioType.SUPPLY_DISRUPTION: self._supply_disruption,
            ScenarioType.DEMAND_SURGE: self._demand_surge,
            ScenarioType.COMPETITOR_PRICE_CUT: self._competitor_price_cut,
            ScenarioType.TARIFF_CHANGE: self._tariff_change,
        }

        handler = handlers.get(scenario_type)
        if not handler:
            return {"error": f"Unknown scenario type: {scenario_type}"}

        result = await handler(parameters)
        result["scenario_type"] = scenario_type
        result["parameters"] = parameters
        result["modeled_at"] = datetime.utcnow().isoformat()

        # Get AI commentary on the scenario
        if settings.anthropic_api_key:
            result["ai_analysis"] = await self._get_ai_commentary(
                scenario_type, parameters, result
            )

        # Store as insight
        await self._store_scenario_insight(scenario_type, parameters, result)

        return result

    async def _commodity_shock(self, params: dict) -> dict:
        """Model impact of a commodity price increase/decrease."""
        commodity_name = params.get("commodity_name", "")
        price_change_pct = params.get("price_change_pct", 0)

        # Find affected commodity
        comm_result = await self.db.execute(
            select(Commodity).where(Commodity.name.ilike(f"%{commodity_name}%"))
        )
        commodity = comm_result.scalar_one_or_none()

        if not commodity:
            return {"error": f"Commodity not found: {commodity_name}"}

        # Get current price
        price_result = await self.db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.commodity_id == commodity.id)
            .order_by(CommodityPrice.recorded_at.desc())
            .limit(1)
        )
        current_price_row = price_result.scalar_one_or_none()
        current_price = current_price_row.price_usd if current_price_row else 0

        new_price = current_price * (1 + price_change_pct / 100)

        # Find products affected by this commodity
        products_result = await self.db.execute(
            select(Product)
            .where(Product.primary_commodity.ilike(f"%{commodity_name}%"))
            .where(Product.is_active.is_(True))
        )
        affected_products = products_result.scalars().all()

        product_impacts = []
        total_margin_impact = 0
        total_monthly_revenue_affected = 0

        for product in affected_products:
            cost = product.current_cost_usd or 0
            sell = product.current_sell_price_usd or 0

            # Estimate commodity cost as portion of product cost (assume 60-80%)
            commodity_share = 0.7
            cost_increase = cost * commodity_share * (price_change_pct / 100)
            new_cost = cost + cost_increase
            new_margin = ((sell - new_cost) / new_cost * 100) if new_cost > 0 else 0
            old_margin = product.margin_percent or 0

            # Get monthly revenue
            from datetime import timedelta

            since = datetime.utcnow() - timedelta(days=30)
            sales_result = await self.db.execute(
                select(func.sum(SalesRecord.total_usd))
                .where(SalesRecord.product_id == product.id)
                .where(SalesRecord.sold_at >= since)
            )
            monthly_rev = float(sales_result.scalar() or 0)

            margin_change = new_margin - old_margin
            total_margin_impact += margin_change
            total_monthly_revenue_affected += monthly_rev

            product_impacts.append(
                {
                    "product_name": product.name,
                    "product_id": product.id,
                    "current_cost": round(cost, 2),
                    "projected_cost": round(new_cost, 2),
                    "sell_price": round(sell, 2),
                    "current_margin_pct": round(old_margin, 2),
                    "projected_margin_pct": round(new_margin, 2),
                    "margin_change_pct": round(margin_change, 2),
                    "monthly_revenue": round(monthly_rev, 2),
                    "price_adjustment_needed": round(
                        max(0, new_cost * 1.12 - sell), 2
                    ),
                }
            )

        return {
            "commodity": commodity.name,
            "current_price_usd": round(current_price, 2),
            "projected_price_usd": round(new_price, 2),
            "price_change_pct": price_change_pct,
            "affected_products_count": len(product_impacts),
            "total_monthly_revenue_affected": round(
                total_monthly_revenue_affected, 2
            ),
            "avg_margin_impact_pct": round(
                total_margin_impact / max(len(product_impacts), 1), 2
            ),
            "product_impacts": product_impacts,
        }

    async def _currency_devaluation(self, params: dict) -> dict:
        """Model impact of LBP devaluation on operations."""
        devaluation_pct = params.get("devaluation_pct", 0)
        current_rate = settings.lbp_exchange_rate
        new_rate = current_rate * (1 + devaluation_pct / 100)

        # All USD-denominated costs effectively increase for LBP-earning businesses
        # But FMCG wholesale in Lebanon largely transacts in USD
        products_result = await self.db.execute(
            select(Product).where(Product.is_active.is_(True))
        )
        products = products_result.scalars().all()

        total_inventory_value_usd = sum(
            p.current_cost_usd or 0 for p in products
        )

        return {
            "current_usd_lbp_rate": current_rate,
            "projected_usd_lbp_rate": round(new_rate, 0),
            "devaluation_pct": devaluation_pct,
            "impact_summary": {
                "total_products": len(products),
                "inventory_value_usd": round(total_inventory_value_usd, 2),
                "inventory_value_lbp_current": round(
                    total_inventory_value_usd * current_rate, 0
                ),
                "inventory_value_lbp_projected": round(
                    total_inventory_value_usd * new_rate, 0
                ),
                "lbp_cost_increase_pct": round(devaluation_pct, 2),
            },
            "recommendations": [
                "Accelerate conversion of LBP receivables to USD",
                "Negotiate shorter payment terms with customers paying in LBP",
                "Increase LBP-denominated prices to match new exchange rate",
                "Consider prepaying USD-denominated supplier invoices at current rate",
            ],
        }

    async def _supply_disruption(self, params: dict) -> dict:
        """Model impact of a supply source being disrupted."""
        from backend.models.supplier import Supplier

        supplier_name = params.get("supplier_name", "")
        disruption_duration_days = params.get("duration_days", 30)

        sup_result = await self.db.execute(
            select(Supplier).where(Supplier.name.ilike(f"%{supplier_name}%"))
        )
        supplier = sup_result.scalar_one_or_none()

        if not supplier:
            return {"error": f"Supplier not found: {supplier_name}"}

        commodities = (
            json.loads(supplier.commodities_supplied)
            if supplier.commodities_supplied
            else []
        )

        # Find products from this supplier
        products_result = await self.db.execute(
            select(Product)
            .where(Product.supplier_name.ilike(f"%{supplier_name}%"))
            .where(Product.is_active.is_(True))
        )
        affected_products = products_result.scalars().all()

        # Estimate supply gap
        from datetime import timedelta

        total_daily_demand = 0
        product_details = []
        for product in affected_products:
            since = datetime.utcnow() - timedelta(days=30)
            sales_result = await self.db.execute(
                select(func.sum(SalesRecord.quantity_sold))
                .where(SalesRecord.product_id == product.id)
                .where(SalesRecord.sold_at >= since)
            )
            monthly_sales = float(sales_result.scalar() or 0)
            daily_demand = monthly_sales / 30
            total_daily_demand += daily_demand

            product_details.append(
                {
                    "product_name": product.name,
                    "daily_demand": round(daily_demand, 1),
                    "supply_gap_units": round(
                        daily_demand * disruption_duration_days, 0
                    ),
                }
            )

        # Find alternative suppliers
        from backend.services.supply_chain.risk_analyzer import (
            SupplyChainRiskAnalyzer,
        )

        analyzer = SupplyChainRiskAnalyzer(self.db)
        alternatives = {}
        for comm in commodities:
            alts = await analyzer.find_alternative_suppliers(
                comm, exclude_countries=[supplier.country]
            )
            if alts:
                alternatives[comm] = alts[:3]

        return {
            "supplier": supplier.name,
            "country": supplier.country,
            "disruption_duration_days": disruption_duration_days,
            "commodities_affected": commodities,
            "affected_products_count": len(affected_products),
            "total_daily_demand_at_risk": round(total_daily_demand, 1),
            "total_supply_gap_units": round(
                total_daily_demand * disruption_duration_days, 0
            ),
            "product_details": product_details,
            "alternative_suppliers": alternatives,
            "recommendations": [
                f"Contact alternative suppliers immediately for {', '.join(commodities)}",
                f"Increase safety stock for {len(affected_products)} affected products",
                f"Review inventory levels to determine runway during {disruption_duration_days}-day disruption",
            ],
        }

    async def _demand_surge(self, params: dict) -> dict:
        """Model impact of unexpected demand increase."""
        surge_pct = params.get("surge_pct", 0)
        category = params.get("category", None)
        duration_days = params.get("duration_days", 14)

        query = select(Product).where(Product.is_active.is_(True))
        if category:
            query = query.where(Product.category.ilike(f"%{category}%"))

        products_result = await self.db.execute(query)
        products = products_result.scalars().all()

        from datetime import timedelta
        from backend.models.inventory import InventorySnapshot

        impacts = []
        stockout_risk = []

        for product in products:
            since = datetime.utcnow() - timedelta(days=30)
            sales_result = await self.db.execute(
                select(func.sum(SalesRecord.quantity_sold))
                .where(SalesRecord.product_id == product.id)
                .where(SalesRecord.sold_at >= since)
            )
            monthly_sales = float(sales_result.scalar() or 0)
            daily_demand = monthly_sales / 30
            surge_daily_demand = daily_demand * (1 + surge_pct / 100)
            additional_demand = (surge_daily_demand - daily_demand) * duration_days

            # Check current stock
            inv_result = await self.db.execute(
                select(InventorySnapshot)
                .where(InventorySnapshot.product_id == product.id)
                .order_by(InventorySnapshot.snapshot_at.desc())
                .limit(1)
            )
            inventory = inv_result.scalar_one_or_none()
            current_stock = inventory.quantity_on_hand if inventory else 0
            days_of_stock_at_surge = (
                current_stock / surge_daily_demand if surge_daily_demand > 0 else 999
            )

            will_stockout = days_of_stock_at_surge < duration_days

            impact = {
                "product_name": product.name,
                "current_daily_demand": round(daily_demand, 1),
                "surge_daily_demand": round(surge_daily_demand, 1),
                "additional_units_needed": round(additional_demand, 0),
                "current_stock": round(current_stock, 0),
                "days_of_stock_at_surge": round(days_of_stock_at_surge, 1),
                "stockout_risk": will_stockout,
            }
            impacts.append(impact)
            if will_stockout:
                stockout_risk.append(impact)

        return {
            "surge_pct": surge_pct,
            "category": category or "all",
            "duration_days": duration_days,
            "products_analyzed": len(impacts),
            "stockout_risk_count": len(stockout_risk),
            "stockout_risk_products": stockout_risk,
            "total_additional_units": round(
                sum(i["additional_units_needed"] for i in impacts), 0
            ),
            "recommendations": [
                f"{len(stockout_risk)} products at stockout risk — place emergency orders",
                f"Total additional inventory needed: {sum(i['additional_units_needed'] for i in impacts):.0f} units",
                "Contact suppliers for expedited shipping where available",
            ],
        }

    async def _competitor_price_cut(self, params: dict) -> dict:
        """Model impact of a competitor cutting prices."""
        competitor_name = params.get("competitor_name", "")
        price_cut_pct = params.get("price_cut_pct", 0)
        category = params.get("category", None)

        query = select(Product).where(Product.is_active.is_(True))
        if category:
            query = query.where(Product.category.ilike(f"%{category}%"))

        products_result = await self.db.execute(query)
        products = products_result.scalars().all()

        impacts = []
        for product in products:
            sell = product.current_sell_price_usd or 0
            cost = product.current_cost_usd or 0
            margin = product.margin_percent or 0

            # If we match the competitor's cut
            new_sell = sell * (1 - price_cut_pct / 100)
            new_margin = ((new_sell - cost) / cost * 100) if cost > 0 else 0

            impacts.append(
                {
                    "product_name": product.name,
                    "current_sell": round(sell, 2),
                    "if_matched_sell": round(new_sell, 2),
                    "current_margin_pct": round(margin, 2),
                    "if_matched_margin_pct": round(new_margin, 2),
                    "margin_loss_pct": round(margin - new_margin, 2),
                    "can_match": new_margin >= 3,
                }
            )

        can_match = [i for i in impacts if i["can_match"]]
        cannot_match = [i for i in impacts if not i["can_match"]]

        return {
            "competitor": competitor_name,
            "price_cut_pct": price_cut_pct,
            "category": category or "all",
            "products_analyzed": len(impacts),
            "can_match_count": len(can_match),
            "cannot_match_count": len(cannot_match),
            "cannot_match_products": cannot_match,
            "avg_margin_if_matched": round(
                sum(i["if_matched_margin_pct"] for i in impacts) / max(len(impacts), 1),
                2,
            ),
            "recommendations": [
                f"{len(can_match)} products can absorb a {price_cut_pct}% cut while maintaining 3%+ margin",
                f"{len(cannot_match)} products cannot match — focus on service differentiation",
                "Consider selective matching on high-volume products only",
            ],
        }

    async def _tariff_change(self, params: dict) -> dict:
        """Model impact of tariff/duty changes on imports."""
        commodity_name = params.get("commodity_name", "")
        tariff_change_pct = params.get("tariff_change_pct", 0)

        comm_result = await self.db.execute(
            select(Commodity).where(Commodity.name.ilike(f"%{commodity_name}%"))
        )
        commodity = comm_result.scalar_one_or_none()

        products_result = await self.db.execute(
            select(Product)
            .where(Product.primary_commodity.ilike(f"%{commodity_name}%"))
            .where(Product.is_active.is_(True))
        )
        products = products_result.scalars().all()

        impacts = []
        for product in products:
            cost = product.current_cost_usd or 0
            tariff_impact = cost * (tariff_change_pct / 100)
            new_cost = cost + tariff_impact
            sell = product.current_sell_price_usd or 0
            new_margin = ((sell - new_cost) / new_cost * 100) if new_cost > 0 else 0

            impacts.append(
                {
                    "product_name": product.name,
                    "current_cost": round(cost, 2),
                    "tariff_impact": round(tariff_impact, 2),
                    "new_cost": round(new_cost, 2),
                    "current_margin_pct": round(product.margin_percent or 0, 2),
                    "new_margin_pct": round(new_margin, 2),
                }
            )

        return {
            "commodity": commodity_name,
            "tariff_change_pct": tariff_change_pct,
            "products_affected": len(impacts),
            "avg_cost_increase_pct": tariff_change_pct,
            "product_impacts": impacts,
            "recommendations": [
                "Evaluate sourcing from countries with preferential trade agreements",
                "Consider bonded warehouse strategies to defer duty payments",
                f"Pass through {tariff_change_pct}% cost increase to maintain margins",
            ],
        }

    async def _get_ai_commentary(
        self, scenario_type: str, params: dict, results: dict
    ) -> str:
        """Get AI-generated strategic commentary on the scenario results."""
        try:
            # Prepare a summary (avoid sending too much data)
            summary_data = {k: v for k, v in results.items() if k != "product_impacts"}
            if "product_impacts" in results:
                summary_data["affected_products_sample"] = results["product_impacts"][
                    :5
                ]

            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                system=(
                    "You are a strategic advisor for a Lebanese FMCG wholesale business. "
                    "Provide concise, actionable commentary on the scenario analysis results. "
                    "Focus on immediate actions and strategic implications."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Scenario: {scenario_type}\n"
                            f"Parameters: {json.dumps(params)}\n"
                            f"Results: {json.dumps(summary_data, default=str)}\n\n"
                            "Provide 2-3 paragraphs of strategic commentary."
                        ),
                    }
                ],
            )
            return response.content[0].text
        except Exception as e:
            logger.warning("AI scenario commentary failed", error=str(e))
            return ""

    async def _store_scenario_insight(
        self, scenario_type: str, params: dict, results: dict
    ):
        """Store scenario results as a market insight."""
        insight = MarketInsight(
            category=InsightCategory.RISK,
            title=f"Scenario Analysis: {scenario_type.replace('_', ' ').title()}",
            summary=json.dumps(params),
            detailed_analysis=json.dumps(results, default=str),
            data_sources=json.dumps(["scenario_engine"]),
            recommended_actions=json.dumps(
                results.get("recommendations", [])
            ),
            confidence_score=0.6,
            generated_by="scenario_engine",
            created_at=datetime.utcnow(),
        )
        self.db.add(insight)
        await self.db.commit()
