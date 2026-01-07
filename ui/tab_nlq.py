from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from nlq import DuckDBExecutor, PostgresExecutor, QueryIntent, QueryParser
from ui.constants import Config, Icons, MimeTypes
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
        st.error(f"{Icons.ERROR} Error in Natural Language Query: {str(e)}")


def _render_content(context: dict) -> None:
    st.title("🔍 Natural Language Query")
    st.caption("Query your data using natural language (English or Polish)")

    data_source = get_data_source()
    is_database_mode = data_source.get_data_source_type() == "database"

    if is_database_mode:
        st.info("Database mode: queries executed via SQL on PostgreSQL")
    else:
        st.info("File mode: queries executed via SQL on DuckDB")

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
    st.subheader("Enter your query")

    query = st.text_input(
        "Query",
        placeholder="e.g., sales of model CH086 last 2 years",
        label_visibility="collapsed",
        key="nlq_query_input",
    )

    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        execute_clicked = st.button("Execute", type="primary", key="nlq_execute")
    with col2:
        clear_clicked = st.button("Clear", key="nlq_clear")

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
    with st.spinner("Processing query..."):  # type: ignore[attr-defined]
        intent = parser.parse(query)
        st.session_state["nlq_last_intent"] = intent

        if not intent.is_valid():
            _display_interpretation(intent, None)
            st.warning(f"{Icons.WARNING} Could not understand the query. Please try rephrasing.")
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
    with st.expander("Query interpretation & SQL", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Confidence:** {intent.confidence:.0%}")
            st.markdown(f"**Interpretation:** {intent.get_description()}")
            if intent.confidence < 0.5:
                st.warning(f"{Icons.WARNING} Low confidence - results may not match your intent")
        with col2:
            if sql:
                st.markdown("**Generated SQL:**")
                st.code(sql, language="sql")


def _display_result(result_df: pd.DataFrame | None, intent: QueryIntent | None) -> None:
    if result_df is None or result_df.empty:
        st.info(f"{Icons.INFO} No results found")
        return

    st.subheader("Results")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rows", len(result_df))
    with col2:
        st.metric("Columns", len(result_df.columns))

    row_height = 35
    header_height = 38
    max_height = Config.DATAFRAME_HEIGHT
    calculated_height = min(header_height + len(result_df) * row_height, max_height)

    st.dataframe(result_df, hide_index=True, height=calculated_height, width='stretch')

    csv = result_df.to_csv(index=False)
    entity = intent.entity_type if intent else "query"
    filename = f"nlq_{entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    st.download_button(
        "📥 Download Results (CSV)",
        csv,
        filename,
        MimeTypes.TEXT_CSV,
        key="nlq_download_results",
    )


def _render_examples() -> None:
    st.markdown("---")
    with st.expander("📚 Example queries", expanded=True):
        st.markdown("Click on any example to copy it to your clipboard:")
        st.markdown("")

        for query, description in EXAMPLE_QUERIES:
            col1, col2 = st.columns([2, 3])
            with col1:
                st.code(query, language=None)
            with col2:
                st.caption(description)
