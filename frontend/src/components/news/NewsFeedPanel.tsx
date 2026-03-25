import { useState } from "react";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { NewsArticle, GeopoliticalScenario, GeopoliticalScenarioResult, CommodityImpact } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  Newspaper,
  Globe,
  ExternalLink,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export default function NewsFeedPanel() {
  const news = useApi<NewsArticle[]>(
    () => api.getNewsFeed(30) as Promise<NewsArticle[]>
  );
  const scenarios = useApi<GeopoliticalScenario[]>(
    () => api.getGeopoliticalScenarios() as Promise<GeopoliticalScenario[]>
  );
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [scenarioResult, setScenarioResult] = useState<GeopoliticalScenarioResult | null>(null);
  const [loadingScenario, setLoadingScenario] = useState(false);
  const [fetching, setFetching] = useState(false);

  const handleFetchNews = async () => {
    setFetching(true);
    try {
      await api.fetchNews();
      // Refresh the news list
      window.location.reload();
    } finally {
      setFetching(false);
    }
  };

  const handleRunScenario = async (id: string) => {
    setSelectedScenario(id);
    setLoadingScenario(true);
    try {
      const result = await api.runGeopoliticalScenario(id) as GeopoliticalScenarioResult;
      setScenarioResult(result);
    } finally {
      setLoadingScenario(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* News Feed */}
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Newspaper className="h-5 w-5" />
                Commodity News
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={handleFetchNews}
                disabled={fetching}
              >
                <RefreshCw className={cn("h-3.5 w-3.5 mr-1.5", fetching && "animate-spin")} />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {news.loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-20" />
                ))}
              </div>
            ) : news.data && news.data.length > 0 ? (
              <div className="space-y-3 max-h-[700px] overflow-y-auto">
                {news.data.map((article) => (
                  <a
                    key={article.id}
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-lg border border-border p-3 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-medium text-foreground line-clamp-2">
                        {article.title}
                      </h4>
                      <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground mt-0.5" />
                    </div>
                    <div className="mt-2 flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-muted-foreground">
                        {article.source}
                      </span>
                      {article.published_at && (
                        <span className="text-xs text-muted-foreground">
                          {new Date(article.published_at).toLocaleDateString()}
                        </span>
                      )}
                      {article.matched_commodities?.map((com) => (
                        <Badge key={com} variant="secondary" className="text-[10px] px-1.5 py-0">
                          {com}
                        </Badge>
                      ))}
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-muted-foreground mb-3">No news articles yet.</p>
                <Button variant="outline" size="sm" onClick={handleFetchNews}>
                  Fetch Latest News
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Geopolitical Scenarios */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              Geopolitical Scenarios
            </CardTitle>
          </CardHeader>
          <CardContent>
            {scenarios.loading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {scenarios.data?.map((scenario) => (
                  <div key={scenario.id}>
                    <button
                      onClick={() => handleRunScenario(scenario.id)}
                      className={cn(
                        "w-full text-left rounded-lg p-3 border transition-colors",
                        selectedScenario === scenario.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-muted/50"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                        <span className="text-sm font-medium">{scenario.name}</span>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                        {scenario.description}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Affects {scenario.affected_count} commodities
                      </p>
                    </button>

                    {/* Scenario Result */}
                    {selectedScenario === scenario.id && scenarioResult && !loadingScenario && (
                      <div className="mt-2 ml-3 pl-3 border-l-2 border-primary/30 space-y-2">
                        {scenarioResult.affected_commodities &&
                          Object.entries(scenarioResult.affected_commodities).map(
                            ([commodity, impact]) => {
                              const typedImpact = impact as CommodityImpact;
                              return (
                                <div key={commodity} className="flex items-center justify-between text-sm">
                                  <span>{commodity}</span>
                                  <span
                                    className={cn(
                                      "font-mono text-xs",
                                      typedImpact.direction === "up"
                                        ? "text-destructive"
                                        : "text-success"
                                    )}
                                  >
                                    {typedImpact.direction === "up" ? "+" : "-"}
                                    {typedImpact.estimated_pct}%
                                  </span>
                                </div>
                              );
                            }
                          )}
                        {scenarioResult.note && (
                          <p className="text-xs text-muted-foreground italic mt-2">
                            {scenarioResult.note}
                          </p>
                        )}
                      </div>
                    )}
                    {selectedScenario === scenario.id && loadingScenario && (
                      <Skeleton className="h-20 mt-2" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
