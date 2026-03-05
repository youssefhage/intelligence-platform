"""API routes for ERP/POS synchronization."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.erp_integration.erp_client import ERPClient
from backend.services.pos_integration.pos_client import POSClient

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/erp/products")
async def sync_erp_products(db: AsyncSession = Depends(get_db)):
    """Trigger manual product sync from ERP."""
    client = ERPClient(db)
    result = await client.sync_products()
    await client.close()
    return result


@router.post("/erp/inventory")
async def sync_erp_inventory(db: AsyncSession = Depends(get_db)):
    """Trigger manual inventory sync from ERP."""
    client = ERPClient(db)
    result = await client.sync_inventory()
    await client.close()
    return result


@router.post("/pos/sales")
async def sync_pos_sales(hours: int = 1, db: AsyncSession = Depends(get_db)):
    """Trigger manual POS sales sync."""
    client = POSClient(db)
    result = await client.sync_recent_sales(hours)
    await client.close()
    return result


@router.get("/erp/low-stock")
async def get_low_stock(
    threshold_days: float = 14, db: AsyncSession = Depends(get_db)
):
    """Get products running low on stock."""
    client = ERPClient(db)
    result = await client.get_low_stock_products(threshold_days)
    await client.close()
    return result


@router.get("/pos/top-selling")
async def get_top_selling(
    days: int = 7, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    """Get top selling products."""
    client = POSClient(db)
    result = await client.get_top_selling_products(days, limit)
    await client.close()
    return result


@router.get("/pos/velocity/{product_id}")
async def get_sales_velocity(
    product_id: int, days: int = 30, db: AsyncSession = Depends(get_db)
):
    """Get sales velocity for a product."""
    client = POSClient(db)
    result = await client.get_sales_velocity(product_id, days)
    await client.close()
    return result
