from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from exceptions import DataLoadError
from sales_data.analysis.forecast_comparison import (
    aggregate_comparison_by_type,
    align_forecasts,
    calculate_comparison_metrics,
    calculate_overall_summary,
)
from sales_data.analysis.internal_forecast import (
    batch_generate_forecasts,
    get_available_methods,
)
from ui.constants import Icons, MimeTypes
from ui.i18n import Keys, t
from ui.shared.session_manager import get_data_source, get_settings
from utils.internal_forecast_repository import create_internal_forecast_repository
from utils.logging_config import get_logger

LINES_MARKERS = "lines+markers"

EXT_MAPE = "Ext MAPE"

INT_MAPE = "Int MAPE"

ACTUAL_VOLUME = "Actual Volume"

AVG_EXT_MAPE = "Avg Ext MAPE"

AVG_INT_MAPE = "Avg Int MAPE"

INTERNAL_WIN_PERCENTILE = "Internal Win %"
MAPE_AVG_EXT_MAPE_ = [
    "Type", "Total", "Internal Wins", "External Wins", "Ties",
    INTERNAL_WIN_PERCENTILE, AVG_INT_MAPE, AVG_EXT_MAPE
]

logger = get_logger("tab_forecast_comparison")

SESSION_KEY_DATA = "forecast_comparison_data"
SESSION_KEY_PARAMS = "forecast_comparison_params"
SESSION_KEY_INTERNAL_FORECASTS = "internal_forecasts_df"


@st.cache_data(ttl=3600)
def _load_monthly_aggregations_cached() -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        return data_source.get_monthly_aggregations()
    except (DataLoadError, KeyError, ValueError):
        return None


@st.cache_data(ttl=3600)
def _load_external_forecast_cached() -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        return data_source.load_forecast_data()
    except (DataLoadError, KeyError, ValueError):
        return None


@st.cache_data(ttl=3600)
def _load_sales_data_cached() -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        return data_source.load_sales_data()
    except (DataLoadError, KeyError, ValueError):
        return None


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Forecast Comparison")
        st.error(f"{Icons.ERROR} {t(Keys.FC_ERROR_IN_TAB).format(error=str(e))}")


def _render_content() -> None:
    st.title(t(Keys.TITLE_FORECAST_COMPARISON))
    st.write(t(Keys.COMPARE_FORECASTS))

    tab_new, tab_history = st.tabs([t(Keys.GENERATE_NEW), t(Keys.HISTORICAL_FORECASTS)])

    with tab_new:
        _render_new_forecast_tab()

    with tab_history:
        _render_historical_tab()


def _render_new_forecast_tab() -> None:
    params = _render_parameters()

    col_gen, col_clear = st.columns([1, 1])
    with col_gen:
        if st.button(t(Keys.BTN_GENERATE), type="primary", key="gen_comparison"):
            _generate_comparison(params)
    with col_clear:
        if st.button(t(Keys.FC_CLEAR_RESULTS), key="clear_comparison"):
            st.session_state.pop(SESSION_KEY_DATA, None)
            st.session_state.pop(SESSION_KEY_PARAMS, None)
            st.session_state.pop(SESSION_KEY_INTERNAL_FORECASTS, None)
            st.rerun()

    if SESSION_KEY_DATA in st.session_state:
        _display_results()
        _render_save_section()


def _render_parameters() -> dict:
    with st.expander(t(Keys.FC_PARAMETERS), expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            settings = get_settings()
            horizon = st.number_input(
                t(Keys.FORECAST_HORIZON),
                min_value=1,
                max_value=12,
                value=int(settings.get("lead_time", 2)),
                key="fc_horizon",
            )

        with col2:
            entity_type = st.selectbox(
                t(Keys.ANALYSIS_LEVEL),
                options=["model", "sku"],
                format_func=lambda x: t(Keys.FC_MODEL_FASTER) if x == "model" else t(Keys.FC_SKU_SLOWER),
                key="fc_entity_type",
            )

        with col3:
            filter_type = st.selectbox(
                t(Keys.ENTITY_FILTER),
                options=["all", "top_n", "by_type"],
                format_func=lambda x: {
                    "all": t(Keys.ALL_ENTITIES),
                    "top_n": t(Keys.TOP_N_BY_VOLUME),
                    "by_type": t(Keys.BY_PRODUCT_TYPE),
                }[x],
                key="fc_filter_type",
            )

        with col4:
            available_methods = get_available_methods()
            method_labels = {
                "auto": t(Keys.AUTO_SELECT),
                "moving_avg": t(Keys.FC_MOVING_AVG),
                "exp_smoothing": t(Keys.FC_EXP_SMOOTHING),
                "holt_winters": t(Keys.FC_HOLT_WINTERS),
                "sarima": t(Keys.FC_SARIMA),
                "auto_arima": t(Keys.FC_AUTO_ARIMA),
            }
            method_options = ["auto"] + available_methods
            forecast_method = st.selectbox(
                t(Keys.FORECAST_METHOD),
                options=method_options,
                format_func=lambda x: method_labels.get(x, x),
                key="fc_method",
                help=t(Keys.FORECAST_METHOD_HELP),
            )

        st.markdown("---")
        col_date1, col_date2, col_info = st.columns([1, 1, 2])

        with col_date1:
            generation_date = st.date_input(
                t(Keys.GENERATE_AS_OF),
                value=pd.Timestamp.now().date(),
                help=t(Keys.FC_GENERATE_AS_OF_HELP),
                key="fc_generation_date",
            )

        with col_date2:
            comparison_date = st.date_input(
                t(Keys.COMPARE_AS_OF),
                value=pd.Timestamp.now().date(),
                help=t(Keys.FC_COMPARE_AS_OF_HELP),
                key="fc_comparison_date",
            )

        with col_info:
            st.caption(t(Keys.DATE_CAPTION))

        filter_params = {}
        if filter_type == "top_n":
            filter_params["top_n"] = st.slider(
                t(Keys.NUMBER_TOP_ENTITIES),
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                key="fc_top_n",
            )
        elif filter_type == "by_type":
            filter_params["product_types"] = st.multiselect(
                t(Keys.PRODUCT_TYPES),
                options=["basic", "regular", "seasonal", "new"],
                default=["basic", "regular", "seasonal"],
                key="fc_product_types",
            )

        if entity_type == "sku":
            filter_params["model_filter"] = st.text_input(
                t(Keys.FILTER_BY_MODEL),
                placeholder="e.g., CH031",
                key="fc_model_filter",
            )

    return {
        "horizon": horizon,
        "entity_type": entity_type,
        "filter_type": filter_type,
        "filter_params": filter_params,
        "forecast_method": forecast_method if forecast_method != "auto" else None,
        "generation_date": generation_date,
        "comparison_date": comparison_date,
    }


def _filter_monthly_agg_by_date(monthly_agg: pd.DataFrame, cutoff_date) -> pd.DataFrame:
    if monthly_agg is None or monthly_agg.empty:
        return monthly_agg

    df = monthly_agg.copy()
    month_col = _find_column(df, ["year_month", "month", "MONTH"])

    if month_col is None:
        return df

    cutoff_period = pd.Period(pd.Timestamp(cutoff_date), freq="M")
    df["_period"] = pd.PeriodIndex(df[month_col].astype(str), freq="M")
    filtered = df[df["_period"] <= cutoff_period].drop(columns=["_period"])

    return filtered


def _generate_comparison(params: dict) -> None:
    progress_bar = st.progress(0, text=t(Keys.FC_LOADING_DATA))

    generation_date = params.get("generation_date", pd.Timestamp.now().date())
    comparison_date = params.get("comparison_date", pd.Timestamp.now().date())

    try:
        progress_bar.progress(5, text=t(Keys.FC_LOADING_MONTHLY_AGG))

        monthly_agg = _load_monthly_aggregations_cached()
        if monthly_agg is None or monthly_agg.empty:
            st.error(t(Keys.FC_NO_MONTHLY_AGG))
            return

        monthly_agg_filtered = _filter_monthly_agg_by_date(monthly_agg, generation_date)
        if monthly_agg_filtered.empty:
            st.error(t(Keys.FC_NO_DATA_BEFORE_DATE).format(date=generation_date))
            return

        progress_bar.progress(10, text=t(Keys.FC_LOADING_FORECASTS))

        external_forecast = _load_external_forecast_cached()
        if external_forecast is None or external_forecast.empty:
            st.warning(t(Keys.FC_NO_EXTERNAL_FORECAST))

        progress_bar.progress(20, text=t(Keys.FC_LOADING_SALES))

        forecast_start_period = pd.Period(pd.Timestamp(generation_date), freq="M") + 1
        comparison_sales_df = _load_sales_for_period(str(forecast_start_period), comparison_date)

        if comparison_sales_df is None or comparison_sales_df.empty:
            st.warning(t(Keys.FC_NO_SALES_FOR_COMPARISON).format(start=forecast_start_period, end=comparison_date))
            comparison_sales_df = pd.DataFrame()

        progress_bar.progress(30, text=t(Keys.FC_PREPARING_ENTITIES))

        entities = _prepare_entity_list(monthly_agg_filtered, params)

        if not entities:
            st.warning(t(Keys.FC_NO_ENTITIES_FOUND))
            return

        st.info(t(Keys.FC_PROCESSING_ENTITIES).format(count=len(entities), date=generation_date))

        def progress_callback(current, total, entity_id):
            pct = 30 + int((current / total) * 60)
            progress_bar.progress(pct, text=t(Keys.FC_FORECASTING_PROGRESS).format(current=current, total=total, entity=entity_id))

        progress_bar.progress(35, text=t(Keys.FC_GENERATING_FORECASTS))

        internal_forecasts, stats = batch_generate_forecasts(
            monthly_agg_filtered,
            entities,
            params["horizon"],
            progress_callback,
            method_override=params.get("forecast_method"),
        )

        progress_bar.progress(90, text=t(Keys.FC_CALCULATING_METRICS))

        if internal_forecasts.empty:
            st.error(t(Keys.FC_NO_INTERNAL_FORECASTS))
            return

        comparison_df = align_forecasts(
            internal_forecasts,
            external_forecast,
            comparison_sales_df,
            params["entity_type"],
        )

        metrics_df = calculate_comparison_metrics(comparison_df)

        entity_metadata = _get_entity_metadata(params["entity_type"])
        type_summary = aggregate_comparison_by_type(metrics_df, entity_metadata)

        overall_summary = calculate_overall_summary(metrics_df)

        progress_bar.progress(100, text=t(Keys.FC_DONE))

        st.session_state[SESSION_KEY_DATA] = {
            "metrics_df": metrics_df,
            "type_summary": type_summary,
            "overall_summary": overall_summary,
            "comparison_df": comparison_df,
            "stats": stats,
            "forecast_start": str(forecast_start_period),
            "as_of_date": str(comparison_date),
            "generation_date": str(generation_date),
        }
        st.session_state[SESSION_KEY_PARAMS] = params
        st.session_state[SESSION_KEY_INTERNAL_FORECASTS] = internal_forecasts

        st.success(t(Keys.FC_COMPARISON_COMPLETE).format(success=stats['success'], gen_date=generation_date, comp_date=comparison_date))
        if stats["failed"] > 0:
            st.warning(t(Keys.FC_ENTITIES_FAILED).format(count=stats['failed']))

        st.rerun()

    except Exception as e:
        logger.exception("Error generating comparison")
        st.error(t(Keys.FC_ERROR).format(error=str(e)))


def _prepare_entity_list(monthly_agg: pd.DataFrame, params: dict) -> list[dict]:
    entity_type = params["entity_type"]
    filter_type = params["filter_type"]
    filter_params = params["filter_params"]

    id_col = _find_column(monthly_agg, ["entity_id", "sku", "SKU"])
    qty_col = _find_column(monthly_agg, ["total_quantity", "TOTAL_QUANTITY"])

    if id_col is None or qty_col is None:
        return []

    df = monthly_agg.copy()

    if entity_type == "model":
        df["_entity"] = df[id_col].astype(str).str[:5]
    else:
        df["_entity"] = df[id_col].astype(str)
        model_filter = filter_params.get("model_filter", "").strip().upper()
        if model_filter:
            df = df[df["_entity"].str.startswith(model_filter)]

    volume = df.groupby("_entity", observed=True)[qty_col].sum().reset_index()
    volume.columns = ["entity_id", "total_volume"]
    volume = volume.sort_values("total_volume", ascending=False)

    if filter_type == "top_n":
        top_n = filter_params.get("top_n", 50)
        volume = volume.head(top_n)

    entities = []
    for _, row in volume.iterrows():
        entities.append({
            "entity_id": row["entity_id"],
            "entity_type": entity_type,
            "product_type": None,
            "cv": None,
        })

    return entities


def _get_entity_metadata(entity_type: str) -> pd.DataFrame:
    try:
        data_source = get_data_source()
        sku_stats = data_source.get_sku_statistics(entity_type=entity_type)
        return sku_stats
    except (DataLoadError, KeyError, ValueError):
        return pd.DataFrame()


def _display_results() -> None:
    data = st.session_state[SESSION_KEY_DATA]
    metrics_df = data["metrics_df"]
    type_summary = data["type_summary"]
    overall_summary = data["overall_summary"]
    stats = data["stats"]

    if data.get("generation_date"):
        st.info(t(Keys.FC_FORECAST_INFO).format(
            gen_date=data['generation_date'],
            start=data.get('forecast_start', 'N/A'),
            end=data.get('as_of_date', 'N/A')
        ))
    elif data.get("forecast_start") and data.get("as_of_date"):
        st.info(t(Keys.FC_FORECAST_PERIOD).format(start=data['forecast_start'], end=data['as_of_date']))

    st.markdown("---")
    _display_overall_summary(overall_summary, stats)

    st.markdown("---")
    _display_type_breakdown(type_summary)

    st.markdown("---")
    _display_all_forecasts_table(data)

    st.markdown("---")
    _display_detailed_table(metrics_df)

    st.markdown("---")
    _display_entity_chart(data)


def _display_all_forecasts_table(data: dict) -> None:
    st.subheader(t(Keys.FC_ALL_FORECAST_ITEMS))

    comparison_df = data.get("comparison_df")
    if comparison_df is None or comparison_df.empty:
        st.info(t(Keys.FC_NO_FORECAST_DATA))
        return

    with st.expander(t(Keys.FC_VIEW_ALL_ITEMS), expanded=False):
        search = st.text_input(t(Keys.FC_SEARCH_ENTITY), key="fc_all_search")

        df = comparison_df.copy()
        if search:
            df = df[df["entity_id"].str.contains(search.upper())]

        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                t(Keys.SORT_BY),
                options=["entity_id", "year_month", "actual", "internal_forecast", "external_forecast"],
                key="fc_all_sort",
            )
        with col2:
            sort_order = st.selectbox(
                t(Keys.FC_ORDER),
                options=[t(Keys.FC_ASCENDING), t(Keys.FC_DESCENDING)],
                key="fc_all_order",
            )

        df = df.sort_values(sort_by, ascending=(sort_order == t(Keys.FC_ASCENDING)))

        display_df = df[[
            "entity_id", "year_month", "internal_forecast", "external_forecast", "actual", "method"
        ]].copy()

        display_df["internal_forecast"] = display_df["internal_forecast"].apply(lambda x: f"{x:,.0f}")
        display_df["external_forecast"] = display_df["external_forecast"].apply(lambda x: f"{x:,.0f}")
        display_df["actual"] = display_df["actual"].apply(lambda x: f"{x:,.0f}")

        display_df.columns = [t(Keys.FC_COL_ENTITY), t(Keys.FC_COL_PERIOD), t(Keys.FC_COL_INTERNAL_FORECAST), t(Keys.FC_COL_EXTERNAL_FORECAST), t(Keys.FC_COL_ACTUAL_SALES), t(Keys.FC_COL_METHOD)]

        from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
        render_dataframe_with_aggrid(display_df, height=400, pinned_columns=[t(Keys.FC_COL_ENTITY)])

        st.caption(t(Keys.FC_TOTAL_ROWS).format(count=len(df)))

        csv = comparison_df.to_csv(index=False)
        st.download_button(
            t(Keys.FC_DOWNLOAD_ALL_FORECASTS),
            csv,
            "all_forecasts.csv",
            MimeTypes.TEXT_CSV,
            key="fc_download_all",
        )


def _display_overall_summary(summary: dict, stats: dict) -> None:
    st.subheader(t(Keys.FC_OVERALL_SUMMARY))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            t(Keys.FC_INTERNAL_MAPE),
            f"{summary.get('avg_internal_mape', 0):.1f}%",
        )
    with col2:
        st.metric(
            t(Keys.FC_EXTERNAL_MAPE),
            f"{summary.get('avg_external_mape', 0):.1f}%",
        )
    with col3:
        internal_wins = summary.get("internal_wins", 0)
        external_wins = summary.get("external_wins", 0)
        if internal_wins > external_wins:
            winner_text = t(Keys.FC_INTERNAL_WINS).format(count=internal_wins)
        elif external_wins > internal_wins:
            winner_text = t(Keys.FC_EXTERNAL_WINS).format(count=external_wins)
        else:
            winner_text = t(Keys.FC_TIE)
        st.metric(t(Keys.FC_MORE_ACCURATE), winner_text)
    with col4:
        st.metric(
            t(Keys.FC_AVG_IMPROVEMENT),
            f"{summary.get('median_improvement', 0):.1f}%",
        )

    st.caption(t(Keys.FC_METHODS_USED).format(methods=stats.get('methods', {})))


def _display_type_breakdown(type_summary: pd.DataFrame) -> None:
    st.subheader(t(Keys.FC_WINNER_BY_TYPE))

    if type_summary.empty:
        st.info(t(Keys.FC_NO_TYPE_BREAKDOWN))
        return

    display_df = type_summary[[
        "product_type",
        "total_entities",
        "internal_wins",
        "external_wins",
        "ties",
        "internal_win_pct",
        "avg_internal_mape",
        "avg_external_mape",
    ]].copy()

    col_type = t(Keys.FC_COL_TYPE)
    col_total = t(Keys.FC_COL_TOTAL)
    col_int_wins = t(Keys.FC_COL_INTERNAL_WINS)
    col_ext_wins = t(Keys.FC_COL_EXTERNAL_WINS)
    col_ties = t(Keys.FC_COL_TIES)
    col_int_win_pct = t(Keys.FC_COL_INTERNAL_WIN_PCT)
    col_avg_int_mape = t(Keys.FC_COL_AVG_INT_MAPE)
    col_avg_ext_mape = t(Keys.FC_COL_AVG_EXT_MAPE)

    display_df.columns = [col_type, col_total, col_int_wins, col_ext_wins, col_ties, col_int_win_pct, col_avg_int_mape, col_avg_ext_mape]

    display_df[col_int_win_pct] = display_df[col_int_win_pct].apply(lambda x: f"{x:.1f}%")
    display_df[col_avg_int_mape] = display_df[col_avg_int_mape].apply(lambda x: f"{x:.1f}%")
    display_df[col_avg_ext_mape] = display_df[col_avg_ext_mape].apply(lambda x: f"{x:.1f}%")

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
    render_dataframe_with_aggrid(display_df, max_height=300)


def _display_detailed_table(metrics_df: pd.DataFrame) -> None:
    st.subheader(t(Keys.FC_DETAILED_COMPARISON))

    if metrics_df.empty:
        st.info(t(Keys.FC_NO_COMPARISON_DATA))
        return

    search = st.text_input(t(Keys.FC_SEARCH_ENTITY), key="fc_search")

    display_df = metrics_df.copy()
    if search:
        display_df = display_df[display_df["entity_id"].str.contains(search.upper())]

    sort_col = st.selectbox(
        t(Keys.SORT_BY),
        options=["improvement_pct", "internal_mape", "external_mape", "entity_id"],
        format_func=lambda x: {
            "improvement_pct": t(Keys.FC_IMPROVEMENT),
            "internal_mape": t(Keys.FC_INTERNAL_MAPE),
            "external_mape": t(Keys.FC_EXTERNAL_MAPE),
            "entity_id": t(Keys.FC_COL_ENTITY),
        }[x],
        key="fc_sort",
    )

    ascending = sort_col == "entity_id"
    display_df = display_df.sort_values(sort_col, ascending=ascending)

    col_entity = t(Keys.FC_COL_ENTITY)
    col_method = t(Keys.FC_COL_METHOD)
    col_months = t(Keys.FC_COL_MONTHS)
    col_actual_vol = t(Keys.FC_COL_ACTUAL_VOLUME)
    col_int_mape = t(Keys.FC_COL_INT_MAPE)
    col_ext_mape = t(Keys.FC_COL_EXT_MAPE)
    col_winner = t(Keys.FC_COL_WINNER)
    col_improvement = t(Keys.FC_IMPROVEMENT)

    show_df = display_df[[
        "entity_id", "method", "months_compared", "total_actual",
        "internal_mape", "external_mape", "winner", "improvement_pct"
    ]].copy()

    show_df.columns = [col_entity, col_method, col_months, col_actual_vol, col_int_mape, col_ext_mape, col_winner, col_improvement]

    show_df[col_int_mape] = show_df[col_int_mape].apply(lambda x: f"{x:.1f}%")
    show_df[col_ext_mape] = show_df[col_ext_mape].apply(lambda x: f"{x:.1f}%")
    show_df[col_improvement] = show_df[col_improvement].apply(lambda x: f"{x:+.1f}%")
    show_df[col_actual_vol] = show_df[col_actual_vol].apply(lambda x: f"{x:,.0f}")

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
    render_dataframe_with_aggrid(show_df, height=400, pinned_columns=[col_entity])

    csv = metrics_df.to_csv(index=False)
    st.download_button(
        t(Keys.FC_DOWNLOAD_FULL_REPORT),
        csv,
        "forecast_comparison_report.csv",
        MimeTypes.TEXT_CSV,
        key="fc_download",
    )


def _display_entity_chart(data: dict) -> None:
    with st.expander(t(Keys.FC_ENTITY_DETAIL_CHART), expanded=False):
        comparison_df = data["comparison_df"]

        if comparison_df.empty:
            st.info(t(Keys.FC_NO_DATA_FOR_CHART))
            return

        entities = sorted(comparison_df["entity_id"].unique())
        selected = st.selectbox(
            t(Keys.FC_SELECT_ENTITY),
            options=entities,
            key="fc_chart_entity",
        )

        if selected:
            entity_data = comparison_df[comparison_df["entity_id"] == selected].sort_values("year_month")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=entity_data["year_month"],
                y=entity_data["actual"],
                mode=LINES_MARKERS,
                name=t(Keys.FC_CHART_ACTUAL),
                line={"color": "green", "width": 2},
            ))

            fig.add_trace(go.Scatter(
                x=entity_data["year_month"],
                y=entity_data["internal_forecast"],
                mode=LINES_MARKERS,
                name=t(Keys.FC_CHART_INTERNAL),
                line={"color": "blue", "width": 2, "dash": "dash"},
            ))

            fig.add_trace(go.Scatter(
                x=entity_data["year_month"],
                y=entity_data["external_forecast"],
                mode=LINES_MARKERS,
                name=t(Keys.FC_CHART_EXTERNAL),
                line={"color": "orange", "width": 2, "dash": "dot"},
            ))

            fig.update_layout(
                title=t(Keys.FC_CHART_TITLE).format(entity=selected),
                xaxis_title=t(Keys.FC_CHART_MONTH),
                yaxis_title=t(Keys.QUANTITY),
                hovermode="x unified",
                height=400,
            )

            st.plotly_chart(fig, width='stretch')


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _render_save_section() -> None:
    st.markdown("---")
    st.subheader(t(Keys.FC_SAVE_FORECAST))

    if SESSION_KEY_INTERNAL_FORECASTS not in st.session_state:
        st.info(t(Keys.FC_NO_FORECAST_TO_SAVE))
        return

    notes = st.text_input(
        t(Keys.FC_NOTES_OPTIONAL),
        placeholder=t(Keys.FC_NOTES_PLACEHOLDER),
        key="fc_save_notes",
    )

    if st.button(t(Keys.FC_SAVE_TO_HISTORY), key="fc_save_btn"):
        try:
            forecasts_df = st.session_state[SESSION_KEY_INTERNAL_FORECASTS]
            params = st.session_state.get(SESSION_KEY_PARAMS, {})
            data = st.session_state.get(SESSION_KEY_DATA, {})
            stats = data.get("stats", {})

            repo = create_internal_forecast_repository()
            batch_id = repo.save_forecast_batch(
                forecasts_df=forecasts_df,
                entity_type=params.get("entity_type", "model"),
                horizon_months=params.get("horizon", 2),
                stats=stats,
                parameters=params,
                notes=notes or None,
            )

            st.success(f"{Icons.SUCCESS} {t(Keys.FC_FORECAST_SAVED).format(batch_id=batch_id[:8])}")
        except Exception as e:
            logger.exception("Error saving forecast")
            st.error(f"{Icons.ERROR} {t(Keys.FC_ERROR_SAVING).format(error=e)}")


def _format_batch_label(batch: dict) -> str:
    generated = batch.get("generated_at", "")
    if isinstance(generated, str) and "T" in generated:
        generated = generated.split("T")[0] + " " + generated.split("T")[1][:8]
    entity_type = batch.get("entity_type", "?")
    success = batch.get("success_count", 0)
    label = f"{generated} | {entity_type} | {success} entities"
    if batch.get("notes"):
        label += f" | {batch['notes'][:30]}"
    return label


def _build_batch_options(batches: list[dict]) -> dict[str, str]:
    return {_format_batch_label(batch): batch["batch_id"] for batch in batches}


def _get_forecast_date_range(batch: dict) -> tuple[str, str]:
    generated = batch.get("generated_at", "")
    horizon = batch.get("horizon_months", 2)

    if isinstance(generated, str):
        try:
            gen_date = pd.to_datetime(generated.split("T")[0])
        except (ValueError, IndexError):
            gen_date = pd.Timestamp.now()
    else:
        gen_date = pd.Timestamp.now()

    start_period = gen_date.to_period("M")
    end_period = start_period + horizon - 1

    return str(start_period), str(end_period)


def _handle_batch_actions(batch_id: str, batch: dict, repo) -> None:
    st.markdown(f"#### {t(Keys.FC_ANALYSIS_SETTINGS)}")

    forecast_start, forecast_end = _get_forecast_date_range(batch)
    st.caption(t(Keys.FC_FORECAST_COVERS).format(start=forecast_start, end=forecast_end))

    col_date, col_info = st.columns([2, 3])
    with col_date:
        as_of_date = st.date_input(
            t(Keys.FC_ANALYZE_AS_OF),
            value=pd.Timestamp.now().date(),
            help=t(Keys.FC_ANALYZE_AS_OF_HELP),
            key="fc_as_of_date",
        )
    with col_info:
        st.info(t(Keys.FC_SET_AS_OF_INFO))

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(t(Keys.FC_LOAD_COMPARE), key="fc_load_historical", type="primary"):
            _load_historical_forecast(batch_id, batch, as_of_date)
    with col2:
        if st.button(t(Keys.FC_DELETE), key="fc_delete_historical"):
            if repo.delete_forecast_batch(batch_id):
                st.success(t(Keys.FC_FORECAST_DELETED))
                st.rerun()
            else:
                st.error(t(Keys.FC_DELETE_FAILED))


@st.fragment
def _render_historical_tab() -> None:
    st.subheader(t(Keys.FC_HISTORICAL_INTERNAL))

    repo = create_internal_forecast_repository()
    batches = repo.get_forecast_batches(limit=20)

    if not batches:
        st.info(t(Keys.FC_NO_HISTORICAL))
        return

    batch_options = _build_batch_options(batches)

    selected_label = st.selectbox(
        t(Keys.FC_SELECT_HISTORICAL),
        options=list(batch_options.keys()),
        key="fc_history_select",
    )

    if not selected_label:
        return

    batch_id = batch_options[selected_label]
    selected_batch = next((b for b in batches if b["batch_id"] == batch_id), None)

    if not selected_batch:
        return

    _display_batch_details(selected_batch)
    _handle_batch_actions(batch_id, selected_batch, repo)


def _display_batch_details(batch: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(t(Keys.FC_ENTITY_TYPE), batch.get("entity_type", "?"))
    with col2:
        st.metric(t(Keys.FC_HORIZON).format(months=batch.get('horizon_months', '?')), "")
    with col3:
        st.metric(t(Keys.FC_SUCCESS), batch.get("success_count", 0))
    with col4:
        st.metric(t(Keys.FC_FAILED), batch.get("failed_count", 0))

    methods = batch.get("methods_used", {})
    if methods:
        st.caption(t(Keys.FC_METHODS).format(methods=methods))

    if batch.get("notes"):
        st.caption(t(Keys.FC_NOTES).format(notes=batch['notes']))


def _load_sales_for_period(start_period: str, end_date) -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        sales_df = data_source.load_sales_data()

        if sales_df is None or sales_df.empty:
            return None

        date_col = _find_column(sales_df, ["data", "sale_date", "date"])
        if date_col is None:
            return sales_df

        df = sales_df.copy()
        df[date_col] = pd.to_datetime(df[date_col])

        start_date = pd.Period(start_period).start_time
        end_dt = pd.to_datetime(end_date)

        filtered = df[(df[date_col] >= start_date) & (df[date_col] <= end_dt)]
        return filtered

    except Exception as e:
        logger.warning("Error loading sales for period: %s", e)
        return None


def _load_historical_forecast(batch_id: str, batch: dict, as_of_date) -> None:
    repo = create_internal_forecast_repository()
    forecasts_df = repo.get_forecast_batch(batch_id)

    if forecasts_df is None or forecasts_df.empty:
        st.error(t(Keys.FC_FAILED_LOAD))
        return

    # noinspection PyTypeChecker
    with st.spinner(t(Keys.FC_LOADING_DATA)):
        external_forecast = _load_external_forecast_cached()

        forecast_start, _ = _get_forecast_date_range(batch)
        sales_df = _load_sales_for_period(forecast_start, as_of_date)

        if sales_df is None or sales_df.empty:
            st.warning(t(Keys.FC_NO_SALES_FOR_PERIOD))
            sales_df = pd.DataFrame()

        entity_type = forecasts_df["entity_type"].iloc[0] if "entity_type" in forecasts_df.columns else "model"

        comparison_df = align_forecasts(
            forecasts_df,
            external_forecast,
            sales_df,
            entity_type,
        )

        metrics_df = calculate_comparison_metrics(comparison_df)

        entity_metadata = _get_entity_metadata(entity_type)
        type_summary = aggregate_comparison_by_type(metrics_df, entity_metadata)

        overall_summary = calculate_overall_summary(metrics_df)

        methods = forecasts_df["method"].value_counts().to_dict() if "method" in forecasts_df.columns else {}
        stats = {
            "total": len(forecasts_df["entity_id"].unique()) if "entity_id" in forecasts_df.columns else 0,
            "success": len(forecasts_df["entity_id"].unique()) if "entity_id" in forecasts_df.columns else 0,
            "failed": 0,
            "methods": methods,
        }

        st.session_state[SESSION_KEY_DATA] = {
            "metrics_df": metrics_df,
            "type_summary": type_summary,
            "overall_summary": overall_summary,
            "comparison_df": comparison_df,
            "stats": stats,
            "forecast_start": forecast_start,
            "as_of_date": str(as_of_date),
        }
        st.session_state[SESSION_KEY_PARAMS] = {
            "entity_type": entity_type,
            "horizon": batch.get("horizon_months", 2),
        }
        st.session_state[SESSION_KEY_INTERNAL_FORECASTS] = forecasts_df

        st.success(t(Keys.FC_HISTORICAL_LOADED).format(start=forecast_start, end=as_of_date))
        st.rerun()
