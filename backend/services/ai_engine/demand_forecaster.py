"""Product-level demand forecasting using sales history and seasonal patterns."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.inventory import SalesRecord
from backend.models.product import Product

logger = structlog.get_logger()

# Lebanese FMCG seasonal demand factors
# Reflects Ramadan, holiday seasons, summer, and typical purchasing patterns
SEASONAL_FACTORS = {
    1: 0.90,   # January - post-holiday slowdown
    2: 0.85,   # February - quiet period
    3: 1.05,   # March - pre-Ramadan stocking (varies with Islamic calendar)
    4: 1.15,   # April - Ramadan/Easter season
    5: 1.10,   # May - Eid al-Fitr celebrations
    6: 1.05,   # June - summer begins
    7: 1.10,   # July - peak summer, tourism
    8: 1.08,   # August - summer tourism
    9: 0.95,   # September - back to school
    10: 0.90,  # October - quieter period
    11: 0.95,  # November - pre-holiday
    12: 1.15,  # December - Christmas/New Year
}

# Category-specific seasonal adjustments
CATEGORY_SEASONAL_OVERRIDES = {
    "beverages": {6: 1.30, 7: 1.40, 8: 1.35, 12: 0.90},
    "cooking_oil": {3: 1.20, 4: 1.25, 12: 1.15},
    "rice": {3: 1.25, 4: 1.30, 12: 1.10},
    "sugar": {3: 1.15, 4: 1.20, 6: 1.10, 12: 1.15},
    "dairy": {1: 1.05, 2: 1.05, 6: 0.90, 7: 0.85, 8: 0.85},
}


class DemandForecaster:
    """Forecasts product demand using sales history, seasonality, and trends."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def forecast_product_demand(
        self, product_id: int, horizon_days: int = 30
    ) -> dict:
        """Generate demand forecast for a specific product."""
        product_result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one_or_none()
        if not product:
            return {"error": "Product not found"}

        # Get sales history (up to 365 days)
        df = await self._get_daily_sales(product_id, days=365)

        if df.empty or len(df) < 7:
            return {
                "product_id": product_id,
                "product_name": product.name,
                "error": "Insufficient sales data (need at least 7 days)",
            }

        # Choose forecasting method based on data availability
        if len(df) >= 60:
            forecast = self._seasonal_decomposition_forecast(
                df, product, horizon_days
            )
        else:
            forecast = self._weighted_average_forecast(df, product, horizon_days)

        return forecast

    async def forecast_category_demand(
        self, category: str, horizon_days: int = 30
    ) -> dict:
        """Forecast aggregate demand for a product category."""
        products_result = await self.db.execute(
            select(Product)
            .where(Product.category == category)
            .where(Product.is_active.is_(True))
        )
        products = products_result.scalars().all()

        if not products:
            return {"error": f"No products in category: {category}"}

        forecasts = []
        total_daily_demand = 0
        total_daily_revenue = 0

        for product in products:
            forecast = await self.forecast_product_demand(product.id, horizon_days)
            if "error" not in forecast:
                forecasts.append(forecast)
                total_daily_demand += forecast.get("avg_daily_forecast", 0)
                total_daily_revenue += forecast.get("avg_daily_revenue_forecast", 0)

        return {
            "category": category,
            "products_analyzed": len(forecasts),
            "horizon_days": horizon_days,
            "total_daily_demand_forecast": round(total_daily_demand, 1),
            "total_daily_revenue_forecast": round(total_daily_revenue, 2),
            "total_period_demand_forecast": round(
                total_daily_demand * horizon_days, 0
            ),
            "total_period_revenue_forecast": round(
                total_daily_revenue * horizon_days, 2
            ),
            "product_forecasts": forecasts,
        }

    async def _get_daily_sales(
        self, product_id: int, days: int = 365
    ) -> pd.DataFrame:
        """Aggregate sales into daily totals."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(
                func.date(SalesRecord.sold_at).label("date"),
                func.sum(SalesRecord.quantity_sold).label("quantity"),
                func.sum(SalesRecord.total_usd).label("revenue"),
                func.count(SalesRecord.id).label("transactions"),
            )
            .where(SalesRecord.product_id == product_id)
            .where(SalesRecord.sold_at >= since)
            .group_by(func.date(SalesRecord.sold_at))
            .order_by(func.date(SalesRecord.sold_at))
        )
        rows = result.all()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(
            [
                {
                    "date": row.date,
                    "quantity": float(row.quantity),
                    "revenue": float(row.revenue),
                    "transactions": int(row.transactions),
                }
                for row in rows
            ]
        )
        df["date"] = pd.to_datetime(df["date"])

        # Fill missing dates with zeros
        date_range = pd.date_range(df["date"].min(), df["date"].max())
        df = df.set_index("date").reindex(date_range, fill_value=0).reset_index()
        df = df.rename(columns={"index": "date"})

        return df

    def _seasonal_decomposition_forecast(
        self, df: pd.DataFrame, product: Product, horizon_days: int
    ) -> dict:
        """Forecast using seasonal decomposition + trend extrapolation."""
        # Calculate trend using rolling average
        df["trend"] = df["quantity"].rolling(window=7, min_periods=1).mean()

        # Extract day-of-week pattern
        df["dow"] = df["date"].dt.dayofweek
        dow_pattern = df.groupby("dow")["quantity"].mean()
        overall_avg = df["quantity"].mean()
        dow_factors = {
            day: (avg / overall_avg if overall_avg > 0 else 1.0)
            for day, avg in dow_pattern.items()
        }

        # Linear trend on the rolling average
        x = np.arange(len(df))
        y = df["trend"].values
        mask = ~np.isnan(y)
        if mask.sum() >= 2:
            slope, intercept = np.polyfit(x[mask], y[mask], 1)
        else:
            slope, intercept = 0, overall_avg

        # Generate forecast
        last_date = df["date"].max()
        forecast_dates = pd.date_range(
            last_date + timedelta(days=1), periods=horizon_days
        )

        forecast_data = []
        for i, date in enumerate(forecast_dates):
            base = slope * (len(df) + i) + intercept
            base = max(base, 0)

            # Apply day-of-week factor
            dow_factor = dow_factors.get(date.dayofweek, 1.0)

            # Apply monthly seasonal factor
            seasonal = SEASONAL_FACTORS.get(date.month, 1.0)
            category = (product.category or "").lower()
            if category in CATEGORY_SEASONAL_OVERRIDES:
                seasonal = CATEGORY_SEASONAL_OVERRIDES[category].get(
                    date.month, seasonal
                )

            predicted = base * dow_factor * seasonal

            forecast_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "predicted_quantity": round(max(predicted, 0), 1),
                    "predicted_revenue": round(
                        max(predicted, 0) * (product.current_sell_price_usd or 0), 2
                    ),
                }
            )

        avg_daily = np.mean([f["predicted_quantity"] for f in forecast_data])
        avg_revenue = np.mean([f["predicted_revenue"] for f in forecast_data])

        return {
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category,
            "method": "seasonal_decomposition",
            "horizon_days": horizon_days,
            "data_points_used": len(df),
            "avg_daily_forecast": round(avg_daily, 1),
            "avg_daily_revenue_forecast": round(avg_revenue, 2),
            "total_period_forecast": round(avg_daily * horizon_days, 0),
            "total_period_revenue_forecast": round(avg_revenue * horizon_days, 2),
            "trend_direction": "up" if slope > 0.01 else (
                "down" if slope < -0.01 else "stable"
            ),
            "trend_slope": round(slope, 4),
            "forecast_data": forecast_data,
        }

    def _weighted_average_forecast(
        self, df: pd.DataFrame, product: Product, horizon_days: int
    ) -> dict:
        """Simple weighted moving average forecast for limited data."""
        # Weight recent data more heavily
        weights = np.exp(np.linspace(-1, 0, len(df)))
        weights /= weights.sum()

        weighted_avg = np.average(df["quantity"].values, weights=weights)

        last_date = df["date"].max()
        forecast_dates = pd.date_range(
            last_date + timedelta(days=1), periods=horizon_days
        )

        forecast_data = []
        for date in forecast_dates:
            seasonal = SEASONAL_FACTORS.get(date.month, 1.0)
            predicted = weighted_avg * seasonal

            forecast_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "predicted_quantity": round(max(predicted, 0), 1),
                    "predicted_revenue": round(
                        max(predicted, 0) * (product.current_sell_price_usd or 0), 2
                    ),
                }
            )

        avg_daily = np.mean([f["predicted_quantity"] for f in forecast_data])

        return {
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category,
            "method": "weighted_moving_average",
            "horizon_days": horizon_days,
            "data_points_used": len(df),
            "avg_daily_forecast": round(avg_daily, 1),
            "avg_daily_revenue_forecast": round(
                avg_daily * (product.current_sell_price_usd or 0), 2
            ),
            "total_period_forecast": round(avg_daily * horizon_days, 0),
            "trend_direction": "insufficient_data",
            "forecast_data": forecast_data,
        }
