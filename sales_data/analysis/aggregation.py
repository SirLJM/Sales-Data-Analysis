from __future__ import annotations

import math
from datetime import datetime, timedelta

import pandas as pd

from ui.shared.sku_utils import ADULT_PREFIXES, CHILDREN_PREFIXES

AVERAGE_SALES = "AVERAGE SALES"


def _aggregate_sales_summary(df: pd.DataFrame, group_col: str, id_col: str) -> pd.DataFrame:
    df = df.copy()
    df["year_month"] = df["data"].dt.to_period("M")  # type: ignore[union-attr]

    first_sale = df.groupby(group_col, observed=True)["data"].min().reset_index()
    first_sale.columns = pd.Index([id_col, "first_sale"])

    monthly_sales = df.groupby([group_col, "year_month"], as_index=False, observed=True)["ilosc"].sum()

    summary = pd.DataFrame(
        monthly_sales.groupby(group_col, as_index=False, observed=True).agg(
            {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}  # type: ignore[arg-type]
        )
    )
    summary.columns = pd.Index([id_col, "MONTHS", "QUANTITY", AVERAGE_SALES, "SD"])

    summary["CV"] = pd.Series(summary["SD"]) / pd.Series(summary[AVERAGE_SALES])
    summary["CV"] = pd.Series(summary["CV"]).fillna(0)

    summary = pd.merge(summary, first_sale, on=id_col, how="left", validate="many_to_many")

    return pd.DataFrame(summary.sort_values(id_col, ascending=False))


def aggregate_by_sku(data: pd.DataFrame) -> pd.DataFrame:
    if data is None or data.empty:
        return pd.DataFrame(columns=pd.Index(["SKU", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD", "CV", "first_sale"]))
    return _aggregate_sales_summary(data, "sku", "SKU")


def aggregate_by_model(data: pd.DataFrame) -> pd.DataFrame:
    if data is None or data.empty:
        return pd.DataFrame(columns=pd.Index(["MODEL", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD", "CV", "first_sale"]))
    df = data.copy()
    df["model"] = df["sku"].astype(str).str[:5]
    return _aggregate_sales_summary(df, "model", "MODEL")


def aggregate_yearly_sales(data: pd.DataFrame, _by_model: bool = False, include_color: bool = False) -> pd.DataFrame:
    df = data.copy()
    df["year"] = df["data"].dt.year  # type: ignore[union-attr]
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
    yearly_sales.columns = pd.Index([id_col, "YEAR", "QUANTITY"])

    return pd.DataFrame(yearly_sales)


def aggregate_forecast_yearly(forecast_df: pd.DataFrame, include_color: bool = False) -> pd.DataFrame:
    df = forecast_df.copy()
    df["data"] = pd.to_datetime(df["data"])
    df = df[df["data"] >= datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)]

    if df.empty:
        id_col = "MODEL_COLOR" if include_color else "MODEL"
        return pd.DataFrame(columns=pd.Index([id_col, "YEAR", "QUANTITY"]))

    df["year"] = df["data"].dt.year  # type: ignore[union-attr]
    df["model"] = pd.Series(df["sku"]).astype(str).str[:5]

    if include_color:
        df["color"] = pd.Series(df["sku"]).astype(str).str[5:7]
        df["model_color"] = df["model"] + df["color"]
        yearly_forecast = df.groupby(["model_color", "year"], as_index=False, observed=True).agg({"forecast": "sum"})
        yearly_forecast.columns = pd.Index(["MODEL_COLOR", "YEAR", "QUANTITY"])
    else:
        yearly_forecast = df.groupby(["model", "year"], as_index=False, observed=True).agg({"forecast": "sum"})
        yearly_forecast.columns = pd.Index(["MODEL", "YEAR", "QUANTITY"])

    return pd.DataFrame(yearly_forecast)


def calculate_last_two_years_avg_sales(data: pd.DataFrame, by_model: bool = False) -> pd.DataFrame:
    df = data.copy()

    two_years_ago = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=730)
    df_last_2_years = df[df["data"] >= two_years_ago].copy()

    if df_last_2_years.empty:
        col_name = "MODEL" if by_model else "SKU"
        return pd.DataFrame(columns=pd.Index([col_name, "LAST_2_YEARS_AVG"]))

    df_last_2_years["year_month"] = df_last_2_years["data"].dt.to_period("M")  # type: ignore[union-attr]

    if by_model:
        df_last_2_years["model"] = pd.Series(df_last_2_years["sku"]).astype(str).str[:5]
        monthly_sales = df_last_2_years.groupby(["model", "year_month"], as_index=False, observed=True).agg(ilosc=("ilosc", "sum"))
        avg_sales = pd.DataFrame(monthly_sales.groupby("model", as_index=False, observed=True).agg(LAST_2_YEARS_AVG=("ilosc", "mean")))
        avg_sales.columns = pd.Index(["MODEL", "LAST_2_YEARS_AVG"])
    else:
        monthly_sales = df_last_2_years.groupby(["sku", "year_month"], as_index=False, observed=True).agg(ilosc=("ilosc", "sum"))
        avg_sales = pd.DataFrame(monthly_sales.groupby("sku", as_index=False, observed=True).agg(LAST_2_YEARS_AVG=("ilosc", "mean")))
        avg_sales.columns = pd.Index(["SKU", "LAST_2_YEARS_AVG"])

    avg_sales["LAST_2_YEARS_AVG"] = pd.Series(avg_sales["LAST_2_YEARS_AVG"]).round(2)

    return avg_sales


_PERIOD_SALES_COLUMNS = pd.Index(["SKU", "PERIOD_SALES"])


def _aggregate_group_sales(
    df: pd.DataFrame, mask: "pd.Series[bool]", month_col: str, sku_col: str, qty_col: str, target_months: list[str],
) -> pd.DataFrame | None:
    if not target_months or not mask.any():
        return None
    filtered = pd.DataFrame(df[mask & df[month_col].isin(target_months)])
    if filtered.empty:
        return None
    sales = pd.DataFrame(filtered.groupby(sku_col, as_index=False, observed=True)[qty_col].sum())
    sales.columns = _PERIOD_SALES_COLUMNS
    return sales


def _resolve_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((c for c in candidates if c in df.columns), None)


def calculate_period_sales(monthly_agg: pd.DataFrame, lead_time: float) -> pd.DataFrame:
    if monthly_agg is None or monthly_agg.empty:
        return pd.DataFrame(columns=_PERIOD_SALES_COLUMNS)

    df = monthly_agg.copy()

    sku_col = _resolve_column(df, ["entity_id", "sku", "SKU"])
    month_col = _resolve_column(df, ["year_month", "month"])
    qty_col = _resolve_column(df, ["total_quantity", "ilosc"])

    if sku_col is None or month_col is None or qty_col is None:
        return pd.DataFrame(columns=_PERIOD_SALES_COLUMNS)

    n_months = math.ceil(lead_time)
    df["_prefix"] = df[sku_col].astype(str).str[:2].str.lower()
    df[month_col] = df[month_col].astype(str)
    all_months = sorted(df[month_col].unique(), reverse=True)

    children_months = all_months[:n_months]
    adult_start = max(0, 12 - n_months)
    adult_months = all_months[adult_start:12] if len(all_months) > 12 else []

    results = [
        r for r in (
            _aggregate_group_sales(df, df["_prefix"].isin(CHILDREN_PREFIXES), month_col, sku_col, qty_col, children_months),
            _aggregate_group_sales(df, df["_prefix"].isin(ADULT_PREFIXES), month_col, sku_col, qty_col, adult_months),
        ) if r is not None
    ]

    if not results:
        return pd.DataFrame(columns=_PERIOD_SALES_COLUMNS)

    return pd.DataFrame(pd.concat(results, ignore_index=True))
