"""Tests for supply chain risk analysis."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.supplier import RiskLevel, Supplier
from backend.services.supply_chain.risk_analyzer import SupplyChainRiskAnalyzer


def _make_supplier(**kwargs) -> Supplier:
    defaults = {
        "id": 1,
        "name": "Test Supplier",
        "country": "Turkey",
        "region": "Eastern Europe",
        "lead_time_days": 20,
        "shipping_route": "Mediterranean, Beirut Port",
        "reliability_score": 75.0,
        "current_risk_level": RiskLevel.LOW,
        "commodities_supplied": '["wheat", "sunflower oil"]',
        "is_active": True,
        "payment_terms": "NET 30",
        "contact_info": None,
    }
    defaults.update(kwargs)
    supplier = MagicMock(spec=Supplier)
    for k, v in defaults.items():
        setattr(supplier, k, v)
    return supplier


class TestRiskCalculations:
    def setup_method(self):
        self.db = AsyncMock()
        self.analyzer = SupplyChainRiskAnalyzer(self.db)

    def test_geopolitical_risk_turkey(self):
        supplier = _make_supplier(country="Turkey", region="Eastern Europe")
        risk = self.analyzer._calculate_geopolitical_risk(supplier)
        assert 30 <= risk <= 50  # Turkey is moderate risk

    def test_geopolitical_risk_ukraine(self):
        supplier = _make_supplier(country="Ukraine", region="Black Sea")
        risk = self.analyzer._calculate_geopolitical_risk(supplier)
        assert risk >= 80  # Ukraine is high risk due to conflict

    def test_geopolitical_risk_new_zealand(self):
        supplier = _make_supplier(country="New Zealand", region="Oceania")
        risk = self.analyzer._calculate_geopolitical_risk(supplier)
        assert risk <= 30  # Low risk region

    def test_logistics_risk_long_lead_time(self):
        supplier = _make_supplier(lead_time_days=75, shipping_route="Atlantic")
        risk = self.analyzer._calculate_logistics_risk(supplier)
        assert risk >= 50  # Long lead time increases risk

    def test_logistics_risk_beirut_port(self):
        supplier = _make_supplier(shipping_route="Beirut Port")
        risk = self.analyzer._calculate_logistics_risk(supplier)
        assert risk >= 60  # Beirut Port has elevated risk

    def test_currency_risk_lebanon(self):
        supplier = _make_supplier(country="Lebanon")
        risk = self.analyzer._calculate_currency_risk(supplier)
        assert risk >= 60  # LBP is highly volatile

    def test_currency_risk_usa(self):
        supplier = _make_supplier(country="USA")
        risk = self.analyzer._calculate_currency_risk(supplier)
        assert risk <= 25  # USD-denominated, low risk

    def test_score_to_risk_level(self):
        assert self.analyzer._score_to_risk_level(20) == RiskLevel.LOW
        assert self.analyzer._score_to_risk_level(40) == RiskLevel.MEDIUM
        assert self.analyzer._score_to_risk_level(60) == RiskLevel.HIGH
        assert self.analyzer._score_to_risk_level(80) == RiskLevel.CRITICAL

    def test_identify_risk_factors_high_geo_risk(self):
        supplier = _make_supplier(country="Ukraine", region="Black Sea")
        factors = self.analyzer._identify_risk_factors(supplier, 85, 30, 30, 30)
        assert any("geopolitical" in f.lower() for f in factors)
        assert any("conflict" in f.lower() for f in factors)

    def test_generate_recommendations_high_risk(self):
        supplier = _make_supplier(country="Ukraine")
        recommendations = self.analyzer._generate_recommendations(
            supplier, RiskLevel.HIGH, ["currency risk"]
        )
        assert len(recommendations) > 0
        assert any("alternative" in r.lower() or "diversify" in r.lower() for r in recommendations)
