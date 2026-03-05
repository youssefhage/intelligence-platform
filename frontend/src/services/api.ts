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
};
