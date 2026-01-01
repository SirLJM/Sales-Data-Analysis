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
from sales_data.analysis.internal_forecast import batch_generate_forecasts
from ui.constants import Icons, MimeTypes
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
        st.error(f"{Icons.ERROR} Error in Forecast Comparison: {str(e)}")


def _render_content() -> None:
    st.title("Forecast Comparison")
    st.write("Compare internal forecasts (generated using statsmodels) vs external forecasts")

    tab_new, tab_history = st.tabs(["Generate New", "Historical Forecasts"])

    with tab_new:
        _render_new_forecast_tab()

    with tab_history:
        _render_historical_tab()


def _render_new_forecast_tab() -> None:
    params = _render_parameters()

    col_gen, col_clear = st.columns([1, 1])
    with col_gen:
        if st.button("Generate Comparison", type="primary", key="gen_comparison"):
            _generate_comparison(params)
    with col_clear:
        if st.button("Clear Results", key="clear_comparison"):
            st.session_state.pop(SESSION_KEY_DATA, None)
            st.session_state.pop(SESSION_KEY_PARAMS, None)
            st.session_state.pop(SESSION_KEY_INTERNAL_FORECASTS, None)
            st.rerun()

    if SESSION_KEY_DATA in st.session_state:
        _display_results()
        _render_save_section()


def _render_parameters() -> dict:
    with st.expander("Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            settings = get_settings()
            horizon = st.number_input(
                "Forecast Horizon (months)",
                min_value=1,
                max_value=12,
                value=int(settings.get("lead_time", 2)),
                key="fc_horizon",
            )

        with col2:
            entity_type = st.selectbox(
                "Analysis Level",
                options=["model", "sku"],
                format_func=lambda x: "Model (faster)" if x == "model" else "SKU (slower)",
                key="fc_entity_type",
            )

        with col3:
            filter_type = st.selectbox(
                "Entity Filter",
                options=["all", "top_n", "by_type"],
                format_func=lambda x: {
                    "all": "All entities",
                    "top_n": "Top N by volume",
                    "by_type": "By product type",
                }[x],
                key="fc_filter_type",
            )

        filter_params = {}
        if filter_type == "top_n":
            filter_params["top_n"] = st.slider(
                "Number of top entities",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                key="fc_top_n",
            )
        elif filter_type == "by_type":
            filter_params["product_types"] = st.multiselect(
                "Product Types",
                options=["basic", "regular", "seasonal", "new"],
                default=["basic", "regular", "seasonal"],
                key="fc_product_types",
            )

        if entity_type == "sku":
            filter_params["model_filter"] = st.text_input(
                "Filter by Model (optional)",
                placeholder="e.g., CH031",
                key="fc_model_filter",
            )

    return {
        "horizon": horizon,
        "entity_type": entity_type,
        "filter_type": filter_type,
        "filter_params": filter_params,
    }


def _generate_comparison(params: dict) -> None:
    progress_bar = st.progress(0, text="Loading data...")

    try:
        monthly_agg = _load_monthly_aggregations_cached()
        if monthly_agg is None or monthly_agg.empty:
            st.error("No monthly aggregation data available")
            return

        progress_bar.progress(10, text="Loading forecasts...")

        external_forecast = _load_external_forecast_cached()
        if external_forecast is None or external_forecast.empty:
            st.warning("No external forecast data available. Will only generate internal forecasts.")

        progress_bar.progress(20, text="Loading sales data...")

        sales_df = _load_sales_data_cached()

        progress_bar.progress(30, text="Preparing entities...")

        entities = _prepare_entity_list(monthly_agg, params)

        if not entities:
            st.warning("No entities found matching the filter criteria")
            return

        st.info(f"Processing {len(entities)} entities...")

        def progress_callback(current, total, entity_id):
            pct = 30 + int((current / total) * 60)
            progress_bar.progress(pct, text=f"Forecasting {current}/{total}: {entity_id}")

        progress_bar.progress(35, text="Generating internal forecasts...")

        internal_forecasts, stats = batch_generate_forecasts(
            monthly_agg,
            entities,
            params["horizon"],
            progress_callback,
        )

        progress_bar.progress(90, text="Calculating comparison metrics...")

        if internal_forecasts.empty:
            st.error("Failed to generate any internal forecasts")
            return

        comparison_df = align_forecasts(
            internal_forecasts,
            external_forecast,
            sales_df,
            params["entity_type"],
        )

        metrics_df = calculate_comparison_metrics(comparison_df)

        entity_metadata = _get_entity_metadata(params["entity_type"])
        type_summary = aggregate_comparison_by_type(metrics_df, entity_metadata)

        overall_summary = calculate_overall_summary(metrics_df)

        progress_bar.progress(100, text="Done!")

        st.session_state[SESSION_KEY_DATA] = {
            "metrics_df": metrics_df,
            "type_summary": type_summary,
            "overall_summary": overall_summary,
            "comparison_df": comparison_df,
            "stats": stats,
        }
        st.session_state[SESSION_KEY_PARAMS] = params
        st.session_state[SESSION_KEY_INTERNAL_FORECASTS] = internal_forecasts

        st.success(f"Comparison complete! Processed {stats['success']} entities successfully.")
        if stats["failed"] > 0:
            st.warning(f"{stats['failed']} entities failed to forecast")

        st.rerun()

    except Exception as e:
        logger.exception("Error generating comparison")
        st.error(f"Error: {str(e)}")


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

    volume = df.groupby("_entity")[qty_col].sum().reset_index()
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

    st.markdown("---")
    _display_overall_summary(overall_summary, stats)

    st.markdown("---")
    _display_type_breakdown(type_summary)

    st.markdown("---")
    _display_detailed_table(metrics_df)

    st.markdown("---")
    _display_entity_chart(data)


def _display_overall_summary(summary: dict, stats: dict) -> None:
    st.subheader("Overall Comparison Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Internal MAPE",
            f"{summary.get('avg_internal_mape', 0):.1f}%",
        )
    with col2:
        st.metric(
            "External MAPE",
            f"{summary.get('avg_external_mape', 0):.1f}%",
        )
    with col3:
        internal_wins = summary.get("internal_wins", 0)
        external_wins = summary.get("external_wins", 0)
        if internal_wins > external_wins:
            winner_text = f"Internal ({internal_wins})"
        elif external_wins > internal_wins:
            winner_text = f"External ({external_wins})"
        else:
            winner_text = "Tie"
        st.metric("More Accurate", winner_text)
    with col4:
        st.metric(
            "Avg Improvement",
            f"{summary.get('median_improvement', 0):.1f}%",
        )

    st.caption(f"Methods used: {stats.get('methods', {})}")


def _display_type_breakdown(type_summary: pd.DataFrame) -> None:
    st.subheader("Winner Breakdown by Product Type")

    if type_summary.empty:
        st.info("No type breakdown available")
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

    display_df.columns = MAPE_AVG_EXT_MAPE_

    display_df[INTERNAL_WIN_PERCENTILE] = display_df[INTERNAL_WIN_PERCENTILE].apply(lambda x: f"{x:.1f}%")
    display_df[AVG_INT_MAPE] = display_df[AVG_INT_MAPE].apply(lambda x: f"{x:.1f}%")
    display_df[AVG_EXT_MAPE] = display_df[AVG_EXT_MAPE].apply(lambda x: f"{x:.1f}%")

    st.dataframe(display_df, hide_index=True)


def _display_detailed_table(metrics_df: pd.DataFrame) -> None:
    st.subheader("Detailed Comparison")

    if metrics_df.empty:
        st.info("No comparison data available")
        return

    search = st.text_input("Search by Entity ID", key="fc_search")

    display_df = metrics_df.copy()
    if search:
        display_df = display_df[display_df["entity_id"].str.contains(search.upper())]

    sort_col = st.selectbox(
        "Sort by",
        options=["improvement_pct", "internal_mape", "external_mape", "entity_id"],
        format_func=lambda x: {
            "improvement_pct": "Improvement %",
            "internal_mape": "Internal MAPE",
            "external_mape": "External MAPE",
            "entity_id": "Entity ID",
        }[x],
        key="fc_sort",
    )

    ascending = sort_col == "entity_id"
    display_df = display_df.sort_values(sort_col, ascending=ascending)

    show_df = display_df[[
        "entity_id", "method", "months_compared", "total_actual",
        "internal_mape", "external_mape", "winner", "improvement_pct"
    ]].copy()

    show_df.columns = [
        "Entity", "Method", "Months", ACTUAL_VOLUME,
        INT_MAPE, EXT_MAPE, "Winner", "Improvement"
    ]

    show_df[INT_MAPE] = show_df[INT_MAPE].apply(lambda x: f"{x:.1f}%")
    show_df[EXT_MAPE] = show_df[EXT_MAPE].apply(lambda x: f"{x:.1f}%")
    show_df["Improvement"] = show_df["Improvement"].apply(lambda x: f"{x:+.1f}%")
    show_df[ACTUAL_VOLUME] = show_df[ACTUAL_VOLUME].apply(lambda x: f"{x:,.0f}")

    st.dataframe(show_df, hide_index=True, height=400)

    csv = metrics_df.to_csv(index=False)
    st.download_button(
        "Download Full Report (CSV)",
        csv,
        "forecast_comparison_report.csv",
        MimeTypes.TEXT_CSV,
        key="fc_download",
    )


def _display_entity_chart(data: dict) -> None:
    with st.expander("Entity Detail Chart", expanded=False):
        comparison_df = data["comparison_df"]

        if comparison_df.empty:
            st.info("No comparison data available for charting")
            return

        entities = sorted(comparison_df["entity_id"].unique())
        selected = st.selectbox(
            "Select Entity",
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
                name="Actual",
                line={"color": "green", "width": 2},
            ))

            fig.add_trace(go.Scatter(
                x=entity_data["year_month"],
                y=entity_data["internal_forecast"],
                mode=LINES_MARKERS,
                name="Internal Forecast",
                line={"color": "blue", "width": 2, "dash": "dash"},
            ))

            fig.add_trace(go.Scatter(
                x=entity_data["year_month"],
                y=entity_data["external_forecast"],
                mode=LINES_MARKERS,
                name="External Forecast",
                line={"color": "orange", "width": 2, "dash": "dot"},
            ))

            fig.update_layout(
                title=f"Forecast Comparison: {selected}",
                xaxis_title="Month",
                yaxis_title="Quantity",
                hovermode="x unified",
                height=400,
            )

            st.plotly_chart(fig, use_container_width=True)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _render_save_section() -> None:
    st.markdown("---")
    st.subheader("Save Forecast")

    if SESSION_KEY_INTERNAL_FORECASTS not in st.session_state:
        st.info("No forecast data to save")
        return

    notes = st.text_input(
        "Notes (optional)",
        placeholder="e.g., Monthly comparison run",
        key="fc_save_notes",
    )

    if st.button("Save Forecast to History", key="fc_save_btn"):
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

            st.success(f"{Icons.SUCCESS} Forecast saved! Batch ID: {batch_id[:8]}...")
        except Exception as e:
            logger.exception("Error saving forecast")
            st.error(f"{Icons.ERROR} Error saving forecast: {e}")


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


def _handle_batch_actions(batch_id: str, repo) -> None:
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Load and Compare", key="fc_load_historical"):
            _load_historical_forecast(batch_id)
    with col2:
        if st.button("Delete", key="fc_delete_historical"):
            if repo.delete_forecast_batch(batch_id):
                st.success("Forecast deleted")
                st.rerun()
            else:
                st.error("Failed to delete forecast")


def _render_historical_tab() -> None:
    st.subheader("Historical Internal Forecasts")

    repo = create_internal_forecast_repository()
    batches = repo.get_forecast_batches(limit=20)

    if not batches:
        st.info("No historical forecasts found. Generate and save a forecast first.")
        return

    batch_options = _build_batch_options(batches)

    selected_label = st.selectbox(
        "Select Historical Forecast",
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
    _handle_batch_actions(batch_id, repo)


def _display_batch_details(batch: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Entity Type", batch.get("entity_type", "?"))
    with col2:
        st.metric("Horizon", f"{batch.get('horizon_months', '?')} months")
    with col3:
        st.metric("Success", batch.get("success_count", 0))
    with col4:
        st.metric("Failed", batch.get("failed_count", 0))

    methods = batch.get("methods_used", {})
    if methods:
        st.caption(f"Methods: {methods}")

    if batch.get("notes"):
        st.caption(f"Notes: {batch['notes']}")


def _load_historical_forecast(batch_id: str) -> None:
    repo = create_internal_forecast_repository()
    forecasts_df = repo.get_forecast_batch(batch_id)

    if forecasts_df is None or forecasts_df.empty:
        st.error("Failed to load forecast data")
        return

    # noinspection PyTypeChecker
    with st.spinner("Loading data and calculating metrics..."):
        external_forecast = _load_external_forecast_cached()
        sales_df = _load_sales_data_cached()

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
        }
        st.session_state[SESSION_KEY_INTERNAL_FORECASTS] = forecasts_df

        st.success("Historical forecast loaded!")
        st.rerun()
