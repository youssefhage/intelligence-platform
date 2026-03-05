"""Tests for the price forecasting engine."""

import numpy as np
import pandas as pd

from backend.services.market_data.price_forecaster import PriceForecaster
from unittest.mock import AsyncMock


class TestStatisticalForecast:
    def setup_method(self):
        self.db = AsyncMock()
        self.forecaster = PriceForecaster(self.db)

    def test_linear_trend_up(self):
        """Test that an upward trend is detected correctly."""
        dates = pd.date_range("2025-01-01", periods=20, freq="D")
        prices = [100 + i * 2 for i in range(20)]  # Clear upward trend
        df = pd.DataFrame({"ds": dates, "y": prices})

        result = self.forecaster._statistical_forecast(df, "Test Commodity", 10)

        assert result["method"] == "linear_regression"
        assert result["expected_change_pct"] > 0
        assert result["forecast_end_price_usd"] > result["current_price_usd"]
        assert len(result["forecast_data"]) == 10

    def test_linear_trend_down(self):
        """Test that a downward trend is detected correctly."""
        dates = pd.date_range("2025-01-01", periods=20, freq="D")
        prices = [200 - i * 3 for i in range(20)]
        df = pd.DataFrame({"ds": dates, "y": prices})

        result = self.forecaster._statistical_forecast(df, "Test Commodity", 10)

        assert result["expected_change_pct"] < 0
        assert result["forecast_end_price_usd"] < result["current_price_usd"]

    def test_forecast_confidence_intervals(self):
        """Test that confidence intervals are generated."""
        dates = pd.date_range("2025-01-01", periods=20, freq="D")
        np.random.seed(42)
        prices = [100 + i + np.random.randn() * 5 for i in range(20)]
        df = pd.DataFrame({"ds": dates, "y": prices})

        result = self.forecaster._statistical_forecast(df, "Test", 5)

        for point in result["forecast_data"]:
            assert point["lower_bound"] < point["predicted"]
            assert point["upper_bound"] > point["predicted"]

    def test_forecast_data_points_count(self):
        """Test that correct number of data points is reported."""
        dates = pd.date_range("2025-01-01", periods=15, freq="D")
        prices = [100] * 15
        df = pd.DataFrame({"ds": dates, "y": prices})

        result = self.forecaster._statistical_forecast(df, "Test", 7)

        assert result["data_points_used"] == 15
        assert len(result["forecast_data"]) == 7
