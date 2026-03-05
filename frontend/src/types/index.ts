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
