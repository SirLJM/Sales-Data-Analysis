from __future__ import annotations

import pandas as pd

from .inventory_metrics import calculate_forecast_date_range
from .utils import parse_sku_components


def calculate_order_priority(
    summary_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    forecast_time_months: float = 5,
    settings: dict | None = None,
) -> pd.DataFrame:
    if settings is None:
        from utils.settings_manager import load_settings
        settings = load_settings()

    config = _extract_priority_config(settings)
    df = summary_df.copy()

    _validate_required_columns(df)
    df = _add_forecast_leadtime(df, forecast_df, forecast_time_months)
    df = _add_sku_components(df)
    df = _calculate_stockout_risk(df, config)
    df = _calculate_revenue_impact(df)
    df = _apply_type_multipliers(df, config["type_multipliers"])
    df = _calculate_priority_score(df, config)
    df["URGENT"] = (df["STOCK"] == 0) & (df["FORECAST_LEADTIME"] > 0)

    return df.sort_values("PRIORITY_SCORE", ascending=False)


def _extract_priority_config(settings: dict) -> dict:
    rec_settings = settings.get("order_recommendations", {})
    stockout_cfg = rec_settings.get("stockout_risk", {})
    weights = rec_settings.get("priority_weights", {})

    return {
        "zero_stock_penalty": stockout_cfg.get("zero_stock_penalty", 100),
        "below_rop_max": stockout_cfg.get("below_rop_max_penalty", 80),
        "weight_stockout": weights.get("stockout_risk", 0.5),
        "weight_revenue": weights.get("revenue_impact", 0.3),
        "weight_demand": weights.get("demand_forecast", 0.2),
        "type_multipliers": rec_settings.get("type_multipliers", {}),
        "demand_cap": rec_settings.get("demand_cap", 100),
    }


def _validate_required_columns(df: pd.DataFrame) -> None:
    required_cols = ["SKU", "STOCK", "ROP", "TYPE"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")


def _add_forecast_leadtime(
    df: pd.DataFrame, forecast_df: pd.DataFrame, forecast_time_months: float
) -> pd.DataFrame:
    if forecast_df.empty:
        df["FORECAST_LEADTIME"] = 0
        return df

    forecast_start, forecast_end = calculate_forecast_date_range(forecast_time_months)

    forecast_window = forecast_df[
        (forecast_df["data"] >= forecast_start) & (forecast_df["data"] < forecast_end)
    ]

    if forecast_window.empty:
        df["FORECAST_LEADTIME"] = 0
        return df

    forecast_sum = forecast_window.groupby("sku", observed=True)["forecast"].sum().reset_index()
    forecast_sum.columns = ["SKU", "FORECAST_LEADTIME"]
    df = df.merge(forecast_sum, on="SKU", how="left")
    df["FORECAST_LEADTIME"] = df["FORECAST_LEADTIME"].fillna(0)
    return df


def _add_sku_components(df: pd.DataFrame) -> pd.DataFrame:
    sku_components = df["SKU"].apply(parse_sku_components)
    df["MODEL"] = sku_components.apply(lambda x: x["model"])
    df["COLOR"] = sku_components.apply(lambda x: x["color"])
    df["SIZE"] = sku_components.apply(lambda x: x["size"])
    return df


def _calculate_stockout_risk(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    df["STOCKOUT_RISK"] = 0.0
    zero_stock_mask = (df["STOCK"] <= 0) & (df["FORECAST_LEADTIME"] > 0)
    df.loc[zero_stock_mask, "STOCKOUT_RISK"] = config["zero_stock_penalty"]

    below_rop_mask = (df["STOCK"] > 0) & (df["STOCK"] < df["ROP"])
    df.loc[below_rop_mask, "STOCKOUT_RISK"] = (
        (df["ROP"] - df["STOCK"]) / df["ROP"] * config["below_rop_max"]
    )
    return df


def _calculate_revenue_impact(df: pd.DataFrame) -> pd.DataFrame:
    if "PRICE" in df.columns:
        df["REVENUE_AT_RISK"] = df["FORECAST_LEADTIME"] * df["PRICE"]
        max_revenue = df["REVENUE_AT_RISK"].max()
        df["REVENUE_IMPACT"] = (df["REVENUE_AT_RISK"] / max_revenue * 100) if max_revenue > 0 else 0
    else:
        max_forecast = df["FORECAST_LEADTIME"].max()
        df["REVENUE_IMPACT"] = (df["FORECAST_LEADTIME"] / max_forecast * 100) if max_forecast > 0 else 0
    return df


def _apply_type_multipliers(df: pd.DataFrame, type_multipliers: dict) -> pd.DataFrame:
    default_type_mult = {"new": 1.2, "seasonal": 1.3, "regular": 1.0, "basic": 0.9}
    type_mult = {k: type_multipliers.get(k, v) for k, v in default_type_mult.items()}
    df["TYPE_MULTIPLIER"] = df["TYPE"].map(type_mult).fillna(1.0)
    return df


def _calculate_priority_score(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    df["DEFICIT"] = (df["ROP"] - df["STOCK"]).clip(lower=0)
    df["PRIORITY_SCORE"] = (
        (df["STOCKOUT_RISK"] * config["weight_stockout"])
        + (df["REVENUE_IMPACT"] * config["weight_revenue"])
        + (df["FORECAST_LEADTIME"].clip(upper=config["demand_cap"]) * config["weight_demand"])
    ) * df["TYPE_MULTIPLIER"]
    return df


def aggregate_order_by_model_color(priority_df: pd.DataFrame) -> pd.DataFrame:
    agg_dict = {
        "PRIORITY_SCORE": "mean",
        "DEFICIT": "sum",
        "FORECAST_LEADTIME": "sum",
        "STOCK": "sum",
        "ROP": "sum",
        "SS": "sum",
        "URGENT": "any",
    }

    if "REVENUE_AT_RISK" in priority_df.columns:
        agg_dict["REVENUE_AT_RISK"] = "sum"

    grouped = (
        priority_df.groupby(["MODEL", "COLOR"], as_index=False, observed=True)
        .agg(agg_dict)
        .sort_values("PRIORITY_SCORE", ascending=False)
    )

    grouped["COVERAGE_GAP"] = grouped["FORECAST_LEADTIME"] - grouped["STOCK"]
    grouped["COVERAGE_GAP"] = grouped["COVERAGE_GAP"].clip(lower=0)

    return grouped


def get_size_quantities_for_model_color(
    priority_df: pd.DataFrame, model: str, color: str
) -> dict[str, int]:
    filtered = priority_df[(priority_df["MODEL"] == model) & (priority_df["COLOR"] == color)]

    size_quantities = {}

    for _, row in filtered.iterrows():
        size = row["SIZE"]
        deficit = row.get("DEFICIT", 0)
        forecast = row.get("FORECAST_LEADTIME", 0)
        deficit = 0 if pd.isna(deficit) else deficit
        forecast = 0 if pd.isna(forecast) else forecast
        qty_needed = max(deficit, forecast)
        if size:
            size_quantities[size] = int(qty_needed)

    return size_quantities


def generate_order_recommendations(
    summary_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    forecast_time_months: float = 5,
    top_n: int = 10,
    settings: dict | None = None,
) -> dict:
    priority_df = calculate_order_priority(
        summary_df, forecast_df, forecast_time_months, settings
    )

    model_color_summary = aggregate_order_by_model_color(priority_df)

    top_model_colors = model_color_summary.head(top_n)

    top_recommendations = []
    for _, row in top_model_colors.iterrows():
        model = row["MODEL"]
        color = row["COLOR"]
        size_breakdown = get_size_quantities_for_model_color(priority_df, model, color)

        top_recommendations.append(
            {
                "model": model,
                "color": color,
                "priority_score": row["PRIORITY_SCORE"],
                "total_deficit": row["DEFICIT"],
                "forecast_demand": row["FORECAST_LEADTIME"],
                "coverage_gap": row["COVERAGE_GAP"],
                "urgent": row["URGENT"],
                "size_quantities": size_breakdown,
            }
        )

    return {
        "priority_skus": priority_df,
        "model_color_summary": model_color_summary,
        "top_recommendations": top_recommendations,
    }


def find_urgent_colors(model_color_summary: pd.DataFrame, model: str) -> list[str]:
    urgent = model_color_summary[
        (model_color_summary["MODEL"] == model) &
        (model_color_summary.get("URGENT", pd.Series([False] * len(model_color_summary))) == True)
    ]
    return urgent["COLOR"].tolist()
