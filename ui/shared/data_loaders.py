from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from ui.constants import Config
from ui.shared.session_manager import get_data_source
from utils.logging_config import get_logger

logger = get_logger("data_loaders")


@st.cache_data(ttl=Config.CACHE_TTL)
def load_data() -> pd.DataFrame:
    logger.info("Loading sales data")
    data_source = get_data_source()
    df = data_source.load_sales_data()
    logger.info("Sales data loaded: %d rows", len(df) if df is not None else 0)
    return df


def _get_stock_cache_key() -> str:
    data_source = get_data_source()
    if data_source.get_data_source_type() == "file":
        from sales_data.loader import SalesDataLoader
        loader = SalesDataLoader()
        latest_file = loader.get_latest_stock_file()
        if latest_file:
            return f"file_{latest_file.name}_{latest_file.stat().st_mtime}"
    return f"db_{date.today().isoformat()}"


def load_stock() -> tuple[pd.DataFrame | None, str | None]:
    cache_key = _get_stock_cache_key()
    return _load_stock_cached(cache_key)


@st.cache_data(ttl=Config.CACHE_TTL)
def _load_stock_cached(_cache_key: str) -> tuple[pd.DataFrame | None, str | None]:
    logger.info("Loading stock data (cache_key=%s)", _cache_key)
    data_source = get_data_source()
    stock_dataframe = data_source.load_stock_data()
    if stock_dataframe is not None and not stock_dataframe.empty:
        source = "database" if data_source.get_data_source_type() == "database" else "file"
        logger.info("Stock data loaded: %d rows from %s", len(stock_dataframe), source)
        return stock_dataframe, source
    logger.warning("No stock data available")
    return None, None


@st.cache_data(ttl=Config.CACHE_TTL)
def load_forecast() -> tuple[pd.DataFrame | None, pd.Timestamp | None, str | None]:
    logger.info("Loading forecast data")
    data_source = get_data_source()
    forecast_dataframe = data_source.load_forecast_data()
    if forecast_dataframe is not None and not forecast_dataframe.empty:
        loaded_forecast_date = None
        if "generated_date" in forecast_dataframe.columns:
            loaded_date = forecast_dataframe["generated_date"].iloc[0]
            if loaded_date is not None and not isinstance(loaded_date, pd.Timestamp):
                loaded_forecast_date = pd.Timestamp(loaded_date)
            else:
                loaded_forecast_date = loaded_date
        source = "database" if data_source.get_data_source_type() == "database" else "file"
        logger.info("Forecast data loaded: %d rows from %s, generated_date=%s",
                    len(forecast_dataframe), source, loaded_forecast_date)
        return forecast_dataframe, loaded_forecast_date, source
    logger.warning("No forecast data available")
    return None, None, None


@st.cache_data(ttl=Config.CACHE_TTL)
def load_model_metadata() -> pd.DataFrame | None:
    data_source = get_data_source()
    return data_source.load_model_metadata()


@st.cache_data(ttl=Config.CACHE_TTL)
def load_category_mappings() -> pd.DataFrame | None:
    data_source = get_data_source()
    return data_source.load_category_mappings()


@st.cache_data(ttl=Config.CACHE_TTL)
def load_size_aliases() -> dict[str, str]:
    data_source = get_data_source()
    return data_source.load_size_aliases()


@st.cache_data(ttl=Config.CACHE_TTL)
def load_color_aliases() -> dict[str, str]:
    data_source = get_data_source()
    return data_source.load_color_aliases()


@st.cache_data(ttl=Config.CACHE_TTL)
def load_size_aliases_reverse() -> dict[str, str]:
    aliases = load_size_aliases()
    return {v: k for k, v in aliases.items()}


@st.cache_data(ttl=Config.CACHE_TTL)
def load_unique_facilities() -> list[str]:
    metadata = load_model_metadata()
    if metadata is None or metadata.empty:
        return []
    col_name = "SZWALNIA GŁÓWNA"
    if col_name not in metadata.columns:
        return []
    facilities = metadata[col_name].dropna().unique().tolist()
    return [f for f in facilities if f]


@st.cache_data(ttl=Config.CACHE_TTL)
def load_unique_categories() -> list[str]:
    mappings = load_category_mappings()
    if mappings is None or mappings.empty:
        return []
    col_name = "kategoria"
    if col_name not in mappings.columns:
        return []
    categories = mappings[col_name].dropna().unique().tolist()
    return [c for c in categories if c]


@st.cache_data(ttl=Config.CACHE_TTL)
def load_yearly_sales(include_color: bool = False) -> pd.DataFrame:
    from sales_data.analysis import aggregate_yearly_sales
    sales_df = load_data()
    return aggregate_yearly_sales(sales_df, by_model=True, include_color=include_color)


@st.cache_data(ttl=Config.CACHE_TTL)
def load_yearly_forecast(include_color: bool = False) -> pd.DataFrame | None:
    from sales_data.analysis import aggregate_forecast_yearly
    forecast_df, _, _ = load_forecast()
    if forecast_df is None:
        return None
    return aggregate_forecast_yearly(forecast_df, include_color=include_color)
