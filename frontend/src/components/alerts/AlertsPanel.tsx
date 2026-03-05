import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { Alert } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

const severityColors: Record<string, string> = {
  info: "#3b82f6",
  warning: "#f59e0b",
  critical: "#ef4444",
};

const typeLabels: Record<string, string> = {
  price_spike: "Price Spike",
  supply_disruption: "Supply Disruption",
  margin_erosion: "Margin Erosion",
  inventory_low: "Low Inventory",
  currency_shift: "Currency Shift",
  geopolitical: "Geopolitical",
  sourcing_opportunity: "Sourcing Opportunity",
};

export default function AlertsPanel() {
  const alerts = useApi<Alert[]>(() => api.getAlerts(50) as Promise<Alert[]>);

  const handleMarkRead = async (id: number) => {
    await api.markAlertRead(id);
    alerts.reload();
  };

  const handleResolve = async (id: number) => {
    await api.resolveAlert(id);
    alerts.reload();
  };

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9", marginBottom: 24 }}>
        Alerts & Notifications
      </h2>

      {alerts.loading ? (
        <div style={{ color: "#94a3b8" }}>Loading alerts...</div>
      ) : alerts.data?.length === 0 ? (
        <div style={cardStyle}>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>No active alerts. All clear.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {alerts.data?.map((alert) => (
            <div
              key={alert.id}
              style={{
                ...cardStyle,
                borderLeft: `4px solid ${severityColors[alert.severity] || "#64748b"}`,
                opacity: alert.is_read ? 0.7 : 1,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span
                    style={{
                      fontSize: 11,
                      padding: "2px 8px",
                      borderRadius: 4,
                      background: severityColors[alert.severity] + "22",
                      color: severityColors[alert.severity],
                      fontWeight: 700,
                      textTransform: "uppercase",
                    }}
                  >
                    {alert.severity}
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      padding: "2px 8px",
                      borderRadius: 4,
                      background: "#334155",
                      color: "#94a3b8",
                    }}
                  >
                    {typeLabels[alert.alert_type] || alert.alert_type}
                  </span>
                </div>
                <span style={{ fontSize: 12, color: "#64748b" }}>
                  {new Date(alert.created_at).toLocaleString()}
                </span>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 600, color: "#f1f5f9", marginBottom: 8 }}>
                {alert.title}
              </h4>
              <p style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6, marginBottom: 12 }}>
                {alert.message}
              </p>

              {alert.action_recommended && (
                <div
                  style={{
                    padding: "10px 14px",
                    background: "#0f172a",
                    borderRadius: 8,
                    fontSize: 13,
                    color: "#3b82f6",
                    marginBottom: 12,
                    borderLeft: "3px solid #3b82f6",
                  }}
                >
                  Recommended: {alert.action_recommended}
                </div>
              )}

              <div style={{ display: "flex", gap: 8 }}>
                {!alert.is_read && (
                  <button
                    onClick={() => handleMarkRead(alert.id)}
                    style={{
                      padding: "6px 14px",
                      border: "1px solid #334155",
                      borderRadius: 6,
                      background: "transparent",
                      color: "#94a3b8",
                      cursor: "pointer",
                      fontSize: 12,
                    }}
                  >
                    Mark Read
                  </button>
                )}
                <button
                  onClick={() => handleResolve(alert.id)}
                  style={{
                    padding: "6px 14px",
                    border: "none",
                    borderRadius: 6,
                    background: "#22c55e22",
                    color: "#22c55e",
                    cursor: "pointer",
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  Resolve
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
