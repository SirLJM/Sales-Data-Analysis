from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd


def _get_midnight_today() -> datetime:
    return datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)


def classify_sku_type(
        sku_summary: pd.DataFrame, cv_basic: float, cv_seasonal: float
) -> pd.DataFrame:
    df = sku_summary.copy()
    one_year_ago = _get_midnight_today() - timedelta(days=365)

    df["TYPE"] = "regular"
    df.loc[df["first_sale"] > one_year_ago, "TYPE"] = "new"

    not_new = df["TYPE"] != "new"
    df.loc[not_new & (df["CV"] < cv_basic), "TYPE"] = "basic"
    df.loc[not_new & (df["CV"] > cv_seasonal), "TYPE"] = "seasonal"

    return df


def determine_seasonal_months(data: pd.DataFrame) -> pd.DataFrame:
    two_years_ago = _get_midnight_today() - timedelta(days=730)

    df = data[data["data"] >= two_years_ago].copy()
    df["month"] = df["data"].dt.month  # type: ignore
    df["year"] = df["data"].dt.year  # type: ignore

    monthly_sales = df.groupby(["sku", "year", "month"], as_index=False, observed=True)["ilosc"].sum()

    agg_result: Any = monthly_sales.groupby(["sku", "month"], as_index=False, observed=True).agg(avg_sales=("ilosc", "mean"))
    avg_monthly_sales: pd.DataFrame = agg_result.rename(columns={"sku": "SKU"})

    overall_avg: Any = avg_monthly_sales.groupby("SKU", as_index=False, observed=True).agg(overall_avg=("avg_sales", "mean"))

    seasonal_data = avg_monthly_sales.merge(overall_avg, on="SKU")
    seasonal_data["seasonal_index"] = seasonal_data["avg_sales"] / seasonal_data["overall_avg"]
    seasonal_data["is_in_season"] = seasonal_data["seasonal_index"] > 1.2

    return pd.DataFrame(seasonal_data[["SKU", "month", "avg_sales", "seasonal_index", "is_in_season"]])
