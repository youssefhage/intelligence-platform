import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { Supplier, SupplyChainOverview } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

const riskColors: Record<string, string> = {
  low: "#22c55e",
  medium: "#f59e0b",
  high: "#ef4444",
  critical: "#dc2626",
};

export default function SupplyChainPanel() {
  const overview = useApi<SupplyChainOverview>(
    () => api.getSupplyChainOverview() as Promise<SupplyChainOverview>
  );
  const suppliers = useApi<Supplier[]>(
    () => api.getSuppliers() as Promise<Supplier[]>
  );

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9", marginBottom: 24 }}>
        Supply Chain Risk Monitor
      </h2>

      {/* Risk Overview */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>
            Total Suppliers
          </div>
          <div style={{ fontSize: 32, fontWeight: 700, color: "#f1f5f9" }}>
            {overview.data?.total_suppliers ?? 0}
          </div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>
            Overall Risk Score
          </div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 700,
              color: (overview.data?.overall_risk_score ?? 0) > 50 ? "#ef4444" : "#22c55e",
            }}
          >
            {overview.data?.overall_risk_score ?? 0}
          </div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>
            High Risk Suppliers
          </div>
          <div style={{ fontSize: 32, fontWeight: 700, color: "#ef4444" }}>
            {overview.data?.high_risk_suppliers?.length ?? 0}
          </div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>
            Risk Distribution
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            {overview.data?.risk_distribution &&
              Object.entries(overview.data.risk_distribution).map(([level, count]) => (
                <span
                  key={level}
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: riskColors[level] + "22",
                    color: riskColors[level],
                    fontWeight: 600,
                  }}
                >
                  {level}: {count as number}
                </span>
              ))}
          </div>
        </div>
      </div>

      {/* Supplier Table */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
          Suppliers
        </h3>
        {suppliers.loading ? (
          <div style={{ color: "#94a3b8" }}>Loading suppliers...</div>
        ) : suppliers.data?.length === 0 ? (
          <p style={{ color: "#94a3b8", fontSize: 14 }}>No suppliers configured yet.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #334155" }}>
                <th style={{ textAlign: "left", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                  Supplier
                </th>
                <th style={{ textAlign: "left", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                  Country
                </th>
                <th style={{ textAlign: "center", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                  Risk Level
                </th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                  Reliability
                </th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                  Lead Time
                </th>
                <th style={{ textAlign: "center", padding: "8px 12px", color: "#94a3b8", fontSize: 12 }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {suppliers.data?.map((s) => (
                <tr key={s.id} style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "10px 12px", color: "#e2e8f0", fontSize: 14 }}>
                    {s.name}
                  </td>
                  <td style={{ padding: "10px 12px", color: "#94a3b8", fontSize: 14 }}>
                    {s.country}
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "center" }}>
                    <span
                      style={{
                        fontSize: 12,
                        padding: "3px 10px",
                        borderRadius: 12,
                        background: (riskColors[s.current_risk_level] || "#64748b") + "22",
                        color: riskColors[s.current_risk_level] || "#64748b",
                        fontWeight: 600,
                      }}
                    >
                      {s.current_risk_level}
                    </span>
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "right", color: "#f1f5f9", fontSize: 14 }}>
                    {s.reliability_score != null ? `${s.reliability_score}%` : "-"}
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "right", color: "#94a3b8", fontSize: 14 }}>
                    {s.lead_time_days != null ? `${s.lead_time_days}d` : "-"}
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "center" }}>
                    <button
                      onClick={async () => {
                        await api.assessRisk(s.id);
                        suppliers.reload();
                        overview.reload();
                      }}
                      style={{
                        padding: "4px 12px",
                        border: "1px solid #334155",
                        borderRadius: 6,
                        background: "transparent",
                        color: "#3b82f6",
                        cursor: "pointer",
                        fontSize: 12,
                      }}
                    >
                      Assess Risk
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* High Risk Suppliers */}
      {overview.data?.high_risk_suppliers && overview.data.high_risk_suppliers.length > 0 && (
        <div style={{ ...cardStyle, marginTop: 24, borderColor: "#ef444444" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#ef4444", marginBottom: 16 }}>
            High Risk Suppliers Requiring Attention
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {overview.data.high_risk_suppliers.map((s) => (
              <div
                key={s.id}
                style={{
                  padding: 16,
                  background: "#0f172a",
                  borderRadius: 8,
                  borderLeft: `3px solid ${riskColors[s.risk_level]}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, color: "#f1f5f9" }}>{s.name}</span>
                  <span style={{ color: riskColors[s.risk_level], fontSize: 13, fontWeight: 600 }}>
                    {s.risk_level.toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: 13, color: "#94a3b8" }}>
                  {s.country} | Commodities: {s.commodities.join(", ") || "N/A"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
