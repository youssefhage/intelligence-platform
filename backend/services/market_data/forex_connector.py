"""Multi-currency forex connector for sourcing country exchange rates."""

from datetime import datetime

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.currency import CurrencyRate as CurrencyRateModel

logger = structlog.get_logger()

# Currency pairs critical for FMCG import sourcing
TRACKED_CURRENCIES = {
    "TRY": "USD/TRY",   # Turkey - grains, oils
    "EGP": "USD/EGP",   # Egypt - regional sourcing
    "CNY": "USD/CNY",   # China - packaging, household
    "LBP": "USD/LBP",   # Lebanon - local operations
}

# Symbols that map to forex pairs
FOREX_SYMBOL_MAP = {
    "USD_TRY": "TRY",
    "USD_EGP": "EGP",
    "USD_CNY": "CNY",
    "USD_LBP": "LBP",
}


class ForexConnector:
    """Fetches exchange rates for sourcing country currencies.

    Uses exchangerate-api.com (free, no API key needed, 1500 req/month).
    Returns all tracked pairs in a single API call.
    """

    API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

    def __init__(self, db: AsyncSession | None = None):
        self.client = httpx.AsyncClient(timeout=15.0)
        self.db = db

    async def fetch_rates(self) -> dict[str, float]:
        """Fetch current exchange rates for all tracked currencies.

        Returns:
            Dict mapping pair name (e.g., 'USD/TRY') to rate value
        """
        try:
            response = await self.client.get(self.API_URL)
            response.raise_for_status()
            data = response.json()
            rates = data.get("rates", {})

            result = {}
            for code, pair_name in TRACKED_CURRENCIES.items():
                if code in rates:
                    result[pair_name] = rates[code]

            logger.info("Forex rates fetched", pairs=len(result))
            return result
        except Exception as e:
            logger.warning("Forex rate fetch failed", error=str(e))
            return {}

    async def fetch_and_persist(self) -> dict[str, float]:
        """Fetch rates and persist to database for historical tracking."""
        rates = await self.fetch_rates()

        if self.db and rates:
            now = datetime.utcnow()
            for pair_name, rate in rates.items():
                record = CurrencyRateModel(
                    pair=pair_name,
                    rate=rate,
                    source="exchangerate_api",
                    recorded_at=now,
                )
                self.db.add(record)
            await self.db.commit()
            logger.info("Forex rates persisted", count=len(rates))

        return rates

    async def get_rate_for_symbol(self, symbol: str) -> float | None:
        """Get the current rate for a commodity symbol like USD_TRY.

        This is used to record currency-type commodities as price records.
        """
        currency_code = FOREX_SYMBOL_MAP.get(symbol)
        if not currency_code:
            return None

        rates = await self.fetch_rates()
        pair_name = TRACKED_CURRENCIES.get(currency_code)
        if pair_name:
            return rates.get(pair_name)
        return None

    async def close(self):
        await self.client.aclose()
