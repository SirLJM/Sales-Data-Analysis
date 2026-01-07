from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_projection_from_forecast(
    forecast_data: pd.DataFrame,
    current_stock: float,
    rop: float,
    safety_stock: float,
    start_date: datetime,
) -> pd.DataFrame:
    projection = [
        {
            "date": start_date,
            "projected_stock": current_stock,
            "rop_reached": current_stock <= rop,
            "zero_reached": current_stock <= 0,
        }
    ]

    running_stock = current_stock

    for _, row in forecast_data.iterrows():
        running_stock -= row["forecast"]

        projection.append(
            {
                "date": row["data"],
                "projected_stock": running_stock,
                "rop_reached": running_stock <= rop,
                "zero_reached": running_stock <= 0,
            }
        )

    projection_df = pd.DataFrame(projection)
    projection_df["date"] = pd.to_datetime(projection_df["date"])
    projection_df["rop"] = rop
    projection_df["safety_stock"] = safety_stock

    return projection_df


def filter_and_prepare_forecast(
    forecast_df: pd.DataFrame,
    start_date: datetime,
    projection_months: int
) -> pd.DataFrame:
    df = forecast_df.copy()
    df["data"] = pd.to_datetime(df["data"])

    if start_date is None:
        start_date = df["data"].min()

    end_date = start_date + pd.DateOffset(months=projection_months)

    mask = (df["data"] >= start_date) & (df["data"] <= end_date)
    filtered = df.loc[mask, :].copy()

    sorted_result = filtered.sort_values(by="data")
    return sorted_result


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
        return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

    sku_forecast = forecast_df[forecast_df["sku"] == sku].copy()

    if sku_forecast.empty:
        return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

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
        return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

    forecast_df = forecast_df.copy()
    forecast_df["model"] = forecast_df["sku"].astype(str).str[:5]

    model_forecast = forecast_df[forecast_df["model"] == model].copy()

    if model_forecast.empty:
        return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

    model_forecast = filter_and_prepare_forecast(model_forecast, start_date, projection_months)

    model_forecast_aggregated = model_forecast.groupby("data", as_index=False, observed=True).agg({"forecast": "sum"})

    return build_projection_from_forecast(
        model_forecast_aggregated, current_stock, rop, safety_stock, start_date
    )
