"""Real commodity price connectors for World Bank, USDA, and open data sources."""

import json
from datetime import datetime, timedelta

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.alert import Alert, AlertSeverity, AlertType
from backend.models.commodity import Commodity, CommodityPrice

logger = structlog.get_logger()

# World Bank commodity indicator codes
WORLD_BANK_INDICATORS = {
    "RICE": "RICE_05",
    "WHEAT_CBOT": "WHEAT_US_HRW",
    "SUNFLOWER_OIL": "SUNFLOWER_OIL",
    "SOYBEAN_OIL": "SOYBEAN_OIL",
    "PALM_OIL": "PALM_OIL",
    "SUGAR_RAW": "SUGAR_WLD",
    "BRENT": "CRUDE_BRENT",
    "WMP": "WMP",
    # New commodities
    "MAIZE": "MAIZE",
    "COCOA": "COCOA",
    "COFFEE_ARABICA": "COFFEE_ARABIC",
    "COFFEE_ROBUSTA": "COFFEE_ROBUS",
    "TEA": "TEA_AVG",
    "OLIVE_OIL": "OLIVE_OIL",
    "BUTTER": "BUTTER",
    "CHEESE": "CHEESE",
    "ALUMINUM": "ALUMINUM",
    "TIN": "TIN",
}

# USDA FAS API commodity codes (for production/trade data)
USDA_COMMODITY_CODES = {
    "RICE": "0422110",
    "WHEAT_CBOT": "0410100",
    "SOYBEAN_OIL": "4232000",
    "SUGAR_RAW": "0612000",
}


class WorldBankConnector:
    """Fetches commodity price data from the World Bank Commodity Price API."""

    BASE_URL = "https://api.worldbank.org/v2"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_monthly_prices(
        self, indicator: str, months: int = 12
    ) -> list[dict]:
        """Fetch monthly commodity prices from World Bank."""
        url = f"{self.BASE_URL}/country/WLD/indicator/COMMODITY_{indicator}"
        params = {
            "format": "json",
            "per_page": months,
            "date": f"{datetime.utcnow().year - 1}:{datetime.utcnow().year}",
        }
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) > 1 and data[1]:
                return [
                    {
                        "date": item.get("date", ""),
                        "value": item.get("value"),
                        "indicator": indicator,
                    }
                    for item in data[1]
                    if item.get("value") is not None
                ]
        except Exception as e:
            logger.warning("World Bank price fetch failed", indicator=indicator, error=str(e))
        return []

    async def fetch_pink_sheet(self) -> dict:
        """Fetch World Bank Commodity Price Data (Pink Sheet).

        The Pink Sheet provides monthly commodity prices across all
        categories. Falls back to a curated set of commodity-specific queries.
        """
        url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/cmopricedatamonthly"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return {"source": "world_bank_pink_sheet", "data": response.text[:5000]}
        except Exception as e:
            logger.warning("Pink Sheet fetch failed", error=str(e))
            return {}

    async def close(self):
        await self.client.aclose()


class USDAConnector:
    """Fetches agricultural commodity data from USDA Foreign Agricultural Service."""

    BASE_URL = "https://apps.fas.usda.gov/OpenData/api/esr"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_export_sales(self, commodity_code: str) -> list[dict]:
        """Fetch weekly export sales report from USDA."""
        url = f"{self.BASE_URL}/commodities/{commodity_code}/allCountries"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(
                "USDA export sales fetch failed",
                commodity=commodity_code,
                error=str(e),
            )
            return []

    async def fetch_production_supply_distribution(
        self, commodity_code: str
    ) -> list[dict]:
        """Fetch USDA PSD (Production, Supply, Distribution) data."""
        url = f"https://apps.fas.usda.gov/OpenData/api/psd/commodity/{commodity_code}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("USDA PSD fetch failed", commodity=commodity_code, error=str(e))
            return []

    async def close(self):
        await self.client.aclose()


class FreightosScraper:
    """Fetches freight/shipping rate indices relevant to Lebanese imports."""

    BASE_URL = "https://fbx.freightos.com"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_container_rates(self) -> dict:
        """Fetch Freightos Baltic Index container shipping rates.

        Returns approximate container shipping rates for routes relevant
        to Lebanese imports (China-Med, India-Med).
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/api/index")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("Freightos rate fetch failed", error=str(e))
            return {}

    async def close(self):
        await self.client.aclose()


class EnhancedCommodityTracker:
    """Enhanced commodity tracker using multiple real data sources."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wb = WorldBankConnector()
        self.usda = USDAConnector()
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def fetch_all_prices(self) -> dict:
        """Fetch prices from all available sources and record them."""
        from backend.services.market_data.imf_connector import IMFConnector
        from backend.services.market_data.fred_connector import FREDConnector
        from backend.services.market_data.forex_connector import ForexConnector

        results = {"world_bank": [], "imf": [], "fred": [], "forex": [], "usda": [], "errors": []}

        # Get all tracked commodities
        commodities_result = await self.db.execute(
            select(Commodity).where(Commodity.is_active.is_(True))
        )
        commodities = {c.global_benchmark_symbol: c for c in commodities_result.scalars().all()}
        all_symbols = list(commodities.keys())

        # --- World Bank prices ---
        for symbol, wb_indicator in WORLD_BANK_INDICATORS.items():
            commodity = commodities.get(symbol)
            if not commodity:
                continue

            prices = await self.wb.fetch_monthly_prices(wb_indicator, months=6)
            for price_data in prices:
                if price_data.get("value"):
                    try:
                        price_lbp = float(price_data["value"]) * settings.lbp_exchange_rate
                        record = CommodityPrice(
                            commodity_id=commodity.id,
                            price_usd=float(price_data["value"]),
                            price_lbp=price_lbp,
                            source="world_bank",
                            recorded_at=self._parse_wb_date(price_data["date"]),
                        )
                        self.db.add(record)
                        results["world_bank"].append(
                            {"commodity": commodity.name, "price": price_data["value"]}
                        )
                    except Exception as e:
                        results["errors"].append(f"{commodity.name} (WB): {e}")

        # --- IMF prices ---
        try:
            imf = IMFConnector()
            imf_data = await imf.fetch_all_tracked(all_symbols)
            for symbol, prices in imf_data.items():
                commodity = commodities.get(symbol)
                if not commodity or not prices:
                    continue
                # Only record the latest price from IMF (avoid duplicates with WB)
                latest = prices[0] if prices else None
                if latest and latest.get("value"):
                    try:
                        record = CommodityPrice(
                            commodity_id=commodity.id,
                            price_usd=float(latest["value"]),
                            price_lbp=float(latest["value"]) * settings.lbp_exchange_rate,
                            source="imf",
                            recorded_at=self._parse_period_date(latest["date"]),
                        )
                        self.db.add(record)
                        results["imf"].append(
                            {"commodity": commodity.name, "price": latest["value"]}
                        )
                    except Exception as e:
                        results["errors"].append(f"{commodity.name} (IMF): {e}")
            await imf.close()
        except Exception as e:
            results["errors"].append(f"IMF connector: {e}")

        # --- FRED prices ---
        try:
            fred = FREDConnector()
            if fred.is_configured:
                fred_data = await fred.fetch_all_tracked(all_symbols)
                for symbol, prices in fred_data.items():
                    commodity = commodities.get(symbol)
                    if not commodity or not prices:
                        continue
                    latest = prices[0] if prices else None
                    if latest and latest.get("value"):
                        try:
                            record = CommodityPrice(
                                commodity_id=commodity.id,
                                price_usd=float(latest["value"]),
                                price_lbp=float(latest["value"]) * settings.lbp_exchange_rate,
                                source="fred",
                                recorded_at=datetime.strptime(latest["date"], "%Y-%m-%d"),
                            )
                            self.db.add(record)
                            results["fred"].append(
                                {"commodity": commodity.name, "price": latest["value"]}
                            )
                        except Exception as e:
                            results["errors"].append(f"{commodity.name} (FRED): {e}")
                await fred.close()
        except Exception as e:
            results["errors"].append(f"FRED connector: {e}")

        # --- Forex rates as commodity prices ---
        try:
            forex = ForexConnector(self.db)
            rates = await forex.fetch_and_persist()
            from backend.services.market_data.forex_connector import FOREX_SYMBOL_MAP
            for symbol, currency_code in FOREX_SYMBOL_MAP.items():
                commodity = commodities.get(symbol)
                if not commodity:
                    continue
                pair_name = f"USD/{currency_code}"
                rate = rates.get(pair_name)
                if rate:
                    try:
                        record = CommodityPrice(
                            commodity_id=commodity.id,
                            price_usd=rate,
                            price_lbp=0,  # Not applicable for currency pairs
                            source="forex",
                            recorded_at=datetime.utcnow(),
                        )
                        self.db.add(record)
                        results["forex"].append(
                            {"commodity": commodity.name, "rate": rate}
                        )
                    except Exception as e:
                        results["errors"].append(f"{commodity.name} (forex): {e}")
            await forex.close()
        except Exception as e:
            results["errors"].append(f"Forex connector: {e}")

        # --- USDA data ---
        for symbol, usda_code in USDA_COMMODITY_CODES.items():
            commodity = commodities.get(symbol)
            if not commodity:
                continue
            export_data = await self.usda.fetch_export_sales(usda_code)
            if export_data:
                results["usda"].append(
                    {"commodity": commodity.name, "records": len(export_data)}
                )

        await self.db.commit()

        logger.info(
            "Multi-source price fetch complete",
            wb_prices=len(results["world_bank"]),
            imf_prices=len(results["imf"]),
            fred_prices=len(results["fred"]),
            forex_rates=len(results["forex"]),
            usda_records=len(results["usda"]),
            errors=len(results["errors"]),
        )
        return results

    async def check_price_alerts(self, threshold_pct: float = 5.0):
        """Check for significant price movements and create alerts."""
        commodities_result = await self.db.execute(
            select(Commodity).where(Commodity.is_active.is_(True))
        )
        commodities = commodities_result.scalars().all()

        for commodity in commodities:
            # Get last 2 price points
            prices_result = await self.db.execute(
                select(CommodityPrice)
                .where(CommodityPrice.commodity_id == commodity.id)
                .order_by(CommodityPrice.recorded_at.desc())
                .limit(2)
            )
            prices = prices_result.scalars().all()

            if len(prices) < 2:
                continue

            latest, previous = prices[0], prices[1]
            if previous.price_usd <= 0:
                continue

            change_pct = (
                (latest.price_usd - previous.price_usd) / previous.price_usd
            ) * 100

            if abs(change_pct) >= threshold_pct:
                direction = "increase" if change_pct > 0 else "decrease"
                severity = (
                    AlertSeverity.CRITICAL
                    if abs(change_pct) >= 10
                    else AlertSeverity.WARNING
                )
                alert = Alert(
                    alert_type=AlertType.PRICE_SPIKE,
                    severity=severity,
                    title=f"Significant price {direction}: {commodity.name}",
                    message=(
                        f"{commodity.name} price has {direction}d by "
                        f"{abs(change_pct):.1f}% from ${previous.price_usd:.2f} "
                        f"to ${latest.price_usd:.2f}."
                    ),
                    related_entity_type="commodity",
                    related_entity_id=commodity.id,
                    action_recommended=(
                        f"Review pricing and inventory for products dependent on {commodity.name}."
                        if change_pct > 0
                        else f"Consider opportunistic purchasing of {commodity.name} at lower prices."
                    ),
                )
                self.db.add(alert)

        await self.db.commit()

    def _parse_wb_date(self, date_str: str) -> datetime:
        """Parse World Bank date format (YYYY or YYYYMDD)."""
        try:
            if "M" in date_str:
                year, month = date_str.split("M")
                return datetime(int(year), int(month), 1)
            return datetime(int(date_str), 1, 1)
        except (ValueError, TypeError):
            return datetime.utcnow()

    def _parse_period_date(self, date_str: str) -> datetime:
        """Parse period date formats like '2024-01', '2024-M01', or '2024-01-15'."""
        try:
            if "-M" in date_str:
                # IMF format: 2024-M01
                parts = date_str.split("-M")
                return datetime(int(parts[0]), int(parts[1]), 1)
            elif len(date_str) == 7:
                # YYYY-MM format
                return datetime.strptime(date_str, "%Y-%m")
            elif len(date_str) == 10:
                return datetime.strptime(date_str, "%Y-%m-%d")
            return datetime.utcnow()
        except (ValueError, TypeError):
            return datetime.utcnow()

    async def close(self):
        await self.wb.close()
        await self.usda.close()
        await self.http_client.aclose()
