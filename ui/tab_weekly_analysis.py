from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import ColumnNames, Config, Icons, MimeTypes
from ui.i18n import t, Keys
from ui.shared.data_loaders import load_data, load_stock
from ui.shared.display_helpers import display_star_product
from ui.shared.session_manager import get_settings
from ui.shared.sku_utils import extract_color, extract_model
from utils.logging_config import get_logger

logger = get_logger("tab_weekly_analysis")


def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        logger.exception("Error in Weekly Analysis")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_WEEKLY_ANALYSIS).format(error=str(e))}")


def _render_content(context: dict) -> None:
    st.title(t(Keys.TITLE_WEEKLY_ANALYSIS))

    if st.button(t(Keys.BTN_REFRESH), type="primary"):
        st.cache_data.clear()
        st.rerun()

    df = load_data()
    stock_df = None
    if context.get("stock_loaded"):
        stock_df, _ = load_stock()

    st.markdown("---")
    _render_top_sales_report(df)

    st.markdown("---")
    _render_top_by_type(df, stock_df)

    st.markdown("---")
    _render_new_products_monitoring(df, stock_df)


def _render_top_sales_report(df: pd.DataFrame) -> None:
    st.header(t(Keys.TITLE_TOP_SALES_REPORT))
    st.caption(t(Keys.WEEKLY_CAPTION))

    try:
        top_sales = SalesAnalyzer.calculate_top_sales_report(
            sales_df=df, reference_date=datetime.today()
        )

        col_dates1, col_dates2 = st.columns(2)
        with col_dates1:
            st.metric(
                t(Keys.METRIC_LAST_WEEK),
                f"{top_sales['last_week_start'].strftime('%d-%m-%Y')} - {top_sales['last_week_end'].strftime('%d-%m-%Y')}",
            )
        with col_dates2:
            st.metric(
                t(Keys.METRIC_SAME_WEEK_LAST_YEAR),
                f"{top_sales['prev_year_start'].strftime('%d-%m-%Y')} - {top_sales['prev_year_end'].strftime('%d-%m-%Y')}",
            )

        col_rising, col_falling = st.columns(2)

        with col_rising:
            st.subheader(t(Keys.RISING_STAR))
            if top_sales["rising_star"] is not None:
                display_star_product(top_sales["rising_star"], is_rising=True)
            else:
                st.info(t(Keys.NO_RISING_PRODUCTS))

        with col_falling:
            st.subheader(t(Keys.FALLING_STAR))
            if top_sales["falling_star"] is not None:
                display_star_product(top_sales["falling_star"], is_rising=False)
            else:
                st.info(t(Keys.NO_FALLING_PRODUCTS))

    except Exception as e:
        logger.exception("Error generating TOP SALES REPORT")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_TOP_SALES_REPORT).format(error=e)}")


def _render_top_by_type(df: pd.DataFrame, stock_df: pd.DataFrame | None) -> None:
    st.header(t(Keys.TITLE_TOP_5_BY_TYPE))
    st.caption(t(Keys.WEEKLY_TOP_SALES_CAPTION))

    try:
        settings = get_settings()
        cv_basic = settings["cv_thresholds"]["basic"]
        cv_seasonal = settings["cv_thresholds"]["seasonal"]

        top_products = SalesAnalyzer.calculate_top_products_by_type(
            sales_df=df, cv_basic=cv_basic, cv_seasonal=cv_seasonal, reference_date=datetime.today()
        )

        col_new, col_seasonal = st.columns(2)
        col_regular, col_basic = st.columns(2)

        _display_top_5(col_new, t(Keys.TYPE_NEW), Icons.NEW, top_products["top_by_type"]["new"], stock_df)
        _display_top_5(col_seasonal, t(Keys.TYPE_SEASONAL), Icons.SEASONAL, top_products["top_by_type"]["seasonal"], stock_df)
        _display_top_5(col_regular, t(Keys.TYPE_REGULAR), Icons.REGULAR, top_products["top_by_type"]["regular"], stock_df)
        _display_top_5(col_basic, t(Keys.TYPE_BASIC), Icons.BASIC, top_products["top_by_type"]["basic"], stock_df)

    except Exception as e:
        logger.exception("Error generating Top 5 by Type")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_TOP_5_BY_TYPE).format(error=e)}")


def _display_top_5(column, type_name: str, emoji: str, df_top: pd.DataFrame, stock_df: pd.DataFrame | None) -> None:
    with column:
        st.subheader(f"{emoji} {type_name.upper()}")
        if df_top.empty:
            st.info(t(Keys.NO_PRODUCTS_FOUND).format(type=type_name))
            return

        top_products_df = df_top.copy()
        top_products_df[ColumnNames.MODEL_COLOR] = top_products_df["model"] + top_products_df["color"]

        final_cols = [ColumnNames.MODEL_COLOR, "sales"]
        col_names = {"sales": "SALES"}

        if stock_df is not None:
            stock_df_copy = stock_df.copy()
            stock_df_copy["model"] = extract_model(stock_df_copy["sku"])
            stock_df_copy["color"] = extract_color(stock_df_copy["sku"])
            descriptions = stock_df_copy.groupby(["model", "color"], observed=True)["nazwa"].first().reset_index()
            top_products_df = top_products_df.merge(descriptions, on=["model", "color"], how="left")
            top_products_df["nazwa"] = top_products_df["nazwa"].astype(str).replace("nan", "")
            final_cols = [ColumnNames.MODEL_COLOR, "nazwa", "sales"]
            col_names = {"nazwa": "DESCRIPTION", "sales": "SALES"}

        st.dataframe(
            top_products_df[final_cols].rename(columns=col_names),
            hide_index=True,
            width='stretch'
        )


def _render_new_products_monitoring(df: pd.DataFrame, stock_df: pd.DataFrame | None) -> None:
    st.header(t(Keys.TITLE_NEW_PRODUCTS_MONITORING))
    st.caption(t(Keys.WEEKLY_NEW_PRODUCTS_CAPTION))

    settings = get_settings()
    lookback_days = settings.get("weekly_analysis", {}).get("lookback_days", Config.WEEKLY_LOOKBACK_DAYS)

    # noinspection PyTypeChecker
    with st.spinner(t(Keys.GENERATING_WEEKLY)):
        try:
            weekly_df = SalesAnalyzer.generate_weekly_new_products_analysis(
                sales_df=df,
                stock_df=stock_df,
                lookback_days=lookback_days,
                reference_date=datetime.today(),
            )

            if weekly_df.empty:
                st.info(f"{Icons.INFO} {t(Keys.NO_NEW_PRODUCTS).format(days=lookback_days)}")
                return

            _display_weekly_metrics(weekly_df)
            _display_weekly_table(weekly_df)
            _display_zero_sales_warning(weekly_df)

        except Exception as e:
            logger.exception("Error generating weekly analysis")
            st.error(f"{Icons.ERROR} {t(Keys.ERR_GENERATING_WEEKLY).format(error=e)}")


def _display_weekly_metrics(weekly_df: pd.DataFrame) -> None:
    week_cols = [col for col in weekly_df.columns if col not in ["SALES_START_DATE", "MODEL", "DESCRIPTION"]]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t(Keys.METRIC_NEW_PRODUCTS), len(weekly_df))
    with col2:
        st.metric(t(Keys.METRIC_WEEKS_TRACKED), len(week_cols))
    with col3:
        total_sales = weekly_df[week_cols].sum().sum() if week_cols else 0
        st.metric(t(Keys.METRIC_TOTAL_SALES), f"{int(total_sales):,}")


def _display_weekly_table(weekly_df: pd.DataFrame) -> None:
    st.subheader(t(Keys.WEEKLY_SALES_BY_MODEL))
    row_height = 35
    header_height = 38
    max_height = 400
    calculated_height = min(header_height + len(weekly_df) * row_height, max_height)
    st.dataframe(weekly_df, width='stretch', hide_index=True, height=calculated_height)

    csv = weekly_df.to_csv(index=False)
    st.download_button(
        t(Keys.DOWNLOAD_WEEKLY_ANALYSIS),
        csv,
        f"weekly_new_products_{datetime.today().strftime('%Y%m%d')}.csv",
        MimeTypes.TEXT_CSV,
        key="download_tab3_weekly_analysis",
    )


def _display_zero_sales_warning(weekly_df: pd.DataFrame) -> None:
    week_cols = [col for col in weekly_df.columns if col not in ["SALES_START_DATE", "MODEL", "DESCRIPTION"]]
    weekly_df_with_total = weekly_df.copy()
    numeric_week_data = weekly_df_with_total[week_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    weekly_df_with_total["TOTAL_SALES"] = numeric_week_data.sum(axis=1)
    zero_sales = weekly_df_with_total[weekly_df_with_total["TOTAL_SALES"] == 0]

    if not zero_sales.empty:
        st.warning(t(Keys.ZERO_SALES_WARNING).format(count=len(zero_sales)))
        with st.expander(t(Keys.VIEW_ZERO_SALES), expanded=False):
            display_cols = ["SALES_START_DATE", "MODEL"]
            if "DESCRIPTION" in zero_sales.columns:
                display_cols.append("DESCRIPTION")
            st.dataframe(zero_sales[display_cols], hide_index=True)
