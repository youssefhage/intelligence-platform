import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { DashboardSummary, CommodityPrice, Alert } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  BarChart3,
  Package,
  ShieldAlert,
  Bell,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

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

  if (summary.loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Skeleton className="h-80 rounded-xl lg:col-span-2" />
          <Skeleton className="h-80 rounded-xl" />
        </div>
      </div>
    );
  }

  const s = summary.data;

  const kpis = [
    {
      label: "Commodities Tracked",
      value: s?.total_commodities_tracked ?? 0,
      icon: BarChart3,
      color: "text-primary",
    },
    {
      label: "Active Products",
      value: s?.total_products ?? 0,
      icon: Package,
      color: "text-primary",
    },
    {
      label: "Supply Risk Score",
      value: s?.overall_supply_risk_score ?? 0,
      icon: ShieldAlert,
      color:
        (s?.overall_supply_risk_score ?? 0) > 50
          ? "text-destructive"
          : "text-success",
    },
    {
      label: "Active Alerts",
      value: s?.active_alerts ?? 0,
      icon: Bell,
      color:
        (s?.active_alerts ?? 0) > 0 ? "text-warning" : "text-success",
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <Card key={kpi.label}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      {kpi.label}
                    </p>
                    <p className={cn("mt-2 text-3xl font-bold", kpi.color)}>
                      {kpi.value}
                    </p>
                  </div>
                  <div className="rounded-lg bg-muted p-3">
                    <Icon className={cn("h-5 w-5", kpi.color)} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Commodity Prices */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Commodity Prices</CardTitle>
          </CardHeader>
          <CardContent>
            {prices.loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-10" />
                ))}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="pb-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        Commodity
                      </th>
                      <th className="pb-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        Price (USD)
                      </th>
                      <th className="pb-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        7d Change
                      </th>
                      <th className="pb-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        Category
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {prices.data?.map((p) => (
                      <tr
                        key={p.commodity_id}
                        className="transition-colors hover:bg-muted/50"
                      >
                        <td className="py-3 text-sm font-medium text-foreground">
                          {p.commodity_name}
                        </td>
                        <td className="py-3 text-right text-sm font-medium text-foreground tabular-nums">
                          {p.current_price_usd != null
                            ? `$${p.current_price_usd.toLocaleString()}`
                            : "-"}
                        </td>
                        <td className="py-3 text-right text-sm">
                          {p.week_change_pct != null ? (
                            <span
                              className={cn(
                                "inline-flex items-center gap-1 font-medium",
                                p.week_change_pct > 0
                                  ? "text-destructive"
                                  : "text-success"
                              )}
                            >
                              {p.week_change_pct > 0 ? (
                                <TrendingUp className="h-3.5 w-3.5" />
                              ) : (
                                <TrendingDown className="h-3.5 w-3.5" />
                              )}
                              {p.week_change_pct > 0 ? "+" : ""}
                              {p.week_change_pct}%
                            </span>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                        <td className="py-3">
                          <Badge variant="secondary">{p.category}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            {alerts.loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : alerts.data?.length === 0 ? (
              <p className="text-sm text-muted-foreground">No active alerts</p>
            ) : (
              <div className="space-y-3">
                {alerts.data?.map((a) => (
                  <div
                    key={a.id}
                    className={cn(
                      "rounded-lg border-l-[3px] bg-muted/50 p-3",
                      a.severity === "critical"
                        ? "border-l-destructive"
                        : a.severity === "warning"
                          ? "border-l-warning"
                          : "border-l-primary"
                    )}
                  >
                    <p className="text-sm font-medium text-foreground">
                      {a.title}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                      {a.message}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
