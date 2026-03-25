"""Morning Brief service — computes the daily intelligence dashboard data."""

import json
from datetime import datetime, timedelta

import numpy as np
import structlog
from redis.asyncio import Redis
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.commodity import Commodity, CommodityPrice
from backend.models.currency import CurrencyRate as CurrencyRateModel

logger = structlog.get_logger()

CACHE_KEY = "morning_brief"
CACHE_TTL = 900  # 15 minutes


class MorningBriefService:
    """Generates the morning brief dashboard data with caching."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.redis = redis

    async def generate(self) -> dict:
        """Generate the complete morning brief. Returns cached if fresh."""
        if self.redis:
            try:
                cached = await self.redis.get(CACHE_KEY)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass  # Redis down, compute fresh

        brief = await self._compute_brief()

        if self.redis:
            try:
                await self.redis.setex(CACHE_KEY, CACHE_TTL, json.dumps(brief, default=str))
            except Exception:
                pass

        return brief

    async def _compute_brief(self) -> dict:
        """Compute all morning brief fields from database."""
        now = datetime.utcnow()

        # Get all active commodities
        result = await self.db.execute(
            select(Commodity).where(Commodity.is_active.is_(True))
        )
        commodities = result.scalars().all()

        commodity_briefs = []
        alert_banner = []
        currencies = []
        shipping = []

        for commodity in commodities:
            brief = await self._compute_commodity_brief(commodity, now)

            # Route to correct section
            if commodity.category == "currency":
                currencies.append(brief)
            elif commodity.category == "shipping":
                shipping.append(brief)
            else:
                commodity_briefs.append(brief)

            # Check alert flags
            if brief.get("alert_flag"):
                alert_banner.append(brief)

        # Also get persisted currency rates for richer currency data
        currency_data = await self._get_currency_trends(now)

        return {
            "generated_at": now.isoformat(),
            "alert_banner": alert_banner,
            "commodities": commodity_briefs,
            "currencies": currency_data if currency_data else currencies,
            "shipping": shipping,
        }

    async def _compute_commodity_brief(self, commodity: Commodity, now: datetime) -> dict:
        """Compute brief data for a single commodity."""
        # Get price history (last 90 days for MA and trend)
        since_90d = now - timedelta(days=90)
        prices_result = await self.db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.commodity_id == commodity.id)
            .where(CommodityPrice.recorded_at >= since_90d)
            .order_by(CommodityPrice.recorded_at.asc())
        )
        prices = prices_result.scalars().all()

        if not prices:
            return self._empty_brief(commodity)

        price_values = [p.price_usd for p in prices]
        current_price = price_values[-1]

        # 7-day change
        week_ago = now - timedelta(days=7)
        week_prices = [p for p in prices if p.recorded_at >= week_ago]
        week_change_pct = self._compute_change_pct(
            week_prices[0].price_usd if week_prices else None, current_price
        )

        # 30-day change
        month_ago = now - timedelta(days=30)
        month_prices = [p for p in prices if p.recorded_at >= month_ago]
        month_change_pct = self._compute_change_pct(
            month_prices[0].price_usd if month_prices else None, current_price
        )

        # 90-day moving average
        ma_90d = np.mean(price_values) if price_values else None

        # 90-day trend (linear regression slope direction)
        trend_90d = self._compute_trend(price_values)

        # BUY/HOLD/WAIT signal
        signal = self._compute_signal(current_price, ma_90d)

        # Sparkline (last 30 data points)
        sparkline = [round(p, 2) for p in price_values[-30:]]

        # Alert flag: ±5% in 7 days or ±10% in 30 days
        alert_flag = (
            (week_change_pct is not None and abs(week_change_pct) >= 5.0)
            or (month_change_pct is not None and abs(month_change_pct) >= 10.0)
        )

        return {
            "commodity_id": commodity.id,
            "commodity_name": commodity.name,
            "category": commodity.category,
            "unit": commodity.unit,
            "current_price_usd": round(current_price, 2),
            "week_change_pct": round(week_change_pct, 2) if week_change_pct is not None else None,
            "month_change_pct": round(month_change_pct, 2) if month_change_pct is not None else None,
            "trend_90d": trend_90d,
            "ma_90d": round(ma_90d, 2) if ma_90d is not None else None,
            "signal": signal,
            "sparkline": sparkline,
            "alert_flag": alert_flag,
            "last_updated": prices[-1].recorded_at.isoformat(),
        }

    def _empty_brief(self, commodity: Commodity) -> dict:
        return {
            "commodity_id": commodity.id,
            "commodity_name": commodity.name,
            "category": commodity.category,
            "unit": commodity.unit,
            "current_price_usd": None,
            "week_change_pct": None,
            "month_change_pct": None,
            "trend_90d": "flat",
            "ma_90d": None,
            "signal": "HOLD",
            "sparkline": [],
            "alert_flag": False,
            "last_updated": None,
        }

    def _compute_change_pct(self, old_price: float | None, new_price: float) -> float | None:
        if old_price is None or old_price <= 0:
            return None
        return ((new_price - old_price) / old_price) * 100

    def _compute_trend(self, prices: list[float]) -> str:
        """Compute trend direction using linear regression slope."""
        if len(prices) < 5:
            return "flat"
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        mean_price = np.mean(prices)
        if mean_price == 0:
            return "flat"
        # Normalize slope as % of mean per data point
        normalized_slope = (slope / mean_price) * 100
        if normalized_slope > 0.05:
            return "up"
        elif normalized_slope < -0.05:
            return "down"
        return "flat"

    def _compute_signal(self, current: float, ma_90d: float | None) -> str:
        """BUY/HOLD/WAIT based on price vs 90-day MA."""
        if ma_90d is None or ma_90d <= 0:
            return "HOLD"
        deviation_pct = ((current - ma_90d) / ma_90d) * 100
        if deviation_pct < -5:
            return "BUY"
        elif deviation_pct > 5:
            return "WAIT"
        return "HOLD"

    async def _get_currency_trends(self, now: datetime) -> list[dict]:
        """Get currency pair trends from persisted CurrencyRate data."""
        pairs = ["USD/TRY", "USD/EGP", "USD/CNY", "USD/LBP"]
        results = []

        for pair in pairs:
            # Get latest rate
            latest_result = await self.db.execute(
                select(CurrencyRateModel)
                .where(CurrencyRateModel.pair == pair)
                .order_by(CurrencyRateModel.recorded_at.desc())
                .limit(1)
            )
            latest = latest_result.scalar_one_or_none()
            if not latest:
                continue

            # Get rate from 1 day ago
            day_ago = now - timedelta(days=1)
            day_result = await self.db.execute(
                select(CurrencyRateModel)
                .where(CurrencyRateModel.pair == pair)
                .where(CurrencyRateModel.recorded_at <= day_ago)
                .order_by(CurrencyRateModel.recorded_at.desc())
                .limit(1)
            )
            day_rate = day_result.scalar_one_or_none()

            # Get rate from 7 days ago
            week_ago = now - timedelta(days=7)
            week_result = await self.db.execute(
                select(CurrencyRateModel)
                .where(CurrencyRateModel.pair == pair)
                .where(CurrencyRateModel.recorded_at <= week_ago)
                .order_by(CurrencyRateModel.recorded_at.desc())
                .limit(1)
            )
            week_rate = week_result.scalar_one_or_none()

            day_change = self._compute_change_pct(
                day_rate.rate if day_rate else None, latest.rate
            )
            week_change = self._compute_change_pct(
                week_rate.rate if week_rate else None, latest.rate
            )

            # Determine trend
            trend = "flat"
            if week_change is not None:
                if week_change > 0.5:
                    trend = "up"
                elif week_change < -0.5:
                    trend = "down"

            results.append({
                "pair": pair,
                "rate": round(latest.rate, 4),
                "day_change_pct": round(day_change, 2) if day_change is not None else None,
                "week_change_pct": round(week_change, 2) if week_change is not None else None,
                "trend": trend,
                "last_updated": latest.recorded_at.isoformat(),
            })

        return results
