import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(200), nullable=True)
    contact_info: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    commodities_supplied: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(200), nullable=True)
    shipping_route: Mapped[str] = mapped_column(Text, nullable=True)
    current_risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel), default=RiskLevel.LOW
    )
    reliability_score: Mapped[float] = mapped_column(Float, nullable=True)  # 0-100
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    risk_assessments: Mapped[list["SupplierRiskAssessment"]] = relationship(
        back_populates="supplier"
    )


class SupplierRiskAssessment(Base):
    __tablename__ = "supplier_risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False)
    risk_factors: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of factors
    geopolitical_risk: Mapped[float] = mapped_column(Float, nullable=True)  # 0-100
    logistics_risk: Mapped[float] = mapped_column(Float, nullable=True)  # 0-100
    financial_risk: Mapped[float] = mapped_column(Float, nullable=True)  # 0-100
    currency_risk: Mapped[float] = mapped_column(Float, nullable=True)  # 0-100
    recommendations: Mapped[str] = mapped_column(Text, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    supplier: Mapped["Supplier"] = relationship(back_populates="risk_assessments")
