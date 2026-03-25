"""Tracks global commodity prices from multiple data sources."""

import json
from datetime import datetime, timedelta

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.commodity import Commodity, CommodityPrice

logger = structlog.get_logger()

# Default commodities relevant to Lebanese FMCG wholesale
DEFAULT_COMMODITIES = [
    # === GRAINS & STAPLES ===
    {
        "name": "Rice (Long Grain)",
        "category": "grain",
        "unit": "ton",
        "origin_countries": json.dumps(["India", "Pakistan", "Thailand", "Vietnam"]),
        "sourcing_regions": json.dumps(["South Asia", "Southeast Asia"]),
        "global_benchmark_symbol": "RICE",
    },
    {
        "name": "Wheat",
        "category": "grain",
        "unit": "ton",
        "origin_countries": json.dumps(["Turkey", "Ukraine", "Russia", "Romania"]),
        "sourcing_regions": json.dumps(["Black Sea", "Eastern Europe"]),
        "global_benchmark_symbol": "WHEAT_CBOT",
    },
    {
        "name": "Maize",
        "category": "grain",
        "unit": "ton",
        "origin_countries": json.dumps(["USA", "Argentina", "Brazil", "Ukraine"]),
        "sourcing_regions": json.dumps(["North America", "South America", "Black Sea"]),
        "global_benchmark_symbol": "MAIZE",
    },
    {
        "name": "Flour",
        "category": "grain",
        "unit": "ton",
        "origin_countries": json.dumps(["Turkey", "Egypt", "Ukraine"]),
        "sourcing_regions": json.dumps(["Eastern Europe", "Middle East"]),
        "global_benchmark_symbol": "FLOUR",
    },
    # === COOKING & FOOD OILS ===
    {
        "name": "Sunflower Oil",
        "category": "oil",
        "unit": "ton",
        "origin_countries": json.dumps(["Ukraine", "Turkey", "Argentina"]),
        "sourcing_regions": json.dumps(["Black Sea", "South America"]),
        "global_benchmark_symbol": "SUNFLOWER_OIL",
    },
    {
        "name": "Soybean Oil",
        "category": "oil",
        "unit": "ton",
        "origin_countries": json.dumps(["Argentina", "Brazil", "USA"]),
        "sourcing_regions": json.dumps(["South America", "North America"]),
        "global_benchmark_symbol": "SOYBEAN_OIL",
    },
    {
        "name": "Palm Oil",
        "category": "oil",
        "unit": "ton",
        "origin_countries": json.dumps(["Malaysia", "Indonesia"]),
        "sourcing_regions": json.dumps(["Southeast Asia"]),
        "global_benchmark_symbol": "PALM_OIL",
    },
    {
        "name": "Olive Oil",
        "category": "oil",
        "unit": "ton",
        "origin_countries": json.dumps(["Spain", "Italy", "Tunisia", "Turkey"]),
        "sourcing_regions": json.dumps(["Mediterranean"]),
        "global_benchmark_symbol": "OLIVE_OIL",
    },
    # === SUGAR ===
    {
        "name": "Sugar (Raw)",
        "category": "sugar",
        "unit": "ton",
        "origin_countries": json.dumps(["Brazil", "India", "Thailand"]),
        "sourcing_regions": json.dumps(["South America", "South Asia"]),
        "global_benchmark_symbol": "SUGAR_RAW",
    },
    # === BEVERAGES ===
    {
        "name": "Coffee (Arabica)",
        "category": "beverage",
        "unit": "ton",
        "origin_countries": json.dumps(["Brazil", "Colombia", "Ethiopia"]),
        "sourcing_regions": json.dumps(["South America", "East Africa"]),
        "global_benchmark_symbol": "COFFEE_ARABICA",
    },
    {
        "name": "Coffee (Robusta)",
        "category": "beverage",
        "unit": "ton",
        "origin_countries": json.dumps(["Vietnam", "Brazil", "Indonesia"]),
        "sourcing_regions": json.dumps(["Southeast Asia", "South America"]),
        "global_benchmark_symbol": "COFFEE_ROBUSTA",
    },
    {
        "name": "Tea",
        "category": "beverage",
        "unit": "ton",
        "origin_countries": json.dumps(["Sri Lanka", "India", "Kenya", "China"]),
        "sourcing_regions": json.dumps(["South Asia", "East Africa", "East Asia"]),
        "global_benchmark_symbol": "TEA",
    },
    {
        "name": "Cocoa",
        "category": "beverage",
        "unit": "ton",
        "origin_countries": json.dumps(["Ivory Coast", "Ghana", "Ecuador"]),
        "sourcing_regions": json.dumps(["West Africa", "South America"]),
        "global_benchmark_symbol": "COCOA",
    },
    # === DAIRY ===
    {
        "name": "Powdered Milk",
        "category": "dairy",
        "unit": "ton",
        "origin_countries": json.dumps(["New Zealand", "Netherlands", "France"]),
        "sourcing_regions": json.dumps(["Oceania", "Western Europe"]),
        "global_benchmark_symbol": "WMP",
    },
    {
        "name": "Butter",
        "category": "dairy",
        "unit": "ton",
        "origin_countries": json.dumps(["New Zealand", "Netherlands", "Ireland"]),
        "sourcing_regions": json.dumps(["Oceania", "Western Europe"]),
        "global_benchmark_symbol": "BUTTER",
    },
    {
        "name": "Cheese",
        "category": "dairy",
        "unit": "ton",
        "origin_countries": json.dumps(["Netherlands", "France", "Germany"]),
        "sourcing_regions": json.dumps(["Western Europe"]),
        "global_benchmark_symbol": "CHEESE",
    },
    # === PACKAGING ===
    {
        "name": "Paper/Cardboard",
        "category": "packaging",
        "unit": "ton",
        "origin_countries": json.dumps(["China", "Turkey", "Germany"]),
        "sourcing_regions": json.dumps(["East Asia", "Eastern Europe"]),
        "global_benchmark_symbol": "PAPER_CARDBOARD",
    },
    {
        "name": "HDPE (Plastic)",
        "category": "packaging",
        "unit": "ton",
        "origin_countries": json.dumps(["Saudi Arabia", "China", "USA"]),
        "sourcing_regions": json.dumps(["Middle East", "East Asia", "North America"]),
        "global_benchmark_symbol": "HDPE",
    },
    {
        "name": "PET Resin",
        "category": "packaging",
        "unit": "ton",
        "origin_countries": json.dumps(["China", "India", "Saudi Arabia"]),
        "sourcing_regions": json.dumps(["East Asia", "Middle East"]),
        "global_benchmark_symbol": "PET",
    },
    {
        "name": "Polypropylene (PP)",
        "category": "packaging",
        "unit": "ton",
        "origin_countries": json.dumps(["Saudi Arabia", "China", "South Korea"]),
        "sourcing_regions": json.dumps(["Middle East", "East Asia"]),
        "global_benchmark_symbol": "PP",
    },
    {
        "name": "Aluminum",
        "category": "packaging",
        "unit": "ton",
        "origin_countries": json.dumps(["China", "Russia", "India", "UAE"]),
        "sourcing_regions": json.dumps(["East Asia", "Middle East"]),
        "global_benchmark_symbol": "ALUMINUM",
    },
    {
        "name": "Tin Plate",
        "category": "packaging",
        "unit": "ton",
        "origin_countries": json.dumps(["China", "Indonesia", "Peru"]),
        "sourcing_regions": json.dumps(["East Asia", "South America"]),
        "global_benchmark_symbol": "TIN",
    },
    # === CLEANING & HOUSEHOLD ===
    {
        "name": "Paraffin Wax",
        "category": "cleaning",
        "unit": "ton",
        "origin_countries": json.dumps(["China", "Saudi Arabia", "India"]),
        "sourcing_regions": json.dumps(["East Asia", "Middle East"]),
        "global_benchmark_symbol": "PARAFFIN_WAX",
    },
    {
        "name": "Caustic Soda",
        "category": "cleaning",
        "unit": "ton",
        "origin_countries": json.dumps(["China", "Turkey", "Saudi Arabia"]),
        "sourcing_regions": json.dumps(["East Asia", "Middle East"]),
        "global_benchmark_symbol": "CAUSTIC_SODA",
    },
    # === ENERGY (cost drivers) ===
    {
        "name": "Diesel",
        "category": "fuel",
        "unit": "barrel",
        "origin_countries": json.dumps(["Saudi Arabia", "Iraq", "Kuwait"]),
        "sourcing_regions": json.dumps(["Middle East"]),
        "global_benchmark_symbol": "DIESEL",
    },
    {
        "name": "Brent Crude Oil",
        "category": "fuel",
        "unit": "barrel",
        "origin_countries": json.dumps(["Global"]),
        "sourcing_regions": json.dumps(["Global"]),
        "global_benchmark_symbol": "BRENT",
    },
    # === SHIPPING (cost drivers) ===
    {
        "name": "Baltic Dry Index",
        "category": "shipping",
        "unit": "index",
        "origin_countries": json.dumps(["Global"]),
        "sourcing_regions": json.dumps(["Global"]),
        "global_benchmark_symbol": "BDI",
    },
    {
        "name": "Container Freight Rate",
        "category": "shipping",
        "unit": "index",
        "origin_countries": json.dumps(["Global"]),
        "sourcing_regions": json.dumps(["Shanghai to Mediterranean"]),
        "global_benchmark_symbol": "CONTAINER_FREIGHT",
    },
    # === CURRENCIES (sourcing cost) ===
    {
        "name": "USD/TRY",
        "category": "currency",
        "unit": "rate",
        "origin_countries": json.dumps(["Turkey"]),
        "sourcing_regions": json.dumps(["Eastern Europe"]),
        "global_benchmark_symbol": "USD_TRY",
    },
    {
        "name": "USD/EGP",
        "category": "currency",
        "unit": "rate",
        "origin_countries": json.dumps(["Egypt"]),
        "sourcing_regions": json.dumps(["Middle East"]),
        "global_benchmark_symbol": "USD_EGP",
    },
    {
        "name": "USD/CNY",
        "category": "currency",
        "unit": "rate",
        "origin_countries": json.dumps(["China"]),
        "sourcing_regions": json.dumps(["East Asia"]),
        "global_benchmark_symbol": "USD_CNY",
    },
    {
        "name": "USD/LBP",
        "category": "currency",
        "unit": "rate",
        "origin_countries": json.dumps(["Lebanon"]),
        "sourcing_regions": json.dumps(["Middle East"]),
        "global_benchmark_symbol": "USD_LBP",
    },
]


class CommodityTracker:
    """Fetches and stores commodity price data from global sources."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def initialize_commodities(self) -> list[Commodity]:
        """Seed the database with default tracked commodities if empty."""
        result = await self.db.execute(select(Commodity))
        existing = result.scalars().all()
        if existing:
            return list(existing)

        commodities = []
        for data in DEFAULT_COMMODITIES:
            commodity = Commodity(**data)
            self.db.add(commodity)
            commodities.append(commodity)

        await self.db.commit()
        logger.info("Initialized default commodities", count=len(commodities))
        return commodities

    async def ensure_all_commodities(self) -> list[Commodity]:
        """Insert any missing commodities from DEFAULT_COMMODITIES.

        Unlike initialize_commodities which only seeds when empty, this method
        checks for missing entries by global_benchmark_symbol and inserts them.
        Safe to call on every startup.
        """
        result = await self.db.execute(select(Commodity))
        existing = result.scalars().all()
        existing_symbols = {c.global_benchmark_symbol for c in existing}

        added = []
        for data in DEFAULT_COMMODITIES:
            if data["global_benchmark_symbol"] not in existing_symbols:
                commodity = Commodity(**data)
                self.db.add(commodity)
                added.append(commodity)

        if added:
            await self.db.commit()
            logger.info("Added missing commodities", count=len(added))

        # Return all commodities
        result = await self.db.execute(select(Commodity))
        return list(result.scalars().all())

    async def fetch_world_bank_prices(self) -> list[dict]:
        """Fetch commodity price data from World Bank API."""
        try:
            url = f"{settings.world_bank_api_url}/country/LBN/indicator/FP.CPI.TOTL"
            params = {"format": "json", "per_page": 50, "date": "2020:2026"}
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                return data[1] or []
        except Exception as e:
            logger.warning("World Bank API fetch failed", error=str(e))
        return []

    async def fetch_fao_food_price_index(self) -> dict | None:
        """Fetch FAO Food Price Index data."""
        try:
            url = f"{settings.fao_api_url}/en/#data/CP"
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("FAO API fetch failed", error=str(e))
        return None

    async def record_price(
        self,
        commodity_id: int,
        price_usd: float,
        source: str,
        recorded_at: datetime | None = None,
        notes: str | None = None,
    ) -> CommodityPrice:
        """Record a new commodity price observation."""
        price_lbp = price_usd * settings.lbp_exchange_rate
        price_record = CommodityPrice(
            commodity_id=commodity_id,
            price_usd=price_usd,
            price_lbp=price_lbp,
            source=source,
            recorded_at=recorded_at or datetime.utcnow(),
            notes=notes,
        )
        self.db.add(price_record)
        await self.db.commit()
        await self.db.refresh(price_record)
        logger.info(
            "Recorded commodity price",
            commodity_id=commodity_id,
            price_usd=price_usd,
            source=source,
        )
        return price_record

    async def get_price_history(
        self, commodity_id: int, days: int = 90
    ) -> list[CommodityPrice]:
        """Get price history for a commodity over a given period."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.commodity_id == commodity_id)
            .where(CommodityPrice.recorded_at >= since)
            .order_by(CommodityPrice.recorded_at.asc())
        )
        return list(result.scalars().all())

    async def get_latest_prices(self) -> list[dict]:
        """Get the latest price for each tracked commodity."""
        commodities_result = await self.db.execute(
            select(Commodity).where(Commodity.is_active.is_(True))
        )
        commodities = commodities_result.scalars().all()

        latest_prices = []
        for commodity in commodities:
            price_result = await self.db.execute(
                select(CommodityPrice)
                .where(CommodityPrice.commodity_id == commodity.id)
                .order_by(CommodityPrice.recorded_at.desc())
                .limit(1)
            )
            latest_price = price_result.scalar_one_or_none()

            # Get price from 7 days ago for comparison
            week_ago = datetime.utcnow() - timedelta(days=7)
            prev_result = await self.db.execute(
                select(CommodityPrice)
                .where(CommodityPrice.commodity_id == commodity.id)
                .where(CommodityPrice.recorded_at <= week_ago)
                .order_by(CommodityPrice.recorded_at.desc())
                .limit(1)
            )
            prev_price = prev_result.scalar_one_or_none()

            change_pct = None
            if latest_price and prev_price and prev_price.price_usd > 0:
                change_pct = (
                    (latest_price.price_usd - prev_price.price_usd) / prev_price.price_usd
                ) * 100

            latest_prices.append(
                {
                    "commodity_id": commodity.id,
                    "commodity_name": commodity.name,
                    "category": commodity.category.value,
                    "unit": commodity.unit,
                    "current_price_usd": latest_price.price_usd if latest_price else None,
                    "current_price_lbp": latest_price.price_lbp if latest_price else None,
                    "week_change_pct": round(change_pct, 2) if change_pct is not None else None,
                    "last_updated": (
                        latest_price.recorded_at.isoformat() if latest_price else None
                    ),
                }
            )
        return latest_prices

    async def close(self):
        await self.http_client.aclose()
