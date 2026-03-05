import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class InsightCategory(str, enum.Enum):
    PRICING = "pricing"
    SUPPLY_CHAIN = "supply_chain"
    SOURCING = "sourcing"
    DEMAND = "demand"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class MarketInsight(Base):
    __tablename__ = "market_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[InsightCategory] = mapped_column(
        Enum(InsightCategory), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    data_sources: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    affected_commodities: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    affected_products: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    recommended_actions: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    confidence_score: Mapped[float] = mapped_column(nullable=True)  # 0-1
    generated_by: Mapped[str] = mapped_column(
        String(100), nullable=False, default="ai_engine"
    )
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
