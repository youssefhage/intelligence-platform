import { useState } from "react";
import {
  LayoutDashboard,
  BarChart3,
  Truck,
  TrendingUp,
  FlaskConical,
  Package,
  Bell,
  Sparkles,
  Sun,
  Moon,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "./context/ThemeContext";
import { Button } from "@/components/ui/button";
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

const NAV_ITEMS: { key: Tab; label: string; icon: typeof LayoutDashboard }[] = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "commodities", label: "Commodities", icon: BarChart3 },
  { key: "supply_chain", label: "Supply Chain", icon: Truck },
  { key: "margins", label: "Margins", icon: TrendingUp },
  { key: "scenarios", label: "What-If", icon: FlaskConical },
  { key: "reorder", label: "Reorder", icon: Package },
  { key: "alerts", label: "Alerts", icon: Bell },
  { key: "insights", label: "AI Insights", icon: Sparkles },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "flex flex-col border-r border-border bg-card transition-all duration-200",
          collapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 border-b border-border px-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
            FI
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <div className="text-sm font-semibold text-foreground truncate">
                FMCG Intelligence
              </div>
              <div className="text-[10px] text-muted-foreground">Lebanon</div>
            </div>
          )}
        </div>

        {/* Nav Items */}
        <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setActiveTab(item.key)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="h-[18px] w-[18px] shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Bottom Controls */}
        <div className="border-t border-border p-2 space-y-1">
          <Button
            variant="ghost"
            size={collapsed ? "icon" : "sm"}
            onClick={toggleTheme}
            className={cn("w-full", !collapsed && "justify-start gap-3")}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 shrink-0" />
            ) : (
              <Moon className="h-4 w-4 shrink-0" />
            )}
            {!collapsed && (
              <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
            )}
          </Button>
          <Button
            variant="ghost"
            size={collapsed ? "icon" : "sm"}
            onClick={() => setCollapsed(!collapsed)}
            className={cn("w-full", !collapsed && "justify-start gap-3")}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4 shrink-0" />
            ) : (
              <ChevronLeft className="h-4 w-4 shrink-0" />
            )}
            {!collapsed && <span>Collapse</span>}
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Top Bar */}
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-background/80 backdrop-blur-sm px-8">
          <h1 className="text-lg font-semibold text-foreground">
            {NAV_ITEMS.find((n) => n.key === activeTab)?.label}
          </h1>
        </header>

        {/* Page Content */}
        <div className="p-8">
          {activeTab === "dashboard" && <DashboardOverview />}
          {activeTab === "commodities" && <CommodityPanel />}
          {activeTab === "supply_chain" && <SupplyChainPanel />}
          {activeTab === "margins" && <MarginPanel />}
          {activeTab === "scenarios" && <ScenarioPanel />}
          {activeTab === "reorder" && <ReorderPanel />}
          {activeTab === "alerts" && <AlertsPanel />}
          {activeTab === "insights" && <InsightsPanel />}
        </div>
      </main>
    </div>
  );
}
