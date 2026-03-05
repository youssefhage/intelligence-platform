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
