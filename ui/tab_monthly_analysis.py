from __future__ import annotations

import pandas as pd
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import ColumnNames, Icons, MimeTypes, SessionKeys
from ui.shared.data_loaders import load_category_mappings, load_data
from ui.shared.session_manager import get_session_value, set_session_value
from utils.logging_config import get_logger

logger = get_logger("tab_monthly_analysis")


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Monthly Analysis")
        st.error(f"{Icons.ERROR} Error in Monthly Analysis: {str(e)}")


def _render_content() -> None:
    st.header("📅 Monthly Year-over-Year Analysis by Category")

    st.markdown("""
    Compare monthly sales quantities from current year to previous year, organized by age group (Podgrupa)
    and clothing category (Kategoria). Automatically excludes the current incomplete month.
    """)

    category_df = load_category_mappings()

    if category_df is None or category_df.empty:
        st.warning(
            "Category mappings not available. Please ensure the Kategorie sheet exists in the data file or database table is populated."
        )
        st.stop()

    _render_generate_button(category_df)
    _render_analysis_results()


def _render_generate_button(category_df: pd.DataFrame) -> None:
    if st.button("🔄 Generate Monthly YoY Analysis", type="primary", width="stretch"):
        # noinspection PyTypeChecker
        with st.spinner("Calculating year-over-year comparison..."):
            try:
                sales_df = load_data()
                if sales_df is None or sales_df.empty:
                    st.error("No sales data loaded. Please ensure data is loaded in Tab 1.")
                    st.stop()

                podgrupa_summary, kategoria_details, metadata = SalesAnalyzer.calculate_monthly_yoy_by_category(
                    sales_df, category_df
                )

                set_session_value(SessionKeys.MONTHLY_YOY_PODGRUPA, podgrupa_summary)
                set_session_value(SessionKeys.MONTHLY_YOY_KATEGORIA, kategoria_details)
                set_session_value(SessionKeys.MONTHLY_YOY_METADATA, metadata)

                st.success("Analysis generated successfully!")

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.stop()


def _render_analysis_results() -> None:
    metadata = get_session_value(SessionKeys.MONTHLY_YOY_METADATA)

    if metadata is None:
        st.info("Click 'Generate Monthly YoY Analysis' to start the analysis.")
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
            ColumnNames.CURRENT_PERIOD,
            metadata["current_label"],
            delta=f"{int(metadata['total_current']):,} units",
        )
    with col2:
        st.metric(
            "Same Period Last Year",
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
            "Total YoY Change",
            f"{overall_pct_change:+.1f}%",
            delta=f"{int(metadata['total_difference']):,} units",
        )
    with col2:
        st.metric("Rising Categories", metadata["rising_count"])
    with col3:
        st.metric("Falling Categories", metadata["falling_count"])
    with col4:
        if metadata["uncategorized_sales"] > 0:
            st.metric(
                f"{Icons.WARNING} Uncategorized",
                f"{metadata['uncategorized_models']} models",
                delta=f"{int(metadata['uncategorized_sales']):,} units",
            )


def _render_category_breakdown(podgrupa_summary: pd.DataFrame, kategoria_details: pd.DataFrame) -> None:
    st.subheader("Sales by Age Group & Category")

    for _, row in podgrupa_summary.iterrows():
        podgrupa = row["Podgrupa"]
        current_qty = int(row["current_qty"])
        pct_change = row["percent_change"]

        if pd.isna(podgrupa):
            podgrupa = f"{Icons.WARNING} Uncategorized"

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
    is_uncategorized = f"{Icons.WARNING} Uncategorized" in str(podgrupa)

    if is_uncategorized:
        podgrupa_categories = kategoria_details[kategoria_details["Podgrupa"].isna()].copy()
    else:
        podgrupa_categories = kategoria_details[kategoria_details["Podgrupa"] == podgrupa].copy()

    if podgrupa_categories.empty:
        st.info("No data for this age group.")
        return

    display_df = podgrupa_categories.copy()
    display_df["Kategoria"] = display_df["Kategoria"].fillna("Unknown")
    display_df = display_df.rename(columns={
        "Kategoria": "Clothing Category",
        "current_qty": ColumnNames.CURRENT_SALES,
        "prior_qty": ColumnNames.PRIOR_YEAR_SALES,
        "difference": "Difference",
        "percent_change": ColumnNames.CHANGE_PCT,
    })

    display_df[ColumnNames.CURRENT_SALES] = display_df[ColumnNames.CURRENT_SALES].apply(lambda x: f"{int(x):,}")
    display_df[ColumnNames.PRIOR_YEAR_SALES] = display_df[ColumnNames.PRIOR_YEAR_SALES].apply(lambda x: f"{int(x):,}")
    display_df["Difference"] = display_df["Difference"].apply(lambda x: f"{int(x):+,}")
    display_df[ColumnNames.CHANGE_PCT] = display_df[ColumnNames.CHANGE_PCT].apply(
        lambda x: f"{Icons.NEW} New" if abs(x - 999.0) < 0.01 else f"{x:+.1f}%"
    )

    st.dataframe(
        display_df[[
            "Clothing Category",
            ColumnNames.CURRENT_SALES,
            ColumnNames.PRIOR_YEAR_SALES,
            "Difference",
            ColumnNames.CHANGE_PCT,
        ]],
        width="stretch",
        hide_index=True,
    )


def _render_downloads(podgrupa_summary: pd.DataFrame, kategoria_details: pd.DataFrame, metadata: dict) -> None:
    col1, col2 = st.columns(2)

    with col1:
        podgrupa_csv = podgrupa_summary.copy()
        podgrupa_csv = podgrupa_csv.rename(columns={
            "Podgrupa": "Age Group",
            "current_qty": ColumnNames.CURRENT_PERIOD,
            "prior_qty": "Prior Period",
            "difference": "Difference",
            "percent_change": ColumnNames.CHANGE_PCT,
        })

        csv_buffer = podgrupa_csv.to_csv(index=False)
        st.download_button(
            label="📥 Download Podgrupa Summary (CSV)",
            data=csv_buffer,
            file_name=f"monthly_yoy_podgrupa_{metadata['current_label']}.csv",
            mime=MimeTypes.TEXT_CSV,
            width="stretch",
        )

    with col2:
        kategoria_csv = kategoria_details.copy()
        kategoria_csv = kategoria_csv.rename(columns={
            "Podgrupa": "Age Group",
            "Kategoria": "Category",
            "current_qty": ColumnNames.CURRENT_PERIOD,
            "prior_qty": "Prior Period",
            "difference": "Difference",
            "percent_change": ColumnNames.CHANGE_PCT,
        })

        csv_buffer = kategoria_csv.to_csv(index=False)
        st.download_button(
            label="📥 Download Category Details (CSV)",
            data=csv_buffer,
            file_name=f"monthly_yoy_kategoria_{metadata['current_label']}.csv",
            mime=MimeTypes.TEXT_CSV,
            width="stretch",
        )
