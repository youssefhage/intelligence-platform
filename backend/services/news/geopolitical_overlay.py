"""Geopolitical event to commodity impact mapping and scenario modeling."""

import structlog

logger = structlog.get_logger()

# Static mapping of geopolitical scenarios to commodity impacts
SCENARIO_IMPACTS = {
    "red_sea_closure": {
        "name": "Red Sea Route Closed",
        "description": "Houthi attacks or military conflict closes the Red Sea shipping route, forcing diversions around Cape of Good Hope.",
        "affected_commodities": {
            "Container Freight Rate": {"direction": "up", "estimated_pct": 40, "confidence": "high"},
            "Baltic Dry Index": {"direction": "up", "estimated_pct": 25, "confidence": "high"},
            "Brent Crude Oil": {"direction": "up", "estimated_pct": 10, "confidence": "medium"},
            "Diesel": {"direction": "up", "estimated_pct": 12, "confidence": "medium"},
        },
        "note": "All imports via Suez Canal (India, SE Asia, China) face 10-14 day delays and ~40% cost increase.",
    },
    "russia_ukraine_escalation": {
        "name": "Russia-Ukraine Conflict Escalation",
        "description": "Renewed fighting disrupts Black Sea grain exports from Ukraine and Russia.",
        "affected_commodities": {
            "Wheat": {"direction": "up", "estimated_pct": 20, "confidence": "high"},
            "Sunflower Oil": {"direction": "up", "estimated_pct": 30, "confidence": "high"},
            "Maize": {"direction": "up", "estimated_pct": 15, "confidence": "medium"},
        },
        "note": "Ukraine and Russia account for ~30% of global wheat exports and ~75% of sunflower oil exports.",
    },
    "turkey_currency_crisis": {
        "name": "Turkey Currency Crisis",
        "description": "Sharp TRY depreciation makes Turkish exports cheaper in USD terms.",
        "affected_commodities": {
            "USD/TRY": {"direction": "up", "estimated_pct": 20, "confidence": "high"},
            "Wheat": {"direction": "down", "estimated_pct": 5, "confidence": "medium"},
            "Flour": {"direction": "down", "estimated_pct": 8, "confidence": "medium"},
            "Sunflower Oil": {"direction": "down", "estimated_pct": 5, "confidence": "low"},
        },
        "note": "Turkish suppliers may offer better FOB prices to generate USD revenue, but supply reliability may decrease.",
    },
    "china_export_restrictions": {
        "name": "China Export Restrictions",
        "description": "China imposes export quotas or tariffs on manufactured goods and packaging materials.",
        "affected_commodities": {
            "HDPE (Plastic)": {"direction": "up", "estimated_pct": 15, "confidence": "medium"},
            "PET Resin": {"direction": "up", "estimated_pct": 15, "confidence": "medium"},
            "Polypropylene (PP)": {"direction": "up", "estimated_pct": 15, "confidence": "medium"},
            "Aluminum": {"direction": "up", "estimated_pct": 10, "confidence": "medium"},
            "Paper/Cardboard": {"direction": "up", "estimated_pct": 8, "confidence": "low"},
        },
        "note": "China is the dominant global supplier of packaging materials. Restrictions would affect all FMCG packaging costs.",
    },
    "middle_east_escalation": {
        "name": "Middle East Conflict Escalation",
        "description": "Regional military escalation affecting Gulf shipping lanes and energy supply.",
        "affected_commodities": {
            "Brent Crude Oil": {"direction": "up", "estimated_pct": 25, "confidence": "high"},
            "Diesel": {"direction": "up", "estimated_pct": 20, "confidence": "high"},
            "Container Freight Rate": {"direction": "up", "estimated_pct": 30, "confidence": "high"},
            "USD/LBP": {"direction": "up", "estimated_pct": 10, "confidence": "medium"},
        },
        "note": "Direct impact on Lebanon's fuel supply and shipping costs. All import costs would increase.",
    },
    "egypt_devaluation": {
        "name": "Egypt Currency Devaluation",
        "description": "Sharp EGP devaluation makes Egyptian imports cheaper in USD.",
        "affected_commodities": {
            "USD/EGP": {"direction": "up", "estimated_pct": 15, "confidence": "high"},
            "Flour": {"direction": "down", "estimated_pct": 5, "confidence": "medium"},
        },
        "note": "Egypt is a key regional supplier. Devaluation may create short-term sourcing opportunities.",
    },
}

# Supply routes used by AHT
SUPPLY_ROUTES = [
    {
        "id": "china_beirut",
        "name": "China → Beirut",
        "origin": {"lat": 31.23, "lng": 121.47, "city": "Shanghai"},
        "destination": {"lat": 33.90, "lng": 35.50, "city": "Beirut"},
        "waypoints": ["Strait of Malacca", "Indian Ocean", "Red Sea / Suez Canal", "Mediterranean"],
        "typical_days": 30,
        "commodities": ["HDPE (Plastic)", "PET Resin", "Polypropylene (PP)", "Aluminum", "Paper/Cardboard", "Paraffin Wax"],
        "risk_factors": ["Red Sea disruption", "Suez Canal congestion"],
    },
    {
        "id": "turkey_beirut",
        "name": "Turkey → Beirut",
        "origin": {"lat": 41.01, "lng": 28.98, "city": "Istanbul"},
        "destination": {"lat": 33.90, "lng": 35.50, "city": "Beirut"},
        "waypoints": ["Aegean Sea", "Mediterranean"],
        "typical_days": 7,
        "commodities": ["Wheat", "Flour", "Sunflower Oil", "Paper/Cardboard", "Caustic Soda"],
        "risk_factors": ["Turkey currency volatility"],
    },
    {
        "id": "egypt_beirut",
        "name": "Egypt → Beirut",
        "origin": {"lat": 31.20, "lng": 29.92, "city": "Alexandria"},
        "destination": {"lat": 33.90, "lng": 35.50, "city": "Beirut"},
        "waypoints": ["Mediterranean"],
        "typical_days": 3,
        "commodities": ["Flour", "Sugar (Raw)"],
        "risk_factors": ["Egypt currency devaluation", "Suez Canal disruption"],
    },
    {
        "id": "india_beirut",
        "name": "India → Beirut",
        "origin": {"lat": 19.08, "lng": 72.88, "city": "Mumbai"},
        "destination": {"lat": 33.90, "lng": 35.50, "city": "Beirut"},
        "waypoints": ["Arabian Sea", "Red Sea / Suez Canal", "Mediterranean"],
        "typical_days": 21,
        "commodities": ["Rice (Long Grain)", "Tea", "Sugar (Raw)"],
        "risk_factors": ["Red Sea disruption", "Monsoon season delays"],
    },
    {
        "id": "brazil_beirut",
        "name": "Brazil → Beirut",
        "origin": {"lat": -23.55, "lng": -46.63, "city": "Santos"},
        "destination": {"lat": 33.90, "lng": 35.50, "city": "Beirut"},
        "waypoints": ["South Atlantic", "Mediterranean"],
        "typical_days": 28,
        "commodities": ["Coffee (Arabica)", "Soybean Oil", "Sugar (Raw)"],
        "risk_factors": ["Long transit time"],
    },
    {
        "id": "gulf_beirut",
        "name": "Gulf → Beirut",
        "origin": {"lat": 24.47, "lng": 54.37, "city": "Abu Dhabi"},
        "destination": {"lat": 33.90, "lng": 35.50, "city": "Beirut"},
        "waypoints": ["Red Sea / Suez Canal", "Mediterranean"],
        "typical_days": 10,
        "commodities": ["Diesel", "HDPE (Plastic)", "Polypropylene (PP)"],
        "risk_factors": ["Red Sea disruption", "Regional conflict"],
    },
]


class GeopoliticalOverlay:
    """Provides geopolitical event impact analysis for commodities."""

    def get_scenario_types(self) -> list[dict]:
        """List all available scenario types."""
        return [
            {
                "id": key,
                "name": scenario["name"],
                "description": scenario["description"],
                "affected_count": len(scenario["affected_commodities"]),
            }
            for key, scenario in SCENARIO_IMPACTS.items()
        ]

    def run_scenario(self, scenario_id: str) -> dict:
        """Run a geopolitical scenario and return commodity impacts."""
        scenario = SCENARIO_IMPACTS.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}"}
        return scenario

    def get_supply_routes(self) -> list[dict]:
        """Get all supply routes with their metadata."""
        return SUPPLY_ROUTES

    def assess_route_risk(self, active_scenarios: list[str]) -> list[dict]:
        """Assess supply route risks based on active scenarios."""
        routes_with_risk = []
        for route in SUPPLY_ROUTES:
            risk_score = 0
            active_risks = []
            for scenario_id in active_scenarios:
                scenario = SCENARIO_IMPACTS.get(scenario_id)
                if not scenario:
                    continue
                # Check if any route commodity is affected
                for commodity in route["commodities"]:
                    if commodity in scenario["affected_commodities"]:
                        impact = scenario["affected_commodities"][commodity]
                        if impact["direction"] == "up":
                            risk_score += impact["estimated_pct"]
                            active_risks.append(scenario["name"])
                            break

            routes_with_risk.append({
                **route,
                "risk_score": min(risk_score, 100),
                "risk_level": "critical" if risk_score > 30 else "high" if risk_score > 15 else "medium" if risk_score > 5 else "low",
                "active_risks": list(set(active_risks)),
            })
        return routes_with_risk
