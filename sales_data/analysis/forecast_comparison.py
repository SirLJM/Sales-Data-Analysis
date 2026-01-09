from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logging_config import get_logger

logger = get_logger("forecast_comparison")


def align_forecasts(
        internal_forecast_df: pd.DataFrame,
        external_forecast_df: pd.DataFrame,
        actual_sales_df: pd.DataFrame,
        entity_type: str = "model",
) -> pd.DataFrame:
    if internal_forecast_df.empty:
        return pd.DataFrame()

    internal = internal_forecast_df.copy()
    internal["year_month"] = internal["period"].astype(str)

    if entity_type == "model":
        external = _aggregate_external_to_model_monthly(external_forecast_df)
        actual = _aggregate_actual_to_model_monthly(actual_sales_df)
    else:
        external = _aggregate_external_to_sku_monthly(external_forecast_df)
        actual = _aggregate_actual_to_sku_monthly(actual_sales_df)

    internal_agg = internal.groupby(["entity_id", "year_month"], as_index=False, observed=True).agg({
        "forecast": "sum",
        "method": "first",
    })
    internal_agg = internal_agg.rename(columns={"forecast": "internal_forecast"})

    comparison = internal_agg.merge(
        external,
        on=["entity_id", "year_month"],
        how="left",
    )

    comparison = comparison.merge(
        actual,
        on=["entity_id", "year_month"],
        how="left",
    )

    with pd.option_context("future.no_silent_downcasting", True):
        comparison["external_forecast"] = comparison["external_forecast"].fillna(0).infer_objects(copy=False)
        comparison["actual"] = comparison["actual"].fillna(0).infer_objects(copy=False)

    return comparison


def _aggregate_external_to_model_monthly(forecast_df: pd.DataFrame) -> pd.DataFrame:
    if forecast_df is None or forecast_df.empty:
        return pd.DataFrame(columns=["entity_id", "year_month", "external_forecast"])

    df = forecast_df.copy()

    date_col = _find_column(df, ["data", "forecast_date", "date"])
    sku_col = _find_column(df, ["sku", "SKU"])
    forecast_col = _find_column(df, ["forecast", "forecast_quantity", "FORECAST"])

    if date_col is None or sku_col is None or forecast_col is None:
        return pd.DataFrame(columns=["entity_id", "year_month", "external_forecast"])

    df["entity_id"] = df[sku_col].astype(str).str[:5]
    df["year_month"] = pd.to_datetime(df[date_col]).dt.to_period("M").astype(str)  # type: ignore[attr-defined]

    monthly = df.groupby(["entity_id", "year_month"], as_index=False, observed=True)[[forecast_col]].sum()
    monthly = monthly.rename(columns={forecast_col: "external_forecast"})

    return monthly


def _aggregate_external_to_sku_monthly(forecast_df: pd.DataFrame) -> pd.DataFrame:
    if forecast_df is None or forecast_df.empty:
        return pd.DataFrame(columns=["entity_id", "year_month", "external_forecast"])

    df = forecast_df.copy()

    date_col = _find_column(df, ["data", "forecast_date", "date"])
    sku_col = _find_column(df, ["sku", "SKU"])
    forecast_col = _find_column(df, ["forecast", "forecast_quantity", "FORECAST"])

    if date_col is None or sku_col is None or forecast_col is None:
        return pd.DataFrame(columns=["entity_id", "year_month", "external_forecast"])

    df["entity_id"] = df[sku_col].astype(str)
    df["year_month"] = pd.to_datetime(df[date_col]).dt.to_period("M").astype(str)  # type: ignore[attr-defined]

    monthly = df.groupby(["entity_id", "year_month"], as_index=False, observed=True)[[forecast_col]].sum()
    monthly = monthly.rename(columns={forecast_col: "external_forecast"})

    return monthly


def _aggregate_actual_to_model_monthly(sales_df: pd.DataFrame) -> pd.DataFrame:
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["entity_id", "year_month", "actual"])

    df = sales_df.copy()

    date_col = _find_column(df, ["data", "sale_date", "date"])
    sku_col = _find_column(df, ["sku", "SKU"])
    qty_col = _find_column(df, ["ilosc", "quantity", "total_quantity"])

    if date_col is None or sku_col is None or qty_col is None:
        return pd.DataFrame(columns=["entity_id", "year_month", "actual"])

    df["entity_id"] = df[sku_col].astype(str).str[:5]
    df["year_month"] = pd.to_datetime(df[date_col]).dt.to_period("M").astype(str)  # type: ignore[attr-defined]

    monthly = df.groupby(["entity_id", "year_month"], as_index=False, observed=True)[[qty_col]].sum()
    monthly = monthly.rename(columns={qty_col: "actual"})

    return monthly


def _aggregate_actual_to_sku_monthly(sales_df: pd.DataFrame) -> pd.DataFrame:
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["entity_id", "year_month", "actual"])

    df = sales_df.copy()

    date_col = _find_column(df, ["data", "sale_date", "date"])
    sku_col = _find_column(df, ["sku", "SKU"])
    qty_col = _find_column(df, ["ilosc", "quantity", "total_quantity"])

    if date_col is None or sku_col is None or qty_col is None:
        return pd.DataFrame(columns=["entity_id", "year_month", "actual"])

    df["entity_id"] = df[sku_col].astype(str)
    df["year_month"] = pd.to_datetime(df[date_col]).dt.to_period("M").astype(str)  # type: ignore[attr-defined]

    monthly = df.groupby(["entity_id", "year_month"], as_index=False, observed=True)[[qty_col]].sum()
    monthly = monthly.rename(columns={qty_col: "actual"})

    return monthly


def calculate_comparison_metrics(comparison_df: pd.DataFrame) -> pd.DataFrame:
    if comparison_df.empty:
        return pd.DataFrame()

    results = []

    for entity_id, group in comparison_df.groupby("entity_id", observed=True):
        valid = group[group["actual"] > 0]

        if valid.empty:
            continue

        internal_errors = np.abs(valid["internal_forecast"] - valid["actual"])
        external_errors = np.abs(valid["external_forecast"] - valid["actual"])

        internal_mape = (internal_errors / valid["actual"]).mean() * 100
        external_mape = (external_errors / valid["actual"]).mean() * 100

        internal_bias = ((valid["internal_forecast"] - valid["actual"]) / valid["actual"]).mean() * 100
        external_bias = ((valid["external_forecast"] - valid["actual"]) / valid["actual"]).mean() * 100

        internal_mae = internal_errors.mean()
        external_mae = external_errors.mean()

        internal_rmse = np.sqrt(((valid["internal_forecast"] - valid["actual"]) ** 2).mean())
        external_rmse = np.sqrt(((valid["external_forecast"] - valid["actual"]) ** 2).mean())

        if internal_mape < external_mape:
            winner = "internal"
            improvement = external_mape - internal_mape
        elif external_mape < internal_mape:
            winner = "external"
            improvement = internal_mape - external_mape
        else:
            winner = "tie"
            improvement = 0

        results.append({
            "entity_id": entity_id,
            "method": group["method"].iloc[0] if "method" in group.columns else "unknown",
            "months_compared": len(valid),
            "total_actual": valid["actual"].sum(),
            "internal_mape": internal_mape,
            "external_mape": external_mape,
            "internal_bias": internal_bias,
            "external_bias": external_bias,
            "internal_mae": internal_mae,
            "external_mae": external_mae,
            "internal_rmse": internal_rmse,
            "external_rmse": external_rmse,
            "winner": winner,
            "improvement_pct": improvement,
        })

    return pd.DataFrame(results)


def _build_type_map(entity_metadata: pd.DataFrame) -> dict | None:
    id_col = _find_column(entity_metadata, ["entity_id", "SKU", "sku", "MODEL", "model"])
    type_col = _find_column(entity_metadata, ["TYPE", "type", "product_type"])

    if not id_col or not type_col:
        return None

    meta = entity_metadata.copy()
    is_model_level = "model" in id_col.lower() or meta[id_col].str.len().max() <= 5
    meta["_id"] = meta[id_col].astype(str) if is_model_level else meta[id_col].astype(str).str[:5]

    return meta.set_index("_id")[type_col].to_dict()


def _add_product_type_column(metrics_df: pd.DataFrame, entity_metadata: pd.DataFrame) -> pd.DataFrame:
    df = metrics_df.copy()

    if entity_metadata is None or entity_metadata.empty:
        df["product_type"] = "unknown"
        return df

    type_map = _build_type_map(entity_metadata)
    if type_map is None:
        df["product_type"] = "unknown"
    else:
        df["product_type"] = df["entity_id"].map(type_map).fillna("unknown")

    return df


def _summarize_group(ptype: str, group: pd.DataFrame) -> dict:
    total = len(group)
    internal_wins = (group["winner"] == "internal").sum()
    external_wins = (group["winner"] == "external").sum()
    ties = (group["winner"] == "tie").sum()

    return {
        "product_type": ptype,
        "total_entities": total,
        "internal_wins": internal_wins,
        "external_wins": external_wins,
        "ties": ties,
        "internal_win_pct": internal_wins / total * 100 if total > 0 else 0,
        "external_win_pct": external_wins / total * 100 if total > 0 else 0,
        "avg_internal_mape": group["internal_mape"].mean(),
        "avg_external_mape": group["external_mape"].mean(),
        "avg_improvement": group["improvement_pct"].mean(),
    }


def aggregate_comparison_by_type(
        metrics_df: pd.DataFrame,
        entity_metadata: pd.DataFrame,
) -> pd.DataFrame:
    if metrics_df.empty:
        return pd.DataFrame()

    metrics_df = _add_product_type_column(metrics_df, entity_metadata)
    summary = [_summarize_group(ptype, group) for ptype, group in metrics_df.groupby("product_type", observed=True)]

    return pd.DataFrame(summary)


def calculate_overall_summary(metrics_df: pd.DataFrame) -> dict:
    if metrics_df.empty:
        return {}

    total = len(metrics_df)
    internal_wins = (metrics_df["winner"] == "internal").sum()
    external_wins = (metrics_df["winner"] == "external").sum()
    ties = (metrics_df["winner"] == "tie").sum()

    return {
        "total_entities": total,
        "internal_wins": internal_wins,
        "external_wins": external_wins,
        "ties": ties,
        "internal_win_pct": internal_wins / total * 100 if total > 0 else 0,
        "external_win_pct": external_wins / total * 100 if total > 0 else 0,
        "avg_internal_mape": metrics_df["internal_mape"].mean(),
        "avg_external_mape": metrics_df["external_mape"].mean(),
        "avg_internal_bias": metrics_df["internal_bias"].mean(),
        "avg_external_bias": metrics_df["external_bias"].mean(),
        "median_improvement": metrics_df["improvement_pct"].median(),
    }


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None
