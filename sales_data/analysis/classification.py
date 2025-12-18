from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd


def classify_sku_type(
        sku_summary: pd.DataFrame, cv_basic: float, cv_seasonal: float
) -> pd.DataFrame:
    df = sku_summary.copy()

    one_year_ago = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)

    df["TYPE"] = "regular"
    df.loc[df["first_sale"] > one_year_ago, "TYPE"] = "new"
    df.loc[(df["TYPE"] != "new") & (df["CV"] < cv_basic), "TYPE"] = "basic"
    df.loc[(df["TYPE"] != "new") & (df["CV"] > cv_seasonal), "TYPE"] = "seasonal"

    return df


def determine_seasonal_months(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()

    two_years_ago = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=730)
    df = df[df["data"] >= two_years_ago]

    df["month"] = df["data"].dt.month  # type: ignore[attr-defined]
    df["year"] = df["data"].dt.year  # type: ignore[attr-defined]

    monthly_sales = df.groupby(["sku", "year", "month"], as_index=False)["ilosc"].sum()

    # noinspection PyUnresolvedReferences
    avg_monthly_sales = monthly_sales.groupby(["sku", "month"], as_index=False)[
        "ilosc"].mean()
    avg_monthly_sales = avg_monthly_sales.rename(columns={"sku": "SKU", "ilosc": "avg_sales"})

    overall_avg = avg_monthly_sales.groupby("SKU", as_index=False)["avg_sales"].mean()  # type: ignore[attr-defined]
    overall_avg = overall_avg.rename(columns={"avg_sales": "overall_avg"})

    seasonal_data = avg_monthly_sales.merge(overall_avg, on="SKU")
    seasonal_data["seasonal_index"] = seasonal_data["avg_sales"] / seasonal_data["overall_avg"]
    seasonal_data["is_in_season"] = seasonal_data["seasonal_index"] > 1.2

    return seasonal_data[["SKU", "month", "avg_sales", "seasonal_index", "is_in_season"]]
