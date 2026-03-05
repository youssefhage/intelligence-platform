#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding data (if needed)..."
python -c "
import asyncio
from sqlalchemy import text
from backend.core.database import async_session

async def check_and_seed():
    async with async_session() as db:
        result = await db.execute(text('SELECT COUNT(*) FROM commodities'))
        count = result.scalar()
        if count == 0:
            print('Database empty, seeding...')
            from backend.seed_data import seed_commodities_and_prices, seed_suppliers
            await seed_commodities_and_prices(db)
            await seed_suppliers(db)
            print('Seeding complete!')
        else:
            print(f'Database already has {count} commodities, skipping seed.')

asyncio.run(check_and_seed())
"

echo "Starting backend server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
