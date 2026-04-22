from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st

from nlq import (
    AIQueryGenerator,
    DuckDBExecutor,
    PostgresExecutor,
    QueryParser,
    is_ai_available,
    validate_read_only,
)
from nlq.intent import QueryIntent
from ui.constants import Config, Icons, MimeTypes
from ui.i18n import Keys, t
from ui.shared.data_loaders import load_data, load_forecast, load_stock
from ui.shared.session_manager import get_data_source, get_excluded_skus
from ui.shared.sku_utils import filter_excluded_skus
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

_MODE_PATTERN = "pattern"
_MODE_SQL = "sql"
_MODE_AI = "ai"


@st.fragment
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
    executor = _create_executor(is_database_mode, data_source, sales_df, stock_df, forecast_df, sku_summary_df)

    mode_labels = {
        _MODE_PATTERN: t(Keys.NLQ_MODE_PATTERN),
        _MODE_SQL: t(Keys.NLQ_MODE_SQL),
        _MODE_AI: t(Keys.NLQ_MODE_AI),
    }
    selected_label = st.radio(
        t(Keys.NLQ_QUERY_MODE),
        list(mode_labels.values()),
        horizontal=True,
        key="nlq_mode",
    )
    label_to_mode = {v: k for k, v in mode_labels.items()}
    mode = label_to_mode.get(str(selected_label), _MODE_PATTERN)

    if mode == _MODE_PATTERN:
        parser = QueryParser()
        _render_pattern_mode(parser, executor)
        _render_examples()
    elif mode == _MODE_SQL:
        _render_sql_mode(executor)
    elif mode == _MODE_AI:
        if not is_ai_available():
            st.warning(t(Keys.NLQ_AI_UNAVAILABLE))
            return
        _render_ai_mode(executor, is_database_mode)


def _load_data(context: dict) -> tuple:
    excluded = get_excluded_skus()
    sales_df = filter_excluded_skus(load_data(), excluded, sku_column="sku")

    stock_df = None
    if context.get("stock_loaded"):
        raw_stock, _ = load_stock()
        stock_df = filter_excluded_skus(raw_stock, excluded) if raw_stock is not None else None

    forecast_df = None
    if context.get("forecast_loaded"):
        raw_forecast, _, _ = load_forecast()
        forecast_df = filter_excluded_skus(raw_forecast, excluded, sku_column="sku") if raw_forecast is not None else None

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


# ---------------------------------------------------------------------------
# Pattern mode (existing)
# ---------------------------------------------------------------------------

def _render_pattern_mode(
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
        _clear_keys("nlq_last_result", "nlq_last_intent", "nlq_last_sql")
        st.rerun()

    if execute_clicked and query:
        _execute_pattern_query(query, parser, executor)
    elif "nlq_last_result" in st.session_state:
        _display_pattern_cached_result()


def _execute_pattern_query(
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


def _display_pattern_cached_result() -> None:
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


# ---------------------------------------------------------------------------
# SQL mode
# ---------------------------------------------------------------------------

def _render_sql_mode(executor: DuckDBExecutor | PostgresExecutor) -> None:
    st.caption(t(Keys.NLQ_SQL_READ_ONLY_WARNING))

    with st.form("nlq_sql_form", clear_on_submit=False, border=False):
        sql_input = st.text_area(
            t(Keys.NLQ_SQL_INPUT),
            placeholder=t(Keys.NLQ_SQL_PLACEHOLDER),
            height=150,
            key="nlq_sql_input",
        )
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            execute_clicked = st.form_submit_button(t(Keys.NLQ_EXECUTE), type="primary")
        with col2:
            clear_clicked = st.form_submit_button(t(Keys.NLQ_CLEAR))

    if clear_clicked:
        _clear_keys("nlq_sql_last_result", "nlq_sql_last_sql")
        st.rerun()

    if execute_clicked and sql_input:
        error = validate_read_only(sql_input)
        if error:
            st.error(f"{Icons.ERROR} {t(Keys.NLQ_SQL_REJECTED)}")
            return
        _execute_raw(sql_input, executor, "nlq_sql_last_result", "nlq_sql_last_sql")
    elif "nlq_sql_last_result" in st.session_state:
        _display_raw_cached("nlq_sql_last_result", "nlq_sql_last_sql")


# ---------------------------------------------------------------------------
# AI mode
# ---------------------------------------------------------------------------

def _render_ai_mode(
        executor: DuckDBExecutor | PostgresExecutor,
        is_database_mode: bool,
) -> None:
    _render_ai_history()

    with st.form("nlq_ai_form", clear_on_submit=True, border=False):
        user_query = st.text_input(
            t(Keys.NLQ_QUERY),
            placeholder=t(Keys.NLQ_AI_PLACEHOLDER),
            label_visibility="collapsed",
            key="nlq_ai_query_input",
        )
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            generate_clicked = st.form_submit_button(t(Keys.NLQ_EXECUTE), type="primary")
        with col2:
            clear_clicked = st.form_submit_button(t(Keys.NLQ_AI_CLEAR_HISTORY))

    if clear_clicked:
        _clear_keys(
            "nlq_ai_history", "nlq_ai_pending_sql", "nlq_ai_pending_explanation",
            "nlq_ai_last_result", "nlq_ai_last_sql",
        )
        st.rerun()

    if generate_clicked and user_query:
        _generate_ai_sql(user_query, is_database_mode)

    if st.session_state.get("nlq_ai_pending_sql"):
        _render_ai_confirm(executor)
    elif "nlq_ai_last_result" in st.session_state:
        _display_raw_cached("nlq_ai_last_result", "nlq_ai_last_sql")


def _generate_ai_sql(user_query: str, is_database_mode: bool) -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    history: list[dict[str, str]] = st.session_state.get("nlq_ai_history", [])

    generator = AIQueryGenerator(api_key, model, is_database_mode)

    with st.spinner(t(Keys.NLQ_AI_GENERATING)):  # type: ignore[attr-defined]
        sql, explanation = generator.generate_sql(user_query, history)

    if not sql:
        st.error(f"{Icons.ERROR} {t(Keys.NLQ_AI_ERROR).format(error=explanation)}")
        return

    history.append({"role": "user", "content": user_query})
    history.append({"role": "assistant", "content": sql})
    st.session_state["nlq_ai_history"] = history
    st.session_state["nlq_ai_pending_sql"] = sql
    st.session_state["nlq_ai_pending_explanation"] = explanation
    st.session_state.pop("nlq_ai_last_result", None)
    st.rerun()


def _render_ai_confirm(executor: DuckDBExecutor | PostgresExecutor) -> None:
    pending_sql = st.session_state.get("nlq_ai_pending_sql", "")
    explanation = st.session_state.get("nlq_ai_pending_explanation", "")

    if explanation:
        with st.expander(t(Keys.NLQ_AI_EXPLANATION), expanded=True):
            st.markdown(explanation)

    st.markdown(f"**{t(Keys.NLQ_AI_GENERATED_SQL)}:**")
    edited_sql = st.text_area(
        t(Keys.NLQ_AI_GENERATED_SQL),
        value=pending_sql,
        height=150,
        key="nlq_ai_edit_sql",
        label_visibility="collapsed",
    )

    col1, _, _ = st.columns([1, 1, 4])
    with col1:
        if st.button(t(Keys.NLQ_AI_CONFIRM_EXECUTE), type="primary", key="nlq_ai_execute_btn"):
            final_sql = edited_sql.strip() if edited_sql else pending_sql
            error = validate_read_only(final_sql)
            if error:
                st.error(f"{Icons.ERROR} {t(Keys.NLQ_SQL_REJECTED)}")
                return
            st.session_state.pop("nlq_ai_pending_sql", None)
            st.session_state.pop("nlq_ai_pending_explanation", None)
            _execute_raw(final_sql, executor, "nlq_ai_last_result", "nlq_ai_last_sql")


def _render_ai_history() -> None:
    history: list[dict[str, str]] = st.session_state.get("nlq_ai_history", [])
    if not history:
        return

    for msg in history:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").code(msg["content"], language="sql")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _execute_raw(
        sql: str,
        executor: DuckDBExecutor | PostgresExecutor,
        result_key: str,
        sql_key: str,
) -> None:
    with st.spinner(t(Keys.NLQ_PROCESSING)):  # type: ignore[attr-defined]
        result_df, error, executed_sql = executor.execute_raw_sql(sql)
        st.session_state[sql_key] = executed_sql

        if executed_sql:
            with st.expander(t(Keys.NLQ_GENERATED_SQL), expanded=False):
                st.code(executed_sql, language="sql")

        if error:
            st.error(f"{Icons.ERROR} {error}")
            st.session_state.pop(result_key, None)
            return

        st.session_state[result_key] = result_df
        _display_result(result_df, None)


def _display_raw_cached(result_key: str, sql_key: str) -> None:
    result_df = st.session_state.get(result_key)
    sql = st.session_state.get(sql_key)
    if sql:
        with st.expander(t(Keys.NLQ_GENERATED_SQL), expanded=False):
            st.code(sql, language="sql")
    if result_df is not None:
        _display_result(result_df, None)


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
        key=f"nlq_download_{entity}",
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


def _clear_keys(*keys: str) -> None:
    for key in keys:
        st.session_state.pop(key, None)
