import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { Alert } from "../../types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { CheckCircle2, Eye } from "lucide-react";

const severityVariant = (severity: string) => {
  switch (severity) {
    case "critical": return "destructive" as const;
    case "warning": return "warning" as const;
    default: return "default" as const;
  }
};

const typeLabels: Record<string, string> = {
  price_spike: "Price Spike",
  supply_disruption: "Supply Disruption",
  margin_erosion: "Margin Erosion",
  inventory_low: "Low Inventory",
  currency_shift: "Currency Shift",
  geopolitical: "Geopolitical",
  sourcing_opportunity: "Sourcing Opportunity",
};

export default function AlertsPanel() {
  const alerts = useApi<Alert[]>(() => api.getAlerts(50) as Promise<Alert[]>);

  const handleMarkRead = async (id: number) => {
    await api.markAlertRead(id);
    alerts.reload();
  };

  const handleResolve = async (id: number) => {
    await api.resolveAlert(id);
    alerts.reload();
  };

  if (alerts.loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  if (alerts.data?.length === 0) {
    return (
      <Card>
        <CardContent className="flex h-48 items-center justify-center">
          <p className="text-sm text-muted-foreground">No active alerts. All clear.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.data?.map((alert) => (
        <Card
          key={alert.id}
          className={cn(
            "border-l-4 transition-opacity",
            alert.severity === "critical"
              ? "border-l-destructive"
              : alert.severity === "warning"
                ? "border-l-warning"
                : "border-l-primary",
            alert.is_read && "opacity-60"
          )}
        >
          <CardContent className="pt-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={severityVariant(alert.severity)} className="uppercase">
                    {alert.severity}
                  </Badge>
                  <Badge variant="secondary">
                    {typeLabels[alert.alert_type] || alert.alert_type}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                </div>

                <h4 className="text-[15px] font-semibold text-foreground">
                  {alert.title}
                </h4>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {alert.message}
                </p>

                {alert.action_recommended && (
                  <div className="rounded-lg border-l-[3px] border-l-primary bg-muted/50 px-4 py-2.5 text-sm text-primary">
                    Recommended: {alert.action_recommended}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              {!alert.is_read && (
                <Button variant="outline" size="sm" onClick={() => handleMarkRead(alert.id)}>
                  <Eye className="h-3.5 w-3.5" /> Mark Read
                </Button>
              )}
              <Button variant="success" size="sm" onClick={() => handleResolve(alert.id)}>
                <CheckCircle2 className="h-3.5 w-3.5" /> Resolve
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
