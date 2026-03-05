"""API routes for supplier management and risk assessment."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import SupplierCreate, SupplierResponse
from backend.core.database import get_db
from backend.models.supplier import Supplier
from backend.services.supply_chain.risk_analyzer import SupplyChainRiskAnalyzer

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("/", response_model=list[SupplierResponse])
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Supplier).where(Supplier.is_active.is_(True))
    )
    return result.scalars().all()


@router.post("/", response_model=SupplierResponse)
async def create_supplier(
    data: SupplierCreate, db: AsyncSession = Depends(get_db)
):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.post("/{supplier_id}/assess-risk")
async def assess_risk(supplier_id: int, db: AsyncSession = Depends(get_db)):
    analyzer = SupplyChainRiskAnalyzer(db)
    assessment = await analyzer.assess_supplier_risk(supplier_id)
    return {
        "id": assessment.id,
        "supplier_id": assessment.supplier_id,
        "risk_level": assessment.risk_level.value,
        "geopolitical_risk": assessment.geopolitical_risk,
        "logistics_risk": assessment.logistics_risk,
        "financial_risk": assessment.financial_risk,
        "currency_risk": assessment.currency_risk,
        "risk_factors": assessment.risk_factors,
        "recommendations": assessment.recommendations,
    }


@router.get("/supply-chain/overview")
async def supply_chain_overview(db: AsyncSession = Depends(get_db)):
    analyzer = SupplyChainRiskAnalyzer(db)
    return await analyzer.get_supply_chain_overview()


@router.get("/alternatives/{commodity_name}")
async def find_alternatives(
    commodity_name: str,
    exclude_countries: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    analyzer = SupplyChainRiskAnalyzer(db)
    exclude = exclude_countries.split(",") if exclude_countries else None
    return await analyzer.find_alternative_suppliers(commodity_name, exclude)
