from __future__ import annotations

from datetime import datetime

import pandas as pd

PROJECTION_COLUMNS = ["date", "projected_stock", "rop_reached", "zero_reached"]


def _empty_projection() -> pd.DataFrame:
    return pd.DataFrame(columns=pd.Index(PROJECTION_COLUMNS))


def build_projection_from_forecast(
    forecast_data: pd.DataFrame,
    current_stock: float,
    rop: float,
    safety_stock: float,
    start_date: datetime,
) -> pd.DataFrame:
    dates = pd.concat([pd.Series([start_date]), forecast_data["data"]], ignore_index=True)
    forecasts = pd.concat([pd.Series([0.0]), forecast_data["forecast"]], ignore_index=True)
    projected_stock = current_stock - forecasts.cumsum()

    projection_df = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "projected_stock": projected_stock,
        "rop_reached": projected_stock <= rop,
        "zero_reached": projected_stock <= 0,
        "rop": rop,
        "safety_stock": safety_stock,
    })

    return projection_df


def filter_and_prepare_forecast(
    forecast_df: pd.DataFrame,
    start_date: datetime,
    projection_months: int
) -> pd.DataFrame:
    dates = pd.to_datetime(forecast_df["data"])

    if start_date is None:
        start_date = dates.min()

    end_date = start_date + pd.DateOffset(months=projection_months)

    mask = (dates >= start_date) & (dates <= end_date)
    filtered = forecast_df.loc[mask, :].copy()
    filtered["data"] = dates[mask]

    return filtered.sort_values(by="data")


def calculate_stock_projection(
    sku: str,
    current_stock: float,
    rop: float,
    safety_stock: float,
    forecast_df: pd.DataFrame,
    start_date: datetime,
    projection_months: int = 12,
) -> pd.DataFrame:
    if forecast_df.empty:
        return _empty_projection()

    sku_forecast = pd.DataFrame(forecast_df[forecast_df["sku"] == sku])
    if sku_forecast.empty:
        return _empty_projection()

    sku_forecast = filter_and_prepare_forecast(sku_forecast, start_date, projection_months)
    return build_projection_from_forecast(sku_forecast, current_stock, rop, safety_stock, start_date)


def calculate_model_stock_projection(
    model: str,
    current_stock: float,
    rop: float,
    safety_stock: float,
    forecast_df: pd.DataFrame,
    start_date: datetime,
    projection_months: int = 12,
) -> pd.DataFrame:
    if forecast_df.empty:
        return _empty_projection()

    mask = forecast_df["sku"].astype(str).str.startswith(model)
    model_forecast = forecast_df[mask].copy()
    if model_forecast.empty:
        return _empty_projection()

    model_forecast = filter_and_prepare_forecast(model_forecast, start_date, projection_months)
    model_forecast_aggregated = pd.DataFrame(model_forecast.groupby("data", as_index=False, observed=True).agg({"forecast": "sum"}))

    return build_projection_from_forecast(
        model_forecast_aggregated, current_stock, rop, safety_stock, start_date
    )
