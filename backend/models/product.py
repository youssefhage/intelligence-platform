from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    erp_product_id: Mapped[str] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    category: Mapped[str] = mapped_column(String(200), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(200), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    current_cost_usd: Mapped[float] = mapped_column(Float, nullable=True)
    current_sell_price_usd: Mapped[float] = mapped_column(Float, nullable=True)
    margin_percent: Mapped[float] = mapped_column(Float, nullable=True)
    primary_commodity: Mapped[str] = mapped_column(
        String(200), nullable=True
    )  # linked commodity name
    supplier_name: Mapped[str] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    price_history: Mapped[list["ProductPriceHistory"]] = relationship(back_populates="product")


class ProductPriceHistory(Base):
    __tablename__ = "product_price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    sell_price_usd: Mapped[float] = mapped_column(Float, nullable=True)
    margin_percent: Mapped[float] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # erp_sync, manual
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="price_history")
