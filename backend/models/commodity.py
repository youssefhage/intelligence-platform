import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class CommodityCategory(str, enum.Enum):
    GRAIN = "grain"
    OIL = "oil"
    DAIRY = "dairy"
    SUGAR = "sugar"
    FUEL = "fuel"
    PACKAGING = "packaging"
    BEVERAGE = "beverage"
    CLEANING = "cleaning"
    SHIPPING = "shipping"
    CURRENCY = "currency"
    OTHER = "other"


class Commodity(Base):
    __tablename__ = "commodities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[CommodityCategory] = mapped_column(
        Enum(CommodityCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # kg, liter, ton, barrel
    origin_countries: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list of countries
    sourcing_regions: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list of regions
    description: Mapped[str] = mapped_column(Text, nullable=True)
    global_benchmark_symbol: Mapped[str] = mapped_column(
        String(50), nullable=True
    )  # e.g., CBOT wheat, Brent crude
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    prices: Mapped[list["CommodityPrice"]] = relationship(back_populates="commodity")


class CommodityPrice(Base):
    __tablename__ = "commodity_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=False, index=True
    )
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    price_lbp: Mapped[float] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(200), nullable=False)  # API, manual, scrape
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    commodity: Mapped["Commodity"] = relationship(back_populates="prices")
