"""Landed cost calculator for FMCG import costing."""

from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.landed_cost import DutyRate, LandedCostCalculation

logger = structlog.get_logger()

# Default port/transport costs for Beirut (USD)
DEFAULT_PORT_CHARGES = {
    "Beirut": 350,
    "Tripoli": 280,
}

# Default freight estimates (USD per container/ton) by origin
DEFAULT_FREIGHT_ESTIMATES = {
    "China": 2800,
    "Turkey": 800,
    "Egypt": 500,
    "India": 1800,
    "Brazil": 2500,
    "Malaysia": 2200,
    "Indonesia": 2300,
    "Thailand": 2100,
    "Vietnam": 2000,
    "Argentina": 2600,
    "Ukraine": 1200,
    "New Zealand": 3500,
    "Netherlands": 1500,
    "Spain": 1000,
    "Saudi Arabia": 600,
    "default": 2000,
}

# Default inland transport to warehouse (USD)
DEFAULT_INLAND_TRANSPORT = 150


class LandedCostCalculator:
    """Calculates total landed cost for importing commodities to Lebanon."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate(
        self,
        commodity_name: str,
        origin_country: str,
        quantity: float = 1.0,
        unit: str = "ton",
        incoterm: str = "FOB",
        fob_price_usd: float = 0,
        freight_cost_usd: float | None = None,
        insurance_pct: float = 0.5,
        duty_pct: float | None = None,
        hs_code: str | None = None,
        port_charges_usd: float | None = None,
        inland_transport_usd: float | None = None,
        commodity_id: int | None = None,
        save: bool = True,
    ) -> dict:
        """Calculate the full landed cost breakdown.

        Args:
            commodity_name: Name of the commodity
            origin_country: Country of origin
            quantity: Quantity in specified unit
            unit: Unit of measurement
            incoterm: Trade term (FOB, CIF, EXW)
            fob_price_usd: FOB price per unit
            freight_cost_usd: Freight cost (auto-estimated if None)
            insurance_pct: Insurance as % of CIF value
            duty_pct: Custom duty % (looked up by HS code if None)
            hs_code: HS code for duty lookup
            port_charges_usd: Port handling fees (default if None)
            inland_transport_usd: Inland transport cost (default if None)
            commodity_id: Optional commodity FK
            save: Whether to persist the calculation
        """
        total_fob = fob_price_usd * quantity

        # Auto-estimate freight if not provided
        if freight_cost_usd is None:
            freight_cost_usd = self._estimate_freight(origin_country, quantity)
        else:
            freight_cost_usd = freight_cost_usd * quantity

        # Insurance
        insurance_cost_usd = (total_fob + freight_cost_usd) * (insurance_pct / 100)

        # CIF = FOB + Freight + Insurance
        cif_price_usd = total_fob + freight_cost_usd + insurance_cost_usd

        # Duty
        if duty_pct is None and hs_code:
            duty_pct = await self._lookup_duty(hs_code, origin_country)
        duty_pct = duty_pct or 0
        duty_usd = cif_price_usd * (duty_pct / 100)

        # Port charges
        if port_charges_usd is None:
            port_charges_usd = DEFAULT_PORT_CHARGES.get("Beirut", 350)

        # Inland transport
        if inland_transport_usd is None:
            inland_transport_usd = DEFAULT_INLAND_TRANSPORT

        # Total landed cost
        total_landed = cif_price_usd + duty_usd + port_charges_usd + inland_transport_usd
        cost_per_unit = total_landed / quantity if quantity > 0 else total_landed

        result = {
            "commodity_name": commodity_name,
            "origin_country": origin_country,
            "quantity": quantity,
            "unit": unit,
            "incoterm": incoterm,
            "fob_price_usd": round(total_fob, 2),
            "freight_cost_usd": round(freight_cost_usd, 2),
            "insurance_pct": insurance_pct,
            "insurance_cost_usd": round(insurance_cost_usd, 2),
            "cif_price_usd": round(cif_price_usd, 2),
            "duty_pct": duty_pct,
            "duty_usd": round(duty_usd, 2),
            "port_charges_usd": round(port_charges_usd, 2),
            "inland_transport_usd": round(inland_transport_usd, 2),
            "total_landed_cost_usd": round(total_landed, 2),
            "cost_per_unit_usd": round(cost_per_unit, 2),
        }

        if save:
            record = LandedCostCalculation(
                commodity_id=commodity_id,
                commodity_name=commodity_name,
                origin_country=origin_country,
                quantity=quantity,
                unit=unit,
                incoterm=incoterm,
                fob_price_usd=round(total_fob, 2),
                freight_cost_usd=round(freight_cost_usd, 2),
                insurance_pct=insurance_pct,
                insurance_cost_usd=round(insurance_cost_usd, 2),
                cif_price_usd=round(cif_price_usd, 2),
                duty_pct=duty_pct,
                duty_usd=round(duty_usd, 2),
                port_charges_usd=round(port_charges_usd, 2),
                inland_transport_usd=round(inland_transport_usd, 2),
                total_landed_cost_usd=round(total_landed, 2),
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            result["id"] = record.id
            result["calculated_at"] = record.calculated_at.isoformat() if record.calculated_at else None

        return result

    async def compare_origins(
        self,
        commodity_name: str,
        origins: list[str],
        fob_price_usd: float,
        quantity: float = 1.0,
        **kwargs,
    ) -> list[dict]:
        """Compare landed costs from different origin countries."""
        results = []
        for origin in origins:
            calc = await self.calculate(
                commodity_name=commodity_name,
                origin_country=origin,
                quantity=quantity,
                fob_price_usd=fob_price_usd,
                save=False,
                **kwargs,
            )
            results.append(calc)
        results.sort(key=lambda x: x["total_landed_cost_usd"])
        return results

    async def get_history(self, limit: int = 50) -> list[dict]:
        """Get past landed cost calculations."""
        result = await self.db.execute(
            select(LandedCostCalculation)
            .order_by(LandedCostCalculation.calculated_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
        return [
            {
                "id": r.id,
                "commodity_name": r.commodity_name,
                "origin_country": r.origin_country,
                "quantity": r.quantity,
                "fob_price_usd": r.fob_price_usd,
                "total_landed_cost_usd": r.total_landed_cost_usd,
                "calculated_at": r.calculated_at.isoformat() if r.calculated_at else None,
            }
            for r in records
        ]

    def _estimate_freight(self, origin_country: str, quantity: float) -> float:
        """Estimate freight cost based on origin country."""
        base_rate = DEFAULT_FREIGHT_ESTIMATES.get(
            origin_country, DEFAULT_FREIGHT_ESTIMATES["default"]
        )
        # Scale roughly by quantity (assumes ~25 tons per container)
        containers = max(1, quantity / 25)
        return base_rate * containers

    async def _lookup_duty(self, hs_code: str, origin_country: str) -> float:
        """Look up duty rate by HS code and origin country."""
        # Try country-specific rate first
        result = await self.db.execute(
            select(DutyRate)
            .where(DutyRate.hs_code == hs_code)
            .where(DutyRate.origin_country == origin_country)
            .limit(1)
        )
        rate = result.scalar_one_or_none()
        if rate:
            return rate.duty_pct

        # Fall back to general rate
        result = await self.db.execute(
            select(DutyRate)
            .where(DutyRate.hs_code == hs_code)
            .where(DutyRate.origin_country.is_(None))
            .limit(1)
        )
        rate = result.scalar_one_or_none()
        return rate.duty_pct if rate else 0
