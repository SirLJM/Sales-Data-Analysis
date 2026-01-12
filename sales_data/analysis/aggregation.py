from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

AVERAGE_SALES = "AVERAGE SALES"


def _aggregate_sales_summary(df: pd.DataFrame, group_col: str, id_col: str) -> pd.DataFrame:
    df = df.copy()
    df["year_month"] = df["data"].dt.to_period("M")  # type: ignore

    first_sale = df.groupby(group_col, observed=True)["data"].min().reset_index()
    first_sale.columns = [id_col, "first_sale"]

    monthly_sales = df.groupby([group_col, "year_month"], as_index=False, observed=True)["ilosc"].sum()

    summary = monthly_sales.groupby(group_col, as_index=False, observed=True).agg(
        {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}  # type: ignore
    )
    summary.columns = [id_col, "MONTHS", "QUANTITY", AVERAGE_SALES, "SD"]

    summary["CV"] = summary["SD"] / summary[AVERAGE_SALES]
    summary["CV"] = summary["CV"].fillna(0)

    summary = pd.merge(summary, first_sale, on=id_col, how="left", validate="many_to_many")

    return summary.sort_values(id_col, ascending=False)


def aggregate_by_sku(data: pd.DataFrame) -> pd.DataFrame:
    if data is None or data.empty:
        return pd.DataFrame(columns=["SKU", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD", "CV", "first_sale"])
    return _aggregate_sales_summary(data, "sku", "SKU")


def aggregate_by_model(data: pd.DataFrame) -> pd.DataFrame:
    if data is None or data.empty:
        return pd.DataFrame(columns=["MODEL", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD", "CV", "first_sale"])
    df = data.copy()
    df["model"] = df["sku"].astype(str).str[:5]
    return _aggregate_sales_summary(df, "model", "MODEL")


def aggregate_yearly_sales(data: pd.DataFrame, _by_model: bool = False, include_color: bool = False) -> pd.DataFrame:
    df = data.copy()
    df["year"] = df["data"].dt.year  # type: ignore
    df["model"] = df["sku"].astype(str).str[:5]

    if include_color:
        df["color"] = df["sku"].astype(str).str[5:7]
        df["model_color"] = df["model"] + df["color"]
        group_cols = ["model_color", "year"]
        id_col = "MODEL_COLOR"
    else:
        group_cols = ["model", "year"]
        id_col = "MODEL"

    yearly_sales = df.groupby(group_cols, as_index=False, observed=True).agg({"ilosc": "sum"})
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
        yearly_forecast = df.groupby(["model_color", "year"], as_index=False, observed=True).agg({"forecast": "sum"})
        yearly_forecast.columns = ["MODEL_COLOR", "YEAR", "QUANTITY"]
    else:
        yearly_forecast = df.groupby(["model", "year"], as_index=False, observed=True).agg({"forecast": "sum"})
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
        monthly_sales = df_last_2_years.groupby(["model", "year_month"], as_index=False, observed=True)["ilosc"].sum()
        # noinspection PyUnresolvedReferences
        avg_sales = monthly_sales.groupby("model", as_index=False, observed=True)["ilosc"].mean()
        avg_sales.columns = ["MODEL", "LAST_2_YEARS_AVG"]
    else:
        monthly_sales = df_last_2_years.groupby(["sku", "year_month"], as_index=False, observed=True)["ilosc"].sum()
        # noinspection PyUnresolvedReferences
        avg_sales = monthly_sales.groupby("sku", as_index=False, observed=True)["ilosc"].mean()
        avg_sales.columns = ["SKU", "LAST_2_YEARS_AVG"]

    avg_sales["LAST_2_YEARS_AVG"] = avg_sales["LAST_2_YEARS_AVG"].round(2)

    return avg_sales
