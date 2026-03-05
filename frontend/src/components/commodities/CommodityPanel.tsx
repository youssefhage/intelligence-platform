import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { CommodityPrice, ForecastData, PriceHistoryPoint } from "../../types";

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
  const [history, setHistory] = useState<PriceHistoryPoint[]>([]);
  const [loadingForecast, setLoadingForecast] = useState(false);

  const handleSelectCommodity = async (id: number) => {
    setSelectedCommodity(id);
    setLoadingForecast(true);
    try {
      const [forecastData, historyData] = await Promise.all([
        api.getForecast(id, 30) as Promise<ForecastData>,
        api.getPriceHistory(id, 90) as Promise<PriceHistoryPoint[]>,
      ]);
      setForecast(forecastData);
      setHistory(Array.isArray(historyData) ? historyData : []);
    } catch {
      setForecast(null);
      setHistory([]);
    } finally {
      setLoadingForecast(false);
    }
  };

  // Build chart data combining history + forecast
  const chartData = buildChartData(history, forecast);

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9", marginBottom: 24 }}>
        Commodity Tracking
      </h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: 24 }}>
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

        {/* Chart + Forecast Panel */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Price Trend & Forecast
          </h3>
          {!selectedCommodity ? (
            <p style={{ color: "#94a3b8", fontSize: 14 }}>
              Select a commodity to view price chart and forecast.
            </p>
          ) : loadingForecast ? (
            <div style={{ color: "#94a3b8" }}>Loading chart data...</div>
          ) : (
            <div>
              {/* Recharts Area Chart */}
              {chartData.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                      <defs>
                        <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorBounds" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#64748b" stopOpacity={0.15} />
                          <stop offset="95%" stopColor="#64748b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#64748b", fontSize: 11 }}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis
                        tick={{ fill: "#64748b", fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                        domain={["auto", "auto"]}
                        tickFormatter={(v) => `$${v}`}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#1e293b",
                          border: "1px solid #334155",
                          borderRadius: 8,
                          fontSize: 12,
                        }}
                        labelStyle={{ color: "#f1f5f9" }}
                      />
                      <Area
                        type="monotone"
                        dataKey="upper_bound"
                        stroke="none"
                        fill="url(#colorBounds)"
                        name="Upper Bound"
                      />
                      <Area
                        type="monotone"
                        dataKey="actual"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        fill="url(#colorActual)"
                        name="Actual Price"
                        dot={false}
                      />
                      <Area
                        type="monotone"
                        dataKey="predicted"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        strokeDasharray="6 3"
                        fill="url(#colorForecast)"
                        name="Forecast"
                        dot={false}
                      />
                      <Area
                        type="monotone"
                        dataKey="lower_bound"
                        stroke="none"
                        fill="none"
                        name="Lower Bound"
                      />
                    </AreaChart>
                  </ResponsiveContainer>

                  {/* Legend */}
                  <div style={{ display: "flex", gap: 20, justifyContent: "center", marginTop: 8 }}>
                    <span style={{ fontSize: 12, color: "#3b82f6" }}>--- Actual</span>
                    <span style={{ fontSize: 12, color: "#f59e0b" }}>- - Forecast</span>
                    <span style={{ fontSize: 12, color: "#64748b" }}>Confidence Band</span>
                  </div>
                </div>
              )}

              {/* Forecast KPIs */}
              {forecast && (
                <div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr 1fr",
                      gap: 12,
                      marginBottom: 16,
                    }}
                  >
                    <div style={{ padding: 12, background: "#0f172a", borderRadius: 8 }}>
                      <div style={{ fontSize: 11, color: "#64748b" }}>Current</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: "#f1f5f9" }}>
                        ${forecast.current_price_usd}
                      </div>
                    </div>
                    <div style={{ padding: 12, background: "#0f172a", borderRadius: 8 }}>
                      <div style={{ fontSize: 11, color: "#64748b" }}>
                        {forecast.forecast_horizon_days}d Forecast
                      </div>
                      <div
                        style={{
                          fontSize: 18,
                          fontWeight: 700,
                          color: forecast.expected_change_pct > 0 ? "#ef4444" : "#22c55e",
                        }}
                      >
                        ${forecast.forecast_end_price_usd}
                      </div>
                    </div>
                    <div style={{ padding: 12, background: "#0f172a", borderRadius: 8 }}>
                      <div style={{ fontSize: 11, color: "#64748b" }}>Change</div>
                      <div
                        style={{
                          fontSize: 18,
                          fontWeight: 700,
                          color: forecast.expected_change_pct > 0 ? "#ef4444" : "#22c55e",
                        }}
                      >
                        {forecast.expected_change_pct > 0 ? "+" : ""}
                        {forecast.expected_change_pct}%
                      </div>
                    </div>
                  </div>

                  <div style={{ fontSize: 12, color: "#64748b" }}>
                    Method: {forecast.method} | Data points: {forecast.data_points_used}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function buildChartData(
  history: PriceHistoryPoint[],
  forecast: ForecastData | null
) {
  const data: {
    label: string;
    actual?: number;
    predicted?: number;
    upper_bound?: number;
    lower_bound?: number;
  }[] = [];

  // Historical data
  for (const point of history) {
    const d = new Date(point.date);
    data.push({
      label: `${d.getMonth() + 1}/${d.getDate()}`,
      actual: point.price_usd,
    });
  }

  // Forecast data
  if (forecast?.forecast_data) {
    for (const point of forecast.forecast_data) {
      const d = new Date(point.date);
      data.push({
        label: `${d.getMonth() + 1}/${d.getDate()}`,
        predicted: point.predicted,
        upper_bound: point.upper_bound,
        lower_bound: point.lower_bound,
      });
    }
  }

  return data;
}
