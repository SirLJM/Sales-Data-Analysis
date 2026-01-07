from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

AVERAGE_SALES = "AVERAGE SALES"


def aggregate_by_sku(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    df["year_month"] = df["data"].dt.to_period("M")  # type: ignore[attr-defined]

    first_sale = df.groupby("sku")["data"].min().reset_index()
    first_sale.columns = ["SKU", "first_sale"]

    monthly_sales = df.groupby(["sku", "year_month"], as_index=False)["ilosc"].sum()

    sku_summary = monthly_sales.groupby("sku", as_index=False).agg(
        {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}  # type: ignore[attr-defined]
    )

    sku_summary.columns = ["SKU", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD"]

    sku_summary["CV"] = sku_summary["SD"] / sku_summary[AVERAGE_SALES]
    sku_summary["CV"] = sku_summary["CV"].fillna(0)

    sku_summary = pd.merge(sku_summary, first_sale, on="SKU", how="left")

    return sku_summary.sort_values("SKU", ascending=False)


def aggregate_by_model(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    df["model"] = df["sku"].astype(str).str[:5]
    df["year_month"] = df["data"].dt.to_period("M")  # type: ignore[attr-defined]

    first_sale = df.groupby("model")["data"].min().reset_index()
    first_sale.columns = ["MODEL", "first_sale"]

    monthly_sales = df.groupby(["model", "year_month"], as_index=False)["ilosc"].sum()

    model_summary = monthly_sales.groupby("model", as_index=False).agg(
        {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}  # type: ignore[attr-defined]
    )

    model_summary.columns = ["MODEL", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD"]

    model_summary["CV"] = model_summary["SD"] / model_summary[AVERAGE_SALES]
    model_summary["CV"] = model_summary["CV"].fillna(0)

    model_summary = pd.merge(model_summary, first_sale, on="MODEL", how="left")

    return model_summary.sort_values("MODEL", ascending=False)


def aggregate_yearly_sales(data: pd.DataFrame, by_model: bool = False, include_color: bool = False) -> pd.DataFrame:
    df = data.copy()
    # noinspection PyTypeChecker
    df["year"] = df["data"].dt.year

    if by_model:
        df["model"] = df["sku"].astype(str).str[:5]
        if include_color:
            df["color"] = df["sku"].astype(str).str[5:7]
            df["model_color"] = df["model"] + df["color"]
            group_cols = ["model_color", "year"]
            id_col = "MODEL_COLOR"
        else:
            group_cols = ["model", "year"]
            id_col = "MODEL"
    else:
        if include_color:
            df["model"] = df["sku"].astype(str).str[:5]
            df["color"] = df["sku"].astype(str).str[5:7]
            df["model_color"] = df["model"] + df["color"]
            group_cols = ["model_color", "year"]
            id_col = "MODEL_COLOR"
        else:
            df["model"] = df["sku"].astype(str).str[:5]
            group_cols = ["model", "year"]
            id_col = "MODEL"

    yearly_sales = df.groupby(group_cols, as_index=False).agg({"ilosc": "sum"})
    yearly_sales.columns = [id_col, "YEAR", "QUANTITY"]

    return yearly_sales


def aggregate_forecast_yearly(forecast_df: pd.DataFrame, include_color: bool = False) -> pd.DataFrame:
    df = forecast_df.copy()
    df["data"] = pd.to_datetime(df["data"])
    df = df[df["data"] >= datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)]

    if df.empty:
        id_col = "MODEL_COLOR" if include_color else "MODEL"
        return pd.DataFrame(columns=[id_col, "YEAR", "QUANTITY"])

    # noinspection PyTypeChecker
    df["year"] = df["data"].dt.year
    df["model"] = df["sku"].astype(str).str[:5]

    if include_color:
        df["color"] = df["sku"].astype(str).str[5:7]
        df["model_color"] = df["model"] + df["color"]
        yearly_forecast = df.groupby(["model_color", "year"], as_index=False).agg({"forecast": "sum"})
        yearly_forecast.columns = ["MODEL_COLOR", "YEAR", "QUANTITY"]
    else:
        yearly_forecast = df.groupby(["model", "year"], as_index=False).agg({"forecast": "sum"})
        yearly_forecast.columns = ["MODEL", "YEAR", "QUANTITY"]

    return yearly_forecast


def calculate_last_two_years_avg_sales(data: pd.DataFrame, by_model: bool = False) -> pd.DataFrame:
    df = data.copy()

    two_years_ago = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=730)
    df_last_2_years = df[df["data"] >= two_years_ago].copy()

    if df_last_2_years.empty:
        col_name = "MODEL" if by_model else "SKU"
        return pd.DataFrame(columns=[col_name, "LAST_2_YEARS_AVG"])

    df_last_2_years["year_month"] = df_last_2_years["data"].dt.to_period("M")  # type: ignore[attr-defined]

    if by_model:
        df_last_2_years["model"] = df_last_2_years["sku"].astype(str).str[:5]
        monthly_sales = df_last_2_years.groupby(["model", "year_month"], as_index=False)["ilosc"].sum()
        avg_sales = monthly_sales.groupby("model", as_index=False)["ilosc"].mean()  # type: ignore[attr-defined]
        avg_sales.columns = ["MODEL", "LAST_2_YEARS_AVG"]
    else:
        monthly_sales = df_last_2_years.groupby(["sku", "year_month"], as_index=False)["ilosc"].sum()
        avg_sales = monthly_sales.groupby("sku", as_index=False)["ilosc"].mean()  # type: ignore[attr-defined]
        avg_sales.columns = ["SKU", "LAST_2_YEARS_AVG"]

    avg_sales["LAST_2_YEARS_AVG"] = avg_sales["LAST_2_YEARS_AVG"].round(2)

    return avg_sales
