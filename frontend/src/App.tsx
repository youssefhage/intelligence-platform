import { useState } from "react";
import DashboardOverview from "./components/dashboard/DashboardOverview";
import CommodityPanel from "./components/commodities/CommodityPanel";
import SupplyChainPanel from "./components/supply_chain/SupplyChainPanel";
import AlertsPanel from "./components/alerts/AlertsPanel";
import InsightsPanel from "./components/dashboard/InsightsPanel";
import ScenarioPanel from "./components/analytics/ScenarioPanel";
import MarginPanel from "./components/analytics/MarginPanel";
import ReorderPanel from "./components/analytics/ReorderPanel";

type Tab =
  | "dashboard"
  | "commodities"
  | "supply_chain"
  | "alerts"
  | "insights"
  | "scenarios"
  | "margins"
  | "reorder";

const TABS: { key: Tab; label: string }[] = [
  { key: "dashboard", label: "Dashboard" },
  { key: "commodities", label: "Commodities" },
  { key: "supply_chain", label: "Supply Chain" },
  { key: "margins", label: "Margins" },
  { key: "scenarios", label: "What-If" },
  { key: "reorder", label: "Reorder" },
  { key: "alerts", label: "Alerts" },
  { key: "insights", label: "AI Insights" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");

  return (
    <div style={{ minHeight: "100vh", background: "#0f172a" }}>
      {/* Header */}
      <header
        style={{
          background: "#1e293b",
          borderBottom: "1px solid #334155",
          padding: "16px 32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 24, fontWeight: 700, color: "#f1f5f9" }}>
            FMCG Intelligence
          </span>
          <span
            style={{
              fontSize: 12,
              color: "#94a3b8",
              background: "#334155",
              padding: "2px 8px",
              borderRadius: 4,
            }}
          >
            Lebanon
          </span>
        </div>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: "8px 14px",
                border: "none",
                borderRadius: 6,
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 500,
                background:
                  activeTab === tab.key ? "#3b82f6" : "transparent",
                color: activeTab === tab.key ? "#fff" : "#94a3b8",
                transition: "all 0.2s",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* Content */}
      <main style={{ padding: 32 }}>
        {activeTab === "dashboard" && <DashboardOverview />}
        {activeTab === "commodities" && <CommodityPanel />}
        {activeTab === "supply_chain" && <SupplyChainPanel />}
        {activeTab === "margins" && <MarginPanel />}
        {activeTab === "scenarios" && <ScenarioPanel />}
        {activeTab === "reorder" && <ReorderPanel />}
        {activeTab === "alerts" && <AlertsPanel />}
        {activeTab === "insights" && <InsightsPanel />}
      </main>
    </div>
  );
}
