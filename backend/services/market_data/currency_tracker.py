"""USD/LBP exchange rate tracker for the Lebanese parallel market."""

import json
from datetime import datetime, timedelta

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.alert import Alert, AlertSeverity, AlertType

logger = structlog.get_logger()


class CurrencyRate:
    """Represents a single currency rate observation."""

    def __init__(
        self,
        pair: str,
        rate: float,
        source: str,
        recorded_at: datetime | None = None,
    ):
        self.pair = pair
        self.rate = rate
        self.source = source
        self.recorded_at = recorded_at or datetime.utcnow()


class CurrencyTracker:
    """Tracks USD/LBP and other relevant exchange rates.

    Lebanon operates with multiple exchange rates:
    - Official rate (Banque du Liban)
    - Sayrafa platform rate
    - Parallel (black) market rate

    This tracker monitors all available rates and provides the most
    accurate effective rate for business calculations.
    """

    RATE_SOURCES = [
        {
            "name": "exchangerate_api",
            "url": "https://api.exchangerate-api.com/v4/latest/USD",
            "parser": "_parse_exchangerate_api",
        },
        {
            "name": "open_exchange_rates",
            "url": "https://openexchangerates.org/api/latest.json",
            "parser": "_parse_open_exchange_rates",
        },
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = httpx.AsyncClient(timeout=15.0)
        self._rate_history: list[CurrencyRate] = []

    async def fetch_current_rates(self) -> dict:
        """Fetch USD/LBP rates from multiple sources."""
        rates = {}

        for source in self.RATE_SOURCES:
            try:
                response = await self.client.get(source["url"])
                response.raise_for_status()
                data = response.json()
                parser = getattr(self, source["parser"])
                rate = parser(data)
                if rate:
                    rates[source["name"]] = {
                        "rate": rate,
                        "fetched_at": datetime.utcnow().isoformat(),
                    }
                    self._rate_history.append(
                        CurrencyRate("USD/LBP", rate, source["name"])
                    )
            except Exception as e:
                logger.warning(
                    "Currency rate fetch failed",
                    source=source["name"],
                    error=str(e),
                )

        # Always include the configured rate as fallback
        rates["configured"] = {
            "rate": settings.lbp_exchange_rate,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        # Determine effective rate (prefer parallel market, fallback to config)
        effective_rate = self._determine_effective_rate(rates)
        rates["effective"] = {
            "rate": effective_rate,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        logger.info("Currency rates fetched", sources=len(rates) - 1, effective=effective_rate)
        return rates

    def _parse_exchangerate_api(self, data: dict) -> float | None:
        """Parse response from exchangerate-api.com."""
        rates = data.get("rates", {})
        return rates.get("LBP")

    def _parse_open_exchange_rates(self, data: dict) -> float | None:
        """Parse response from openexchangerates.org."""
        rates = data.get("rates", {})
        return rates.get("LBP")

    def _determine_effective_rate(self, rates: dict) -> float:
        """Determine the most accurate effective rate.

        In Lebanon, the parallel market rate is typically the most relevant
        for wholesale FMCG transactions.
        """
        # Use the highest non-official rate as approximation of parallel market
        real_rates = [
            v["rate"]
            for k, v in rates.items()
            if k not in ("configured", "effective") and v.get("rate")
        ]

        if real_rates:
            return max(real_rates)

        return settings.lbp_exchange_rate

    async def check_rate_movement(self, threshold_pct: float = 3.0):
        """Check for significant USD/LBP movements and create alerts."""
        if len(self._rate_history) < 2:
            return

        latest = self._rate_history[-1]
        previous = self._rate_history[-2]

        if previous.rate <= 0:
            return

        change_pct = ((latest.rate - previous.rate) / previous.rate) * 100

        if abs(change_pct) >= threshold_pct:
            direction = "depreciation" if change_pct > 0 else "appreciation"
            alert = Alert(
                alert_type=AlertType.CURRENCY_SHIFT,
                severity=(
                    AlertSeverity.CRITICAL
                    if abs(change_pct) >= 10
                    else AlertSeverity.WARNING
                ),
                title=f"LBP {direction}: {abs(change_pct):.1f}% movement",
                message=(
                    f"USD/LBP rate moved from {previous.rate:,.0f} to "
                    f"{latest.rate:,.0f} ({change_pct:+.1f}%). "
                    f"This affects all USD-denominated import costs."
                ),
                related_entity_type="currency",
                action_recommended=(
                    "Review all USD-priced inventory and consider adjusting sell prices."
                    if change_pct > 0
                    else "Opportunity to lock in favorable exchange rates for upcoming purchases."
                ),
            )
            self.db.add(alert)
            await self.db.commit()

    async def get_rate_summary(self) -> dict:
        """Get a summary of current exchange rate information."""
        rates = await self.fetch_current_rates()
        return {
            "usd_lbp": rates,
            "configured_rate": settings.lbp_exchange_rate,
            "primary_currency": settings.default_currency,
            "secondary_currency": settings.secondary_currency,
            "rate_history_count": len(self._rate_history),
        }

    async def close(self):
        await self.client.aclose()
