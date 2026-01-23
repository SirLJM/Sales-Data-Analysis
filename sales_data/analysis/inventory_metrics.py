from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

AVERAGE_SALES = "AVERAGE SALES"


def calculate_safety_stock_and_rop(
    sku_summary: pd.DataFrame,
    seasonal_data: pd.DataFrame,
    z_basic: float,
    z_regular: float,
    z_seasonal_in: float,
    z_seasonal_out: float,
    z_new: float,
    lead_time_months: float = 1.36,
) -> pd.DataFrame:
    df = sku_summary.copy()

    id_column = "MODEL" if "MODEL" in df.columns else "SKU"

    z_score_map = {
        "basic": z_basic,
        "regular": z_regular,
        "seasonal": z_seasonal_in,
        "new": z_new,
    }
    df["z_score"] = df["TYPE"].map(z_score_map)  # type: ignore[arg-type]

    current_month = datetime.today().month

    sqrt_lead_time = np.sqrt(lead_time_months)

    df["SS"] = df["z_score"] * df["SD"] * sqrt_lead_time
    df["ROP"] = df[AVERAGE_SALES] * lead_time_months + df["SS"]

    seasonal_mask = df["TYPE"] == "seasonal"
    if isinstance(seasonal_mask, pd.Series) and seasonal_mask.any():
        seasonal_items = df[seasonal_mask][id_column].tolist()
        seasonal_current = seasonal_data[
            (seasonal_data["SKU"].isin(seasonal_items))
            & (seasonal_data["month"] == current_month)
        ][["SKU", "is_in_season"]]

        df = df.merge(pd.DataFrame(seasonal_current), left_on=id_column, right_on="SKU", how="left")
        if id_column == "MODEL":
            df = df.drop(columns=["SKU"], errors="ignore")

        df["SS_IN"] = np.where(seasonal_mask, z_seasonal_in * df["SD"] * sqrt_lead_time, np.nan)
        df["ROP_IN"] = np.where(
            seasonal_mask, df[AVERAGE_SALES] * lead_time_months + df["SS_IN"], np.nan
        )

        df["SS_OUT"] = np.where(
            seasonal_mask, z_seasonal_out * df["SD"] * sqrt_lead_time, np.nan
        )
        df["ROP_OUT"] = np.where(
            seasonal_mask, df[AVERAGE_SALES] * lead_time_months + df["SS_OUT"], np.nan
        )

        is_in_season = df["is_in_season"].astype("boolean").fillna(False)
        in_season_mask = is_in_season.astype(bool)
        out_season_mask = ~in_season_mask

        df.loc[seasonal_mask & in_season_mask, "SS"] = df["SS_IN"]
        df.loc[seasonal_mask & in_season_mask, "ROP"] = df["ROP_IN"]
        df.loc[seasonal_mask & out_season_mask, "SS"] = df["SS_OUT"]
        df.loc[seasonal_mask & out_season_mask, "ROP"] = df["ROP_OUT"]

        df = df.drop(columns=["is_in_season"], errors="ignore")

    df = df.drop(columns=["z_score"], errors="ignore")

    df["SS"] = df["SS"].round(2)
    df["ROP"] = df["ROP"].round(2)
    if "SS_IN" in df.columns:
        df["SS_IN"] = df["SS_IN"].round(2)
        df["SS_OUT"] = df["SS_OUT"].round(2)
        df["ROP_IN"] = df["ROP_IN"].round(2)
        df["ROP_OUT"] = df["ROP_OUT"].round(2)

    base_cols = ["MONTHS", "QUANTITY", AVERAGE_SALES, "SD", "CV", "TYPE", "SS", "ROP"]
    result = pd.DataFrame(df[[id_column] + base_cols])
    return result


def calculate_forecast_date_range(forecast_time_months: float) -> tuple[pd.Timestamp, pd.Timestamp]:
    today = datetime.now()

    if today.day == 1:
        forecast_start = pd.Timestamp(today.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    else:
        next_month_dt = today.replace(day=1) + pd.DateOffset(months=1)
        forecast_start = pd.Timestamp(next_month_dt)  # type: ignore[arg-type]

    forecast_end_dt = forecast_start + pd.DateOffset(months=int(forecast_time_months))
    forecast_end = pd.Timestamp(forecast_end_dt)  # type: ignore[arg-type]
    return forecast_start, forecast_end  # type: ignore[return-value]


def calculate_forecast_metrics(
    forecast_df: pd.DataFrame, forecast_time_months: float | None = None
) -> pd.DataFrame:
    if forecast_df.empty:
        columns = ["sku"]
        if forecast_time_months is not None:
            columns.append("FORECAST_LEADTIME")
        return pd.DataFrame(columns=pd.Index(columns))

    forecast_df = forecast_df.copy()
    forecast_df["data"] = pd.to_datetime(forecast_df["data"])

    if forecast_time_months is not None:
        forecast_start, forecast_end = calculate_forecast_date_range(forecast_time_months)

        forecast_leadtime = forecast_df[
            (forecast_df["data"] >= forecast_start) & (forecast_df["data"] < forecast_end)
        ]

        result = pd.DataFrame(forecast_leadtime.groupby("sku", as_index=False, observed=True).agg({"forecast": "sum"}))
        result = pd.DataFrame(result.rename(columns={"forecast": "FORECAST_LEADTIME"}))
        result["FORECAST_LEADTIME"] = pd.Series(result["FORECAST_LEADTIME"]).fillna(0).round(2)
    else:
        result = pd.DataFrame({"sku": forecast_df["sku"].unique()})

    return result
