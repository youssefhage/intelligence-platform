import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { LandedCostResult, LandedCostHistoryItem } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Calculator, History } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

const ORIGIN_COUNTRIES = [
  "China",
  "Turkey",
  "Egypt",
  "India",
  "Brazil",
  "Malaysia",
  "Indonesia",
  "Thailand",
  "Vietnam",
  "Argentina",
  "Ukraine",
  "New Zealand",
  "Netherlands",
  "Spain",
  "Saudi Arabia",
];

export default function LandedCostPanel() {
  const [form, setForm] = useState({
    commodity_name: "",
    origin_country: "Turkey",
    quantity: 25,
    unit: "ton",
    incoterm: "FOB",
    fob_price_usd: 0,
    insurance_pct: 0.5,
    duty_pct: 0,
  });
  const [result, setResult] = useState<LandedCostResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const history = useApi<LandedCostHistoryItem[]>(
    () => api.getLandedCostHistory(20) as Promise<LandedCostHistoryItem[]>
  );

  const { theme } = useTheme();
  const gridColor = theme === "dark" ? "#262626" : "#e5e5e5";
  const tickColor = theme === "dark" ? "#737373" : "#a3a3a3";

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const data = await api.calculateLandedCost(form) as LandedCostResult;
      setResult(data);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const costBreakdown = result
    ? [
        { name: "FOB", value: result.fob_price_usd },
        { name: "Freight", value: result.freight_cost_usd },
        { name: "Insurance", value: result.insurance_cost_usd },
        { name: "Duty", value: result.duty_usd },
        { name: "Port", value: result.port_charges_usd },
        { name: "Transport", value: result.inland_transport_usd },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Landed Cost Calculator
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Commodity Name</label>
                <Input
                  value={form.commodity_name}
                  onChange={(e) => setForm({ ...form, commodity_name: e.target.value })}
                  placeholder="e.g., Palm Oil"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Origin Country</label>
                  <select
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    value={form.origin_country}
                    onChange={(e) => setForm({ ...form, origin_country: e.target.value })}
                  >
                    {ORIGIN_COUNTRIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Incoterm</label>
                  <select
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    value={form.incoterm}
                    onChange={(e) => setForm({ ...form, incoterm: e.target.value })}
                  >
                    <option value="FOB">FOB</option>
                    <option value="CIF">CIF</option>
                    <option value="EXW">EXW</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Quantity</label>
                  <Input
                    type="number"
                    value={form.quantity}
                    onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">FOB Price (USD/unit)</label>
                  <Input
                    type="number"
                    value={form.fob_price_usd || ""}
                    onChange={(e) => setForm({ ...form, fob_price_usd: Number(e.target.value) })}
                    placeholder="e.g., 900"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Insurance %</label>
                  <Input
                    type="number"
                    step="0.1"
                    value={form.insurance_pct}
                    onChange={(e) => setForm({ ...form, insurance_pct: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Duty %</label>
                  <Input
                    type="number"
                    step="0.1"
                    value={form.duty_pct}
                    onChange={(e) => setForm({ ...form, duty_pct: Number(e.target.value) })}
                  />
                </div>
              </div>
              <Button onClick={handleCalculate} disabled={loading || !form.commodity_name || !form.fob_price_usd} className="w-full">
                {loading ? "Calculating..." : "Calculate Landed Cost"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Result */}
        <Card>
          <CardHeader>
            <CardTitle>Cost Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: "FOB Total", value: result.fob_price_usd },
                    { label: "Freight", value: result.freight_cost_usd },
                    { label: "Insurance", value: result.insurance_cost_usd },
                    { label: "CIF Total", value: result.cif_price_usd },
                    { label: "Duty", value: result.duty_usd },
                    { label: "Port Charges", value: result.port_charges_usd },
                    { label: "Inland Transport", value: result.inland_transport_usd },
                  ].map((item) => (
                    <div key={item.label} className="rounded-lg bg-muted p-3">
                      <div className="text-[11px] text-muted-foreground">{item.label}</div>
                      <div className="mt-1 text-sm font-semibold tabular-nums">
                        ${item.value.toLocaleString()}
                      </div>
                    </div>
                  ))}
                  <div className="rounded-lg bg-primary/10 p-3 col-span-2">
                    <div className="text-[11px] text-primary font-medium">Total Landed Cost</div>
                    <div className="mt-1 text-2xl font-bold text-primary tabular-nums">
                      ${result.total_landed_cost_usd.toLocaleString()}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      ${result.cost_per_unit_usd.toLocaleString()}/{form.unit}
                    </div>
                  </div>
                </div>

                {/* Cost breakdown chart */}
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={costBreakdown} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis type="number" tick={{ fill: tickColor, fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                    <YAxis type="category" dataKey="name" tick={{ fill: tickColor, fontSize: 11 }} width={70} />
                    <Tooltip
                      formatter={(v: number) => [`$${v.toLocaleString()}`, "Cost"]}
                      contentStyle={{ background: theme === "dark" ? "#0a0a0a" : "#fff", border: `1px solid ${gridColor}`, borderRadius: 8, fontSize: 12 }}
                    />
                    <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  Fill in the form and calculate to see the cost breakdown.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Calculation History
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setShowHistory(!showHistory)}>
              {showHistory ? "Hide" : "Show"}
            </Button>
          </div>
        </CardHeader>
        {showHistory && (
          <CardContent>
            {history.loading ? (
              <Skeleton className="h-32" />
            ) : history.data && history.data.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="pb-2 text-left text-xs font-medium text-muted-foreground">Commodity</th>
                      <th className="pb-2 text-left text-xs font-medium text-muted-foreground">Origin</th>
                      <th className="pb-2 text-right text-xs font-medium text-muted-foreground">FOB</th>
                      <th className="pb-2 text-right text-xs font-medium text-muted-foreground">Total Landed</th>
                      <th className="pb-2 text-right text-xs font-medium text-muted-foreground">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {history.data.map((h) => (
                      <tr key={h.id} className="hover:bg-muted/50">
                        <td className="py-2 text-sm">{h.commodity_name}</td>
                        <td className="py-2 text-sm">{h.origin_country}</td>
                        <td className="py-2 text-sm text-right tabular-nums">${h.fob_price_usd?.toLocaleString()}</td>
                        <td className="py-2 text-sm text-right tabular-nums font-medium">${h.total_landed_cost_usd?.toLocaleString()}</td>
                        <td className="py-2 text-sm text-right text-muted-foreground">
                          {h.calculated_at ? new Date(h.calculated_at).toLocaleDateString() : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No calculations yet.</p>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}
