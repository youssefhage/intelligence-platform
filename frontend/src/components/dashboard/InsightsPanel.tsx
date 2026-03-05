import { useState } from "react";
import { api } from "../../services/api";
import { useApi } from "../../hooks/useApi";
import type { MarketInsight } from "../../types";

const cardStyle: React.CSSProperties = {
  background: "#1e293b",
  borderRadius: 12,
  padding: 24,
  border: "1px solid #334155",
};

const btnStyle: React.CSSProperties = {
  padding: "10px 20px",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
  background: "#3b82f6",
  color: "#fff",
};

export default function InsightsPanel() {
  const insights = useApi<MarketInsight[]>(
    () => api.getInsights(20) as Promise<MarketInsight[]>
  );
  const [generating, setGenerating] = useState(false);
  const [selectedInsight, setSelectedInsight] = useState<MarketInsight | null>(null);

  const handleGenerateBriefing = async () => {
    setGenerating(true);
    try {
      await api.getDailyBriefing();
      insights.reload();
    } finally {
      setGenerating(false);
    }
  };

  const handleAnalyzeMarket = async () => {
    setGenerating(true);
    try {
      await api.analyzeMarket();
      insights.reload();
    } finally {
      setGenerating(false);
    }
  };

  const parseActions = (actionsStr: string | null): string[] => {
    if (!actionsStr) return [];
    try {
      return JSON.parse(actionsStr);
    } catch {
      return [];
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ fontSize: 22, fontWeight: 600, color: "#f1f5f9" }}>
          AI-Powered Insights
        </h2>
        <div style={{ display: "flex", gap: 12 }}>
          <button
            style={{ ...btnStyle, background: "#059669" }}
            onClick={handleGenerateBriefing}
            disabled={generating}
          >
            {generating ? "Generating..." : "Daily Briefing"}
          </button>
          <button style={btnStyle} onClick={handleAnalyzeMarket} disabled={generating}>
            {generating ? "Analyzing..." : "Market Analysis"}
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: selectedInsight ? "1fr 1fr" : "1fr", gap: 24 }}>
        {/* Insights List */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {insights.loading ? (
            <div style={{ color: "#94a3b8" }}>Loading insights...</div>
          ) : insights.data?.length === 0 ? (
            <div style={cardStyle}>
              <p style={{ color: "#94a3b8" }}>
                No insights yet. Click "Daily Briefing" or "Market Analysis" to generate AI-powered insights.
              </p>
            </div>
          ) : (
            insights.data?.map((insight) => (
              <div
                key={insight.id}
                style={{
                  ...cardStyle,
                  cursor: "pointer",
                  borderColor: selectedInsight?.id === insight.id ? "#3b82f6" : "#334155",
                }}
                onClick={() => setSelectedInsight(insight)}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span
                    style={{
                      fontSize: 11,
                      textTransform: "uppercase",
                      padding: "2px 8px",
                      borderRadius: 4,
                      background:
                        insight.category === "risk"
                          ? "#7f1d1d"
                          : insight.category === "pricing"
                            ? "#1e3a5f"
                            : insight.category === "sourcing"
                              ? "#14532d"
                              : "#334155",
                      color: "#e2e8f0",
                    }}
                  >
                    {insight.category}
                  </span>
                  <span style={{ fontSize: 12, color: "#64748b" }}>
                    {new Date(insight.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h4 style={{ fontSize: 15, fontWeight: 600, color: "#f1f5f9", marginBottom: 8 }}>
                  {insight.title}
                </h4>
                <p style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.5 }}>
                  {insight.summary}
                </p>
                {insight.confidence_score != null && (
                  <div style={{ marginTop: 8, fontSize: 12, color: "#64748b" }}>
                    Confidence: {(insight.confidence_score * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Detail Panel */}
        {selectedInsight && (
          <div style={cardStyle}>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
              {selectedInsight.title}
            </h3>
            <div
              style={{
                fontSize: 14,
                color: "#cbd5e1",
                lineHeight: 1.7,
                marginBottom: 24,
                whiteSpace: "pre-wrap",
              }}
            >
              {selectedInsight.detailed_analysis}
            </div>

            {parseActions(selectedInsight.recommended_actions).length > 0 && (
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9", marginBottom: 12 }}>
                  Recommended Actions
                </h4>
                <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: 8 }}>
                  {parseActions(selectedInsight.recommended_actions).map((action, i) => (
                    <li
                      key={i}
                      style={{
                        padding: "10px 14px",
                        background: "#0f172a",
                        borderRadius: 8,
                        fontSize: 13,
                        color: "#e2e8f0",
                        borderLeft: "3px solid #3b82f6",
                      }}
                    >
                      {action}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
