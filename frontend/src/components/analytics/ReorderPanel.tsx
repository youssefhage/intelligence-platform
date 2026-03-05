import { useState } from "react";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { ReorderSuggestion, PortStatus } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

export default function ReorderPanel() {
  const suggestions = useApi<ReorderSuggestion[]>(
    () => api.getReorderSuggestions() as Promise<ReorderSuggestion[]>
  );
  const ports = useApi<{ ports: PortStatus[] }>(
    () => api.getPortStatus() as Promise<{ ports: PortStatus[] }>
  );

  const urgencyColor = (urgency: string) => {
    switch (urgency) {
      case "critical": return "#ef4444";
      case "urgent": return "#f59e0b";
      default: return "#3b82f6";
    }
  };

  const congestionColor = (level: string) => {
    switch (level) {
      case "severe": return "#ef4444";
      case "high": return "#f59e0b";
      case "medium": return "#eab308";
      default: return "#22c55e";
    }
  };

  const totalCost = (suggestions.data || []).reduce((s, r) => s + r.estimated_cost_usd, 0);
  const criticalCount = (suggestions.data || []).filter((r) => r.urgency === "critical").length;

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9", marginBottom: 24 }}>
        Reorder & Logistics
      </h2>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#64748b" }}>Items to Reorder</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#f1f5f9" }}>
            {suggestions.data?.length || 0}
          </div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#64748b" }}>Critical</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#ef4444" }}>{criticalCount}</div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#64748b" }}>Est. Order Cost</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#f1f5f9" }}>
            ${totalCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 12, color: "#64748b" }}>Ports Monitored</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#f1f5f9" }}>
            {ports.data?.ports?.length || 0}
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 24 }}>
        {/* Reorder Suggestions Table */}
        <div style={cardStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9" }}>
              Auto-Reorder Suggestions
            </h3>
            <button
              onClick={() => suggestions.reload()}
              style={{
                background: "#334155",
                color: "#f1f5f9",
                border: "none",
                borderRadius: 6,
                padding: "6px 14px",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Refresh
            </button>
          </div>

          {suggestions.loading ? (
            <div style={{ color: "#94a3b8" }}>Calculating...</div>
          ) : !suggestions.data?.length ? (
            <p style={{ color: "#94a3b8", fontSize: 14 }}>
              All products have adequate stock levels.
            </p>
          ) : (
            <div style={{ maxHeight: 500, overflowY: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #334155" }}>
                    <th style={{ textAlign: "left", padding: 8, color: "#64748b", fontSize: 11 }}>Product</th>
                    <th style={{ textAlign: "right", padding: 8, color: "#64748b", fontSize: 11 }}>Stock</th>
                    <th style={{ textAlign: "right", padding: 8, color: "#64748b", fontSize: 11 }}>Days Left</th>
                    <th style={{ textAlign: "right", padding: 8, color: "#64748b", fontSize: 11 }}>Order Qty</th>
                    <th style={{ textAlign: "right", padding: 8, color: "#64748b", fontSize: 11 }}>Est. Cost</th>
                    <th style={{ textAlign: "center", padding: 8, color: "#64748b", fontSize: 11 }}>Urgency</th>
                  </tr>
                </thead>
                <tbody>
                  {suggestions.data.map((s) => (
                    <tr key={s.product_id} style={{ borderBottom: "1px solid #1e293b" }}>
                      <td style={{ padding: 8 }}>
                        <div style={{ color: "#f1f5f9", fontWeight: 500 }}>{s.product_name}</div>
                        <div style={{ fontSize: 11, color: "#64748b" }}>{s.supplier || "—"}</div>
                      </td>
                      <td style={{ padding: 8, textAlign: "right", color: "#f1f5f9" }}>
                        {s.current_stock.toLocaleString()}
                      </td>
                      <td
                        style={{
                          padding: 8,
                          textAlign: "right",
                          color: s.days_of_stock <= 3 ? "#ef4444" : s.days_of_stock <= 7 ? "#f59e0b" : "#f1f5f9",
                          fontWeight: 600,
                        }}
                      >
                        {s.days_of_stock}
                      </td>
                      <td style={{ padding: 8, textAlign: "right", color: "#f1f5f9" }}>
                        {s.suggested_order_qty.toLocaleString()}
                      </td>
                      <td style={{ padding: 8, textAlign: "right", color: "#f1f5f9" }}>
                        ${s.estimated_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </td>
                      <td style={{ padding: 8, textAlign: "center" }}>
                        <span
                          style={{
                            padding: "3px 10px",
                            borderRadius: 12,
                            fontSize: 11,
                            fontWeight: 600,
                            color: "white",
                            background: urgencyColor(s.urgency),
                          }}
                        >
                          {s.urgency}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Port Status */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Port Status
          </h3>
          {ports.loading ? (
            <div style={{ color: "#94a3b8" }}>Loading...</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {ports.data?.ports?.map((port) => (
                <div
                  key={port.port_name}
                  style={{
                    padding: 16,
                    background: "#0f172a",
                    borderRadius: 8,
                    borderLeft: `3px solid ${congestionColor(port.congestion_level)}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9" }}>
                      {port.port_name}
                    </span>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: 10,
                        fontSize: 11,
                        background: congestionColor(port.congestion_level),
                        color: "white",
                        fontWeight: 600,
                      }}
                    >
                      {port.congestion_level}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: "#94a3b8" }}>
                    Status: {port.status} | Wait: {port.avg_wait_days} days
                  </div>
                  <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>
                    {port.notes}
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
