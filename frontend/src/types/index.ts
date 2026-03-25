export interface DashboardSummary {
  total_commodities_tracked: number;
  total_products: number;
  total_suppliers: number;
  active_alerts: number;
  overall_supply_risk_score: number;
  commodities_with_price_increase: number;
  low_stock_items: number;
}

export interface CommodityPrice {
  commodity_id: number;
  commodity_name: string;
  category: string;
  unit: string;
  current_price_usd: number | null;
  current_price_lbp: number | null;
  week_change_pct: number | null;
  last_updated: string | null;
}

export interface Alert {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  related_entity_type: string | null;
  related_entity_id: number | null;
  action_recommended: string | null;
  is_read: boolean;
  is_resolved: boolean;
  created_at: string;
}

export interface Supplier {
  id: number;
  name: string;
  country: string;
  region: string | null;
  current_risk_level: string;
  reliability_score: number | null;
  lead_time_days: number | null;
  is_active: boolean;
}

export interface MarketInsight {
  id: number;
  category: string;
  title: string;
  summary: string;
  detailed_analysis: string;
  recommended_actions: string | null;
  confidence_score: number | null;
  generated_by: string;
  created_at: string;
}

export interface SupplyChainOverview {
  total_suppliers: number;
  risk_distribution: Record<string, number>;
  high_risk_suppliers: {
    id: number;
    name: string;
    country: string;
    risk_level: string;
    commodities: string[];
  }[];
  overall_risk_score: number;
}

export interface ForecastData {
  commodity: string;
  current_price_usd: number;
  forecast_horizon_days: number;
  forecast_end_price_usd: number;
  expected_change_pct: number;
  forecast_data: {
    date: string;
    predicted: number;
    lower_bound: number;
    upper_bound: number;
  }[];
  method: string;
  data_points_used: number;
}

export interface PriceHistoryPoint {
  date: string;
  price_usd: number;
  source: string;
}

export interface MarginAnalysis {
  total_products_analyzed: number;
  negative_margin_count: number;
  eroding_margin_count: number;
  healthy_count: number;
  opportunities_count: number;
  negative_margin_products: MarginProduct[];
  eroding_margin_products: MarginProduct[];
  pricing_opportunities: MarginProduct[];
}

export interface MarginProduct {
  product_id: number;
  product_name: string;
  category: string | null;
  sku: string | null;
  current_cost_usd: number;
  current_sell_usd: number;
  current_margin_pct: number;
  margin_trend: string;
  margin_change_30d: number;
  monthly_revenue_usd: number;
  status: string;
  opportunity: {
    current_sell: number;
    suggested_sell: number;
    increase_needed: number;
    increase_pct: number;
    monthly_revenue_impact: number;
  } | null;
}

export interface DemandForecast {
  product_id: number;
  product_name: string;
  category: string | null;
  method: string;
  horizon_days: number;
  avg_daily_forecast: number;
  avg_daily_revenue_forecast: number;
  total_period_forecast: number;
  trend_direction: string;
  forecast_data: {
    date: string;
    predicted_quantity: number;
    predicted_revenue: number;
  }[];
}

export interface ScenarioResult {
  scenario_type: string;
  parameters: Record<string, unknown>;
  modeled_at: string;
  ai_analysis?: string;
  recommendations?: string[];
  [key: string]: unknown;
}

export interface PortStatus {
  port_name: string;
  status: string;
  congestion_level: string;
  avg_wait_days: number;
  notes: string;
  checked_at: string;
}

export interface CurrencyRates {
  usd_lbp: Record<string, { rate: number; fetched_at: string }>;
  configured_rate: number;
}

export interface ReorderSuggestion {
  product_id: number;
  product_name: string;
  sku: string | null;
  category: string | null;
  supplier: string | null;
  current_stock: number;
  days_of_stock: number;
  daily_avg_sales: number;
  suggested_order_qty: number;
  estimated_cost_usd: number;
  urgency: string;
}

export interface NotificationChannels {
  channels: Record<string, { configured: boolean; [key: string]: unknown }>;
}

// --- Morning Brief ---
export interface MorningBriefCommodity {
  commodity_id: number;
  commodity_name: string;
  category: string;
  unit: string;
  current_price_usd: number | null;
  week_change_pct: number | null;
  month_change_pct: number | null;
  trend_90d: "up" | "down" | "flat";
  ma_90d: number | null;
  signal: "BUY" | "HOLD" | "WAIT";
  sparkline: number[];
  alert_flag: boolean;
  last_updated: string | null;
}

export interface MorningBriefCurrency {
  pair: string;
  rate: number;
  day_change_pct: number | null;
  week_change_pct: number | null;
  trend: "up" | "down" | "flat";
  last_updated?: string | null;
}

export interface MorningBriefResponse {
  generated_at: string;
  alert_banner: MorningBriefCommodity[];
  commodities: MorningBriefCommodity[];
  currencies: MorningBriefCurrency[];
  shipping: MorningBriefCommodity[];
}

// --- Commodity Detail ---
export interface CommodityDetail {
  commodity_id: number;
  commodity_name: string;
  category: string;
  price_history: {
    date: string;
    price_usd: number;
    ma_30: number | null;
    ma_90: number | null;
  }[];
  volatility_current: number | null;
  volatility_level: "high" | "medium" | "low";
  price_context: {
    avg_1y?: number;
    vs_1y_avg_pct?: number;
    avg_3y?: number;
    vs_3y_avg_pct?: number;
    percentile?: number;
  };
  correlations: {
    commodity_id: number;
    commodity_name: string;
    correlation: number;
    strength: "strong" | "moderate" | "weak";
  }[];
}

export interface AISummary {
  commodity_id: number;
  commodity_name: string;
  summary: string;
  current_price_usd: number;
  vs_90d_avg_pct: number;
  generated_at: string;
}

// --- Landed Cost ---
export interface LandedCostResult {
  id?: number;
  commodity_name: string;
  origin_country: string;
  quantity: number;
  unit: string;
  incoterm: string;
  fob_price_usd: number;
  freight_cost_usd: number;
  insurance_pct: number;
  insurance_cost_usd: number;
  cif_price_usd: number;
  duty_pct: number;
  duty_usd: number;
  port_charges_usd: number;
  inland_transport_usd: number;
  total_landed_cost_usd: number;
  cost_per_unit_usd: number;
  calculated_at?: string;
}

// --- News ---
export interface NewsArticle {
  id: number;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  summary: string | null;
  matched_commodities: string[];
  sentiment: string | null;
  impact_score: number | null;
}

// --- Geopolitical ---
export interface GeopoliticalScenario {
  id: string;
  name: string;
  description: string;
  affected_count: number;
}

export interface SupplyRoute {
  id: string;
  name: string;
  origin: { lat: number; lng: number; city: string };
  destination: { lat: number; lng: number; city: string };
  waypoints: string[];
  typical_days: number;
  commodities: string[];
  risk_factors: string[];
}

// --- Geopolitical Scenario Result ---
export interface CommodityImpact {
  direction: "up" | "down";
  estimated_pct: number;
  confidence: "high" | "medium" | "low";
}

export interface GeopoliticalScenarioResult {
  name: string;
  description: string;
  affected_commodities: Record<string, CommodityImpact>;
  note: string;
}

// --- Alert Threshold ---
export interface AlertThreshold {
  id: number;
  commodity_id: number | null;
  alert_type: string;
  threshold_value: number;
  is_active: boolean;
  notify_channels: string | null;
}

// --- Landed Cost History Item ---
export interface LandedCostHistoryItem {
  id: number;
  commodity_name: string;
  origin_country: string;
  quantity: number;
  fob_price_usd: number;
  total_landed_cost_usd: number;
  calculated_at: string | null;
}
