"""Seed script to populate initial data for demo/development."""

import asyncio
import json
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import async_session
from backend.models.commodity import CommodityPrice
from backend.models.supplier import Supplier
from backend.services.market_data.commodity_tracker import CommodityTracker


async def seed_commodities_and_prices(db: AsyncSession):
    """Initialize commodities and generate sample price history."""
    tracker = CommodityTracker(db)
    commodities = await tracker.initialize_commodities()

    # Sample base prices per commodity (USD per unit)
    base_prices = {
        "Rice (Long Grain)": 450,
        "Wheat": 280,
        "Sunflower Oil": 1100,
        "Soybean Oil": 1050,
        "Palm Oil": 900,
        "Sugar (Raw)": 420,
        "Diesel": 85,
        "Brent Crude Oil": 78,
        "Powdered Milk": 3200,
    }

    now = datetime.utcnow()
    for commodity in commodities:
        base = base_prices.get(commodity.name, 100)
        for day in range(90, -1, -1):
            date = now - timedelta(days=day)
            # Random walk with slight upward bias (inflation)
            drift = random.gauss(0.001, 0.02)
            base *= 1 + drift
            price = CommodityPrice(
                commodity_id=commodity.id,
                price_usd=round(base, 2),
                price_lbp=round(base * 89500, 2),
                source="seed_data",
                recorded_at=date,
            )
            db.add(price)

    await db.commit()
    print(f"Seeded price history for {len(commodities)} commodities (90 days each)")


async def seed_suppliers(db: AsyncSession):
    """Create sample suppliers."""
    suppliers_data = [
        {
            "name": "Anatolian Grains Co.",
            "country": "Turkey",
            "region": "Eastern Europe",
            "commodities_supplied": json.dumps(["Wheat", "Sunflower Oil"]),
            "lead_time_days": 14,
            "shipping_route": "Mediterranean, Beirut Port",
            "reliability_score": 82,
            "payment_terms": "NET 30",
        },
        {
            "name": "Black Sea Commodities",
            "country": "Ukraine",
            "region": "Black Sea",
            "commodities_supplied": json.dumps(["Wheat", "Sunflower Oil"]),
            "lead_time_days": 21,
            "shipping_route": "Black Sea, Mediterranean, Beirut Port",
            "reliability_score": 55,
            "payment_terms": "LC at sight",
        },
        {
            "name": "Indo Rice Exports",
            "country": "India",
            "region": "South Asia",
            "commodities_supplied": json.dumps(["Rice (Long Grain)", "Sugar (Raw)"]),
            "lead_time_days": 35,
            "shipping_route": "Indian Ocean, Suez Canal, Mediterranean, Beirut Port",
            "reliability_score": 78,
            "payment_terms": "NET 60",
        },
        {
            "name": "Thai Premium Foods",
            "country": "Thailand",
            "region": "Southeast Asia",
            "commodities_supplied": json.dumps(["Rice (Long Grain)", "Sugar (Raw)", "Palm Oil"]),
            "lead_time_days": 40,
            "shipping_route": "Indian Ocean, Suez Canal, Mediterranean, Beirut Port",
            "reliability_score": 85,
            "payment_terms": "NET 45",
        },
        {
            "name": "Brazilian Agri SA",
            "country": "Brazil",
            "region": "South America",
            "commodities_supplied": json.dumps(["Soybean Oil", "Sugar (Raw)"]),
            "lead_time_days": 45,
            "shipping_route": "Atlantic, Mediterranean, Beirut Port",
            "reliability_score": 80,
            "payment_terms": "NET 60",
        },
        {
            "name": "Gulf Petroleum Trading",
            "country": "Saudi Arabia",
            "region": "Middle East",
            "commodities_supplied": json.dumps(["Diesel", "Brent Crude Oil"]),
            "lead_time_days": 7,
            "shipping_route": "Mediterranean, Beirut Port",
            "reliability_score": 90,
            "payment_terms": "NET 15",
        },
        {
            "name": "Fonterra ME Distribution",
            "country": "New Zealand",
            "region": "Oceania",
            "commodities_supplied": json.dumps(["Powdered Milk"]),
            "lead_time_days": 50,
            "shipping_route": "Indian Ocean, Suez Canal, Mediterranean, Beirut Port",
            "reliability_score": 92,
            "payment_terms": "NET 30",
        },
        {
            "name": "Malaysian Palm Oil Corp",
            "country": "Malaysia",
            "region": "Southeast Asia",
            "commodities_supplied": json.dumps(["Palm Oil"]),
            "lead_time_days": 38,
            "shipping_route": "Indian Ocean, Suez Canal, Mediterranean, Beirut Port",
            "reliability_score": 88,
            "payment_terms": "NET 45",
        },
    ]

    for data in suppliers_data:
        supplier = Supplier(**data)
        db.add(supplier)

    await db.commit()
    print(f"Seeded {len(suppliers_data)} suppliers")


async def main():
    async with async_session() as db:
        await seed_commodities_and_prices(db)
        await seed_suppliers(db)
    print("Seed data complete!")


if __name__ == "__main__":
    asyncio.run(main())
