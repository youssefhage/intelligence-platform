"""Alert threshold configuration model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class AlertThreshold(Base):
    __tablename__ = "alert_thresholds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commodity_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=True, index=True
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_channels: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
