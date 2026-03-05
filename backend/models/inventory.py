from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    erp_product_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    quantity_on_hand: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_reserved: Mapped[float] = mapped_column(Float, default=0)
    quantity_on_order: Mapped[float] = mapped_column(Float, default=0)
    warehouse_location: Mapped[str] = mapped_column(String(200), nullable=True)
    reorder_point: Mapped[float] = mapped_column(Float, nullable=True)
    days_of_stock: Mapped[float] = mapped_column(Float, nullable=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pos_transaction_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    quantity_sold: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    total_usd: Mapped[float] = mapped_column(Float, nullable=False)
    customer_type: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # retail, wholesale, distributor
    channel: Mapped[str] = mapped_column(String(100), nullable=True)
    sold_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
