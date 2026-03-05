"""Pydantic schemas for API request/response models."""

from datetime import datetime

from pydantic import BaseModel


# --- Commodity Schemas ---
class CommodityBase(BaseModel):
    name: str
    category: str
    unit: str
    origin_countries: str | None = None
    sourcing_regions: str | None = None
    description: str | None = None
    global_benchmark_symbol: str | None = None


class CommodityCreate(CommodityBase):
    pass


class CommodityResponse(CommodityBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CommodityPriceRecord(BaseModel):
    commodity_id: int
    price_usd: float
    source: str = "manual"
    recorded_at: datetime | None = None
    notes: str | None = None


class CommodityPriceResponse(BaseModel):
    commodity_id: int
    commodity_name: str
    category: str
    unit: str
    current_price_usd: float | None
    current_price_lbp: float | None
    week_change_pct: float | None
    last_updated: str | None


# --- Product Schemas ---
class ProductResponse(BaseModel):
    id: int
    erp_product_id: str | None
    name: str
    sku: str | None
    category: str | None
    brand: str | None
    current_cost_usd: float | None
    current_sell_price_usd: float | None
    margin_percent: float | None

    model_config = {"from_attributes": True}


# --- Supplier Schemas ---
class SupplierCreate(BaseModel):
    name: str
    country: str
    region: str | None = None
    commodities_supplied: str | None = None
    lead_time_days: int | None = None
    payment_terms: str | None = None
    shipping_route: str | None = None
    reliability_score: float | None = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    country: str
    region: str | None
    current_risk_level: str
    reliability_score: float | None
    lead_time_days: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class RiskAssessmentResponse(BaseModel):
    id: int
    supplier_id: int
    risk_level: str
    risk_factors: str
    geopolitical_risk: float | None
    logistics_risk: float | None
    financial_risk: float | None
    currency_risk: float | None
    recommendations: str | None
    assessed_at: datetime

    model_config = {"from_attributes": True}


# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    related_entity_type: str | None
    related_entity_id: int | None
    action_recommended: str | None
    is_read: bool
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Insight Schemas ---
class InsightResponse(BaseModel):
    id: int
    category: str
    title: str
    summary: str
    detailed_analysis: str
    recommended_actions: str | None
    confidence_score: float | None
    generated_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Forecast Schemas ---
class ForecastRequest(BaseModel):
    commodity_id: int
    horizon_days: int = 30


# --- Dashboard Schemas ---
class DashboardSummary(BaseModel):
    total_commodities_tracked: int
    total_products: int
    total_suppliers: int
    active_alerts: int
    overall_supply_risk_score: float
    commodities_with_price_increase: int
    low_stock_items: int
