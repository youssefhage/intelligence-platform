import { useState } from "react";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { CommodityPrice } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Settings, Plus, Trash2 } from "lucide-react";

interface AlertThreshold {
  id: number;
  commodity_id: number | null;
  alert_type: string;
  threshold_value: number;
  is_active: boolean;
  notify_channels: string | null;
}

const ALERT_TYPES = [
  { value: "price_spike", label: "Price Spike (%)" },
  { value: "buy_window", label: "Buy Window (% below MA)" },
  { value: "shipping_rate_change", label: "Shipping Rate Change (%)" },
  { value: "sourcing_currency_move", label: "Currency Move (%)" },
  { value: "margin_erosion", label: "Margin Erosion (%)" },
];

export default function AlertSettings() {
  const thresholds = useApi<AlertThreshold[]>(
    () => api.getAlertThresholds() as Promise<AlertThreshold[]>
  );
  const commodities = useApi<CommodityPrice[]>(
    () => api.getLatestPrices() as Promise<CommodityPrice[]>
  );

  const [newThreshold, setNewThreshold] = useState({
    commodity_id: null as number | null,
    alert_type: "price_spike",
    threshold_value: 5,
  });
  const [adding, setAdding] = useState(false);

  const handleAdd = async () => {
    setAdding(true);
    try {
      await api.createAlertThreshold({
        commodity_id: newThreshold.commodity_id || null,
        alert_type: newThreshold.alert_type,
        threshold_value: newThreshold.threshold_value,
      });
      thresholds.reload();
      setNewThreshold({ commodity_id: null, alert_type: "price_spike", threshold_value: 5 });
    } finally {
      setAdding(false);
    }
  };

  const getCommodityName = (id: number | null) => {
    if (!id) return "All Commodities";
    return commodities.data?.find((c) => c.commodity_id === id)?.commodity_name || `#${id}`;
  };

  const getAlertTypeLabel = (type: string) => {
    return ALERT_TYPES.find((t) => t.value === type)?.label || type;
  };

  return (
    <div className="space-y-6">
      {/* Add New Threshold */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add Alert Threshold
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3 items-end">
            <div className="flex-1 min-w-[180px]">
              <label className="text-xs font-medium text-muted-foreground">Commodity</label>
              <select
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={newThreshold.commodity_id ?? ""}
                onChange={(e) =>
                  setNewThreshold({
                    ...newThreshold,
                    commodity_id: e.target.value ? Number(e.target.value) : null,
                  })
                }
              >
                <option value="">All Commodities</option>
                {commodities.data?.map((c) => (
                  <option key={c.commodity_id} value={c.commodity_id}>
                    {c.commodity_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1 min-w-[180px]">
              <label className="text-xs font-medium text-muted-foreground">Alert Type</label>
              <select
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={newThreshold.alert_type}
                onChange={(e) =>
                  setNewThreshold({ ...newThreshold, alert_type: e.target.value })
                }
              >
                {ALERT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-28">
              <label className="text-xs font-medium text-muted-foreground">Threshold</label>
              <Input
                type="number"
                step="0.5"
                value={newThreshold.threshold_value}
                onChange={(e) =>
                  setNewThreshold({
                    ...newThreshold,
                    threshold_value: Number(e.target.value),
                  })
                }
              />
            </div>
            <Button onClick={handleAdd} disabled={adding}>
              {adding ? "Adding..." : "Add"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Existing Thresholds */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configured Thresholds
          </CardTitle>
        </CardHeader>
        <CardContent>
          {thresholds.loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : !thresholds.data?.length ? (
            <p className="text-sm text-muted-foreground">
              No alert thresholds configured. Add one above to get started.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="pb-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Commodity
                    </th>
                    <th className="pb-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Alert Type
                    </th>
                    <th className="pb-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Threshold
                    </th>
                    <th className="pb-3 text-center text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {thresholds.data.map((t) => (
                    <tr key={t.id} className="hover:bg-muted/50">
                      <td className="py-3 text-sm font-medium text-foreground">
                        {getCommodityName(t.commodity_id)}
                      </td>
                      <td className="py-3">
                        <Badge variant="secondary" className="text-xs">
                          {getAlertTypeLabel(t.alert_type)}
                        </Badge>
                      </td>
                      <td className="py-3 text-right text-sm font-mono tabular-nums">
                        {t.threshold_value}%
                      </td>
                      <td className="py-3 text-center">
                        <Badge
                          variant={t.is_active ? "default" : "secondary"}
                          className="text-[10px]"
                        >
                          {t.is_active ? "Active" : "Paused"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
