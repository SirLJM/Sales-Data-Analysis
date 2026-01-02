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
    if sales_df is not None and not sales_df.empty:
        return sales_df
    return None


@st.cache_data(ttl=Config.CACHE_TTL)
def load_forecast_for_accuracy(
    analysis_start: datetime, lookback_months: int = 4
) -> tuple[pd.DataFrame | None, datetime | None]:
    target_generated_date = analysis_start - timedelta(days=int(lookback_months * 30.44))

    data_source = get_data_source()
    forecast_df = data_source.load_forecast_data(generated_date=target_generated_date)

    if forecast_df is not None and not forecast_df.empty:
        generated_date = None
        if "generated_date" in forecast_df.columns:
            gen_date = forecast_df["generated_date"].iloc[0]
            if gen_date is not None:
                generated_date = pd.Timestamp(gen_date).to_pydatetime()
        return forecast_df, generated_date

    return None, None


@st.cache_data(ttl=Config.CACHE_TTL)
def load_stock_history_for_accuracy(
    start_date: datetime, end_date: datetime
) -> pd.DataFrame | None:
    data_source = get_data_source()
    stock_df = data_source.load_stock_history(start_date=start_date, end_date=end_date)
    if stock_df is not None and not stock_df.empty:
        return stock_df
    return None


def get_available_forecast_dates() -> list[datetime]:
    data_source = get_data_source()

    if data_source.get_data_source_type() == "file":
        from sales_data.loader import SalesDataLoader
        loader = SalesDataLoader()
        forecast_files = loader.find_forecast_files()
        return [date for _, date in forecast_files]

    return []


def get_date_range_from_sales() -> tuple[datetime | None, datetime | None]:
    data_source = get_data_source()

    try:
        sales_df = data_source.load_sales_data()
    except ValueError:
        return None, None

    if sales_df is None or sales_df.empty:
        return None, None

    sales_df["data"] = pd.to_datetime(sales_df["data"])
    min_date = sales_df["data"].min().to_pydatetime()
    max_date = sales_df["data"].max().to_pydatetime()

    return min_date, max_date
