import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../services/api";
import type { MarginAnalysis } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

const btnStyle: React.CSSProperties = {
  background: "#3b82f6",
  color: "white",
  border: "none",
  borderRadius: 8,
  padding: "10px 20px",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};

export default function MarginPanel() {
  const [analysis, setAnalysis] = useState<MarginAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const data = (await api.getMarginAnalysis()) as MarginAnalysis;
      setAnalysis(data);
    } catch {
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "negative": return "#ef4444";
      case "critical": return "#f59e0b";
      case "warning": return "#eab308";
      default: return "#22c55e";
    }
  };

  // Build bar chart data from eroding + negative products
  const chartData = analysis
    ? [...(analysis.negative_margin_products || []), ...(analysis.eroding_margin_products || [])]
        .slice(0, 15)
        .map((p) => ({
          name: p.product_name.length > 20 ? p.product_name.slice(0, 20) + "..." : p.product_name,
          margin: p.current_margin_pct,
          status: p.status,
        }))
    : [];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9" }}>
          Margin Analysis
        </h2>
        <button onClick={runAnalysis} disabled={loading} style={btnStyle}>
          {loading ? "Analyzing..." : "Run Margin Analysis"}
        </button>
      </div>

      {!analysis ? (
        <div style={cardStyle}>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>
            Click "Run Margin Analysis" to scan all products for margin erosion and pricing opportunities.
          </p>
        </div>
      ) : (
        <div>
          {/* KPI Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
            {[
              { label: "Products Analyzed", value: analysis.total_products_analyzed, color: "#f1f5f9" },
              { label: "Negative Margin", value: analysis.negative_margin_count, color: "#ef4444" },
              { label: "Eroding Margin", value: analysis.eroding_margin_count, color: "#f59e0b" },
              { label: "Opportunities", value: analysis.opportunities_count, color: "#22c55e" },
            ].map((kpi) => (
              <div key={kpi.label} style={cardStyle}>
                <div style={{ fontSize: 12, color: "#64748b" }}>{kpi.label}</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: kpi.color }}>{kpi.value}</div>
              </div>
            ))}
          </div>

          {/* Margin Bar Chart */}
          {chartData.length > 0 && (
            <div style={{ ...cardStyle, marginBottom: 24 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
                Products with Low Margins
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 120, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                  <YAxis dataKey="name" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} width={120} />
                  <Tooltip
                    contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                    formatter={(value: number) => [`${value}%`, "Margin"]}
                  />
                  <Bar dataKey="margin" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={index} fill={statusColor(entry.status)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Pricing Opportunities */}
          {analysis.pricing_opportunities.length > 0 && (
            <div style={cardStyle}>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: "#22c55e", marginBottom: 16 }}>
                Pricing Opportunities
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {analysis.pricing_opportunities.slice(0, 10).map((p) => (
                  <div
                    key={p.product_id}
                    style={{
                      padding: "14px 16px",
                      background: "#0f172a",
                      borderRadius: 8,
                      borderLeft: "3px solid #22c55e",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9" }}>
                        {p.product_name}
                      </div>
                      <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
                        Current: ${p.current_sell_usd} | Margin: {p.current_margin_pct}%
                        {p.margin_trend !== "stable" && ` | Trend: ${p.margin_trend}`}
                      </div>
                    </div>
                    {p.opportunity && (
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: 14, fontWeight: 600, color: "#22c55e" }}>
                          Suggest: ${p.opportunity.suggested_sell}
                        </div>
                        <div style={{ fontSize: 11, color: "#64748b" }}>
                          +${p.opportunity.monthly_revenue_impact}/mo
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
