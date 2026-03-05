"""Price forecasting engine using Prophet and statistical methods."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.commodity import Commodity, CommodityPrice

logger = structlog.get_logger()


class PriceForecaster:
    """Forecasts commodity prices using time series analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_price_dataframe(
        self, commodity_id: int, days: int = 365
    ) -> pd.DataFrame:
        """Load price history into a DataFrame."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.commodity_id == commodity_id)
            .where(CommodityPrice.recorded_at >= since)
            .order_by(CommodityPrice.recorded_at.asc())
        )
        prices = result.scalars().all()

        if not prices:
            return pd.DataFrame()

        df = pd.DataFrame(
            [{"ds": p.recorded_at, "y": p.price_usd} for p in prices]
        )
        df["ds"] = pd.to_datetime(df["ds"])
        return df

    async def forecast_prices(
        self, commodity_id: int, horizon_days: int = 30
    ) -> dict:
        """Generate price forecast for a commodity.

        Uses Prophet if sufficient data is available, falls back to
        linear trend extrapolation for smaller datasets.
        """
        df = await self._get_price_dataframe(commodity_id, days=365)

        if df.empty:
            return {"error": "Insufficient price data for forecasting"}

        commodity_result = await self.db.execute(
            select(Commodity).where(Commodity.id == commodity_id)
        )
        commodity = commodity_result.scalar_one_or_none()
        commodity_name = commodity.name if commodity else f"Commodity {commodity_id}"

        # Use Prophet for datasets with enough data points
        if len(df) >= 30:
            return await self._prophet_forecast(df, commodity_name, horizon_days)

        # Fallback to statistical extrapolation
        return self._statistical_forecast(df, commodity_name, horizon_days)

    async def _prophet_forecast(
        self, df: pd.DataFrame, commodity_name: str, horizon_days: int
    ) -> dict:
        """Forecast using Facebook Prophet."""
        try:
            from prophet import Prophet

            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.1,
            )
            model.fit(df)

            future = model.make_future_dataframe(periods=horizon_days)
            forecast = model.predict(future)

            forecast_data = forecast.tail(horizon_days)[
                ["ds", "yhat", "yhat_lower", "yhat_upper"]
            ].to_dict("records")

            current_price = df["y"].iloc[-1]
            forecast_end_price = forecast_data[-1]["yhat"]
            expected_change_pct = (
                (forecast_end_price - current_price) / current_price
            ) * 100

            return {
                "commodity": commodity_name,
                "current_price_usd": round(current_price, 2),
                "forecast_horizon_days": horizon_days,
                "forecast_end_price_usd": round(forecast_end_price, 2),
                "expected_change_pct": round(expected_change_pct, 2),
                "forecast_data": [
                    {
                        "date": r["ds"].isoformat(),
                        "predicted": round(r["yhat"], 2),
                        "lower_bound": round(r["yhat_lower"], 2),
                        "upper_bound": round(r["yhat_upper"], 2),
                    }
                    for r in forecast_data
                ],
                "method": "prophet",
                "data_points_used": len(df),
            }
        except Exception as e:
            logger.warning("Prophet forecast failed, falling back", error=str(e))
            return self._statistical_forecast(df, commodity_name, horizon_days)

    def _statistical_forecast(
        self, df: pd.DataFrame, commodity_name: str, horizon_days: int
    ) -> dict:
        """Simple linear regression forecast as fallback."""
        df = df.copy()
        df["day_num"] = (df["ds"] - df["ds"].min()).dt.days
        x = df["day_num"].values
        y = df["y"].values

        # Linear regression
        n = len(x)
        x_mean, y_mean = np.mean(x), np.mean(y)
        slope = np.sum((x - x_mean) * (y - y_mean)) / max(np.sum((x - x_mean) ** 2), 1e-10)
        intercept = y_mean - slope * x_mean

        # Forecast
        last_day = x[-1]
        forecast_days = np.arange(last_day + 1, last_day + horizon_days + 1)
        predicted = slope * forecast_days + intercept

        # Compute volatility for confidence intervals
        residuals = y - (slope * x + intercept)
        std_err = np.std(residuals)

        current_price = y[-1]
        forecast_end_price = predicted[-1]
        expected_change_pct = ((forecast_end_price - current_price) / current_price) * 100

        base_date = df["ds"].max()
        forecast_data = []
        for i, day in enumerate(forecast_days):
            date = base_date + timedelta(days=int(day - last_day))
            forecast_data.append(
                {
                    "date": date.isoformat(),
                    "predicted": round(predicted[i], 2),
                    "lower_bound": round(predicted[i] - 1.96 * std_err, 2),
                    "upper_bound": round(predicted[i] + 1.96 * std_err, 2),
                }
            )

        return {
            "commodity": commodity_name,
            "current_price_usd": round(current_price, 2),
            "forecast_horizon_days": horizon_days,
            "forecast_end_price_usd": round(forecast_end_price, 2),
            "expected_change_pct": round(expected_change_pct, 2),
            "forecast_data": forecast_data,
            "method": "linear_regression",
            "data_points_used": len(df),
            "trend_direction": "up" if slope > 0 else "down",
            "daily_volatility_usd": round(std_err, 2),
        }

    async def detect_price_anomalies(
        self, commodity_id: int, threshold_std: float = 2.0
    ) -> list[dict]:
        """Detect unusual price movements using z-score analysis."""
        df = await self._get_price_dataframe(commodity_id, days=90)
        if len(df) < 10:
            return []

        df["returns"] = df["y"].pct_change()
        mean_return = df["returns"].mean()
        std_return = df["returns"].std()

        if std_return == 0:
            return []

        df["z_score"] = (df["returns"] - mean_return) / std_return
        anomalies = df[df["z_score"].abs() > threshold_std]

        return [
            {
                "date": row["ds"].isoformat(),
                "price_usd": round(row["y"], 2),
                "return_pct": round(row["returns"] * 100, 2),
                "z_score": round(row["z_score"], 2),
                "direction": "spike" if row["z_score"] > 0 else "drop",
            }
            for _, row in anomalies.iterrows()
        ]
