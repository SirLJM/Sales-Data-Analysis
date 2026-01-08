from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from ui.constants import ColumnNames, Icons
from ui.i18n import Keys, t
from utils.logging_config import get_logger

logger = get_logger("display_helpers")


def display_metrics_row(metrics: list[tuple[str, Any, str | None]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            st.metric(label, value, delta=delta)


def display_star_product(star: dict, is_rising: bool) -> None:
    product_model = star["model"]

    st.markdown(f"**{t(Keys.DISPLAY_MODEL)}:** {product_model}")

    sign = "+" if is_rising else ""
    display_metrics_row([
        (ColumnNames.LAST_WEEK, f"{int(star['current_week_sales']):,}", None),
        (t(Keys.DISPLAY_LAST_YEAR), f"{int(star['prev_year_sales']):,}", None),
        (t(Keys.DISPLAY_CHANGE), f"{sign}{int(star['difference']):,}", f"{sign}{star['percent_change']:.1f}%"),
    ])


def display_optimization_metrics(result: dict) -> None:
    coverage_icon = Icons.SUCCESS if result["all_covered"] else Icons.ERROR
    display_metrics_row([
        (t(Keys.DISPLAY_TOTAL_PATTERNS), result["total_patterns"], None),
        (t(Keys.DISPLAY_TOTAL_EXCESS), result["total_excess"], None),
        (t(Keys.DISPLAY_COVERAGE), coverage_icon, None),
    ])


def display_error(message: str, log_exception: bool = True) -> None:
    st.error(f"{Icons.ERROR} {message}")
    if log_exception:
        logger.exception(message)


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
        label: str | None = None,
        key: str | None = None,
) -> None:
    csv = data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label or t(Keys.DISPLAY_DOWNLOAD_CSV),
        data=csv,
        file_name=filename,
        mime="text/csv",
        key=key,
    )
