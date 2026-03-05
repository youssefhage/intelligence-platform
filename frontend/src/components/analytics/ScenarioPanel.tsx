import { useState } from "react";
import { api } from "../../services/api";
import type { ScenarioResult } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

const inputStyle: React.CSSProperties = {
  background: "#0f172a",
  border: "1px solid #334155",
  borderRadius: 6,
  color: "#f1f5f9",
  padding: "8px 12px",
  fontSize: 14,
  width: "100%",
};

const btnStyle: React.CSSProperties = {
  background: "#7c3aed",
  color: "white",
  border: "none",
  borderRadius: 8,
  padding: "10px 20px",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};

const SCENARIOS = [
  {
    type: "commodity_price_shock",
    label: "Commodity Price Shock",
    description: "What if a commodity price changes significantly?",
    fields: [
      { key: "commodity_name", label: "Commodity", placeholder: "e.g. Wheat" },
      { key: "price_change_pct", label: "Price Change %", placeholder: "e.g. 20", type: "number" },
    ],
  },
  {
    type: "currency_devaluation",
    label: "LBP Devaluation",
    description: "What if the Lebanese pound devalues further?",
    fields: [
      { key: "devaluation_pct", label: "Devaluation %", placeholder: "e.g. 15", type: "number" },
    ],
  },
  {
    type: "supply_disruption",
    label: "Supply Disruption",
    description: "What if a key supplier is disrupted?",
    fields: [
      { key: "supplier_name", label: "Supplier Name", placeholder: "e.g. Black Sea Grains" },
      { key: "duration_days", label: "Duration (days)", placeholder: "e.g. 30", type: "number" },
    ],
  },
  {
    type: "demand_surge",
    label: "Demand Surge",
    description: "What if demand unexpectedly increases?",
    fields: [
      { key: "surge_pct", label: "Surge %", placeholder: "e.g. 30", type: "number" },
      { key: "category", label: "Category (optional)", placeholder: "e.g. rice" },
      { key: "duration_days", label: "Duration (days)", placeholder: "e.g. 14", type: "number" },
    ],
  },
  {
    type: "competitor_price_cut",
    label: "Competitor Price Cut",
    description: "What if a competitor cuts prices?",
    fields: [
      { key: "competitor_name", label: "Competitor", placeholder: "e.g. Competitor A" },
      { key: "price_cut_pct", label: "Price Cut %", placeholder: "e.g. 10", type: "number" },
      { key: "category", label: "Category (optional)", placeholder: "" },
    ],
  },
  {
    type: "tariff_change",
    label: "Tariff / Duty Change",
    description: "What if import tariffs change?",
    fields: [
      { key: "commodity_name", label: "Commodity", placeholder: "e.g. Sugar" },
      { key: "tariff_change_pct", label: "Tariff Change %", placeholder: "e.g. 5", type: "number" },
    ],
  },
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
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9", marginBottom: 24 }}>
        What-If Scenario Modeling
      </h2>

      <div style={{ display: "grid", gridTemplateColumns: "350px 1fr", gap: 24 }}>
        {/* Scenario Selector */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Select Scenario
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
            {SCENARIOS.map((s) => (
              <div
                key={s.type}
                onClick={() => { setSelectedScenario(s); setParams({}); setResult(null); }}
                style={{
                  padding: "12px 14px",
                  borderRadius: 8,
                  background: selectedScenario.type === s.type ? "#334155" : "#0f172a",
                  cursor: "pointer",
                  transition: "background 0.15s",
                }}
              >
                <div style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9" }}>{s.label}</div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{s.description}</div>
              </div>
            ))}
          </div>

          {/* Parameter Inputs */}
          <h4 style={{ fontSize: 14, fontWeight: 600, color: "#94a3b8", marginBottom: 12 }}>
            Parameters
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {selectedScenario.fields.map((field) => (
              <div key={field.key}>
                <label style={{ fontSize: 12, color: "#64748b", marginBottom: 4, display: "block" }}>
                  {field.label}
                </label>
                <input
                  type={field.type || "text"}
                  placeholder={field.placeholder}
                  value={params[field.key] || ""}
                  onChange={(e) => setParams({ ...params, [field.key]: e.target.value })}
                  style={inputStyle}
                />
              </div>
            ))}
          </div>

          <button onClick={handleRun} disabled={loading} style={{ ...btnStyle, width: "100%", marginTop: 16 }}>
            {loading ? "Running..." : "Run Scenario"}
          </button>
        </div>

        {/* Results */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
            Scenario Results
          </h3>
          {!result ? (
            <p style={{ color: "#94a3b8", fontSize: 14 }}>
              Configure parameters and run a scenario to see results.
            </p>
          ) : (
            <div>
              {/* Recommendations */}
              {result.recommendations && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ fontSize: 14, fontWeight: 600, color: "#f59e0b", marginBottom: 8 }}>
                    Recommendations
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {(result.recommendations as string[]).map((r: string, i: number) => (
                      <div
                        key={i}
                        style={{
                          padding: "10px 14px",
                          background: "#0f172a",
                          borderRadius: 6,
                          borderLeft: "3px solid #f59e0b",
                          fontSize: 13,
                          color: "#e2e8f0",
                        }}
                      >
                        {r}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Commentary */}
              {result.ai_analysis && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ fontSize: 14, fontWeight: 600, color: "#8b5cf6", marginBottom: 8 }}>
                    AI Strategic Commentary
                  </h4>
                  <div
                    style={{
                      padding: 16,
                      background: "#0f172a",
                      borderRadius: 8,
                      borderLeft: "3px solid #8b5cf6",
                      fontSize: 13,
                      color: "#cbd5e1",
                      lineHeight: 1.7,
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {result.ai_analysis as string}
                  </div>
                </div>
              )}

              {/* Raw results summary */}
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 600, color: "#94a3b8", marginBottom: 8 }}>
                  Details
                </h4>
                <div style={{ fontSize: 12, color: "#64748b", maxHeight: 400, overflowY: "auto" }}>
                  <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
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
        </div>
      </div>
    </div>
  );
}
