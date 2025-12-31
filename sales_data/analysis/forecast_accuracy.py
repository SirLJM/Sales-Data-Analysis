from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def prepare_daily_comparison(
        sales_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        stock_history_df: pd.DataFrame,
        analysis_start: datetime,
        analysis_end: datetime,
        entity_type: str = "sku",
) -> pd.DataFrame:
    if sales_df.empty or forecast_df.empty:
        return pd.DataFrame()

    entity_col = "model" if entity_type == "model" else "sku"

    daily_actual = _aggregate_daily_sales(sales_df, analysis_start, analysis_end, entity_col)
    daily_forecast = _prepare_daily_forecast(forecast_df, analysis_start, analysis_end, entity_col)
    daily_stock = _prepare_daily_stock(stock_history_df, analysis_start, analysis_end, entity_col)

    comparison = daily_forecast.merge(daily_actual, on=[entity_col, "date"], how="left")
    comparison["actual"] = comparison["actual"].fillna(0)

    if not daily_stock.empty:
        comparison = comparison.merge(daily_stock, on=[entity_col, "date"], how="left")
        comparison["stock_level"] = comparison["stock_level"].ffill()
        comparison["stock_level"] = comparison["stock_level"].fillna(0)
    else:
        comparison["stock_level"] = np.nan

    comparison["had_stock"] = comparison["stock_level"].isna() | (comparison["stock_level"] > 0)

    return comparison


def _aggregate_daily_sales(
        sales_df: pd.DataFrame, start: datetime, end: datetime, entity_col: str
) -> pd.DataFrame:
    df = sales_df.copy()
    df["date"] = pd.to_datetime(df["data"]).dt.date  # type: ignore[attr-defined]

    if entity_col == "model":
        if "model" not in df.columns:
            df["model"] = df["sku"].astype(str).str[:5]
    else:
        df[entity_col] = df["sku"]

    df = df[(df["date"] >= start.date()) & (df["date"] <= end.date())]

    daily = df.groupby([entity_col, "date"], as_index=False).agg(actual=("ilosc", "sum"))

    return daily


def _prepare_daily_forecast(
        forecast_df: pd.DataFrame, start: datetime, end: datetime, entity_col: str
) -> pd.DataFrame:
    df = forecast_df.copy()
    df["date"] = pd.to_datetime(df["data"]).dt.date  # type: ignore[attr-defined]

    if entity_col == "model":
        if "model" not in df.columns:
            df["model"] = df["sku"].astype(str).str[:5]
    else:
        df[entity_col] = df["sku"]

    daily = df.groupby([entity_col, "date"], as_index=False).agg(forecast=("forecast", "sum"))
    daily = daily[(daily["date"] >= start.date()) & (daily["date"] <= end.date())]

    return daily


def _prepare_daily_stock(
        stock_df: pd.DataFrame, start: datetime, end: datetime, entity_col: str
) -> pd.DataFrame:
    if stock_df.empty:
        return pd.DataFrame()

    df = stock_df.copy()
    df["date"] = pd.to_datetime(df["snapshot_date"]).dt.date  # type: ignore[attr-defined]

    if entity_col == "model":
        df["model"] = df["sku"].astype(str).str[:5]
    else:
        df[entity_col] = df["sku"]

    daily = df.groupby([entity_col, "date"], as_index=False).agg(
        stock_level=("available_stock", "sum")
    )
    daily = daily[(daily["date"] >= start.date()) & (daily["date"] <= end.date())]

    return daily


def calculate_accuracy_metrics(comparison_df: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    if comparison_df.empty:
        return pd.DataFrame()

    def compute_entity_metrics(group: pd.DataFrame) -> pd.Series:
        g_with_stock = group[group["had_stock"]]
        g_without_stock = group[~group["had_stock"]]

        forecast_total = g_with_stock["forecast"].sum() if not g_with_stock.empty else 0
        actual_total = g_with_stock["actual"].sum() if not g_with_stock.empty else 0
        days_analyzed = len(g_with_stock)
        days_stockout = len(g_without_stock)
        missed_opportunity = g_without_stock["forecast"].sum() if not g_without_stock.empty else 0

        mape = _calculate_mape(g_with_stock)
        bias = _calculate_bias(g_with_stock)
        mae = _calculate_mae(g_with_stock)
        rmse = _calculate_rmse(g_with_stock)

        return pd.Series({
            "MAPE": mape,
            "BIAS": bias,
            "MAE": mae,
            "RMSE": rmse,
            "FORECAST_TOTAL": forecast_total,
            "ACTUAL_TOTAL": actual_total,
            "DAYS_ANALYZED": days_analyzed,
            "DAYS_STOCKOUT": days_stockout,
            "MISSED_OPPORTUNITY": missed_opportunity,
        })

    results = comparison_df.groupby(entity_col).apply(compute_entity_metrics, include_groups=False).reset_index()
    results.columns = [entity_col.upper()] + list(results.columns[1:])

    return results


def _calculate_mape(df: pd.DataFrame) -> float:
    if df.empty:
        return np.nan
    valid = df[df["actual"] > 0]
    if valid.empty:
        return np.nan
    ape = np.abs(valid["actual"] - valid["forecast"]) / valid["actual"]
    return round(ape.mean() * 100, 2)


def _calculate_bias(df: pd.DataFrame) -> float:
    if df.empty:
        return np.nan
    valid = df[df["actual"] > 0]
    if valid.empty:
        return np.nan
    pe = (valid["forecast"] - valid["actual"]) / valid["actual"]
    return round(pe.mean() * 100, 2)


def _calculate_mae(df: pd.DataFrame) -> float:
    if df.empty:
        return np.nan
    ae = np.abs(df["actual"] - df["forecast"])
    return round(ae.mean(), 2)


def _calculate_rmse(df: pd.DataFrame) -> float:
    if df.empty:
        return np.nan
    se = (df["actual"] - df["forecast"]) ** 2
    return round(np.sqrt(se.mean()), 2)


def calculate_forecast_accuracy(
        sales_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        stock_history_df: pd.DataFrame,
        analysis_start: datetime,
        analysis_end: datetime,
        entity_type: str = "sku",
) -> pd.DataFrame:
    comparison = prepare_daily_comparison(
        sales_df, forecast_df, stock_history_df, analysis_start, analysis_end, entity_type
    )

    if comparison.empty:
        return pd.DataFrame()

    entity_col = "model" if entity_type == "model" else "sku"
    return calculate_accuracy_metrics(comparison, entity_col)


def aggregate_accuracy_by_product_type(
        accuracy_df: pd.DataFrame, sku_summary: pd.DataFrame, entity_type: str = "sku"
) -> pd.DataFrame:
    if accuracy_df.empty or sku_summary.empty:
        return pd.DataFrame()

    id_col = "MODEL" if entity_type == "model" else "SKU"

    if id_col not in sku_summary.columns or "TYPE" not in sku_summary.columns:
        return pd.DataFrame()

    type_lookup = sku_summary[[id_col, "TYPE"]].drop_duplicates()

    merged = accuracy_df.merge(type_lookup, on=id_col, how="left")
    merged["TYPE"] = merged["TYPE"].fillna("unknown")

    type_summary = merged.groupby("TYPE").agg({
        "MAPE": "mean",
        "BIAS": "mean",
        "MAE": "mean",
        "RMSE": "mean",
        "FORECAST_TOTAL": "sum",
        "ACTUAL_TOTAL": "sum",
        "DAYS_ANALYZED": "sum",
        "DAYS_STOCKOUT": "sum",
        "MISSED_OPPORTUNITY": "sum",
        id_col: "count",
    }).reset_index()

    type_summary = type_summary.rename(columns={id_col: "COUNT"})
    type_summary["MAPE"] = type_summary["MAPE"].round(2)
    type_summary["BIAS"] = type_summary["BIAS"].round(2)
    type_summary["MAE"] = type_summary["MAE"].round(2)
    type_summary["RMSE"] = type_summary["RMSE"].round(2)

    return type_summary


def calculate_accuracy_trend(
        sales_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        stock_history_df: pd.DataFrame,
        analysis_start: datetime,
        analysis_end: datetime,
        entity_type: str = "sku",
        period: str = "week",
) -> pd.DataFrame:
    comparison = prepare_daily_comparison(
        sales_df, forecast_df, stock_history_df, analysis_start, analysis_end, entity_type
    )

    if comparison.empty:
        return pd.DataFrame()

    comparison["date"] = pd.to_datetime(comparison["date"])

    if period == "week":
        # noinspection PyUnresolvedReferences
        comparison["period"] = comparison["date"].dt.to_period("W").apply(lambda x: x.start_time)
    else:
        # noinspection PyUnresolvedReferences
        comparison["period"] = comparison["date"].dt.to_period("M").apply(lambda x: x.start_time)

    def compute_period_metrics(group: pd.DataFrame) -> pd.Series:
        g_with_stock = group[group["had_stock"]]
        mape = _calculate_mape(g_with_stock)
        bias = _calculate_bias(g_with_stock)
        return pd.Series({"MAPE": mape, "BIAS": bias})

    trend = comparison.groupby("period").apply(compute_period_metrics, include_groups=False).reset_index()
    trend = trend.sort_values("period")

    return trend


def find_historical_forecast(
        forecast_files: list[tuple[Path, datetime]],
        target_date: datetime,
        lookback_months: int = 4,
) -> tuple[Path, datetime] | None:
    if not forecast_files:
        return None

    target_generated_date = target_date - timedelta(days=lookback_months * 30.44)
    tolerance_days = 14

    matching = [
        (path, date) for path, date in forecast_files
        if abs((date - target_generated_date).days) <= tolerance_days
    ]

    if not matching:
        return None

    return min(matching, key=lambda x: abs((x[1] - target_generated_date).days))


def get_overall_metrics(accuracy_df: pd.DataFrame) -> dict:
    if accuracy_df.empty:
        return {
            "mape": None,
            "bias": None,
            "mae": None,
            "rmse": None,
            "total_forecast": 0,
            "total_actual": 0,
            "total_missed_opportunity": 0,
            "total_days_analyzed": 0,
            "total_days_stockout": 0,
        }

    valid_mape = accuracy_df[accuracy_df["MAPE"].notna()]["MAPE"]
    valid_bias = accuracy_df[accuracy_df["BIAS"].notna()]["BIAS"]

    return {
        "mape": round(valid_mape.mean(), 2) if not valid_mape.empty else None,
        "bias": round(valid_bias.mean(), 2) if not valid_bias.empty else None,
        "mae": round(accuracy_df["MAE"].mean(), 2),
        "rmse": round(accuracy_df["RMSE"].mean(), 2),
        "total_forecast": int(accuracy_df["FORECAST_TOTAL"].sum()),
        "total_actual": int(accuracy_df["ACTUAL_TOTAL"].sum()),
        "total_missed_opportunity": int(accuracy_df["MISSED_OPPORTUNITY"].sum()),
        "total_days_analyzed": int(accuracy_df["DAYS_ANALYZED"].sum()),
        "total_days_stockout": int(accuracy_df["DAYS_STOCKOUT"].sum()),
    }
