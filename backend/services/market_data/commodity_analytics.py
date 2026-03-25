"""Extended commodity analytics — MA overlays, volatility, correlations, AI summaries."""

import json
from datetime import datetime, timedelta

import numpy as np
import structlog
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.commodity import Commodity, CommodityPrice

logger = structlog.get_logger()

RANGE_DAYS = {"6M": 180, "1Y": 365, "3Y": 1095, "5Y": 1825}


class CommodityAnalytics:
    """Extended analytics for the commodity detail view."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.redis = redis

    async def compute_detail(self, commodity_id: int, range_str: str = "1Y") -> dict:
        """Compute full detail view data for a commodity."""
        days = RANGE_DAYS.get(range_str, 365)
        commodity = await self.db.get(Commodity, commodity_id)
        if not commodity:
            return {"error": "Commodity not found"}

        since = datetime.utcnow() - timedelta(days=days)
        prices_result = await self.db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.commodity_id == commodity_id)
            .where(CommodityPrice.recorded_at >= since)
            .order_by(CommodityPrice.recorded_at.asc())
        )
        prices = prices_result.scalars().all()

        if not prices:
            return {
                "commodity_id": commodity_id,
                "commodity_name": commodity.name,
                "category": commodity.category.value,
                "price_history": [],
                "ma_30": [],
                "ma_90": [],
                "volatility_current": None,
                "volatility_level": "low",
                "price_context": {},
                "correlations": [],
            }

        values = np.array([p.price_usd for p in prices])
        dates = [p.recorded_at.isoformat() for p in prices]

        # Moving averages
        ma_30 = self._rolling_mean(values, 30)
        ma_90 = self._rolling_mean(values, 90)

        # Volatility (rolling 90-day stdev)
        vol_90 = self._rolling_std(values, 90)
        current_vol = vol_90[-1] if len(vol_90) > 0 and vol_90[-1] is not None else None
        vol_level = self._classify_volatility(current_vol, values)

        # Price context
        current_price = float(values[-1])
        price_context = self._compute_price_context(values, current_price, days)

        # Correlations
        correlations = await self._compute_correlations(commodity_id, days)

        # Build price history with MA overlays
        price_history = []
        for i, p in enumerate(prices):
            entry = {
                "date": dates[i],
                "price_usd": round(p.price_usd, 2),
                "ma_30": round(ma_30[i], 2) if ma_30[i] is not None else None,
                "ma_90": round(ma_90[i], 2) if ma_90[i] is not None else None,
            }
            price_history.append(entry)

        return {
            "commodity_id": commodity_id,
            "commodity_name": commodity.name,
            "category": commodity.category.value,
            "price_history": price_history,
            "volatility_current": round(current_vol, 2) if current_vol is not None else None,
            "volatility_level": vol_level,
            "price_context": price_context,
            "correlations": correlations,
        }

    async def generate_ai_summary(self, commodity_id: int) -> dict:
        """Generate an AI market summary for a commodity using Claude."""
        # Check Redis cache first (6 hour TTL)
        cache_key = f"ai_summary:{commodity_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        commodity = await self.db.get(Commodity, commodity_id)
        if not commodity:
            return {"error": "Commodity not found"}

        # Get recent data for context
        now = datetime.utcnow()
        since = now - timedelta(days=90)
        prices_result = await self.db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.commodity_id == commodity_id)
            .where(CommodityPrice.recorded_at >= since)
            .order_by(CommodityPrice.recorded_at.asc())
        )
        prices = prices_result.scalars().all()
        if not prices:
            return {"summary": "Insufficient price data for analysis.", "commodity_name": commodity.name}

        values = [p.price_usd for p in prices]
        current = values[-1]
        avg_90d = np.mean(values)
        change_30d = ((current - values[-30]) / values[-30] * 100) if len(values) >= 30 else None
        change_7d = ((current - values[-7]) / values[-7] * 100) if len(values) >= 7 else None

        # Build prompt
        context = (
            f"Commodity: {commodity.name} ({commodity.category.value})\n"
            f"Current price: ${current:.2f}/{commodity.unit}\n"
            f"90-day average: ${avg_90d:.2f}\n"
            f"vs 90d avg: {((current - avg_90d) / avg_90d * 100):+.1f}%\n"
        )
        if change_30d is not None:
            context += f"30-day change: {change_30d:+.1f}%\n"
        if change_7d is not None:
            context += f"7-day change: {change_7d:+.1f}%\n"
        context += f"Origin countries: {commodity.origin_countries}\n"

        try:
            from backend.services.ai_engine.ai_client import get_sync_client

            client = get_sync_client()
            response = client.chat.completions.create(
                model=settings.ai_model,
                max_tokens=300,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a commodity market analyst for a Lebanese FMCG wholesale importer.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Based on the following data, write a 3-4 sentence actionable market summary. "
                            f"Focus on whether this is a good time to buy, what's driving prices, and any risks. "
                            f"Be concise and practical.\n\n{context}"
                        ),
                    },
                ],
            )
            summary_text = response.choices[0].message.content
        except Exception as e:
            logger.warning("AI summary generation failed", error=str(e))
            summary_text = (
                f"{commodity.name} is currently at ${current:.2f}/{commodity.unit}, "
                f"which is {((current - avg_90d) / avg_90d * 100):+.1f}% vs the 90-day average."
            )
            if change_30d is not None:
                if change_30d < -5:
                    summary_text += f" Prices have dropped {abs(change_30d):.1f}% over the past month, suggesting a potential buying window."
                elif change_30d > 5:
                    summary_text += f" Prices have risen {change_30d:.1f}% over the past month. Consider waiting for a pullback."

        result = {
            "commodity_id": commodity_id,
            "commodity_name": commodity.name,
            "summary": summary_text,
            "current_price_usd": round(current, 2),
            "vs_90d_avg_pct": round(((current - avg_90d) / avg_90d * 100), 1),
            "generated_at": now.isoformat(),
        }

        # Cache for 6 hours
        if self.redis:
            try:
                await self.redis.setex(cache_key, 21600, json.dumps(result))
            except Exception:
                pass

        return result

    def _rolling_mean(self, values: np.ndarray, window: int) -> list[float | None]:
        """Compute rolling mean, returning None for insufficient data points."""
        result = []
        for i in range(len(values)):
            if i < window - 1:
                result.append(None)
            else:
                result.append(float(np.mean(values[i - window + 1 : i + 1])))
        return result

    def _rolling_std(self, values: np.ndarray, window: int) -> list[float | None]:
        """Compute rolling standard deviation."""
        result = []
        for i in range(len(values)):
            if i < window - 1:
                result.append(None)
            else:
                result.append(float(np.std(values[i - window + 1 : i + 1])))
        return result

    def _classify_volatility(self, current_vol: float | None, values: np.ndarray) -> str:
        """Classify volatility as high/medium/low relative to price level."""
        if current_vol is None or len(values) == 0:
            return "low"
        mean_price = float(np.mean(values))
        if mean_price == 0:
            return "low"
        cv = current_vol / mean_price  # coefficient of variation
        if cv > 0.1:
            return "high"
        elif cv > 0.03:
            return "medium"
        return "low"

    def _compute_price_context(self, values: np.ndarray, current: float, days: int) -> dict:
        """Compute price context — current vs historical averages."""
        context = {}

        # vs 1-year average (or all data if less)
        one_year = values[-365:] if len(values) > 365 else values
        avg_1y = float(np.mean(one_year))
        context["avg_1y"] = round(avg_1y, 2)
        context["vs_1y_avg_pct"] = round(((current - avg_1y) / avg_1y * 100), 1) if avg_1y > 0 else 0

        # vs 3-year average
        if days >= 1095 and len(values) > 365:
            three_year = values[-1095:] if len(values) > 1095 else values
            avg_3y = float(np.mean(three_year))
            context["avg_3y"] = round(avg_3y, 2)
            context["vs_3y_avg_pct"] = round(((current - avg_3y) / avg_3y * 100), 1) if avg_3y > 0 else 0

        # Price percentile (where current price falls in historical distribution)
        percentile = float(np.sum(values <= current) / len(values) * 100)
        context["percentile"] = round(percentile, 0)

        return context

    async def _compute_correlations(self, commodity_id: int, days: int) -> list[dict]:
        """Compute Pearson correlations with other commodities."""
        since = datetime.utcnow() - timedelta(days=days)

        # Get target commodity daily returns
        target_prices = await self._get_daily_prices(commodity_id, since)
        if len(target_prices) < 30:
            return []

        target_returns = np.diff(target_prices) / target_prices[:-1]

        # Get all other commodities
        result = await self.db.execute(
            select(Commodity)
            .where(Commodity.is_active.is_(True))
            .where(Commodity.id != commodity_id)
            .where(Commodity.category.notin_(["currency", "shipping"]))
        )
        other_commodities = result.scalars().all()

        correlations = []
        for other in other_commodities:
            other_prices = await self._get_daily_prices(other.id, since)
            if len(other_prices) < 30:
                continue

            other_returns = np.diff(other_prices) / other_prices[:-1]

            # Align lengths
            min_len = min(len(target_returns), len(other_returns))
            if min_len < 20:
                continue

            corr = float(np.corrcoef(target_returns[:min_len], other_returns[:min_len])[0, 1])
            if not np.isnan(corr):
                correlations.append({
                    "commodity_id": other.id,
                    "commodity_name": other.name,
                    "correlation": round(corr, 2),
                    "strength": "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak",
                })

        # Sort by absolute correlation, return top 5
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return correlations[:5]

    async def _get_daily_prices(self, commodity_id: int, since: datetime) -> np.ndarray:
        """Get daily price values as a numpy array."""
        result = await self.db.execute(
            select(CommodityPrice.price_usd)
            .where(CommodityPrice.commodity_id == commodity_id)
            .where(CommodityPrice.recorded_at >= since)
            .order_by(CommodityPrice.recorded_at.asc())
        )
        values = [row[0] for row in result.fetchall()]
        return np.array(values) if values else np.array([])
