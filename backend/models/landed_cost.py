"""Models for landed cost calculations and duty rates."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class LandedCostCalculation(Base):
    __tablename__ = "landed_cost_calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commodity_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=True, index=True
    )
    commodity_name: Mapped[str] = mapped_column(String(200), nullable=False)
    origin_country: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    incoterm: Mapped[str] = mapped_column(String(10), nullable=False, default="FOB")
    fob_price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    freight_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    insurance_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    insurance_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    cif_price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    duty_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    duty_usd: Mapped[float] = mapped_column(Float, nullable=False)
    port_charges_usd: Mapped[float] = mapped_column(Float, nullable=False)
    inland_transport_usd: Mapped[float] = mapped_column(Float, nullable=False)
    total_landed_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class DutyRate(Base):
    __tablename__ = "duty_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hs_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duty_pct: Mapped[float] = mapped_column(Float, nullable=False)
    origin_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
