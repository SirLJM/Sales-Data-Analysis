from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from ui.constants import Config
from ui.i18n import t, Keys
from ui.shared.session_manager import get_data_source
from utils.logging_config import get_logger

logger = get_logger("data_loaders")


def _is_data_loaded() -> bool:
    return st.session_state.get("_data_loaded", False)


def _mark_data_loaded() -> None:
    st.session_state["_data_loaded"] = True


def load_all_data_with_progress(
        include_forecast: bool = True,
        include_metadata: bool = True,
) -> dict[str, Any]:
    if _is_data_loaded():
        return {
            "sales": load_data(),
            "stock": load_stock(),
            "forecast": load_forecast() if include_forecast else (None, None, None),
            "metadata": load_model_metadata() if include_metadata else None,
        }

    results: dict[str, Any] = {}
    progress_bar = st.progress(0, text=t(Keys.PROGRESS_LOADING_DATA))

    try:
        progress_bar.progress(0.1, text=t(Keys.PROGRESS_LOADING_SALES))
        results["sales"] = load_data()

        progress_bar.progress(0.4, text=t(Keys.PROGRESS_LOADING_STOCK))
        results["stock"] = load_stock()

        if include_forecast:
            progress_bar.progress(0.7, text=t(Keys.PROGRESS_LOADING_FORECAST))
            results["forecast"] = load_forecast()
        else:
            results["forecast"] = (None, None, None)

        if include_metadata:
            progress_bar.progress(0.9, text=t(Keys.PROGRESS_LOADING_METADATA))
            results["metadata"] = load_model_metadata()
        else:
            results["metadata"] = None

        progress_bar.progress(1.0, text=t(Keys.PROGRESS_DONE))
        _mark_data_loaded()

    finally:
        progress_bar.empty()

    return results


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


def _parse_forecast_date(forecast_df: pd.DataFrame) -> pd.Timestamp | None:
    if "generated_date" not in forecast_df.columns:
        return None
    loaded_date = forecast_df["generated_date"].iloc[0]
    if loaded_date is None:
        return None
    return loaded_date if isinstance(loaded_date, pd.Timestamp) else pd.Timestamp(loaded_date)


@st.cache_data(ttl=Config.CACHE_TTL)
def load_forecast() -> tuple[pd.DataFrame | None, pd.Timestamp | None, str | None]:
    logger.info("Loading forecast data")
    data_source = get_data_source()
    forecast_dataframe = data_source.load_forecast_data()

    if forecast_dataframe is None or forecast_dataframe.empty:
        logger.warning("No forecast data available")
        return None, None, None

    loaded_forecast_date = _parse_forecast_date(forecast_dataframe)
    source = "database" if data_source.get_data_source_type() == "database" else "file"
    logger.info("Forecast data loaded: %d rows from %s, generated_date=%s",
                len(forecast_dataframe), source, loaded_forecast_date)
    return forecast_dataframe, loaded_forecast_date, source


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
def load_outlet_models() -> set[str]:
    data_source = get_data_source()
    return data_source.load_outlet_models()


@st.cache_data(ttl=Config.CACHE_TTL)
def load_size_aliases_reverse() -> dict[str, str]:
    aliases = load_size_aliases()
    return {v: k for k, v in aliases.items()}


@st.cache_data(ttl=Config.CACHE_TTL)
def load_unique_facilities() -> list[str]:
    metadata = load_model_metadata()
    if metadata is None or metadata.empty:
        return []
    facilities_set: set[str] = set()
    for col_name in ["SZWALNIA GŁÓWNA", "SZWALNIA DRUGA"]:
        if col_name in metadata.columns:
            values = metadata[col_name].dropna().astype(str).str.strip().unique()
            facilities_set.update(v for v in values if v)
    return sorted(facilities_set)


@st.cache_data(ttl=Config.CACHE_TTL)
def load_unique_materials() -> list[str]:
    metadata = load_model_metadata()
    if metadata is None or metadata.empty:
        return []
    col_name = "RODZAJ MATERIAŁU"
    if col_name not in metadata.columns:
        return []
    materials = metadata[col_name].dropna().astype(str).str.strip().unique()
    return sorted({m for m in materials if m})


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
    return aggregate_yearly_sales(sales_df, _by_model=True, include_color=include_color)


@st.cache_data(ttl=Config.CACHE_TTL)
def load_yearly_forecast(include_color: bool = False) -> pd.DataFrame | None:
    from sales_data.analysis import aggregate_forecast_yearly
    forecast_df, _, _ = load_forecast()
    if forecast_df is None:
        return None
    return aggregate_forecast_yearly(forecast_df, include_color=include_color)


def _add_default_stock_columns(df: pd.DataFrame, stock_column: str) -> pd.DataFrame:
    if stock_column not in df.columns:
        df[stock_column] = 0
    if "PRICE" not in df.columns:
        df["PRICE"] = 0
    return df


def _normalize_stock_df(stock_df: pd.DataFrame, stock_column: str) -> pd.DataFrame:
    df = stock_df.copy()
    if "sku" in df.columns:
        df = df.rename(columns={"sku": "SKU"})
    if stock_column not in df.columns:
        source_col = "available_stock" if "available_stock" in df.columns else "stock"
        if source_col in df.columns:
            df[stock_column] = df[source_col]
    if "cena_netto" in df.columns:
        df["PRICE"] = df["cena_netto"]
    return df


def merge_stock_into_summary(
        sku_summary: pd.DataFrame,
        stock_df: pd.DataFrame | None,
        stock_column: str = "STOCK",
) -> pd.DataFrame:
    if stock_df is None or stock_df.empty:
        return _add_default_stock_columns(sku_summary, stock_column)

    stock_df_copy = _normalize_stock_df(stock_df, stock_column)

    if stock_column not in stock_df_copy.columns:
        logger.warning("Stock column '%s' not found in stock data, adding defaults", stock_column)
        return _add_default_stock_columns(sku_summary, stock_column)

    stock_cols = ["SKU", stock_column]
    if "PRICE" in stock_df_copy.columns:
        stock_cols.append("PRICE")

    sku_stock = stock_df_copy[stock_cols].copy()
    sku_summary = sku_summary.merge(sku_stock, on="SKU", how="left")
    sku_summary[stock_column] = sku_summary[stock_column].astype(float).fillna(0)
    if "PRICE" in stock_cols:
        sku_summary["PRICE"] = sku_summary["PRICE"].astype(float).fillna(0)

    return sku_summary
