"""FRED (Federal Reserve Economic Data) connector for commodity and economic data."""

from datetime import datetime, timedelta

import httpx
import structlog

from backend.core.config import settings

logger = structlog.get_logger()

# FRED series IDs for relevant economic indicators
FRED_SERIES_MAP = {
    # Energy (daily/weekly)
    "BRENT": "DCOILBRENTEU",
    "DIESEL": "GASDESW",
    # Grains & Staples (monthly, IMF via FRED)
    "WHEAT_CBOT": "PWHEAMTUSDM",
    "RICE": "PRICENPQUSDM",
    "SUGAR_RAW": "PSUGAISAUSDM",
    # Oils (monthly, IMF via FRED)
    "PALM_OIL": "PPOILUSDM",
    "SOYBEAN_OIL": "PSOILUSDM",
    "SUNFLOWER_OIL": "PSUNOUSDM",
    "OLIVE_OIL": "POLVOILUSDM",
    # Beverages (monthly, IMF via FRED)
    "COFFEE_ARABICA": "PCOFFOTMUSDM",
    "COCOA": "PCOCOUSDM",
    "TEA": "PTEAUSDM",
    # Metals (monthly, IMF via FRED)
    "TIN": "PTINUSDM",
    # Packaging PPI indices (monthly)
    "HDPE": "WPU072104",
    "PET": "WPU07210603",
    "PP": "WPU072105",
    "PAPER_CARDBOARD": "WPU0911",
}


class FREDConnector:
    """Fetches economic data from the FRED API."""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_key = settings.fred_api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def fetch_series(
        self, series_id: str, months: int = 12
    ) -> list[dict]:
        """Fetch observations for a FRED series.

        Args:
            series_id: FRED series ID (e.g., 'DCOILBRENTEU')
            months: Number of months of history

        Returns:
            List of dicts with 'date', 'value' keys
        """
        if not self.is_configured:
            logger.debug("FRED API key not configured, skipping")
            return []

        start_date = (datetime.utcnow() - timedelta(days=months * 30)).strftime(
            "%Y-%m-%d"
        )

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "sort_order": "desc",
            "limit": months * 31,
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_observations(data)
        except Exception as e:
            logger.warning(
                "FRED series fetch failed", series_id=series_id, error=str(e)
            )
            return []

    def _parse_observations(self, data: dict) -> list[dict]:
        """Parse FRED API response into price records."""
        results = []
        for obs in data.get("observations", []):
            value = obs.get("value")
            date = obs.get("date")
            if value and value != "." and date:
                try:
                    results.append(
                        {
                            "date": date,
                            "value": float(value),
                            "source": "fred",
                        }
                    )
                except (ValueError, TypeError):
                    continue
        return results

    async def fetch_commodity_price(
        self, symbol: str, months: int = 12
    ) -> list[dict]:
        """Fetch price data for a commodity using its benchmark symbol."""
        series_id = FRED_SERIES_MAP.get(symbol)
        if not series_id:
            return []

        observations = await self.fetch_series(series_id, months)
        return [
            {
                "date": obs["date"],
                "value": obs["value"],
                "indicator": symbol,
                "source": "fred",
            }
            for obs in observations
        ]

    async def fetch_all_tracked(self, symbols: list[str]) -> dict[str, list[dict]]:
        """Fetch data for all tracked symbols that have FRED mappings."""
        results = {}
        for symbol in symbols:
            if symbol in FRED_SERIES_MAP:
                prices = await self.fetch_commodity_price(symbol)
                if prices:
                    results[symbol] = prices
        return results

    async def close(self):
        await self.client.aclose()
