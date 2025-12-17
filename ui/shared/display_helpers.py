from __future__ import annotations

import traceback
from typing import Any

import pandas as pd
import streamlit as st

from ui.constants import ColumnNames, Icons
from ui.shared.sku_utils import extract_model


def display_metrics_row(metrics: list[tuple[str, Any, str | None]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            st.metric(label, value, delta=delta)


def display_star_product(star: dict, stock_df: pd.DataFrame | None, is_rising: bool) -> None:
    product_model = star["model"]

    desc = ""
    if stock_df is not None:
        stock_copy = stock_df.copy()
        stock_copy["model"] = extract_model(stock_copy["sku"])
        model_desc = stock_copy[stock_copy["model"] == product_model]
        if not model_desc.empty:
            desc = model_desc.iloc[0]["nazwa"]

    st.markdown(f"**Model:** {product_model}")
    if desc:
        st.caption(desc)

    sign = "+" if is_rising else ""
    display_metrics_row([
        (ColumnNames.LAST_WEEK, f"{int(star['current_week_sales']):,}", None),
        ("Last Year", f"{int(star['prev_year_sales']):,}", None),
        ("Change", f"{sign}{int(star['difference']):,}", f"{sign}{star['percent_change']:.1f}%"),
    ])


def display_optimization_metrics(result: dict) -> None:
    coverage_icon = Icons.SUCCESS if result["all_covered"] else Icons.ERROR
    display_metrics_row([
        ("Total Patterns", result["total_patterns"], None),
        ("Total Excess", result["total_excess"], None),
        ("Coverage", coverage_icon, None),
    ])


def display_error(message: str, show_traceback: bool = True) -> None:
    st.error(f"{Icons.ERROR} {message}")
    if show_traceback:
        st.code(traceback.format_exc())


def display_success(message: str) -> None:
    st.success(f"{Icons.SUCCESS} {message}")


def display_warning(message: str) -> None:
    st.warning(f"{Icons.WARNING} {message}")


def display_info(message: str) -> None:
    st.info(f"{Icons.INFO} {message}")


def format_number(value: int | float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"{int(value):,}"
    return f"{value:,.{decimals}f}"


def create_download_button(
    data: pd.DataFrame,
    filename: str,
    label: str = "Download CSV",
    key: str | None = None,
) -> None:
    csv = data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
        key=key,
    )
