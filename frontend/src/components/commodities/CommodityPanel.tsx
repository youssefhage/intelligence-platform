import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { CommodityPrice, CommodityDetail, AISummary } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Sparkles, Activity, BarChart3, Link2 } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

const TIME_RANGES = ["6M", "1Y", "3Y", "5Y"] as const;

export default function CommodityPanel() {
  const prices = useApi<CommodityPrice[]>(
    () => api.getLatestPrices() as Promise<CommodityPrice[]>
  );
  const [selectedCommodity, setSelectedCommodity] = useState<number | null>(null);
  const [selectedRange, setSelectedRange] = useState<string>("1Y");
  const [detail, setDetail] = useState<CommodityDetail | null>(null);
  const [aiSummary, setAiSummary] = useState<AISummary | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingAI, setLoadingAI] = useState(false);
  const { theme } = useTheme();

  const handleSelectCommodity = async (id: number, range = selectedRange) => {
    setSelectedCommodity(id);
    setSelectedRange(range);
    setLoadingDetail(true);
    setAiSummary(null);
    try {
      const data = await api.getCommodityDetail(id, range) as CommodityDetail;
      setDetail(data);
    } catch {
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleRangeChange = (range: string) => {
    if (selectedCommodity) {
      handleSelectCommodity(selectedCommodity, range);
    }
  };

  const handleLoadAISummary = async () => {
    if (!selectedCommodity) return;
    setLoadingAI(true);
    try {
      const data = await api.getCommodityAISummary(selectedCommodity) as AISummary;
      setAiSummary(data);
    } catch {
      setAiSummary(null);
    } finally {
      setLoadingAI(false);
    }
  };

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
            <div className="space-y-1.5 max-h-[600px] overflow-y-auto">
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
                      {p.category}
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

      {/* Detail Panel */}
      <div className="lg:col-span-3 space-y-6">
        {/* Chart */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                {detail ? detail.commodity_name : "Price Chart"}
              </CardTitle>
              <div className="flex gap-1">
                {TIME_RANGES.map((r) => (
                  <Button
                    key={r}
                    variant={selectedRange === r ? "default" : "ghost"}
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => handleRangeChange(r)}
                    disabled={!selectedCommodity}
                  >
                    {r}
                  </Button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {!selectedCommodity ? (
              <div className="flex h-64 items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  Select a commodity to view detailed analytics.
                </p>
              </div>
            ) : loadingDetail ? (
              <Skeleton className="h-72" />
            ) : detail?.price_history && detail.price_history.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={detail.price_history.map((p) => ({
                    label: new Date(p.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
                    price: p.price_usd,
                    ma30: p.ma_30,
                    ma90: p.ma_90,
                  }))}
                  margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis
                    dataKey="label"
                    tick={{ fill: tickColor, fontSize: 11 }}
                    tickLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fill: tickColor, fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    domain={["auto", "auto"]}
                    tickFormatter={(v) => `$${v}`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: tooltipBg,
                      border: `1px solid ${tooltipBorder}`,
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="Price"
                  />
                  <Line
                    type="monotone"
                    dataKey="ma30"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    dot={false}
                    name="30d MA"
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="ma90"
                    stroke="#8b5cf6"
                    strokeWidth={1.5}
                    strokeDasharray="6 3"
                    dot={false}
                    name="90d MA"
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-12">
                No price data available for this range.
              </p>
            )}
            {detail && (
              <div className="mt-2 flex items-center justify-center gap-6 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <span className="h-0.5 w-4 bg-blue-500 inline-block rounded" /> Price
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-0.5 w-4 bg-amber-500 inline-block rounded" /> 30d MA
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-0.5 w-4 bg-violet-500 inline-block rounded" /> 90d MA
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Analytics Cards */}
        {detail && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {/* Volatility */}
            <Card>
              <CardContent className="pt-5">
                <div className="flex items-center gap-2 text-muted-foreground mb-2">
                  <Activity className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">Volatility</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      detail.volatility_level === "high"
                        ? "destructive"
                        : detail.volatility_level === "medium"
                          ? "secondary"
                          : "default"
                    }
                  >
                    {detail.volatility_level}
                  </Badge>
                  {detail.volatility_current != null && (
                    <span className="text-sm text-muted-foreground">
                      (stdev: {detail.volatility_current})
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Price Context */}
            <Card>
              <CardContent className="pt-5">
                <div className="flex items-center gap-2 text-muted-foreground mb-2">
                  <BarChart3 className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">Price Context</span>
                </div>
                <div className="space-y-1">
                  {detail.price_context.vs_1y_avg_pct != null && (
                    <p className="text-sm">
                      <span
                        className={cn(
                          "font-semibold",
                          detail.price_context.vs_1y_avg_pct > 0
                            ? "text-destructive"
                            : "text-success"
                        )}
                      >
                        {detail.price_context.vs_1y_avg_pct > 0 ? "+" : ""}
                        {detail.price_context.vs_1y_avg_pct}%
                      </span>{" "}
                      vs 1Y avg
                    </p>
                  )}
                  {detail.price_context.vs_3y_avg_pct != null && (
                    <p className="text-sm">
                      <span
                        className={cn(
                          "font-semibold",
                          detail.price_context.vs_3y_avg_pct > 0
                            ? "text-destructive"
                            : "text-success"
                        )}
                      >
                        {detail.price_context.vs_3y_avg_pct > 0 ? "+" : ""}
                        {detail.price_context.vs_3y_avg_pct}%
                      </span>{" "}
                      vs 3Y avg
                    </p>
                  )}
                  {detail.price_context.percentile != null && (
                    <p className="text-xs text-muted-foreground">
                      {detail.price_context.percentile}th percentile
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Correlations */}
            <Card>
              <CardContent className="pt-5">
                <div className="flex items-center gap-2 text-muted-foreground mb-2">
                  <Link2 className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">Correlations</span>
                </div>
                {detail.correlations.length > 0 ? (
                  <div className="space-y-1">
                    {detail.correlations.slice(0, 3).map((cor) => (
                      <p key={cor.commodity_id} className="text-sm">
                        <span className="font-medium">{cor.correlation > 0 ? "+" : ""}{(cor.correlation * 100).toFixed(0)}%</span>{" "}
                        <span className="text-muted-foreground">{cor.commodity_name}</span>
                      </p>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">Insufficient data</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* AI Summary */}
        {selectedCommodity && (
          <Card>
            <CardContent className="pt-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Sparkles className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">AI Market Summary</span>
                </div>
                {!aiSummary && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleLoadAISummary}
                    disabled={loadingAI}
                  >
                    {loadingAI ? "Generating..." : "Generate"}
                  </Button>
                )}
              </div>
              {aiSummary ? (
                <div className="space-y-2">
                  <p className="text-sm text-foreground leading-relaxed">{aiSummary.summary}</p>
                  <p className="text-xs text-muted-foreground">
                    Generated {new Date(aiSummary.generated_at).toLocaleString()}
                  </p>
                </div>
              ) : !loadingAI ? (
                <p className="text-sm text-muted-foreground">
                  Click Generate to get an AI-powered market analysis.
                </p>
              ) : (
                <Skeleton className="h-20" />
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
