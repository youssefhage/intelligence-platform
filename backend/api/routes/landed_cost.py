"""API routes for landed cost calculations."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import DutyRateCreate, DutyRateResponse, LandedCostRequest
from backend.core.database import get_db
from backend.models.landed_cost import DutyRate
from backend.services.market_data.landed_cost_calculator import LandedCostCalculator

router = APIRouter(prefix="/landed-cost", tags=["landed-cost"])


@router.post("/calculate")
async def calculate_landed_cost(
    data: LandedCostRequest, db: AsyncSession = Depends(get_db)
):
    calculator = LandedCostCalculator(db)
    return await calculator.calculate(
        commodity_name=data.commodity_name,
        commodity_id=data.commodity_id,
        origin_country=data.origin_country,
        quantity=data.quantity,
        unit=data.unit,
        incoterm=data.incoterm,
        fob_price_usd=data.fob_price_usd,
        freight_cost_usd=data.freight_cost_usd,
        insurance_pct=data.insurance_pct,
        duty_pct=data.duty_pct,
        hs_code=data.hs_code,
        port_charges_usd=data.port_charges_usd,
        inland_transport_usd=data.inland_transport_usd,
    )


@router.post("/compare")
async def compare_origins(
    commodity_name: str,
    origins: list[str],
    fob_price_usd: float,
    quantity: float = 1.0,
    db: AsyncSession = Depends(get_db),
):
    calculator = LandedCostCalculator(db)
    return await calculator.compare_origins(
        commodity_name=commodity_name,
        origins=origins,
        fob_price_usd=fob_price_usd,
        quantity=quantity,
    )


@router.get("/history")
async def get_calculation_history(
    limit: int = 50, db: AsyncSession = Depends(get_db)
):
    calculator = LandedCostCalculator(db)
    return await calculator.get_history(limit)


@router.get("/duty-rates", response_model=list[DutyRateResponse])
async def list_duty_rates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DutyRate))
    return result.scalars().all()


@router.post("/duty-rates", response_model=DutyRateResponse)
async def create_duty_rate(
    data: DutyRateCreate, db: AsyncSession = Depends(get_db)
):
    rate = DutyRate(**data.model_dump())
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return rate
