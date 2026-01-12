from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from .utils import get_completed_last_week_range


def generate_weekly_new_products_analysis(
        sales_df: pd.DataFrame,
        stock_df: pd.DataFrame | None = None,
        lookback_days: int = 60,
        reference_date: datetime | None = None,
) -> pd.DataFrame:
    def get_week_start_wednesday(date: datetime) -> datetime:
        days_since_wed = (date.weekday() - 2) % 7
        return date - timedelta(days=days_since_wed)

    if reference_date is None:
        reference_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    cutoff_date = reference_date - timedelta(days=lookback_days)

    df = sales_df.copy()
    df["model"] = df["sku"].astype(str).str[:5]

    first_sales = df.groupby("model", observed=True)["data"].min().reset_index()
    first_sales.columns = ["model", "first_sale_date"]

    new_products = first_sales[first_sales["first_sale_date"] >= cutoff_date].copy()

    if new_products.empty:
        return pd.DataFrame()

    new_products["monitoring_end_date"] = new_products["first_sale_date"] + timedelta(days=lookback_days)

    df_new = df[df["model"].isin(new_products["model"])].copy()

    df_new = df_new.merge(
        new_products[["model", "first_sale_date", "monitoring_end_date"]],
        on="model",
        how="left",
    )

    df_new = df_new[
        (df_new["data"] >= df_new["first_sale_date"])
        & (df_new["data"] <= df_new["monitoring_end_date"])
        ]

    df_new["week_start"] = df_new["data"].apply(get_week_start_wednesday)

    weekly_sales = df_new.groupby(["model", "week_start"], as_index=False, observed=True)["ilosc"].sum()

    model_week_ranges = []
    for _, row in new_products.iterrows():
        model = row["model"]
        first_sale = row["first_sale_date"]
        monitoring_end = row["monitoring_end_date"]

        first_week = get_week_start_wednesday(first_sale)
        last_week = get_week_start_wednesday(min(monitoring_end, reference_date))

        model_weeks = pd.date_range(start=first_week, end=last_week, freq="W-WED")

        for week in model_weeks:
            model_week_ranges.append({"model": model, "week_start": week})

    full_combinations = pd.DataFrame(model_week_ranges)

    weekly_complete = full_combinations.merge(weekly_sales, on=["model", "week_start"], how="left",
                                              validate="many_to_many")
    weekly_complete["ilosc"] = weekly_complete["ilosc"].fillna(0).astype(int)

    pivot_df = weekly_complete.pivot(index="model", columns="week_start", values="ilosc")

    pivot_df.columns = [col.strftime("%Y-%m-%d") for col in pivot_df.columns]
    pivot_df = pivot_df.reset_index()

    result = new_products[["model", "first_sale_date"]].merge(pivot_df, on="model", how="left")

    result["first_sale_date"] = result["first_sale_date"].dt.strftime("%d-%m-%Y")

    result = result.rename(columns={"first_sale_date": "SALES_START_DATE", "model": "MODEL"})

    if stock_df is not None:
        stock_df = stock_df.copy()
        stock_df["model"] = stock_df["sku"].astype(str).str[:5]
        descriptions = stock_df.groupby("model", observed=True)["nazwa"].first().reset_index()
        descriptions.columns = ["MODEL", "DESCRIPTION"]
        result = result.merge(descriptions, on="MODEL", how="left")

    week_cols = [col for col in result.columns if col not in ["SALES_START_DATE", "MODEL", "DESCRIPTION"]]
    week_cols.sort()

    base_cols = ["SALES_START_DATE", "MODEL"]
    if "DESCRIPTION" in result.columns:
        base_cols.append("DESCRIPTION")

    result = result[base_cols + week_cols]

    result = result.sort_values("SALES_START_DATE", ascending=False)

    return result


def calculate_top_sales_report(
        sales_df: pd.DataFrame, reference_date: datetime | None = None
) -> dict:
    if reference_date is None:
        reference_date = datetime.today()

    last_week_start, last_week_end = get_completed_last_week_range(reference_date)

    prev_year_start = last_week_start - timedelta(days=364)
    prev_year_end = last_week_end - timedelta(days=364)

    df = sales_df.copy()
    df["model"] = df["sku"].astype(str).str[:5]

    last_week_sales = (
        df[(df["data"] >= last_week_start) & (df["data"] <= last_week_end)]
        .groupby("model", as_index=False, observed=True)["ilosc"]
        .sum()
    )
    last_week_sales.columns = ["model", "current_week_sales"]

    prev_year_sales = (
        df[(df["data"] >= prev_year_start) & (df["data"] <= prev_year_end)]
        .groupby("model", as_index=False, observed=True)["ilosc"]
        .sum()
    )
    prev_year_sales.columns = ["model", "prev_year_sales"]

    comparison = last_week_sales.merge(prev_year_sales, on="model", how="outer")
    comparison["current_week_sales"] = comparison["current_week_sales"].fillna(0)
    comparison["prev_year_sales"] = comparison["prev_year_sales"].fillna(0)

    comparison["difference"] = comparison["current_week_sales"] - comparison["prev_year_sales"]
    comparison["percent_change"] = 0.0

    mask = comparison["prev_year_sales"] > 0
    comparison.loc[mask, "percent_change"] = (
                                                     comparison.loc[mask, "difference"] / comparison.loc[
                                                 mask, "prev_year_sales"]
                                             ) * 100

    comparison.loc[~mask & (comparison["current_week_sales"] > 0), "percent_change"] = 999.0

    rising = comparison[comparison["difference"] > 0].sort_values("difference", ascending=False)
    falling = comparison[comparison["difference"] < 0].sort_values("difference", ascending=True)

    rising_star = rising.iloc[0] if not rising.empty else None
    falling_star = falling.iloc[0] if not falling.empty else None

    return {
        "last_week_start": last_week_start,
        "last_week_end": last_week_end,
        "prev_year_start": prev_year_start,
        "prev_year_end": prev_year_end,
        "rising_star": rising_star,
        "falling_star": falling_star,
    }


def calculate_top_products_by_type(
        sales_df: pd.DataFrame,
        cv_basic: float = 0.6,
        cv_seasonal: float = 1.0,
        reference_date: datetime | None = None,
) -> dict:
    if reference_date is None:
        reference_date = datetime.today()

    last_week_start, last_week_end = get_completed_last_week_range(reference_date)

    df = sales_df.copy()
    df["model"] = df["sku"].astype(str).str[:5]
    df["color"] = df["sku"].astype(str).str[5:7]

    last_week_sales = df[(df["data"] >= last_week_start) & (df["data"] <= last_week_end)].copy()

    model_color_sales = last_week_sales.groupby(["model", "color"], as_index=False, observed=True)["ilosc"].sum()
    model_color_sales.columns = ["model", "color", "sales"]

    monthly_sales = df.copy()
    monthly_sales["month"] = monthly_sales["data"].dt.to_period("M")  # type: ignore[attr-defined]
    monthly_agg = monthly_sales.groupby(["model", "month"], as_index=False, observed=True)["ilosc"].sum()

    stats = monthly_agg.groupby("model", as_index=False, observed=True).agg(
        avg_sales=("ilosc", "mean"),
        sd_sales=("ilosc", "std"),
        months_with_sales=("month", "nunique"),
    )
    stats["sd_sales"] = stats["sd_sales"].fillna(0)
    stats["cv"] = 0.0
    mask = stats["avg_sales"] > 0
    stats.loc[mask, "cv"] = stats.loc[mask, "sd_sales"] / stats.loc[mask, "avg_sales"]

    first_sales = df.groupby("model", observed=True)["data"].min().reset_index()
    first_sales.columns = ["model", "first_sale"]

    stats = stats.merge(first_sales, on="model", how="left")

    one_year_ago = reference_date - timedelta(days=365)
    stats["type"] = "regular"
    stats.loc[stats["first_sale"] > one_year_ago, "type"] = "new"
    stats.loc[(stats["type"] != "new") & (stats["cv"] < cv_basic), "type"] = "basic"
    stats.loc[(stats["type"] != "new") & (stats["cv"] > cv_seasonal), "type"] = "seasonal"

    model_color_sales = model_color_sales.merge(stats[["model", "type"]], on="model", how="left")

    top_by_type = {}
    for product_type in ["new", "seasonal", "regular", "basic"]:
        type_products = model_color_sales[model_color_sales["type"] == product_type]
        top_5 = type_products.nlargest(5, "sales")
        top_by_type[product_type] = top_5

    return {
        "last_week_start": last_week_start,
        "last_week_end": last_week_end,
        "top_by_type": top_by_type,
    }


def _calculate_percent_change(current: float, prior: float) -> float:
    if prior > 0:
        return ((current - prior) / prior) * 100
    return 999.0 if current > 0 else 0.0


def calculate_monthly_yoy_by_category(
        sales_df: pd.DataFrame,
        category_df: pd.DataFrame,
        reference_date: datetime = None
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if reference_date is None:
        reference_date = datetime.now()

    current_year = reference_date.year
    current_month = reference_date.month

    last_complete_month = current_month - 1 if current_month > 1 else 12
    year_for_range = current_year if current_month > 1 else current_year - 1

    current_start = datetime(year_for_range, 1, 1)
    current_end = datetime(year_for_range, last_complete_month, 1) + pd.DateOffset(months=1) - timedelta(seconds=1)

    prior_start = current_start - pd.DateOffset(years=1)
    prior_end = current_end - pd.DateOffset(years=1)

    sales_df = sales_df.copy()
    sales_df["data"] = pd.to_datetime(sales_df["data"])

    current_sales = sales_df[(sales_df["data"] >= current_start) & (sales_df["data"] <= current_end)].copy()
    prior_sales = sales_df[(sales_df["data"] >= prior_start) & (sales_df["data"] <= prior_end)].copy()

    current_sales["model"] = current_sales["sku"].str[:5]
    prior_sales["model"] = prior_sales["sku"].str[:5]

    category_lookup = category_df[["Model", "Podgrupa", "Kategoria", "Nazwa"]].copy()
    category_lookup["model"] = category_lookup["Model"].str.upper()
    category_lookup = category_lookup[["model", "Podgrupa", "Kategoria", "Nazwa"]]

    current_with_cat = current_sales.merge(category_lookup, on="model", how="left")
    prior_with_cat = prior_sales.merge(category_lookup, on="model", how="left")

    uncategorized_current = current_with_cat[current_with_cat["Podgrupa"].isna()]
    uncategorized_count = uncategorized_current["model"].nunique()
    uncategorized_sales = uncategorized_current["ilosc"].sum()

    current_agg = current_with_cat.groupby(
        ["Podgrupa", "Kategoria"], as_index=False, dropna=False
    )["ilosc"].sum().rename(columns={"ilosc": "current_qty"})  # type: ignore[union-attr]

    prior_agg = prior_with_cat.groupby(
        ["Podgrupa", "Kategoria"], as_index=False, dropna=False
    )["ilosc"].sum().rename(columns={"ilosc": "prior_qty"})  # type: ignore[union-attr]

    kategoria_details = current_agg.merge(
        prior_agg, on=["Podgrupa", "Kategoria"], how="outer"
    ).fillna({"current_qty": 0, "prior_qty": 0})

    kategoria_details["difference"] = kategoria_details["current_qty"] - kategoria_details["prior_qty"]

    kategoria_details["percent_change"] = kategoria_details.apply(
        lambda row: _calculate_percent_change(row["current_qty"], row["prior_qty"]),
        axis=1
    )

    kategoria_details = kategoria_details.sort_values(["Podgrupa", "current_qty"], ascending=[True, False])

    podgrupa_summary = kategoria_details.groupby("Podgrupa", as_index=False, observed=True).agg({
        "current_qty": "sum",
        "prior_qty": "sum",
        "difference": "sum"
    })

    podgrupa_summary["percent_change"] = podgrupa_summary.apply(
        lambda row: _calculate_percent_change(row["current_qty"], row["prior_qty"]),
        axis=1
    )

    podgrupa_summary = podgrupa_summary.sort_values("current_qty", ascending=False)

    rising_count = len(kategoria_details[kategoria_details["difference"] > 0])
    falling_count = len(kategoria_details[kategoria_details["difference"] < 0])

    metadata = {
        "current_start": current_start,
        "current_end": current_end,
        "prior_start": prior_start,
        "prior_end": prior_end,
        "current_label": f"{current_start.strftime('%b %Y')} - {current_end.strftime('%b %Y')}",
        "prior_label": f"{prior_start.strftime('%b %Y')} - {prior_end.strftime('%b %Y')}",
        "total_current": podgrupa_summary["current_qty"].sum(),
        "total_prior": podgrupa_summary["prior_qty"].sum(),
        "total_difference": podgrupa_summary["difference"].sum(),
        "rising_count": rising_count,
        "falling_count": falling_count,
        "uncategorized_models": uncategorized_count,
        "uncategorized_sales": uncategorized_sales
    }

    return podgrupa_summary, kategoria_details, metadata


def normalize_monthly_agg_columns(df: pd.DataFrame) -> pd.DataFrame:
    column_mapping = {
        "entity_id": "SKU",
        "year_month": "YEAR_MONTH",
        "total_quantity": "TOTAL_QUANTITY"
    }
    return df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})


def filter_and_pivot_sales(
        df: pd.DataFrame,
        model: str,
        colors: list[str],
        months: int
) -> pd.DataFrame:
    df = df.copy()
    df["model"] = df["SKU"].astype(str).str[:5]
    df["color"] = df["SKU"].astype(str).str[5:7]

    all_months = sorted(df["YEAR_MONTH"].unique())
    last_n_months = all_months[-months:] if len(all_months) >= months else all_months

    filtered = df[
        (df["model"] == model) &
        (df["color"].isin(colors)) &
        (df["YEAR_MONTH"].isin(last_n_months))
        ]

    if filtered.empty:
        return pd.DataFrame()

    pivot_df = filtered.pivot_table(
        index="color",
        columns="YEAR_MONTH",
        values="TOTAL_QUANTITY",
        aggfunc="sum",
        fill_value=0
    )

    return pivot_df.reset_index()


def get_last_n_months_sales_by_color(
        monthly_agg: pd.DataFrame,
        model: str,
        colors: list[str],
        months: int = 4
) -> pd.DataFrame:
    if monthly_agg is None or monthly_agg.empty:
        return pd.DataFrame()

    df = normalize_monthly_agg_columns(monthly_agg.copy())
    return filter_and_pivot_sales(df, model, colors, months)
