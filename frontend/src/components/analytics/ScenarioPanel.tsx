import { useState } from "react";
import { api } from "../../services/api";
import type { ScenarioResult } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Play, Sparkles, ListChecks, FileText } from "lucide-react";

const SCENARIOS = [
  { type: "commodity_price_shock", label: "Commodity Price Shock", description: "What if a commodity price changes significantly?", fields: [{ key: "commodity_name", label: "Commodity", placeholder: "e.g. Wheat" }, { key: "price_change_pct", label: "Price Change %", placeholder: "e.g. 20", type: "number" }] },
  { type: "currency_devaluation", label: "LBP Devaluation", description: "What if the Lebanese pound devalues further?", fields: [{ key: "devaluation_pct", label: "Devaluation %", placeholder: "e.g. 15", type: "number" }] },
  { type: "supply_disruption", label: "Supply Disruption", description: "What if a key supplier is disrupted?", fields: [{ key: "supplier_name", label: "Supplier Name", placeholder: "e.g. Black Sea Grains" }, { key: "duration_days", label: "Duration (days)", placeholder: "e.g. 30", type: "number" }] },
  { type: "demand_surge", label: "Demand Surge", description: "What if demand unexpectedly increases?", fields: [{ key: "surge_pct", label: "Surge %", placeholder: "e.g. 30", type: "number" }, { key: "category", label: "Category (optional)", placeholder: "e.g. rice" }, { key: "duration_days", label: "Duration (days)", placeholder: "e.g. 14", type: "number" }] },
  { type: "competitor_price_cut", label: "Competitor Price Cut", description: "What if a competitor cuts prices?", fields: [{ key: "competitor_name", label: "Competitor", placeholder: "e.g. Competitor A" }, { key: "price_cut_pct", label: "Price Cut %", placeholder: "e.g. 10", type: "number" }, { key: "category", label: "Category (optional)", placeholder: "" }] },
  { type: "tariff_change", label: "Tariff / Duty Change", description: "What if import tariffs change?", fields: [{ key: "commodity_name", label: "Commodity", placeholder: "e.g. Sugar" }, { key: "tariff_change_pct", label: "Tariff Change %", placeholder: "e.g. 5", type: "number" }] },
];

export default function ScenarioPanel() {
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0]);
  const [params, setParams] = useState<Record<string, string>>({});
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      const parsedParams: Record<string, unknown> = {};
      for (const field of selectedScenario.fields) {
        const val = params[field.key] || "";
        parsedParams[field.key] = field.type === "number" ? parseFloat(val) || 0 : val;
      }
      const data = (await api.runScenario(selectedScenario.type, parsedParams)) as ScenarioResult;
      setResult(data);
    } catch { setResult(null); }
    finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
      {/* Scenario Selector */}
      <Card className="lg:col-span-2">
        <CardHeader><CardTitle>Select Scenario</CardTitle></CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-1.5">
            {SCENARIOS.map((s) => (
              <button
                key={s.type}
                onClick={() => { setSelectedScenario(s); setParams({}); setResult(null); }}
                className={cn(
                  "flex w-full flex-col rounded-lg px-4 py-3 text-left transition-colors",
                  selectedScenario.type === s.type
                    ? "bg-primary/10 ring-1 ring-primary/20"
                    : "hover:bg-muted"
                )}
              >
                <span className="text-sm font-semibold text-foreground">{s.label}</span>
                <span className="mt-0.5 text-[11px] text-muted-foreground">{s.description}</span>
              </button>
            ))}
          </div>

          {/* Parameters */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Parameters</h4>
            {selectedScenario.fields.map((field) => (
              <div key={field.key}>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">{field.label}</label>
                <Input
                  type={field.type || "text"}
                  placeholder={field.placeholder}
                  value={params[field.key] || ""}
                  onChange={(e) => setParams({ ...params, [field.key]: e.target.value })}
                />
              </div>
            ))}
          </div>

          <Button onClick={handleRun} disabled={loading} className="w-full">
            <Play className="h-4 w-4" />
            {loading ? "Running..." : "Run Scenario"}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      <Card className="lg:col-span-3">
        <CardHeader><CardTitle>Scenario Results</CardTitle></CardHeader>
        <CardContent>
          {!result ? (
            <div className="flex h-64 items-center justify-center">
              <p className="text-sm text-muted-foreground">Configure parameters and run a scenario to see results.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Recommendations */}
              {result.recommendations && (
                <div>
                  <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-warning">
                    <ListChecks className="h-4 w-4" /> Recommendations
                  </h4>
                  <div className="space-y-2">
                    {(result.recommendations as string[]).map((r: string, i: number) => (
                      <div key={i} className="rounded-lg border-l-[3px] border-l-warning bg-muted/50 px-4 py-3 text-sm text-foreground">
                        {r}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Commentary */}
              {result.ai_analysis && (
                <div>
                  <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-purple-500">
                    <Sparkles className="h-4 w-4" /> AI Strategic Commentary
                  </h4>
                  <div className="whitespace-pre-wrap rounded-lg border-l-[3px] border-l-purple-500 bg-muted/50 p-4 text-sm leading-relaxed text-foreground">
                    {result.ai_analysis as string}
                  </div>
                </div>
              )}

              {/* Details */}
              <div>
                <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                  <FileText className="h-4 w-4" /> Details
                </h4>
                <div className="max-h-96 overflow-y-auto rounded-lg bg-muted p-4">
                  <pre className="whitespace-pre-wrap font-mono text-xs text-muted-foreground">
                    {JSON.stringify(
                      Object.fromEntries(
                        Object.entries(result).filter(
                          ([k]) => !["ai_analysis", "recommendations", "product_impacts", "scenario_type", "parameters", "modeled_at"].includes(k)
                        )
                      ),
                      null,
                      2
                    )}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
