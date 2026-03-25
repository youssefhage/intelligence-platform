const API_BASE = "/api";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function postJSON<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function putJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "PUT" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchJSON("/dashboard/summary"),
  getAlerts: (limit = 50) => fetchJSON(`/dashboard/alerts?limit=${limit}`),
  markAlertRead: (id: number) => putJSON(`/dashboard/alerts/${id}/read`),
  resolveAlert: (id: number) => putJSON(`/dashboard/alerts/${id}/resolve`),

  // Commodities
  getCommodities: () => fetchJSON("/commodities/"),
  getLatestPrices: () => fetchJSON("/commodities/prices/latest"),
  getPriceHistory: (id: number, days = 90) =>
    fetchJSON(`/commodities/${id}/history?days=${days}`),
  getForecast: (id: number, days = 30) =>
    fetchJSON(`/commodities/${id}/forecast?horizon_days=${days}`),
  getAnomalies: (id: number) => fetchJSON(`/commodities/${id}/anomalies`),
  initializeCommodities: () => postJSON("/commodities/initialize"),

  // Suppliers
  getSuppliers: () => fetchJSON("/suppliers/"),
  assessRisk: (id: number) => postJSON(`/suppliers/${id}/assess-risk`),
  getSupplyChainOverview: () => fetchJSON("/suppliers/supply-chain/overview"),
  findAlternatives: (commodity: string, excludeCountries?: string) =>
    fetchJSON(
      `/suppliers/alternatives/${commodity}${excludeCountries ? `?exclude_countries=${excludeCountries}` : ""}`
    ),

  // Intelligence
  getInsights: (limit = 20) => fetchJSON(`/intelligence/insights?limit=${limit}`),
  analyzeMarket: () => postJSON("/intelligence/analyze-market"),
  getDailyBriefing: () => postJSON("/intelligence/daily-briefing"),
  analyzePricing: (productId: number) =>
    postJSON(`/intelligence/pricing-analysis/${productId}`),

  // Sync
  syncERPProducts: () => postJSON("/sync/erp/products"),
  syncERPInventory: () => postJSON("/sync/erp/inventory"),
  syncPOSSales: () => postJSON("/sync/pos/sales"),
  getTopSelling: (days = 7) => fetchJSON(`/sync/pos/top-selling?days=${days}`),
  getLowStock: () => fetchJSON("/sync/erp/low-stock"),

  // Analytics — Margin
  getMarginAnalysis: () => fetchJSON("/analytics/margin/analysis"),

  // Analytics — Demand
  getDemandForecast: (productId: number, days = 30) =>
    fetchJSON(`/analytics/demand/product/${productId}?horizon_days=${days}`),
  getCategoryDemand: (category: string, days = 30) =>
    fetchJSON(`/analytics/demand/category/${category}?horizon_days=${days}`),

  // Analytics — Competitors
  recordCompetitorPrice: (data: unknown) =>
    postJSON("/analytics/competitors/prices", data),
  recordBulkCompetitorPrices: (data: unknown) =>
    postJSON("/analytics/competitors/prices/bulk", data),
  getCompetitivePosition: (productId?: number) =>
    fetchJSON(`/analytics/competitors/position${productId ? `?product_id=${productId}` : ""}`),

  // Analytics — Scenarios
  runScenario: (scenarioType: string, parameters: Record<string, unknown>) =>
    postJSON("/analytics/scenarios/run", { scenario_type: scenarioType, parameters }),
  getScenarioTypes: () => fetchJSON("/analytics/scenarios/types"),

  // Analytics — Currency
  getCurrencyRates: () => fetchJSON("/analytics/currency/rates"),

  // Analytics — Ports
  getPortStatus: () => fetchJSON("/analytics/ports/status"),
  getShippingRoutes: () => fetchJSON("/analytics/ports/routes"),
  getImportTimeline: (origin: string, commodity: string) =>
    fetchJSON(`/analytics/ports/timeline?origin_region=${encodeURIComponent(origin)}&commodity_name=${encodeURIComponent(commodity)}`),

  // Analytics — Reorder
  getReorderSuggestions: () => fetchJSON("/analytics/reorder/suggestions"),

  // Notifications
  getNotificationChannels: () => fetchJSON("/notifications/channels"),
  sendTestNotification: (channels: string[], message: string) =>
    postJSON("/notifications/test", { channels, message }),
  sendDailyDigest: (channels?: string[]) =>
    postJSON("/notifications/daily-digest", channels ? { channels } : undefined),

  // Morning Brief
  getMorningBrief: () => fetchJSON("/commodities/morning-brief"),

  // Commodity Detail
  getCommodityDetail: (id: number, range = "1Y") =>
    fetchJSON(`/commodities/${id}/detail?range=${range}`),
  getCommodityAISummary: (id: number) =>
    fetchJSON(`/commodities/${id}/ai-summary`),

  // Landed Cost
  calculateLandedCost: (data: unknown) =>
    postJSON("/landed-cost/calculate", data),
  getLandedCostHistory: (limit = 50) =>
    fetchJSON(`/landed-cost/history?limit=${limit}`),
  getDutyRates: () => fetchJSON("/landed-cost/duty-rates"),
  createDutyRate: (data: unknown) =>
    postJSON("/landed-cost/duty-rates", data),

  // News
  getNewsFeed: (limit = 30, commodity?: string) =>
    fetchJSON(`/news/feed?limit=${limit}${commodity ? `&commodity=${encodeURIComponent(commodity)}` : ""}`),
  fetchNews: () => postJSON("/news/fetch"),
  getGeopoliticalScenarios: () => fetchJSON("/news/geopolitical/scenarios"),
  runGeopoliticalScenario: (id: string) =>
    fetchJSON(`/news/geopolitical/scenario/${id}`),
  getSupplyRoutes: () => fetchJSON("/news/geopolitical/supply-routes"),

  // Reports
  getWeeklyReport: () => fetchJSON("/reports/weekly"),

  // Alert Thresholds
  getAlertThresholds: () => fetchJSON("/dashboard/alert-thresholds"),
  createAlertThreshold: (data: unknown) =>
    postJSON("/dashboard/alert-thresholds", data),
};
