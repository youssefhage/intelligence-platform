import { useState } from "react";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { CommodityPrice, ForecastData, PriceHistoryPoint } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

export default function CommodityPanel() {
  const prices = useApi<CommodityPrice[]>(
    () => api.getLatestPrices() as Promise<CommodityPrice[]>
  );
  const [selectedCommodity, setSelectedCommodity] = useState<number | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [history, setHistory] = useState<PriceHistoryPoint[]>([]);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const { theme } = useTheme();

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

  const chartData = buildChartData(history, forecast);
  const gridColor = theme === "dark" ? "#334155" : "#e2e8f0";
  const tickColor = theme === "dark" ? "#64748b" : "#94a3b8";
  const tooltipBg = theme === "dark" ? "#1e293b" : "#ffffff";
  const tooltipBorder = theme === "dark" ? "#334155" : "#e2e8f0";

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
      {/* Commodity List */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Tracked Commodities</CardTitle>
        </CardHeader>
        <CardContent>
          {prices.loading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : (
            <div className="space-y-1.5">
              {prices.data?.map((p) => (
                <button
                  key={p.commodity_id}
                  onClick={() => handleSelectCommodity(p.commodity_id)}
                  className={cn(
                    "flex w-full items-center justify-between rounded-lg px-4 py-3 text-left transition-colors",
                    selectedCommodity === p.commodity_id
                      ? "bg-primary/10 ring-1 ring-primary/20"
                      : "hover:bg-muted"
                  )}
                >
                  <div>
                    <div className="text-sm font-semibold text-foreground">
                      {p.commodity_name}
                    </div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {p.category} / {p.unit}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-foreground tabular-nums">
                      {p.current_price_usd != null
                        ? `$${p.current_price_usd.toLocaleString()}`
                        : "N/A"}
                    </div>
                    {p.week_change_pct != null && (
                      <div
                        className={cn(
                          "mt-0.5 flex items-center justify-end gap-1 text-xs font-medium",
                          p.week_change_pct > 0 ? "text-destructive" : "text-success"
                        )}
                      >
                        {p.week_change_pct > 0 ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        {p.week_change_pct > 0 ? "+" : ""}
                        {p.week_change_pct}%
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chart + Forecast */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Price Trend & Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          {!selectedCommodity ? (
            <div className="flex h-64 items-center justify-center">
              <p className="text-sm text-muted-foreground">
                Select a commodity to view price chart and forecast.
              </p>
            </div>
          ) : loadingForecast ? (
            <Skeleton className="h-72" />
          ) : (
            <div className="space-y-6">
              {chartData.length > 0 && (
                <div>
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
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis dataKey="label" tick={{ fill: tickColor, fontSize: 11 }} tickLine={false} interval="preserveStartEnd" />
                      <YAxis tick={{ fill: tickColor, fontSize: 11 }} tickLine={false} axisLine={false} domain={["auto", "auto"]} tickFormatter={(v) => `$${v}`} />
                      <Tooltip contentStyle={{ background: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: 8, fontSize: 12 }} />
                      <Area type="monotone" dataKey="upper_bound" stroke="none" fill={gridColor} fillOpacity={0.3} name="Upper Bound" />
                      <Area type="monotone" dataKey="actual" stroke="#3b82f6" strokeWidth={2} fill="url(#colorActual)" name="Actual Price" dot={false} />
                      <Area type="monotone" dataKey="predicted" stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 3" fill="url(#colorForecast)" name="Forecast" dot={false} />
                      <Area type="monotone" dataKey="lower_bound" stroke="none" fill="none" name="Lower Bound" />
                    </AreaChart>
                  </ResponsiveContainer>
                  <div className="mt-2 flex items-center justify-center gap-6 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 bg-primary inline-block rounded" /> Actual</span>
                    <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 bg-warning inline-block rounded border-dashed" /> Forecast</span>
                  </div>
                </div>
              )}

              {forecast && (
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "Current", value: `$${forecast.current_price_usd}`, color: "text-foreground" },
                    { label: `${forecast.forecast_horizon_days}d Forecast`, value: `$${forecast.forecast_end_price_usd}`, color: forecast.expected_change_pct > 0 ? "text-destructive" : "text-success" },
                    { label: "Change", value: `${forecast.expected_change_pct > 0 ? "+" : ""}${forecast.expected_change_pct}%`, color: forecast.expected_change_pct > 0 ? "text-destructive" : "text-success" },
                  ].map((kpi) => (
                    <div key={kpi.label} className="rounded-lg bg-muted p-3">
                      <div className="text-[11px] text-muted-foreground">{kpi.label}</div>
                      <div className={cn("mt-1 text-lg font-bold tabular-nums", kpi.color)}>{kpi.value}</div>
                    </div>
                  ))}
                </div>
              )}

              {forecast && (
                <p className="text-xs text-muted-foreground">
                  Method: {forecast.method} | Data points: {forecast.data_points_used}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function buildChartData(history: PriceHistoryPoint[], forecast: ForecastData | null) {
  const data: { label: string; actual?: number; predicted?: number; upper_bound?: number; lower_bound?: number }[] = [];
  for (const point of history) {
    const d = new Date(point.date);
    data.push({ label: `${d.getMonth() + 1}/${d.getDate()}`, actual: point.price_usd });
  }
  if (forecast?.forecast_data) {
    for (const point of forecast.forecast_data) {
      const d = new Date(point.date);
      data.push({ label: `${d.getMonth() + 1}/${d.getDate()}`, predicted: point.predicted, upper_bound: point.upper_bound, lower_bound: point.lower_bound });
    }
  }
  return data;
}
