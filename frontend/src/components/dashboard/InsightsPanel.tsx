import { useState } from "react";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { MarketInsight } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Sparkles, FileBarChart, X } from "lucide-react";

const categoryVariant = (category: string) => {
  switch (category) {
    case "risk": return "destructive" as const;
    case "pricing": return "default" as const;
    case "sourcing": return "success" as const;
    default: return "secondary" as const;
  }
};

export default function InsightsPanel() {
  const insights = useApi<MarketInsight[]>(
    () => api.getInsights(20) as Promise<MarketInsight[]>
  );
  const [generating, setGenerating] = useState(false);
  const [selectedInsight, setSelectedInsight] = useState<MarketInsight | null>(null);

  const handleGenerateBriefing = async () => {
    setGenerating(true);
    try { await api.getDailyBriefing(); insights.reload(); }
    finally { setGenerating(false); }
  };

  const handleAnalyzeMarket = async () => {
    setGenerating(true);
    try { await api.analyzeMarket(); insights.reload(); }
    finally { setGenerating(false); }
  };

  const parseActions = (actionsStr: string | null): string[] => {
    if (!actionsStr) return [];
    try { return JSON.parse(actionsStr); }
    catch { return []; }
  };

  return (
    <div className="space-y-6">
      {/* Actions Bar */}
      <div className="flex flex-wrap gap-3">
        <Button variant="success" onClick={handleGenerateBriefing} disabled={generating}>
          <Sparkles className="h-4 w-4" />
          {generating ? "Generating..." : "Daily Briefing"}
        </Button>
        <Button onClick={handleAnalyzeMarket} disabled={generating}>
          <FileBarChart className="h-4 w-4" />
          {generating ? "Analyzing..." : "Market Analysis"}
        </Button>
      </div>

      <div className={cn("grid grid-cols-1 gap-6", selectedInsight && "lg:grid-cols-2")}>
        {/* Insights List */}
        <div className="space-y-3">
          {insights.loading ? (
            [1, 2, 3].map((i) => <Skeleton key={i} className="h-32 rounded-xl" />)
          ) : insights.data?.length === 0 ? (
            <Card>
              <CardContent className="flex h-48 items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  No insights yet. Click "Daily Briefing" or "Market Analysis" to generate AI-powered insights.
                </p>
              </CardContent>
            </Card>
          ) : (
            insights.data?.map((insight) => (
              <Card
                key={insight.id}
                className={cn(
                  "cursor-pointer transition-all hover:shadow-md",
                  selectedInsight?.id === insight.id && "ring-2 ring-primary"
                )}
                onClick={() => setSelectedInsight(insight)}
              >
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <Badge variant={categoryVariant(insight.category)}>{insight.category}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(insight.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h4 className="mt-3 text-[15px] font-semibold text-foreground">{insight.title}</h4>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground line-clamp-3">
                    {insight.summary}
                  </p>
                  {insight.confidence_score != null && (
                    <div className="mt-3 flex items-center gap-2">
                      <div className="h-1.5 flex-1 rounded-full bg-muted">
                        <div
                          className="h-1.5 rounded-full bg-primary"
                          style={{ width: `${insight.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {(insight.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Detail Panel */}
        {selectedInsight && (
          <Card className="sticky top-24 self-start">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base">{selectedInsight.title}</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setSelectedInsight(null)} className="h-8 w-8 shrink-0">
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                {selectedInsight.detailed_analysis}
              </div>

              {parseActions(selectedInsight.recommended_actions).length > 0 && (
                <div>
                  <h4 className="mb-3 text-sm font-semibold text-foreground">Recommended Actions</h4>
                  <div className="space-y-2">
                    {parseActions(selectedInsight.recommended_actions).map((action, i) => (
                      <div
                        key={i}
                        className="rounded-lg border-l-[3px] border-l-primary bg-muted/50 px-4 py-2.5 text-sm text-foreground"
                      >
                        {action}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
