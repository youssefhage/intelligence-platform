import { useState } from "react";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { CommodityPrice, ForecastData } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

export default function CommodityPanel() {
  const prices = useApi<CommodityPrice[]>(
    () => api.getLatestPrices() as Promise<CommodityPrice[]>
  );
  const [selectedCommodity, setSelectedCommodity] = useState<number | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [loadingForecast, setLoadingForecast] = useState(false);

  const handleSelectCommodity = async (id: number) => {
    setSelectedCommodity(id);
    setLoadingForecast(true);
    try {
      const data = (await api.getForecast(id, 30)) as ForecastData;
      setForecast(data);
    } catch {
      setForecast(null);
    } finally {
      setLoadingForecast(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9", marginBottom: 24 }}>
        Commodity Tracking
      </h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        {/* Commodity List */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Tracked Commodities
          </h3>
          {prices.loading ? (
            <div style={{ color: "#94a3b8" }}>Loading...</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {prices.data?.map((p) => (
                <div
                  key={p.commodity_id}
                  onClick={() => handleSelectCommodity(p.commodity_id)}
                  style={{
                    padding: "14px 16px",
                    borderRadius: 8,
                    background:
                      selectedCommodity === p.commodity_id ? "#334155" : "#0f172a",
                    cursor: "pointer",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    transition: "background 0.15s",
                  }}
                >
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9" }}>
                      {p.commodity_name}
                    </div>
                    <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
                      {p.category} / {p.unit}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 15, fontWeight: 600, color: "#f1f5f9" }}>
                      {p.current_price_usd != null
                        ? `$${p.current_price_usd.toLocaleString()}`
                        : "N/A"}
                    </div>
                    {p.week_change_pct != null && (
                      <div
                        style={{
                          fontSize: 12,
                          color: p.week_change_pct > 0 ? "#ef4444" : "#22c55e",
                        }}
                      >
                        {p.week_change_pct > 0 ? "+" : ""}
                        {p.week_change_pct}%
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Forecast Panel */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Price Forecast
          </h3>
          {!selectedCommodity ? (
            <p style={{ color: "#94a3b8", fontSize: 14 }}>
              Select a commodity to view its price forecast.
            </p>
          ) : loadingForecast ? (
            <div style={{ color: "#94a3b8" }}>Generating forecast...</div>
          ) : forecast ? (
            <div>
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 14, color: "#94a3b8", marginBottom: 4 }}>
                  {forecast.commodity}
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 16,
                    marginBottom: 16,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 12, color: "#64748b" }}>Current Price</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: "#f1f5f9" }}>
                      ${forecast.current_price_usd}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: "#64748b" }}>
                      Forecast ({forecast.forecast_horizon_days}d)
                    </div>
                    <div
                      style={{
                        fontSize: 20,
                        fontWeight: 700,
                        color:
                          forecast.expected_change_pct > 0 ? "#ef4444" : "#22c55e",
                      }}
                    >
                      ${forecast.forecast_end_price_usd}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    padding: "12px 16px",
                    background: "#0f172a",
                    borderRadius: 8,
                    display: "flex",
                    justifyContent: "space-between",
                  }}
                >
                  <span style={{ fontSize: 13, color: "#94a3b8" }}>Expected Change</span>
                  <span
                    style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color:
                        forecast.expected_change_pct > 0 ? "#ef4444" : "#22c55e",
                    }}
                  >
                    {forecast.expected_change_pct > 0 ? "+" : ""}
                    {forecast.expected_change_pct}%
                  </span>
                </div>
              </div>

              <div style={{ fontSize: 12, color: "#64748b" }}>
                Method: {forecast.method} | Data points: {forecast.data_points_used}
              </div>

              {/* Forecast table */}
              {forecast.forecast_data.length > 0 && (
                <div style={{ marginTop: 16, maxHeight: 300, overflowY: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid #334155" }}>
                        <th style={{ textAlign: "left", padding: 6, color: "#64748b" }}>Date</th>
                        <th style={{ textAlign: "right", padding: 6, color: "#64748b" }}>Predicted</th>
                        <th style={{ textAlign: "right", padding: 6, color: "#64748b" }}>Range</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.forecast_data.slice(0, 10).map((f, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid #1e293b" }}>
                          <td style={{ padding: 6, color: "#94a3b8" }}>
                            {new Date(f.date).toLocaleDateString()}
                          </td>
                          <td style={{ padding: 6, textAlign: "right", color: "#f1f5f9" }}>
                            ${f.predicted}
                          </td>
                          <td style={{ padding: 6, textAlign: "right", color: "#64748b" }}>
                            ${f.lower_bound} - ${f.upper_bound}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: "#94a3b8", fontSize: 14 }}>
              Insufficient data for forecast.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
