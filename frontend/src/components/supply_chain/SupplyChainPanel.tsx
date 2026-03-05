import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { Supplier, SupplyChainOverview } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { ShieldAlert, Users, AlertTriangle } from "lucide-react";

const riskVariant = (level: string) => {
  switch (level) {
    case "low": return "success" as const;
    case "medium": return "warning" as const;
    case "high":
    case "critical": return "destructive" as const;
    default: return "secondary" as const;
  }
};

export default function SupplyChainPanel() {
  const overview = useApi<SupplyChainOverview>(
    () => api.getSupplyChainOverview() as Promise<SupplyChainOverview>
  );
  const suppliers = useApi<Supplier[]>(
    () => api.getSuppliers() as Promise<Supplier[]>
  );

  const kpis = [
    { label: "Total Suppliers", value: overview.data?.total_suppliers ?? 0, icon: Users, color: "text-primary" },
    { label: "Overall Risk Score", value: overview.data?.overall_risk_score ?? 0, icon: ShieldAlert, color: (overview.data?.overall_risk_score ?? 0) > 50 ? "text-destructive" : "text-success" },
    { label: "High Risk Suppliers", value: overview.data?.high_risk_suppliers?.length ?? 0, icon: AlertTriangle, color: "text-destructive" },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <Card key={kpi.label}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{kpi.label}</p>
                    <p className={cn("mt-2 text-3xl font-bold", kpi.color)}>{kpi.value}</p>
                  </div>
                  <div className="rounded-lg bg-muted p-3"><Icon className={cn("h-5 w-5", kpi.color)} /></div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Risk Distribution */}
      {overview.data?.risk_distribution && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(overview.data.risk_distribution).map(([level, count]) => (
            <Badge key={level} variant={riskVariant(level)} className="text-xs">
              {level}: {count as number}
            </Badge>
          ))}
        </div>
      )}

      {/* Supplier Table */}
      <Card>
        <CardHeader>
          <CardTitle>Suppliers</CardTitle>
        </CardHeader>
        <CardContent>
          {suppliers.loading ? (
            <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12" />)}</div>
          ) : suppliers.data?.length === 0 ? (
            <p className="text-sm text-muted-foreground">No suppliers configured yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    {["Supplier", "Country", "Risk Level", "Reliability", "Lead Time", "Actions"].map((h, i) => (
                      <th key={h} className={cn("pb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground", i >= 3 ? "text-right" : "text-left", i === 5 && "text-center")}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {suppliers.data?.map((s) => (
                    <tr key={s.id} className="transition-colors hover:bg-muted/50">
                      <td className="py-3 text-sm font-medium text-foreground">{s.name}</td>
                      <td className="py-3 text-sm text-muted-foreground">{s.country}</td>
                      <td className="py-3"><Badge variant={riskVariant(s.current_risk_level)}>{s.current_risk_level}</Badge></td>
                      <td className="py-3 text-right text-sm font-medium text-foreground tabular-nums">{s.reliability_score != null ? `${s.reliability_score}%` : "-"}</td>
                      <td className="py-3 text-right text-sm text-muted-foreground tabular-nums">{s.lead_time_days != null ? `${s.lead_time_days}d` : "-"}</td>
                      <td className="py-3 text-center">
                        <Button variant="outline" size="sm" onClick={async () => { await api.assessRisk(s.id); suppliers.reload(); overview.reload(); }}>
                          Assess Risk
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* High Risk Suppliers */}
      {overview.data?.high_risk_suppliers && overview.data.high_risk_suppliers.length > 0 && (
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="text-destructive">High Risk Suppliers Requiring Attention</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {overview.data.high_risk_suppliers.map((s) => (
                <div key={s.id} className="rounded-lg border-l-[3px] border-l-destructive bg-muted/50 p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground">{s.name}</span>
                    <Badge variant="destructive">{s.risk_level.toUpperCase()}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {s.country} | Commodities: {s.commodities.join(", ") || "N/A"}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
