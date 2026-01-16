from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from nlq import DuckDBExecutor, PostgresExecutor, QueryIntent, QueryParser
from ui.constants import Config, Icons, MimeTypes
from ui.i18n import Keys, t
from ui.shared.data_loaders import load_data, load_forecast, load_stock
from ui.shared.session_manager import get_data_source
from utils.logging_config import get_logger

logger = get_logger("tab_nlq")

EXAMPLE_QUERIES = [
    ("sales of model CH086 last 4 years", "Sales data for specific model over time"),
    ("sales by month for model CH086", "Monthly breakdown of model sales"),
    ("stock below rop", "Items that need reordering"),
    ("top 10 models by sales", "Best selling models"),
    ("stock type = seasonal", "Seasonal products inventory"),
    ("forecast for model DO322", "Forecast data for specific model"),
    ("sprzedaz modelu JU386 ostatnie 2 lata", "Polish: Sales for model last 2 years"),
    ("stan ponizej rop", "Polish: Stock below ROP"),
    ("top 5 modeli wg sprzedazy", "Polish: Top 5 models by sales"),
]


def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        logger.exception("Error in NLQ tab")
        st.error(f"{Icons.ERROR} {t(Keys.NLQ_ERROR_IN_TAB).format(error=str(e))}")


def _render_content(context: dict) -> None:
    st.title(t(Keys.NLQ_TITLE))
    st.caption(t(Keys.NLQ_CAPTION))

    data_source = get_data_source()
    is_database_mode = data_source.get_data_source_type() == "database"

    if is_database_mode:
        st.info(t(Keys.NLQ_DATABASE_MODE))
    else:
        st.info(t(Keys.NLQ_FILE_MODE))

    sales_df, stock_df, forecast_df, sku_summary_df = _load_data(context)

    parser = QueryParser()
    executor = _create_executor(is_database_mode, data_source, sales_df, stock_df, forecast_df, sku_summary_df)

    _render_query_input(parser, executor)
    _render_examples()


def _load_data(context: dict) -> tuple:
    sales_df = load_data()

    stock_df = None
    if context.get("stock_loaded"):
        stock_df, _ = load_stock()

    forecast_df = None
    if context.get("forecast_loaded"):
        forecast_df, _, _ = load_forecast()

    sku_summary_df = context.get("sku_summary_df")

    return sales_df, stock_df, forecast_df, sku_summary_df


def _create_executor(
        is_database_mode: bool,
        data_source: object,
        sales_df: pd.DataFrame,
        stock_df: pd.DataFrame | None,
        forecast_df: pd.DataFrame | None,
        sku_summary_df: pd.DataFrame | None,
) -> DuckDBExecutor | PostgresExecutor:
    if is_database_mode:
        engine = getattr(data_source, "engine", None)
        return PostgresExecutor(engine=engine)
    return DuckDBExecutor(
        sales_df=sales_df,
        stock_df=stock_df,
        forecast_df=forecast_df,
        sku_summary_df=sku_summary_df,
    )


def _render_query_input(
        parser: QueryParser,
        executor: DuckDBExecutor | PostgresExecutor,
) -> None:
    st.subheader(t(Keys.NLQ_ENTER_QUERY))

    with st.form("nlq_query_form", clear_on_submit=False, border=False):
        query = st.text_input(
            t(Keys.NLQ_QUERY),
            placeholder=t(Keys.NLQ_PLACEHOLDER),
            label_visibility="collapsed",
            key="nlq_query_input",
        )
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            execute_clicked = st.form_submit_button(t(Keys.NLQ_EXECUTE), type="primary")
        with col2:
            clear_clicked = st.form_submit_button(t(Keys.NLQ_CLEAR))

    if clear_clicked:
        _clear_session_state()
        st.rerun()

    if execute_clicked and query:
        _execute_query(query, parser, executor)
    elif "nlq_last_result" in st.session_state:
        _display_cached_result()


def _clear_session_state() -> None:
    keys_to_remove = ["nlq_last_result", "nlq_last_intent", "nlq_last_sql"]
    for key in keys_to_remove:
        st.session_state.pop(key, None)


def _execute_query(
        query: str,
        parser: QueryParser,
        executor: DuckDBExecutor | PostgresExecutor,
) -> None:
    with st.spinner(t(Keys.NLQ_PROCESSING)):  # type: ignore[attr-defined]
        intent = parser.parse(query)
        st.session_state["nlq_last_intent"] = intent

        if not intent.is_valid():
            _display_interpretation(intent, None)
            st.warning(f"{Icons.WARNING} {t(Keys.NLQ_COULD_NOT_UNDERSTAND)}")
            return

        result_df, error, sql = executor.execute(intent)
        st.session_state["nlq_last_sql"] = sql

        _display_interpretation(intent, sql)

        if error:
            st.error(f"{Icons.ERROR} {error}")
            st.session_state.pop("nlq_last_result", None)
            return

        st.session_state["nlq_last_result"] = result_df
        _display_result(result_df, intent)


def _display_cached_result() -> None:
    intent = st.session_state.get("nlq_last_intent")
    result_df = st.session_state.get("nlq_last_result")
    sql = st.session_state.get("nlq_last_sql")

    if intent:
        _display_interpretation(intent, sql)
    if result_df is not None:
        _display_result(result_df, intent)


def _display_interpretation(intent: QueryIntent, sql: str | None) -> None:
    with st.expander(t(Keys.NLQ_INTERPRETATION_SQL), expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{t(Keys.NLQ_CONFIDENCE)}:** {intent.confidence:.0%}")
            st.markdown(f"**{t(Keys.NLQ_INTERPRETATION)}:** {intent.get_description()}")
            if intent.confidence < 0.5:
                st.warning(f"{Icons.WARNING} {t(Keys.NLQ_LOW_CONFIDENCE)}")
        with col2:
            if sql:
                st.markdown(f"**{t(Keys.NLQ_GENERATED_SQL)}:**")
                st.code(sql, language="sql")


def _display_result(result_df: pd.DataFrame | None, intent: QueryIntent | None) -> None:
    if result_df is None or result_df.empty:
        st.info(f"{Icons.INFO} {t(Keys.NLQ_NO_RESULTS)}")
        return

    st.subheader(t(Keys.NLQ_RESULTS))

    col1, col2 = st.columns(2)
    with col1:
        st.metric(t(Keys.NLQ_ROWS), len(result_df))
    with col2:
        st.metric(t(Keys.NLQ_COLUMNS), len(result_df.columns))

    row_height = 35
    header_height = 38
    max_height = Config.DATAFRAME_HEIGHT
    calculated_height = min(header_height + len(result_df) * row_height, max_height)

    display_df = result_df.copy()
    for col in display_df.columns:
        if display_df[col].dtype == object:
            display_df[col] = display_df[col].astype(str)

    st.dataframe(display_df, hide_index=True, height=calculated_height, width='stretch')

    csv = result_df.to_csv(index=False)
    entity = intent.entity_type if intent else "query"
    filename = f"nlq_{entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    st.download_button(
        t(Keys.NLQ_DOWNLOAD_RESULTS),
        csv,
        filename,
        MimeTypes.TEXT_CSV,
        key="nlq_download_results",
    )


def _render_examples() -> None:
    st.markdown("---")
    with st.expander(t(Keys.NLQ_EXAMPLE_QUERIES), expanded=True):
        st.markdown(t(Keys.NLQ_CLICK_EXAMPLE))
        st.markdown("")

        for query, description in EXAMPLE_QUERIES:
            col1, col2 = st.columns([2, 3])
            with col1:
                st.code(query, language=None)
            with col2:
                st.caption(description)
