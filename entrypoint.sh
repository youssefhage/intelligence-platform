#!/bin/sh

echo "=== FMCG Intelligence Platform Backend ==="
echo "Waiting for database to be ready..."
sleep 5

echo "Running database migrations..."
alembic upgrade head || echo "WARNING: Migrations failed, continuing..."

echo "Seeding data (if needed)..."
python -c "
import asyncio
import traceback
from sqlalchemy import text
from backend.core.database import async_session

async def check_and_seed():
    try:
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
    except Exception:
        traceback.print_exc()
        print('WARNING: Seeding failed, continuing...')

asyncio.run(check_and_seed())
" || echo "WARNING: Seed script failed, continuing..."

echo "Starting backend server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
