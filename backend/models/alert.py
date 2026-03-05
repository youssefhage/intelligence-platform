import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, enum.Enum):
    PRICE_SPIKE = "price_spike"
    SUPPLY_DISRUPTION = "supply_disruption"
    MARGIN_EROSION = "margin_erosion"
    INVENTORY_LOW = "inventory_low"
    CURRENCY_SHIFT = "currency_shift"
    GEOPOLITICAL = "geopolitical"
    SOURCING_OPPORTUNITY = "sourcing_opportunity"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), nullable=False, index=True)
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity_type: Mapped[str] = mapped_column(
        String(50), nullable=True
    )  # commodity, product, supplier
    related_entity_id: Mapped[int] = mapped_column(Integer, nullable=True)
    action_recommended: Mapped[str] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
