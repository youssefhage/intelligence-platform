import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { ReorderSuggestion, PortStatus } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Package, AlertTriangle, DollarSign, Anchor, RefreshCw } from "lucide-react";

const urgencyVariant = (urgency: string) => {
  switch (urgency) {
    case "critical": return "destructive" as const;
    case "urgent": return "warning" as const;
    default: return "default" as const;
  }
};

const congestionVariant = (level: string) => {
  switch (level) {
    case "severe": return "destructive" as const;
    case "high": return "warning" as const;
    case "medium": return "warning" as const;
    default: return "success" as const;
  }
};

export default function ReorderPanel() {
  const suggestions = useApi<ReorderSuggestion[]>(
    () => api.getReorderSuggestions() as Promise<ReorderSuggestion[]>
  );
  const ports = useApi<{ ports: PortStatus[] }>(
    () => api.getPortStatus() as Promise<{ ports: PortStatus[] }>
  );

  const totalCost = (suggestions.data || []).reduce((s, r) => s + r.estimated_cost_usd, 0);
  const criticalCount = (suggestions.data || []).filter((r) => r.urgency === "critical").length;

  const kpis = [
    { label: "Items to Reorder", value: suggestions.data?.length || 0, icon: Package, color: "text-foreground" },
    { label: "Critical", value: criticalCount, icon: AlertTriangle, color: "text-destructive" },
    { label: "Est. Order Cost", value: `$${totalCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, icon: DollarSign, color: "text-foreground" },
    { label: "Ports Monitored", value: ports.data?.ports?.length || 0, icon: Anchor, color: "text-foreground" },
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
                    <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{kpi.label}</p>
                    <p className={cn("mt-2 text-2xl font-bold", kpi.color)}>{kpi.value}</p>
                  </div>
                  <div className="rounded-lg bg-muted p-3"><Icon className={cn("h-5 w-5", kpi.color)} /></div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Reorder Suggestions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Auto-Reorder Suggestions</CardTitle>
              <Button variant="outline" size="sm" onClick={() => suggestions.reload()}>
                <RefreshCw className="h-3.5 w-3.5" /> Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {suggestions.loading ? (
              <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12" />)}</div>
            ) : !suggestions.data?.length ? (
              <p className="text-sm text-muted-foreground">All products have adequate stock levels.</p>
            ) : (
              <div className="max-h-[500px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      {["Product", "Stock", "Days Left", "Order Qty", "Est. Cost", "Urgency"].map((h) => (
                        <th key={h} className="pb-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {suggestions.data.map((s) => (
                      <tr key={s.product_id} className="transition-colors hover:bg-muted/50">
                        <td className="py-3">
                          <div className="font-medium text-foreground">{s.product_name}</div>
                          <div className="text-[11px] text-muted-foreground">{s.supplier || "—"}</div>
                        </td>
                        <td className="py-3 tabular-nums text-foreground">{s.current_stock.toLocaleString()}</td>
                        <td className={cn("py-3 font-semibold tabular-nums", s.days_of_stock <= 3 ? "text-destructive" : s.days_of_stock <= 7 ? "text-warning" : "text-foreground")}>
                          {s.days_of_stock}
                        </td>
                        <td className="py-3 tabular-nums text-foreground">{s.suggested_order_qty.toLocaleString()}</td>
                        <td className="py-3 tabular-nums text-foreground">${s.estimated_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                        <td className="py-3"><Badge variant={urgencyVariant(s.urgency)}>{s.urgency}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Port Status */}
        <Card>
          <CardHeader><CardTitle>Port Status</CardTitle></CardHeader>
          <CardContent>
            {ports.loading ? (
              <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}</div>
            ) : (
              <div className="space-y-3">
                {ports.data?.ports?.map((port) => (
                  <div key={port.port_name} className="rounded-lg border-l-[3px] bg-muted/50 p-4" style={{ borderLeftColor: port.congestion_level === "severe" ? "var(--color-destructive)" : port.congestion_level === "high" ? "var(--color-warning)" : "var(--color-success)" }}>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-foreground">{port.port_name}</span>
                      <Badge variant={congestionVariant(port.congestion_level)}>{port.congestion_level}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">Status: {port.status} | Wait: {port.avg_wait_days} days</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{port.notes}</p>
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
