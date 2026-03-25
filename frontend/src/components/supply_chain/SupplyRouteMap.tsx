import { useState } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Line,
  Marker,
} from "react-simple-maps";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { SupplyRoute } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Map, Ship, Clock } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const RISK_COLORS: Record<string, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#ef4444",
  critical: "#dc2626",
};

export default function SupplyRouteMap() {
  const routes = useApi<SupplyRoute[]>(
    () => api.getSupplyRoutes() as Promise<SupplyRoute[]>
  );
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const { theme } = useTheme();

  const mapBg = theme === "dark" ? "#0f172a" : "#f1f5f9";
  const landFill = theme === "dark" ? "#1e293b" : "#e2e8f0";
  const landStroke = theme === "dark" ? "#334155" : "#cbd5e1";

  if (routes.loading) {
    return <Skeleton className="h-[400px] rounded-xl" />;
  }

  const routeData = routes.data || [];

  return (
    <div className="space-y-4">
      {/* Map */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Map className="h-5 w-5" />
            Import Supply Routes
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 overflow-hidden rounded-b-xl">
          <div style={{ background: mapBg }}>
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{ center: [50, 25], scale: 300 }}
              width={800}
              height={450}
              style={{ width: "100%", height: "auto" }}
            >
              <Geographies geography={GEO_URL}>
                {({ geographies }) =>
                  geographies.map((geo) => (
                    <Geography
                      key={geo.rsSVGKey}
                      geography={geo}
                      fill={landFill}
                      stroke={landStroke}
                      strokeWidth={0.5}
                      style={{
                        default: { outline: "none" },
                        hover: { outline: "none", fill: theme === "dark" ? "#334155" : "#cbd5e1" },
                        pressed: { outline: "none" },
                      }}
                    />
                  ))
                }
              </Geographies>

              {/* Route Lines */}
              {routeData.map((route) => {
                const isSelected = selectedRoute === route.id;
                return (
                  <Line
                    key={route.id}
                    from={[route.origin.lng, route.origin.lat]}
                    to={[route.destination.lng, route.destination.lat]}
                    stroke={isSelected ? "#3b82f6" : theme === "dark" ? "#64748b" : "#94a3b8"}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    strokeLinecap="round"
                    strokeDasharray={isSelected ? "none" : "4 2"}
                    style={{ cursor: "pointer" }}
                  />
                );
              })}

              {/* Origin Markers */}
              {routeData.map((route) => (
                <Marker
                  key={`origin-${route.id}`}
                  coordinates={[route.origin.lng, route.origin.lat]}
                  onClick={() =>
                    setSelectedRoute(selectedRoute === route.id ? null : route.id)
                  }
                  style={{ cursor: "pointer" }}
                >
                  <circle
                    r={selectedRoute === route.id ? 6 : 4}
                    fill={selectedRoute === route.id ? "#3b82f6" : "#f59e0b"}
                    stroke="#fff"
                    strokeWidth={1.5}
                  />
                  {selectedRoute === route.id && (
                    <text
                      textAnchor="middle"
                      y={-12}
                      style={{
                        fontFamily: "system-ui",
                        fontSize: 10,
                        fill: theme === "dark" ? "#e2e8f0" : "#1e293b",
                        fontWeight: 600,
                      }}
                    >
                      {route.origin.city}
                    </text>
                  )}
                </Marker>
              ))}

              {/* Beirut Destination Marker */}
              <Marker coordinates={[35.5, 33.9]}>
                <circle r={7} fill="#ef4444" stroke="#fff" strokeWidth={2} />
                <text
                  textAnchor="middle"
                  y={-14}
                  style={{
                    fontFamily: "system-ui",
                    fontSize: 11,
                    fill: theme === "dark" ? "#f8fafc" : "#0f172a",
                    fontWeight: 700,
                  }}
                >
                  Beirut
                </text>
              </Marker>
            </ComposableMap>
          </div>
        </CardContent>
      </Card>

      {/* Route Cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {routeData.map((route) => (
          <Card
            key={route.id}
            className={cn(
              "cursor-pointer transition-all",
              selectedRoute === route.id
                ? "ring-2 ring-primary"
                : "hover:bg-muted/50"
            )}
            onClick={() =>
              setSelectedRoute(selectedRoute === route.id ? null : route.id)
            }
          >
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-foreground">
                  {route.name}
                </h4>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {route.typical_days}d
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mb-2">
                {route.commodities.slice(0, 3).map((c) => (
                  <Badge
                    key={c}
                    variant="secondary"
                    className="text-[10px] px-1.5 py-0"
                  >
                    {c}
                  </Badge>
                ))}
                {route.commodities.length > 3 && (
                  <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                    +{route.commodities.length - 3}
                  </Badge>
                )}
              </div>
              {route.risk_factors.length > 0 && (
                <div className="text-[11px] text-amber-600 dark:text-amber-400">
                  Risks: {route.risk_factors.join(", ")}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
