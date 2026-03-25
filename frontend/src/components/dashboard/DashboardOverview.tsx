import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type {
  DashboardSummary,
  Alert,
  MorningBriefResponse,
  MorningBriefCommodity,
} from "../../types";
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
  Minus,
  ArrowUp,
  ArrowDown,
  DollarSign,
  Ship,
} from "lucide-react";
import SparklineChart from "./SparklineChart";

const SIGNAL_STYLES = {
  BUY: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  HOLD: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  WAIT: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
};

const TREND_ICON = {
  up: ArrowUp,
  down: ArrowDown,
  flat: Minus,
};

export default function DashboardOverview() {
  const summary = useApi<DashboardSummary>(
    () => api.getDashboardSummary() as Promise<DashboardSummary>
  );
  const brief = useApi<MorningBriefResponse>(
    () => api.getMorningBrief() as Promise<MorningBriefResponse>
  );
  const alerts = useApi<Alert[]>(
    () => api.getAlerts(5) as Promise<Alert[]>
  );

  if (summary.loading || brief.loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-40 rounded-xl" />
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  const s = summary.data;
  const b = brief.data;

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

      {/* Alert Banner */}
      {b?.alert_banner && b.alert_banner.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Price Alerts
          </h3>
          <div className="flex flex-wrap gap-2">
            {b.alert_banner.map((c) => {
              const isDropping =
                (c.week_change_pct ?? 0) < 0 || (c.month_change_pct ?? 0) < 0;
              return (
                <div
                  key={c.commodity_id}
                  className={cn(
                    "rounded-lg px-3 py-2 text-sm border",
                    isDropping
                      ? "bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800"
                      : "bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800"
                  )}
                >
                  <span className="font-semibold">{c.commodity_name}</span>
                  {c.week_change_pct != null && (
                    <span
                      className={cn(
                        "ml-2 font-mono text-xs",
                        c.week_change_pct < 0
                          ? "text-emerald-700 dark:text-emerald-400"
                          : "text-red-700 dark:text-red-400"
                      )}
                    >
                      {c.week_change_pct > 0 ? "+" : ""}
                      {c.week_change_pct}% (7d)
                    </span>
                  )}
                  {c.month_change_pct != null && Math.abs(c.month_change_pct) >= 10 && (
                    <span
                      className={cn(
                        "ml-1 font-mono text-xs",
                        c.month_change_pct < 0
                          ? "text-emerald-700 dark:text-emerald-400"
                          : "text-red-700 dark:text-red-400"
                      )}
                    >
                      {c.month_change_pct > 0 ? "+" : ""}
                      {c.month_change_pct}% (30d)
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Content: Watchlist + Alerts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Commodity Watchlist */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Commodity Watchlist</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="pb-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Commodity
                    </th>
                    <th className="pb-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Price
                    </th>
                    <th className="pb-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      7d
                    </th>
                    <th className="pb-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      30d
                    </th>
                    <th className="pb-3 text-center text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Trend
                    </th>
                    <th className="pb-3 text-center text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Signal
                    </th>
                    <th className="pb-3 text-center text-xs font-medium uppercase tracking-wider text-muted-foreground hidden sm:table-cell">
                      30d Chart
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {b?.commodities?.map((c) => (
                    <CommodityRow key={c.commodity_id} commodity={c} />
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Right Column: Alerts + Currency + Shipping */}
        <div className="space-y-6">
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
                  {alerts.data?.slice(0, 5).map((a) => (
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

          {/* Currency Monitor */}
          {b?.currencies && b.currencies.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Currency Monitor
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {b.currencies.map((cur) => {
                    const TrendIcon = TREND_ICON[cur.trend] || Minus;
                    return (
                      <div
                        key={cur.pair}
                        className="flex items-center justify-between py-1.5"
                      >
                        <span className="text-sm font-medium text-foreground">
                          {cur.pair}
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono tabular-nums">
                            {cur.rate?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                          </span>
                          {cur.week_change_pct != null && (
                            <span
                              className={cn(
                                "text-xs font-mono flex items-center gap-0.5",
                                cur.week_change_pct > 0
                                  ? "text-destructive"
                                  : "text-success"
                              )}
                            >
                              <TrendIcon className="h-3 w-3" />
                              {cur.week_change_pct > 0 ? "+" : ""}
                              {cur.week_change_pct}%
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Shipping Tracker */}
          {b?.shipping && b.shipping.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2">
                  <Ship className="h-4 w-4" />
                  Shipping Costs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {b.shipping.map((s) => {
                    const TrendIcon = TREND_ICON[s.trend_90d] || Minus;
                    return (
                      <div
                        key={s.commodity_id}
                        className="flex items-center justify-between py-1.5"
                      >
                        <span className="text-sm font-medium text-foreground">
                          {s.commodity_name}
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono tabular-nums">
                            {s.current_price_usd?.toLocaleString() ?? "N/A"}
                          </span>
                          <TrendIcon
                            className={cn(
                              "h-3.5 w-3.5",
                              s.trend_90d === "up"
                                ? "text-destructive"
                                : s.trend_90d === "down"
                                  ? "text-success"
                                  : "text-muted-foreground"
                            )}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function CommodityRow({ commodity: c }: { commodity: MorningBriefCommodity }) {
  const TrendIcon = TREND_ICON[c.trend_90d] || Minus;
  const sparkColor =
    c.trend_90d === "up"
      ? "#ef4444"
      : c.trend_90d === "down"
        ? "#10b981"
        : "#6b7280";

  return (
    <tr className="transition-colors hover:bg-muted/50">
      <td className="py-2.5">
        <div className="text-sm font-medium text-foreground">
          {c.commodity_name}
        </div>
        <div className="text-[11px] text-muted-foreground">{c.category}</div>
      </td>
      <td className="py-2.5 text-right text-sm font-medium text-foreground tabular-nums">
        {c.current_price_usd != null
          ? c.unit === "rate"
            ? c.current_price_usd.toLocaleString(undefined, { maximumFractionDigits: 2 })
            : `$${c.current_price_usd.toLocaleString()}`
          : "-"}
      </td>
      <td className="py-2.5 text-right text-sm tabular-nums">
        {c.week_change_pct != null ? (
          <span
            className={cn(
              "font-medium",
              c.week_change_pct > 0 ? "text-destructive" : "text-success"
            )}
          >
            {c.week_change_pct > 0 ? "+" : ""}
            {c.week_change_pct}%
          </span>
        ) : (
          "-"
        )}
      </td>
      <td className="py-2.5 text-right text-sm tabular-nums">
        {c.month_change_pct != null ? (
          <span
            className={cn(
              "font-medium",
              c.month_change_pct > 0 ? "text-destructive" : "text-success"
            )}
          >
            {c.month_change_pct > 0 ? "+" : ""}
            {c.month_change_pct}%
          </span>
        ) : (
          "-"
        )}
      </td>
      <td className="py-2.5 text-center">
        <TrendIcon
          className={cn(
            "mx-auto h-4 w-4",
            c.trend_90d === "up"
              ? "text-destructive"
              : c.trend_90d === "down"
                ? "text-success"
                : "text-muted-foreground"
          )}
        />
      </td>
      <td className="py-2.5 text-center">
        <span
          className={cn(
            "inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold",
            SIGNAL_STYLES[c.signal] || SIGNAL_STYLES.HOLD
          )}
        >
          {c.signal}
        </span>
      </td>
      <td className="py-2.5 text-center hidden sm:table-cell">
        <div className="flex justify-center">
          <SparklineChart data={c.sparkline} color={sparkColor} />
        </div>
      </td>
    </tr>
  );
}
