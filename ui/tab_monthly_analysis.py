from __future__ import annotations

import pandas as pd
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import Icons, MimeTypes, SessionKeys
from ui.i18n import t, Keys
from ui.shared.data_loaders import load_category_mappings, load_data
from ui.shared.session_manager import get_session_value, set_session_value
from utils.logging_config import get_logger

logger = get_logger("tab_monthly_analysis")


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Monthly Analysis")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_MONTHLY_ANALYSIS).format(error=str(e))}")


def _render_content() -> None:
    st.header(t(Keys.TITLE_MONTHLY_ANALYSIS))

    st.markdown(t(Keys.MONTHLY_CAPTION))

    category_df = load_category_mappings()

    if category_df is None or category_df.empty:
        st.warning(t(Keys.CATEGORY_MAPPINGS_ERROR))
        st.stop()

    _render_generate_button(category_df)
    _render_analysis_results()


def _render_generate_button(category_df: pd.DataFrame) -> None:
    if st.button(t(Keys.BTN_GENERATE_MONTHLY_YOY), type="primary"):
        # noinspection PyTypeChecker
        with st.spinner(t(Keys.CALCULATING_YOY)):
            try:
                sales_df = load_data()
                if sales_df is None or sales_df.empty:
                    st.error(t(Keys.NO_SALES_DATA))
                    st.stop()

                podgrupa_summary, kategoria_details, metadata = SalesAnalyzer.calculate_monthly_yoy_by_category(
                    sales_df, category_df
                )

                set_session_value(SessionKeys.MONTHLY_YOY_PODGRUPA, podgrupa_summary)
                set_session_value(SessionKeys.MONTHLY_YOY_KATEGORIA, kategoria_details)
                set_session_value(SessionKeys.MONTHLY_YOY_METADATA, metadata)

                st.success(t(Keys.ANALYSIS_SUCCESS))

            except Exception as e:
                st.error(t(Keys.ANALYSIS_FAILED).format(error=str(e)))
                st.stop()


def _render_analysis_results() -> None:
    metadata = get_session_value(SessionKeys.MONTHLY_YOY_METADATA)

    if metadata is None:
        st.info(t(Keys.CLICK_GENERATE))
        return

    podgrupa_summary = get_session_value(SessionKeys.MONTHLY_YOY_PODGRUPA)
    kategoria_details = get_session_value(SessionKeys.MONTHLY_YOY_KATEGORIA)

    st.divider()
    _render_period_comparison(metadata)

    st.divider()
    _render_summary_metrics(metadata)

    st.divider()
    _render_category_breakdown(podgrupa_summary, kategoria_details)

    st.divider()
    _render_downloads(podgrupa_summary, kategoria_details, metadata)


def _render_period_comparison(metadata: dict) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            t(Keys.METRIC_CURRENT_PERIOD),
            metadata["current_label"],
            delta=f"{int(metadata['total_current']):,} units",
        )
    with col2:
        st.metric(
            t(Keys.METRIC_SAME_PERIOD_LAST_YEAR),
            metadata["prior_label"],
            delta=f"{int(metadata['total_prior']):,} units",
        )


def _render_summary_metrics(metadata: dict) -> None:
    overall_pct_change = (
        (metadata["total_difference"] / metadata["total_prior"]) * 100
        if metadata["total_prior"] > 0
        else 999.0
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            t(Keys.METRIC_TOTAL_YOY_CHANGE),
            f"{overall_pct_change:+.1f}%",
            delta=f"{int(metadata['total_difference']):,} units",
        )
    with col2:
        st.metric(t(Keys.METRIC_RISING_CATEGORIES), metadata["rising_count"])
    with col3:
        st.metric(t(Keys.METRIC_FALLING_CATEGORIES), metadata["falling_count"])
    with col4:
        if metadata["uncategorized_sales"] > 0:
            st.metric(
                f"{Icons.WARNING} {t(Keys.METRIC_UNCATEGORIZED)}",
                f"{metadata['uncategorized_models']} models",
                delta=f"{int(metadata['uncategorized_sales']):,} units",
            )


def _render_category_breakdown(podgrupa_summary: pd.DataFrame, kategoria_details: pd.DataFrame) -> None:
    st.subheader(t(Keys.SALES_BY_AGE_GROUP))

    for _, row in podgrupa_summary.iterrows():
        podgrupa = row["Podgrupa"]
        current_qty = int(row["current_qty"])
        pct_change = row["percent_change"]

        if pd.isna(podgrupa):
            podgrupa = f"{Icons.WARNING} {t(Keys.METRIC_UNCATEGORIZED)}"

        title = f"**{podgrupa}** | {current_qty:,} units ({pct_change:+.1f}% YoY)"

        if pct_change > 10:
            title = f"🟢 {title}"
        elif pct_change < -10:
            title = f"🔴 {title}"
        else:
            title = f"🟡 {title}"

        with st.expander(title, expanded=False):
            _render_kategoria_table(podgrupa, kategoria_details)


def _render_kategoria_table(podgrupa: str, kategoria_details: pd.DataFrame) -> None:
    is_uncategorized = t(Keys.METRIC_UNCATEGORIZED) in str(podgrupa)

    if is_uncategorized:
        podgrupa_categories = kategoria_details[kategoria_details["Podgrupa"].isna()].copy()
    else:
        podgrupa_categories = kategoria_details[kategoria_details["Podgrupa"] == podgrupa].copy()

    if podgrupa_categories.empty:
        st.info(t(Keys.NO_DATA_AGE_GROUP))
        return

    display_df = podgrupa_categories.copy()
    display_df["Kategoria"] = display_df["Kategoria"].fillna(t(Keys.UNKNOWN))
    display_df = display_df.rename(columns={
        "Kategoria": t(Keys.CLOTHING_CATEGORY),
        "current_qty": t(Keys.CURRENT_SALES),
        "prior_qty": t(Keys.PRIOR_YEAR_SALES),
        "difference": t(Keys.DIFFERENCE),
        "percent_change": t(Keys.CHANGE_PCT),
    })

    display_df[t(Keys.CURRENT_SALES)] = display_df[t(Keys.CURRENT_SALES)].apply(lambda x: f"{int(x):,}")
    display_df[t(Keys.PRIOR_YEAR_SALES)] = display_df[t(Keys.PRIOR_YEAR_SALES)].apply(lambda x: f"{int(x):,}")
    display_df[t(Keys.DIFFERENCE)] = display_df[t(Keys.DIFFERENCE)].apply(lambda x: f"{int(x):+,}")
    display_df[t(Keys.CHANGE_PCT)] = display_df[t(Keys.CHANGE_PCT)].apply(
        lambda x: f"{Icons.NEW} {t(Keys.NEW)}" if abs(x - 999.0) < 0.01 else f"{x:+.1f}%"
    )

    table_df = display_df[[
        t(Keys.CLOTHING_CATEGORY),
        t(Keys.CURRENT_SALES),
        t(Keys.PRIOR_YEAR_SALES),
        t(Keys.DIFFERENCE),
        t(Keys.CHANGE_PCT),
    ]].reset_index(drop=True)
    table_df.index = [""] * len(table_df)
    st.table(table_df)


def _render_downloads(podgrupa_summary: pd.DataFrame, kategoria_details: pd.DataFrame, metadata: dict) -> None:
    col1, col2 = st.columns(2)

    with col1:
        podgrupa_csv = podgrupa_summary.copy()
        podgrupa_csv = podgrupa_csv.rename(columns={
            "Podgrupa": t(Keys.AGE_GROUP),
            "current_qty": t(Keys.METRIC_CURRENT_PERIOD),
            "prior_qty": t(Keys.PRIOR_PERIOD),
            "difference": t(Keys.DIFFERENCE),
            "percent_change": t(Keys.CHANGE_PCT),
        })

        csv_buffer = podgrupa_csv.to_csv(index=False)
        st.download_button(
            label=t(Keys.DOWNLOAD_PODGRUPA_SUMMARY),
            data=csv_buffer,
            file_name=f"monthly_yoy_podgrupa_{metadata['current_label']}.csv",
            mime=MimeTypes.TEXT_CSV,
        )

    with col2:
        kategoria_csv = kategoria_details.copy()
        kategoria_csv = kategoria_csv.rename(columns={
            "Podgrupa": t(Keys.AGE_GROUP),
            "Kategoria": t(Keys.CATEGORY),
            "current_qty": t(Keys.METRIC_CURRENT_PERIOD),
            "prior_qty": t(Keys.PRIOR_PERIOD),
            "difference": t(Keys.DIFFERENCE),
            "percent_change": t(Keys.CHANGE_PCT),
        })

        csv_buffer = kategoria_csv.to_csv(index=False)
        st.download_button(
            label=t(Keys.DOWNLOAD_CATEGORY_DETAILS),
            data=csv_buffer,
            file_name=f"monthly_yoy_kategoria_{metadata['current_label']}.csv",
            mime=MimeTypes.TEXT_CSV,
        )
