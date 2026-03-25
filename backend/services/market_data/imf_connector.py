"""IMF Primary Commodity Prices connector."""

from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger()

# IMF PCPS (Primary Commodity Price System) indicator codes
IMF_INDICATOR_MAP = {
    "COFFEE_ARABICA": "PCOFFOTM",
    "COFFEE_ROBUSTA": "PCOFFROB",
    "TEA": "PTEA",
    "COCOA": "PCOCO",
    "OLIVE_OIL": "POLVOIL",
    "ALUMINUM": "PALUM",
    "TIN": "PTIN",
    "SUGAR_RAW": "PSUGAISA",
    "PALM_OIL": "PPOIL",
    "SUNFLOWER_OIL": "PSUNO",
    "SOYBEAN_OIL": "PSOIL",
    "MAIZE": "PMAIZMT",
    "WHEAT_CBOT": "PWHEAMT",
    "RICE": "PRICENPQ",
    "BRENT": "POILBRE",
    "BUTTER": "PBUTTER",
}


class IMFConnector:
    """Fetches commodity price data from the IMF Primary Commodity Prices API."""

    BASE_URL = "https://dataservices.imf.org/REST/SDMX_JSON.svc"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_commodity_price(
        self, symbol: str, months: int = 12
    ) -> list[dict]:
        """Fetch monthly price data for a commodity from IMF PCPS dataset.

        Args:
            symbol: Internal benchmark symbol (e.g., 'COFFEE_ARABICA')
            months: Number of months of history to fetch

        Returns:
            List of dicts with 'date', 'value', 'indicator' keys
        """
        imf_code = IMF_INDICATOR_MAP.get(symbol)
        if not imf_code:
            return []

        now = datetime.utcnow()
        start_year = now.year - (months // 12 + 1)
        freq = "M"

        url = (
            f"{self.BASE_URL}/CompactData/PCPS/"
            f"{freq}.W00.{imf_code}"
            f"?startPeriod={start_year}&endPeriod={now.year}"
        )

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data, symbol)
        except Exception as e:
            logger.warning("IMF price fetch failed", symbol=symbol, error=str(e))
            return []

    def _parse_response(self, data: dict, symbol: str) -> list[dict]:
        """Parse IMF SDMX JSON response into price records."""
        results = []
        try:
            datasets = data.get("CompactData", {}).get("DataSet", {})
            series = datasets.get("Series", {})
            observations = series.get("Obs", [])

            if isinstance(observations, dict):
                observations = [observations]

            for obs in observations:
                period = obs.get("@TIME_PERIOD", "")
                value = obs.get("@OBS_VALUE")
                if value is not None:
                    try:
                        results.append(
                            {
                                "date": period,
                                "value": float(value),
                                "indicator": symbol,
                                "source": "imf",
                            }
                        )
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            logger.warning("IMF response parse error", symbol=symbol, error=str(e))

        return results

    async def fetch_all_tracked(self, symbols: list[str]) -> dict[str, list[dict]]:
        """Fetch prices for all tracked commodities that have IMF mappings."""
        results = {}
        for symbol in symbols:
            if symbol in IMF_INDICATOR_MAP:
                prices = await self.fetch_commodity_price(symbol)
                if prices:
                    results[symbol] = prices
        return results

    async def close(self):
        await self.client.aclose()
