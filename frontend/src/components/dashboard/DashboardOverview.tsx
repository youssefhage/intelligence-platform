import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { DashboardSummary, CommodityPrice, Alert } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

const statStyle: React.CSSProperties = {
  fontSize: 32,
  fontWeight: 700,
  color: "#f1f5f9",
  marginBottom: 4,
};

const labelStyle: React.CSSProperties = {
  fontSize: 13,
  color: "#94a3b8",
  textTransform: "uppercase" as const,
  letterSpacing: 1,
};

export default function DashboardOverview() {
  const summary = useApi<DashboardSummary>(
    () => api.getDashboardSummary() as Promise<DashboardSummary>
  );
  const prices = useApi<CommodityPrice[]>(
    () => api.getLatestPrices() as Promise<CommodityPrice[]>
  );
  const alerts = useApi<Alert[]>(
    () => api.getAlerts(5) as Promise<Alert[]>
  );

  if (summary.loading) return <div style={{ color: "#94a3b8" }}>Loading dashboard...</div>;

  const s = summary.data;

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9", marginBottom: 24 }}>
        Market Intelligence Dashboard
      </h2>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
        <div style={cardStyle}>
          <div style={labelStyle}>Commodities Tracked</div>
          <div style={statStyle}>{s?.total_commodities_tracked ?? 0}</div>
        </div>
        <div style={cardStyle}>
          <div style={labelStyle}>Active Products</div>
          <div style={statStyle}>{s?.total_products ?? 0}</div>
        </div>
        <div style={cardStyle}>
          <div style={labelStyle}>Supply Risk Score</div>
          <div style={{ ...statStyle, color: (s?.overall_supply_risk_score ?? 0) > 50 ? "#ef4444" : "#22c55e" }}>
            {s?.overall_supply_risk_score ?? 0}
          </div>
        </div>
        <div style={cardStyle}>
          <div style={labelStyle}>Active Alerts</div>
          <div style={{ ...statStyle, color: (s?.active_alerts ?? 0) > 0 ? "#f59e0b" : "#22c55e" }}>
            {s?.active_alerts ?? 0}
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 24 }}>
        {/* Commodity Prices */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Commodity Prices
          </h3>
          {prices.loading ? (
            <div style={{ color: "#94a3b8" }}>Loading prices...</div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #334155" }}>
                  <th style={{ textAlign: "left", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                    Commodity
                  </th>
                  <th style={{ textAlign: "right", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                    Price (USD)
                  </th>
                  <th style={{ textAlign: "right", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                    7d Change
                  </th>
                  <th style={{ textAlign: "left", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                    Category
                  </th>
                </tr>
              </thead>
              <tbody>
                {prices.data?.map((p) => (
                  <tr key={p.commodity_id} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td style={{ padding: "10px 12px", color: "#e2e8f0", fontSize: 14 }}>
                      {p.commodity_name}
                    </td>
                    <td style={{ padding: "10px 12px", textAlign: "right", color: "#f1f5f9", fontSize: 14 }}>
                      {p.current_price_usd != null
                        ? `$${p.current_price_usd.toLocaleString()}`
                        : "-"}
                    </td>
                    <td
                      style={{
                        padding: "10px 12px",
                        textAlign: "right",
                        fontSize: 14,
                        color:
                          p.week_change_pct == null
                            ? "#94a3b8"
                            : p.week_change_pct > 0
                              ? "#ef4444"
                              : "#22c55e",
                      }}
                    >
                      {p.week_change_pct != null ? `${p.week_change_pct > 0 ? "+" : ""}${p.week_change_pct}%` : "-"}
                    </td>
                    <td style={{ padding: "10px 12px", color: "#94a3b8", fontSize: 13 }}>
                      <span
                        style={{
                          background: "#334155",
                          padding: "2px 8px",
                          borderRadius: 4,
                          fontSize: 12,
                        }}
                      >
                        {p.category}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Recent Alerts */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Recent Alerts
          </h3>
          {alerts.loading ? (
            <div style={{ color: "#94a3b8" }}>Loading alerts...</div>
          ) : alerts.data?.length === 0 ? (
            <div style={{ color: "#94a3b8", fontSize: 14 }}>No active alerts</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {alerts.data?.map((a) => (
                <div
                  key={a.id}
                  style={{
                    padding: 12,
                    borderRadius: 8,
                    background: "#0f172a",
                    borderLeft: `3px solid ${
                      a.severity === "critical"
                        ? "#ef4444"
                        : a.severity === "warning"
                          ? "#f59e0b"
                          : "#3b82f6"
                    }`,
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0", marginBottom: 4 }}>
                    {a.title}
                  </div>
                  <div style={{ fontSize: 12, color: "#94a3b8" }}>
                    {a.message.slice(0, 120)}{a.message.length > 120 ? "..." : ""}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
