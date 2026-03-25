"""AI-powered intelligence engine using Moonshot Kimi for market analysis and recommendations."""

import json
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.insight import InsightCategory, MarketInsight
from backend.services.ai_engine.ai_client import get_async_client, is_configured

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are an AI market intelligence analyst for a wholesale FMCG business
operating in Lebanon. Your role is to analyze commodity prices, supply chain data, inventory
levels, and sales patterns to provide actionable business intelligence.

Key context about the Lebanese market:
- The Lebanese pound (LBP) has experienced extreme devaluation since 2019
- Most wholesale transactions are conducted in USD
- The business imports commodities including rice, wheat, oils, sugar, and dairy
- Key sourcing regions include Turkey, Black Sea (Ukraine/Russia), South/Southeast Asia,
  and South America
- Beirut Port is the primary import gateway, with Tripoli as secondary
- Regional instability (Syria, broader Middle East) affects supply routes
- Electricity shortages require diesel generators, making fuel prices critical

When analyzing data, always consider:
1. Currency risk and USD pricing implications
2. Geopolitical risks affecting supply routes
3. Seasonal demand patterns in the Lebanese/Middle Eastern market
4. Alternative sourcing opportunities when primary routes are disrupted
5. Margin protection strategies given volatile input costs

Provide responses in structured JSON format with clear, actionable recommendations."""


class IntelligenceEngine:
    """Uses Moonshot Kimi to analyze market data and generate actionable insights."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = get_async_client()

    async def analyze_market_conditions(
        self, commodity_data: list[dict], supply_chain_data: dict
    ) -> MarketInsight:
        """Generate comprehensive market analysis from current data."""
        prompt = f"""Analyze the following market data for our Lebanese FMCG wholesale business
and provide strategic insights:

## Current Commodity Prices
{json.dumps(commodity_data, indent=2)}

## Supply Chain Status
{json.dumps(supply_chain_data, indent=2)}

Provide your analysis as JSON with these fields:
- "title": A concise title for this market briefing
- "summary": 2-3 sentence executive summary
- "detailed_analysis": Detailed analysis covering price trends, supply risks, and opportunities
- "affected_commodities": List of commodity names most impacted
- "recommended_actions": List of specific, actionable recommendations
- "risk_level": Overall risk level (low/medium/high/critical)
- "confidence_score": Your confidence in this analysis (0.0-1.0)"""

        response = await self.client.chat.completions.create(
            model=settings.ai_model,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        analysis = self._parse_response(response.choices[0].message.content)

        insight = MarketInsight(
            category=InsightCategory.RISK,
            title=analysis.get("title", "Market Conditions Update"),
            summary=analysis.get("summary", ""),
            detailed_analysis=analysis.get("detailed_analysis", ""),
            data_sources=json.dumps(["commodity_tracker", "supply_chain_analyzer"]),
            affected_commodities=json.dumps(analysis.get("affected_commodities", [])),
            recommended_actions=json.dumps(analysis.get("recommended_actions", [])),
            confidence_score=analysis.get("confidence_score", 0.7),
            generated_by="kimi_ai",
            created_at=datetime.utcnow(),
        )
        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)

        logger.info("Market analysis generated", insight_id=insight.id)
        return insight

    async def analyze_pricing_opportunity(
        self,
        product_data: dict,
        commodity_forecast: dict,
        sales_velocity: dict,
    ) -> MarketInsight:
        """Analyze pricing opportunities for a specific product."""
        prompt = f"""Analyze pricing opportunity for the following product in our Lebanese
wholesale FMCG business:

## Product Data
{json.dumps(product_data, indent=2)}

## Commodity Price Forecast (key input cost)
{json.dumps(commodity_forecast, indent=2)}

## Sales Velocity
{json.dumps(sales_velocity, indent=2)}

Provide your analysis as JSON with:
- "title": Concise title
- "summary": 2-3 sentence summary
- "detailed_analysis": Analysis of pricing opportunity
- "recommended_actions": Specific pricing recommendations with reasoning
- "optimal_price_range_usd": {{"min": X, "max": Y}}
- "margin_impact_pct": Expected margin change
- "confidence_score": 0.0-1.0"""

        response = await self.client.chat.completions.create(
            model=settings.ai_model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        analysis = self._parse_response(response.choices[0].message.content)

        insight = MarketInsight(
            category=InsightCategory.PRICING,
            title=analysis.get("title", "Pricing Opportunity Analysis"),
            summary=analysis.get("summary", ""),
            detailed_analysis=analysis.get("detailed_analysis", ""),
            data_sources=json.dumps(
                ["product_catalog", "price_forecaster", "pos_sales"]
            ),
            affected_products=json.dumps([product_data.get("name", "")]),
            recommended_actions=json.dumps(analysis.get("recommended_actions", [])),
            confidence_score=analysis.get("confidence_score", 0.7),
            generated_by="kimi_ai",
            created_at=datetime.utcnow(),
        )
        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)

        return insight

    async def generate_sourcing_recommendations(
        self,
        commodity_name: str,
        current_suppliers: list[dict],
        alternative_suppliers: list[dict],
        price_trend: dict,
    ) -> MarketInsight:
        """Generate sourcing recommendations when supply chain risks are elevated."""
        prompt = f"""Provide sourcing recommendations for {commodity_name} given the following
data for our Lebanese FMCG wholesale business:

## Current Suppliers
{json.dumps(current_suppliers, indent=2)}

## Alternative Suppliers Available
{json.dumps(alternative_suppliers, indent=2)}

## Price Trend & Forecast
{json.dumps(price_trend, indent=2)}

Provide your analysis as JSON with:
- "title": Concise title
- "summary": 2-3 sentence summary
- "detailed_analysis": Full sourcing analysis
- "recommended_actions": Prioritized sourcing actions
- "preferred_suppliers": Ranked list of recommended suppliers with reasoning
- "estimated_savings_pct": Potential savings from optimal sourcing
- "confidence_score": 0.0-1.0"""

        response = await self.client.chat.completions.create(
            model=settings.ai_model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        analysis = self._parse_response(response.choices[0].message.content)

        insight = MarketInsight(
            category=InsightCategory.SOURCING,
            title=analysis.get("title", f"Sourcing Analysis: {commodity_name}"),
            summary=analysis.get("summary", ""),
            detailed_analysis=analysis.get("detailed_analysis", ""),
            data_sources=json.dumps(
                ["supplier_database", "risk_analyzer", "price_forecaster"]
            ),
            affected_commodities=json.dumps([commodity_name]),
            recommended_actions=json.dumps(analysis.get("recommended_actions", [])),
            confidence_score=analysis.get("confidence_score", 0.7),
            generated_by="kimi_ai",
            created_at=datetime.utcnow(),
        )
        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)

        return insight

    async def generate_daily_briefing(
        self,
        commodity_prices: list[dict],
        supply_chain_overview: dict,
        low_stock_items: list[dict],
        top_selling: list[dict],
        recent_alerts: list[dict],
    ) -> MarketInsight:
        """Generate a comprehensive daily intelligence briefing."""
        prompt = f"""Generate a daily intelligence briefing for our Lebanese FMCG wholesale
business leadership:

## Today's Commodity Prices
{json.dumps(commodity_prices, indent=2)}

## Supply Chain Overview
{json.dumps(supply_chain_overview, indent=2)}

## Low Stock Items Requiring Attention
{json.dumps(low_stock_items, indent=2)}

## Top Selling Products (last 7 days)
{json.dumps(top_selling, indent=2)}

## Recent Alerts
{json.dumps(recent_alerts, indent=2)}

Provide a comprehensive daily briefing as JSON with:
- "title": "Daily Intelligence Briefing - [date]"
- "summary": 3-4 sentence executive summary hitting the key points
- "detailed_analysis": Organized analysis covering:
  1. Market conditions and price movements
  2. Supply chain status and risks
  3. Inventory concerns
  4. Sales performance highlights
  5. Key actions needed today
- "recommended_actions": Prioritized list of actions for today
- "confidence_score": 0.0-1.0"""

        response = await self.client.chat.completions.create(
            model=settings.ai_model,
            max_tokens=3000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        analysis = self._parse_response(response.choices[0].message.content)

        insight = MarketInsight(
            category=InsightCategory.RISK,
            title=analysis.get(
                "title",
                f"Daily Intelligence Briefing - {datetime.utcnow().strftime('%Y-%m-%d')}",
            ),
            summary=analysis.get("summary", ""),
            detailed_analysis=analysis.get("detailed_analysis", ""),
            data_sources=json.dumps(
                [
                    "commodity_tracker",
                    "supply_chain_analyzer",
                    "erp_inventory",
                    "pos_sales",
                    "alert_system",
                ]
            ),
            recommended_actions=json.dumps(analysis.get("recommended_actions", [])),
            confidence_score=analysis.get("confidence_score", 0.7),
            generated_by="kimi_ai",
            created_at=datetime.utcnow(),
        )
        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)

        logger.info("Daily briefing generated", insight_id=insight.id)
        return insight

    def _parse_response(self, text: str) -> dict:
        """Extract JSON from Claude's response."""
        # Try to parse the entire response as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON block from markdown
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass

        if "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass

        # Return raw text as analysis
        return {
            "title": "Market Analysis",
            "summary": text[:500],
            "detailed_analysis": text,
        }
