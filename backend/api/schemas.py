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


# --- Morning Brief Schemas ---
class MorningBriefCommodity(BaseModel):
    commodity_id: int
    commodity_name: str
    category: str
    unit: str
    current_price_usd: float | None
    week_change_pct: float | None
    month_change_pct: float | None
    trend_90d: str  # "up", "down", "flat"
    ma_90d: float | None
    signal: str  # "BUY", "HOLD", "WAIT"
    sparkline: list[float]
    alert_flag: bool
    last_updated: str | None


class MorningBriefCurrency(BaseModel):
    pair: str
    rate: float
    day_change_pct: float | None
    week_change_pct: float | None
    trend: str  # "up", "down", "flat"
    last_updated: str | None = None


class MorningBriefResponse(BaseModel):
    generated_at: str
    alert_banner: list[MorningBriefCommodity]
    commodities: list[MorningBriefCommodity]
    currencies: list[MorningBriefCurrency | dict]
    shipping: list[MorningBriefCommodity | dict]


# --- Commodity Detail Schemas ---
class CommodityDetailResponse(BaseModel):
    commodity_id: int
    commodity_name: str
    category: str
    price_history: list[dict]
    ma_30: list[float | None]
    ma_90: list[float | None]
    volatility_current: float | None
    volatility_level: str  # "high", "medium", "low"
    price_context: dict
    correlations: list[dict]


# --- Landed Cost Schemas ---
class LandedCostRequest(BaseModel):
    commodity_name: str
    commodity_id: int | None = None
    origin_country: str
    quantity: float = 1.0
    unit: str = "ton"
    incoterm: str = "FOB"
    fob_price_usd: float
    freight_cost_usd: float | None = None
    insurance_pct: float = 0.5
    duty_pct: float = 0.0
    hs_code: str | None = None
    port_charges_usd: float | None = None
    inland_transport_usd: float | None = None


class LandedCostResponse(BaseModel):
    id: int | None = None
    commodity_name: str
    origin_country: str
    quantity: float
    unit: str
    incoterm: str
    fob_price_usd: float
    freight_cost_usd: float
    insurance_pct: float
    insurance_cost_usd: float
    cif_price_usd: float
    duty_pct: float
    duty_usd: float
    port_charges_usd: float
    inland_transport_usd: float
    total_landed_cost_usd: float
    cost_per_unit_usd: float
    calculated_at: str | None = None


class DutyRateCreate(BaseModel):
    hs_code: str
    description: str | None = None
    duty_pct: float
    origin_country: str | None = None


class DutyRateResponse(BaseModel):
    id: int
    hs_code: str
    description: str | None
    duty_pct: float
    origin_country: str | None

    model_config = {"from_attributes": True}


# --- Alert Threshold Schemas ---
class AlertThresholdCreate(BaseModel):
    commodity_id: int | None = None
    alert_type: str
    threshold_value: float
    notify_channels: str | None = None


class AlertThresholdResponse(BaseModel):
    id: int
    commodity_id: int | None
    alert_type: str
    threshold_value: float
    is_active: bool
    notify_channels: str | None

    model_config = {"from_attributes": True}


# --- News Schemas ---
class NewsArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    source: str
    published_at: str | None
    summary: str | None
    matched_commodities: str | None
    sentiment: str | None
    impact_score: float | None

    model_config = {"from_attributes": True}
