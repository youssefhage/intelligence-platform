"""Supply chain risk analysis engine for Lebanese FMCG wholesale."""

import json
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.alert import Alert, AlertSeverity, AlertType
from backend.models.supplier import RiskLevel, Supplier, SupplierRiskAssessment

logger = structlog.get_logger()

# Geopolitical risk scores by region (0-100, higher = riskier)
# Reflects current instability relevant to Lebanese supply chains
REGIONAL_RISK_SCORES = {
    "Lebanon": 85,
    "Syria": 95,
    "Iraq": 70,
    "Turkey": 45,
    "Ukraine": 90,
    "Russia": 75,
    "Black Sea": 80,
    "Eastern Europe": 40,
    "South Asia": 35,
    "Southeast Asia": 25,
    "South America": 30,
    "North America": 15,
    "Western Europe": 15,
    "Oceania": 10,
    "Middle East": 60,
    "Global": 40,
}

# Shipping route risk factors (port congestion, piracy, sanctions)
ROUTE_RISK_FACTORS = {
    "Suez Canal": 55,
    "Mediterranean": 40,
    "Beirut Port": 70,
    "Tripoli Port": 60,
    "Black Sea": 80,
    "Indian Ocean": 50,
    "Atlantic": 20,
    "Overland Turkey": 50,
    "Overland Syria": 90,
}


class SupplyChainRiskAnalyzer:
    """Analyzes and monitors supply chain risks for the Lebanese market."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_supplier_risk(self, supplier_id: int) -> SupplierRiskAssessment:
        """Perform a comprehensive risk assessment for a supplier."""
        result = await self.db.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )
        supplier = result.scalar_one_or_none()
        if not supplier:
            raise ValueError(f"Supplier {supplier_id} not found")

        # Calculate component risk scores
        geo_risk = self._calculate_geopolitical_risk(supplier)
        logistics_risk = self._calculate_logistics_risk(supplier)
        financial_risk = self._calculate_financial_risk(supplier)
        currency_risk = self._calculate_currency_risk(supplier)

        # Weighted composite score
        composite = (
            geo_risk * 0.35
            + logistics_risk * 0.25
            + financial_risk * 0.20
            + currency_risk * 0.20
        )

        risk_level = self._score_to_risk_level(composite)
        risk_factors = self._identify_risk_factors(
            supplier, geo_risk, logistics_risk, financial_risk, currency_risk
        )
        recommendations = self._generate_recommendations(
            supplier, risk_level, risk_factors
        )

        assessment = SupplierRiskAssessment(
            supplier_id=supplier_id,
            risk_level=risk_level,
            risk_factors=json.dumps(risk_factors),
            geopolitical_risk=round(geo_risk, 1),
            logistics_risk=round(logistics_risk, 1),
            financial_risk=round(financial_risk, 1),
            currency_risk=round(currency_risk, 1),
            recommendations=json.dumps(recommendations),
            assessed_at=datetime.utcnow(),
        )
        self.db.add(assessment)

        # Update supplier current risk level
        supplier.current_risk_level = risk_level
        await self.db.commit()
        await self.db.refresh(assessment)

        # Generate alert if risk is high
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            await self._create_risk_alert(supplier, assessment)

        logger.info(
            "Supplier risk assessed",
            supplier=supplier.name,
            risk_level=risk_level.value,
            composite_score=round(composite, 1),
        )
        return assessment

    def _calculate_geopolitical_risk(self, supplier: Supplier) -> float:
        country_score = REGIONAL_RISK_SCORES.get(supplier.country, 50)
        region_score = REGIONAL_RISK_SCORES.get(supplier.region or "", 50)
        return (country_score * 0.6 + region_score * 0.4)

    def _calculate_logistics_risk(self, supplier: Supplier) -> float:
        base_risk = 30.0

        # Lead time risk
        if supplier.lead_time_days:
            if supplier.lead_time_days > 60:
                base_risk += 30
            elif supplier.lead_time_days > 30:
                base_risk += 15

        # Shipping route risk
        if supplier.shipping_route:
            for route, risk in ROUTE_RISK_FACTORS.items():
                if route.lower() in supplier.shipping_route.lower():
                    base_risk = max(base_risk, risk)

        return min(base_risk, 100)

    def _calculate_financial_risk(self, supplier: Supplier) -> float:
        base_risk = 25.0

        # Reliability score inversely affects financial risk
        if supplier.reliability_score is not None:
            base_risk = 100 - supplier.reliability_score

        return min(base_risk, 100)

    def _calculate_currency_risk(self, supplier: Supplier) -> float:
        """Lebanese operations face significant currency risk."""
        # Lebanon's LBP has been highly volatile
        base_currency_risk = 65.0

        # Suppliers in USD-denominated economies have lower currency risk
        low_currency_risk_countries = {"USA", "Panama", "Ecuador"}
        if supplier.country in low_currency_risk_countries:
            base_currency_risk = 20.0
        elif supplier.country in {"Turkey"}:
            base_currency_risk = 70.0  # TRY also volatile

        return base_currency_risk

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        if score >= 75:
            return RiskLevel.CRITICAL
        if score >= 55:
            return RiskLevel.HIGH
        if score >= 35:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _identify_risk_factors(
        self,
        supplier: Supplier,
        geo_risk: float,
        logistics_risk: float,
        financial_risk: float,
        currency_risk: float,
    ) -> list[str]:
        factors = []
        if geo_risk > 60:
            factors.append(
                f"High geopolitical instability in {supplier.country}/{supplier.region}"
            )
        if logistics_risk > 60:
            factors.append(
                f"Logistics risk due to shipping route or extended lead times ({supplier.lead_time_days} days)"
            )
        if financial_risk > 60:
            factors.append("Elevated financial/counterparty risk")
        if currency_risk > 60:
            factors.append("Significant currency exposure risk (LBP volatility)")
        if supplier.country in ("Ukraine", "Russia"):
            factors.append("Active conflict zone affecting supply reliability")
        return factors

    def _generate_recommendations(
        self,
        supplier: Supplier,
        risk_level: RiskLevel,
        risk_factors: list[str],
    ) -> list[str]:
        recommendations = []

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recommendations.append(
                "Identify and pre-qualify alternative suppliers in lower-risk regions"
            )
            recommendations.append(
                "Increase safety stock for products dependent on this supplier"
            )

        if supplier.country in ("Ukraine", "Russia"):
            recommendations.append(
                "Diversify grain/oil sourcing to Turkey, India, or South America"
            )

        if any("currency" in f.lower() for f in risk_factors):
            recommendations.append(
                "Negotiate USD-denominated contracts to hedge currency risk"
            )
            recommendations.append(
                "Consider forward contracts to lock in prices"
            )

        if any("logistics" in f.lower() for f in risk_factors):
            recommendations.append(
                "Explore alternative shipping routes (e.g., Tripoli port as backup)"
            )
            recommendations.append(
                "Build buffer inventory to cover extended transit times"
            )

        return recommendations

    async def _create_risk_alert(
        self, supplier: Supplier, assessment: SupplierRiskAssessment
    ):
        severity = (
            AlertSeverity.CRITICAL
            if assessment.risk_level == RiskLevel.CRITICAL
            else AlertSeverity.WARNING
        )
        risk_factors = json.loads(assessment.risk_factors)

        alert = Alert(
            alert_type=AlertType.SUPPLY_DISRUPTION,
            severity=severity,
            title=f"Supply chain risk elevated: {supplier.name}",
            message=(
                f"Supplier {supplier.name} ({supplier.country}) has been assessed as "
                f"{assessment.risk_level.value} risk. "
                f"Key factors: {'; '.join(risk_factors)}"
            ),
            related_entity_type="supplier",
            related_entity_id=supplier.id,
            action_recommended=json.loads(assessment.recommendations)[0]
            if assessment.recommendations
            else None,
        )
        self.db.add(alert)
        await self.db.commit()

    async def get_supply_chain_overview(self) -> dict:
        """Get a high-level overview of supply chain risk status."""
        result = await self.db.execute(
            select(Supplier).where(Supplier.is_active.is_(True))
        )
        suppliers = result.scalars().all()

        risk_distribution = {level.value: 0 for level in RiskLevel}
        high_risk_suppliers = []

        for supplier in suppliers:
            risk_distribution[supplier.current_risk_level.value] += 1
            if supplier.current_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                high_risk_suppliers.append(
                    {
                        "id": supplier.id,
                        "name": supplier.name,
                        "country": supplier.country,
                        "risk_level": supplier.current_risk_level.value,
                        "commodities": (
                            json.loads(supplier.commodities_supplied)
                            if supplier.commodities_supplied
                            else []
                        ),
                    }
                )

        return {
            "total_suppliers": len(suppliers),
            "risk_distribution": risk_distribution,
            "high_risk_suppliers": high_risk_suppliers,
            "overall_risk_score": self._compute_overall_risk(suppliers),
        }

    def _compute_overall_risk(self, suppliers: list[Supplier]) -> float:
        if not suppliers:
            return 0.0
        risk_values = {
            RiskLevel.LOW: 15,
            RiskLevel.MEDIUM: 40,
            RiskLevel.HIGH: 70,
            RiskLevel.CRITICAL: 95,
        }
        scores = [risk_values[s.current_risk_level] for s in suppliers]
        return round(sum(scores) / len(scores), 1)

    async def find_alternative_suppliers(
        self, commodity_name: str, exclude_countries: list[str] | None = None
    ) -> list[dict]:
        """Suggest alternative suppliers for a commodity, avoiding risky regions."""
        exclude = set(exclude_countries or [])
        result = await self.db.execute(
            select(Supplier).where(Supplier.is_active.is_(True))
        )
        suppliers = result.scalars().all()

        alternatives = []
        for supplier in suppliers:
            if supplier.country in exclude:
                continue
            if not supplier.commodities_supplied:
                continue
            commodities = json.loads(supplier.commodities_supplied)
            if commodity_name.lower() in [c.lower() for c in commodities]:
                alternatives.append(
                    {
                        "id": supplier.id,
                        "name": supplier.name,
                        "country": supplier.country,
                        "risk_level": supplier.current_risk_level.value,
                        "lead_time_days": supplier.lead_time_days,
                        "reliability_score": supplier.reliability_score,
                    }
                )

        # Sort by risk level then reliability
        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        alternatives.sort(
            key=lambda s: (
                risk_order.get(s["risk_level"], 99),
                -(s["reliability_score"] or 0),
            )
        )
        return alternatives
