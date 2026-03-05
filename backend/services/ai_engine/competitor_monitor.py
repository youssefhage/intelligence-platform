"""Competitor price monitoring and market positioning analysis."""

import json
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import Base
from backend.models.insight import InsightCategory, MarketInsight
from backend.models.product import Product

logger = structlog.get_logger()


class CompetitorPrice:
    """Represents a competitor's price observation."""

    def __init__(
        self,
        competitor_name: str,
        product_name: str,
        sku_match: str | None,
        price_usd: float,
        source: str,
        observed_at: datetime | None = None,
        notes: str = "",
    ):
        self.competitor_name = competitor_name
        self.product_name = product_name
        self.sku_match = sku_match
        self.price_usd = price_usd
        self.source = source
        self.observed_at = observed_at or datetime.utcnow()
        self.notes = notes

    def to_dict(self) -> dict:
        return {
            "competitor_name": self.competitor_name,
            "product_name": self.product_name,
            "sku_match": self.sku_match,
            "price_usd": self.price_usd,
            "source": self.source,
            "observed_at": self.observed_at.isoformat(),
            "notes": self.notes,
        }


class CompetitorMonitor:
    """Monitors competitor pricing and market positioning.

    In the Lebanese FMCG wholesale market, competitor intelligence is gathered
    through a combination of manual price surveys, sales rep reports, and
    market data feeds. This service manages that data and provides analysis.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._price_observations: list[CompetitorPrice] = []
        self._competitors: dict[str, dict] = {}

    def register_competitor(
        self,
        name: str,
        location: str = "",
        market_segment: str = "wholesale",
    ):
        """Register a competitor for tracking."""
        self._competitors[name] = {
            "name": name,
            "location": location,
            "market_segment": market_segment,
            "registered_at": datetime.utcnow().isoformat(),
        }

    async def record_price_observation(
        self,
        competitor_name: str,
        product_name: str,
        price_usd: float,
        source: str = "manual_survey",
        sku_match: str | None = None,
        notes: str = "",
    ) -> dict:
        """Record a price observation from a competitor."""
        observation = CompetitorPrice(
            competitor_name=competitor_name,
            product_name=product_name,
            sku_match=sku_match,
            price_usd=price_usd,
            source=source,
            notes=notes,
        )
        self._price_observations.append(observation)

        logger.info(
            "Competitor price recorded",
            competitor=competitor_name,
            product=product_name,
            price=price_usd,
        )
        return observation.to_dict()

    async def record_bulk_prices(self, observations: list[dict]) -> dict:
        """Record multiple competitor price observations at once."""
        recorded = 0
        errors = []
        for obs in observations:
            try:
                await self.record_price_observation(
                    competitor_name=obs["competitor_name"],
                    product_name=obs["product_name"],
                    price_usd=obs["price_usd"],
                    source=obs.get("source", "bulk_import"),
                    sku_match=obs.get("sku_match"),
                    notes=obs.get("notes", ""),
                )
                recorded += 1
            except Exception as e:
                errors.append(str(e))

        return {"recorded": recorded, "errors": errors}

    async def analyze_competitive_position(
        self, product_id: int | None = None
    ) -> dict:
        """Analyze our pricing position relative to competitors."""
        if product_id:
            return await self._analyze_single_product(product_id)

        return await self._analyze_portfolio()

    async def _analyze_single_product(self, product_id: int) -> dict:
        """Compare a specific product's pricing against competitors."""
        prod_result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = prod_result.scalar_one_or_none()
        if not product:
            return {"error": "Product not found"}

        our_price = product.current_sell_price_usd or 0

        # Find matching competitor observations
        matches = [
            obs
            for obs in self._price_observations
            if (
                obs.sku_match == product.sku
                or obs.product_name.lower() in product.name.lower()
                or product.name.lower() in obs.product_name.lower()
            )
        ]

        if not matches:
            return {
                "product_id": product_id,
                "product_name": product.name,
                "our_price_usd": our_price,
                "competitor_data": [],
                "position": "no_data",
                "message": "No competitor price data available for this product.",
            }

        competitor_prices = []
        for obs in matches:
            diff = our_price - obs.price_usd
            diff_pct = (diff / obs.price_usd * 100) if obs.price_usd > 0 else 0
            competitor_prices.append(
                {
                    **obs.to_dict(),
                    "price_diff_usd": round(diff, 2),
                    "price_diff_pct": round(diff_pct, 2),
                    "position": (
                        "cheaper"
                        if diff < 0
                        else "pricier" if diff > 0 else "matched"
                    ),
                }
            )

        avg_competitor_price = sum(m["price_usd"] for m in competitor_prices) / len(
            competitor_prices
        )
        position_vs_avg = (
            ((our_price - avg_competitor_price) / avg_competitor_price * 100)
            if avg_competitor_price > 0
            else 0
        )

        position = (
            "below_market"
            if position_vs_avg < -3
            else "above_market" if position_vs_avg > 3 else "at_market"
        )

        return {
            "product_id": product_id,
            "product_name": product.name,
            "our_price_usd": our_price,
            "avg_competitor_price_usd": round(avg_competitor_price, 2),
            "position_vs_market_pct": round(position_vs_avg, 2),
            "position": position,
            "competitor_count": len(set(m["competitor_name"] for m in competitor_prices)),
            "competitor_prices": competitor_prices,
            "recommendation": self._get_positioning_recommendation(
                position, position_vs_avg, product
            ),
        }

    async def _analyze_portfolio(self) -> dict:
        """Analyze competitive position across all tracked products."""
        products_result = await self.db.execute(
            select(Product).where(Product.is_active.is_(True))
        )
        products = products_result.scalars().all()

        analyses = []
        below_market = 0
        above_market = 0
        at_market = 0

        for product in products:
            analysis = await self._analyze_single_product(product.id)
            if analysis.get("position") == "no_data":
                continue
            analyses.append(analysis)
            if analysis["position"] == "below_market":
                below_market += 1
            elif analysis["position"] == "above_market":
                above_market += 1
            else:
                at_market += 1

        # Store as insight
        if analyses:
            await self._store_competitive_insight(
                analyses, below_market, above_market, at_market
            )

        return {
            "products_analyzed": len(analyses),
            "below_market": below_market,
            "above_market": above_market,
            "at_market": at_market,
            "competitors_tracked": len(self._competitors),
            "total_observations": len(self._price_observations),
            "product_analyses": analyses,
        }

    def _get_positioning_recommendation(
        self, position: str, diff_pct: float, product: Product
    ) -> str:
        margin = product.margin_percent or 0
        if position == "below_market" and margin > 15:
            return (
                f"Opportunity: {product.name} is priced {abs(diff_pct):.1f}% below market "
                f"with a healthy {margin:.1f}% margin. Consider a price increase to capture "
                f"additional margin without losing competitiveness."
            )
        if position == "above_market" and diff_pct > 10:
            return (
                f"Risk: {product.name} is priced {diff_pct:.1f}% above market. "
                f"Consider reducing price or emphasizing value-adds to maintain volume."
            )
        return f"{product.name} is competitively priced relative to the market."

    async def _store_competitive_insight(
        self,
        analyses: list[dict],
        below: int,
        above: int,
        at: int,
    ):
        """Store competitive analysis as market insight."""
        # Identify biggest opportunities (below market with good margin)
        opportunities = [
            a
            for a in analyses
            if a["position"] == "below_market"
            and a.get("position_vs_market_pct", 0) < -5
        ]

        insight = MarketInsight(
            category=InsightCategory.PRICING,
            title="Competitive Position Analysis",
            summary=(
                f"Analyzed {len(analyses)} products: {below} below market, "
                f"{at} at market, {above} above market. "
                f"{len(opportunities)} pricing opportunities identified."
            ),
            detailed_analysis=json.dumps(
                {
                    "summary": {"below": below, "at": at, "above": above},
                    "opportunities": [
                        {
                            "product": a["product_name"],
                            "our_price": a["our_price_usd"],
                            "market_avg": a["avg_competitor_price_usd"],
                            "gap_pct": a["position_vs_market_pct"],
                        }
                        for a in opportunities[:10]
                    ],
                }
            ),
            data_sources=json.dumps(["competitor_survey", "product_catalog"]),
            recommended_actions=json.dumps(
                [a["recommendation"] for a in opportunities[:5]]
            ),
            confidence_score=0.75,
            generated_by="competitor_monitor",
            created_at=datetime.utcnow(),
        )
        self.db.add(insight)
        await self.db.commit()
