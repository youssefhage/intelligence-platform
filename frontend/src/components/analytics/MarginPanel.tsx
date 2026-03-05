import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../services/api";
import type { MarginAnalysis } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Play, TrendingDown, AlertTriangle, Target, Package } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

const statusColor = (status: string) => {
  switch (status) {
    case "negative": return "#ef4444";
    case "critical": return "#f59e0b";
    case "warning": return "#eab308";
    default: return "#22c55e";
  }
};

export default function MarginPanel() {
  const [analysis, setAnalysis] = useState<MarginAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const { theme } = useTheme();

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const data = (await api.getMarginAnalysis()) as MarginAnalysis;
      setAnalysis(data);
    } catch { setAnalysis(null); }
    finally { setLoading(false); }
  };

  const chartData = analysis
    ? [...(analysis.negative_margin_products || []), ...(analysis.eroding_margin_products || [])]
        .slice(0, 15)
        .map((p) => ({
          name: p.product_name.length > 20 ? p.product_name.slice(0, 20) + "..." : p.product_name,
          margin: p.current_margin_pct,
          status: p.status,
        }))
    : [];

  const gridColor = theme === "dark" ? "#334155" : "#e2e8f0";
  const tickColor = theme === "dark" ? "#64748b" : "#94a3b8";
  const tooltipBg = theme === "dark" ? "#1e293b" : "#ffffff";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div />
        <Button onClick={runAnalysis} disabled={loading}>
          <Play className="h-4 w-4" />
          {loading ? "Analyzing..." : "Run Margin Analysis"}
        </Button>
      </div>

      {!analysis ? (
        <Card>
          <CardContent className="flex h-48 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              Click "Run Margin Analysis" to scan all products for margin erosion and pricing opportunities.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Products Analyzed", value: analysis.total_products_analyzed, icon: Package, color: "text-foreground" },
              { label: "Negative Margin", value: analysis.negative_margin_count, icon: TrendingDown, color: "text-destructive" },
              { label: "Eroding Margin", value: analysis.eroding_margin_count, icon: AlertTriangle, color: "text-warning" },
              { label: "Opportunities", value: analysis.opportunities_count, icon: Target, color: "text-success" },
            ].map((kpi) => {
              const Icon = kpi.icon;
              return (
                <Card key={kpi.label}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">{kpi.label}</p>
                        <p className={cn("mt-2 text-3xl font-bold", kpi.color)}>{kpi.value}</p>
                      </div>
                      <div className="rounded-lg bg-muted p-3"><Icon className={cn("h-5 w-5", kpi.color)} /></div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Chart */}
          {chartData.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Products with Low Margins</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData} layout="vertical" margin={{ left: 120, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis type="number" tick={{ fill: tickColor, fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                    <YAxis dataKey="name" type="category" tick={{ fill: tickColor, fontSize: 11 }} width={120} />
                    <Tooltip contentStyle={{ background: tooltipBg, border: `1px solid ${gridColor}`, borderRadius: 8 }} formatter={(value: number) => [`${value}%`, "Margin"]} />
                    <Bar dataKey="margin" radius={[0, 4, 4, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={index} fill={statusColor(entry.status)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Pricing Opportunities */}
          {analysis.pricing_opportunities.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-success">Pricing Opportunities</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analysis.pricing_opportunities.slice(0, 10).map((p) => (
                    <div key={p.product_id} className="flex items-center justify-between rounded-lg border-l-[3px] border-l-success bg-muted/50 p-4">
                      <div>
                        <div className="text-sm font-semibold text-foreground">{p.product_name}</div>
                        <div className="mt-0.5 text-xs text-muted-foreground">
                          Current: ${p.current_sell_usd} | Margin: {p.current_margin_pct}%
                          {p.margin_trend !== "stable" && ` | Trend: ${p.margin_trend}`}
                        </div>
                      </div>
                      {p.opportunity && (
                        <div className="text-right">
                          <div className="text-sm font-semibold text-success">Suggest: ${p.opportunity.suggested_sell}</div>
                          <div className="text-[11px] text-muted-foreground">+${p.opportunity.monthly_revenue_impact}/mo</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
