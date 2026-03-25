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
  Calculator,
  Newspaper,
  FileText,
  Menu,
  X,
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
import LandedCostPanel from "./components/calculator/LandedCostPanel";
import NewsFeedPanel from "./components/news/NewsFeedPanel";

type Tab =
  | "dashboard"
  | "commodities"
  | "supply_chain"
  | "alerts"
  | "insights"
  | "scenarios"
  | "margins"
  | "reorder"
  | "calculator"
  | "news";

const NAV_ITEMS: { key: Tab; label: string; icon: typeof LayoutDashboard }[] = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "commodities", label: "Commodities", icon: BarChart3 },
  { key: "calculator", label: "Calculator", icon: Calculator },
  { key: "news", label: "News & Geo", icon: Newspaper },
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
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const handleNav = (tab: Tab) => {
    setActiveTab(tab);
    setMobileOpen(false); // Auto-close on mobile
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "flex flex-col border-r border-border bg-card transition-all duration-200 z-40",
          // Desktop
          "hidden lg:flex",
          collapsed ? "lg:w-16" : "lg:w-60",
          // Mobile: overlay when open
          mobileOpen && "!flex fixed inset-y-0 left-0 w-60"
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
              CI
            </div>
            {(!collapsed || mobileOpen) && (
              <div className="overflow-hidden">
                <div className="text-sm font-semibold text-foreground truncate">
                  Commodity Intel
                </div>
                <div className="text-[10px] text-muted-foreground">AHT Lebanon</div>
              </div>
            )}
          </div>
          {/* Close button on mobile */}
          {mobileOpen && (
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
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
                onClick={() => handleNav(item.key)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="h-[18px] w-[18px] shrink-0" />
                {(!collapsed || mobileOpen) && (
                  <span className="truncate">{item.label}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Bottom Controls */}
        <div className="border-t border-border p-2 space-y-1">
          <Button
            variant="ghost"
            size={(collapsed && !mobileOpen) ? "icon" : "sm"}
            onClick={toggleTheme}
            className={cn("w-full", (!collapsed || mobileOpen) && "justify-start gap-3")}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 shrink-0" />
            ) : (
              <Moon className="h-4 w-4 shrink-0" />
            )}
            {(!collapsed || mobileOpen) && (
              <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
            )}
          </Button>
          <Button
            variant="ghost"
            size={(collapsed && !mobileOpen) ? "icon" : "sm"}
            onClick={() => setCollapsed(!collapsed)}
            className={cn("w-full hidden lg:flex", !collapsed && "justify-start gap-3")}
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
        <header className="sticky top-0 z-10 flex h-14 sm:h-16 items-center justify-between border-b border-border bg-background/80 backdrop-blur-sm px-4 sm:px-8">
          <div className="flex items-center gap-3">
            {/* Mobile hamburger */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <h1 className="text-base sm:text-lg font-semibold text-foreground">
              {NAV_ITEMS.find((n) => n.key === activeTab)?.label}
            </h1>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="hidden sm:flex"
            onClick={() => {
              window.open("/api/reports/weekly", "_blank");
            }}
          >
            <FileText className="h-3.5 w-3.5 mr-1.5" />
            Weekly Report
          </Button>
          {/* Mobile: icon-only report button */}
          <Button
            variant="outline"
            size="icon"
            className="sm:hidden h-8 w-8"
            onClick={() => {
              window.open("/api/reports/weekly", "_blank");
            }}
          >
            <FileText className="h-3.5 w-3.5" />
          </Button>
        </header>

        {/* Page Content */}
        <div className="p-4 sm:p-6 lg:p-8">
          {activeTab === "dashboard" && <DashboardOverview />}
          {activeTab === "commodities" && <CommodityPanel />}
          {activeTab === "calculator" && <LandedCostPanel />}
          {activeTab === "news" && <NewsFeedPanel />}
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
