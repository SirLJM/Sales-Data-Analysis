from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from ui.constants import Config
from ui.shared.session_manager import get_data_source


@st.cache_data(ttl=Config.CACHE_TTL)
def load_sales_for_accuracy(
    start_date: datetime, end_date: datetime
) -> pd.DataFrame | None:
    data_source = get_data_source()
    sales_df = data_source.load_sales_data(start_date=start_date, end_date=end_date)
    return sales_df if sales_df is not None and not sales_df.empty else None


def _extract_generated_date(forecast_df: pd.DataFrame) -> datetime | None:
    if "generated_date" not in forecast_df.columns:
        return None

    gen_date = forecast_df["generated_date"].iloc[0]
    if gen_date is None or bool(pd.isnull(gen_date)):
        return None

    try:
        ts = pd.Timestamp(gen_date)
        if bool(pd.isnull(ts)):
            return None
        dt = ts.to_pydatetime()
        return dt if isinstance(dt, datetime) else None
    except (ValueError, TypeError):
        return None


@st.cache_data(ttl=Config.CACHE_TTL)
def load_forecast_for_accuracy(
    analysis_start: datetime, lookback_months: int = 4
) -> tuple[pd.DataFrame | None, datetime | None]:
    target_generated_date = analysis_start - timedelta(days=int(lookback_months * 30.44))

    data_source = get_data_source()
    forecast_df = data_source.load_forecast_data(generated_date=target_generated_date)

    if forecast_df is None or forecast_df.empty:
        return None, None

    return forecast_df, _extract_generated_date(forecast_df)


@st.cache_data(ttl=Config.CACHE_TTL)
def load_stock_history_for_accuracy(
    start_date: datetime, end_date: datetime
) -> pd.DataFrame | None:
    data_source = get_data_source()
    stock_df = data_source.load_stock_history(start_date=start_date, end_date=end_date)
    return stock_df if stock_df is not None and not stock_df.empty else None


def get_available_forecast_dates() -> list[datetime]:
    data_source = get_data_source()

    if data_source.get_data_source_type() == "file":
        from sales_data.loader import SalesDataLoader
        loader = SalesDataLoader()
        forecast_files = loader.find_forecast_files()
        return [date for _, date in forecast_files]

    return []


@st.cache_data(ttl=Config.CACHE_TTL)
def get_date_range_from_sales() -> tuple[datetime | None, datetime | None]:
    from ui.shared.data_loaders import load_data

    try:
        sales_df = load_data()
    except ValueError:
        return None, None

    if sales_df is None or sales_df.empty:
        return None, None

    sales_df = sales_df.copy()
    sales_df["data"] = pd.to_datetime(sales_df["data"])
    min_date = sales_df["data"].min().to_pydatetime()
    max_date = sales_df["data"].max().to_pydatetime()

    return min_date, max_date
