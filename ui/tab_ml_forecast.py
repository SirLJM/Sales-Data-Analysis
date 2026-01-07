from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from exceptions import DataLoadError
from sales_data.analysis.ml_forecast import (
    batch_train_and_forecast,
    generate_ml_forecast,
)
from sales_data.analysis.ml_model_selection import get_available_ml_models
from ui.constants import Config, Icons, MimeTypes, SessionKeys
from ui.shared.session_manager import get_data_source, get_settings
from utils.logging_config import get_logger
from utils.ml_model_repository import create_ml_model_repository

logger = get_logger("tab_ml_forecast")


@st.cache_data(ttl=Config.CACHE_TTL)
def _load_monthly_aggregations_cached() -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        return data_source.get_monthly_aggregations()
    except (DataLoadError, KeyError, ValueError):
        return None


@st.cache_data(ttl=Config.CACHE_TTL)
def _load_sku_statistics_cached(entity_type: str) -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        return data_source.get_sku_statistics(entity_type=entity_type)
    except (DataLoadError, KeyError, ValueError):
        return None


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in ML Forecast")
        st.error(f"{Icons.ERROR} Error in ML Forecast: {str(e)}")


def _render_content() -> None:
    st.title("ML Forecast")
    st.write("Train ML models with automatic selection per entity")

    tab_train, tab_generate, tab_manage = st.tabs([
        "Train Models",
        "Generate Forecasts",
        "Manage Models"
    ])

    with tab_train:
        _render_train_tab()

    with tab_generate:
        _render_generate_tab()

    with tab_manage:
        _render_manage_tab()


def _render_train_tab() -> None:
    params = _render_training_parameters()

    col_train, col_clear = st.columns([1, 1])
    with col_train:
        if st.button("Train Models", type="primary", key="ml_train_btn"):
            _run_training(params)
    with col_clear:
        if st.button("Clear Results", key="ml_clear_btn"):
            _clear_session_data()
            st.rerun()

    if SessionKeys.ML_TRAINING_STATS in st.session_state:
        _display_training_results()


def _render_training_parameters() -> dict:
    with st.expander("Training Parameters", expanded=True):
        entity_type, top_n = _render_entity_settings()
        horizon, cv_metric = _render_forecast_settings()

        st.markdown("---")
        selected_ml, include_statistical = _render_model_selection()

        st.markdown("---")
        cv_splits, cv_test_size = _render_cv_settings()

    return {
        "entity_type": entity_type,
        "top_n": top_n,
        "horizon": horizon,
        "cv_metric": cv_metric,
        "models_to_evaluate": selected_ml if selected_ml else None,
        "include_statistical": include_statistical,
        "cv_splits": cv_splits,
        "cv_test_size": cv_test_size,
    }


def _render_entity_settings() -> tuple[str, int]:
    col1, _ = st.columns(2)

    with col1:
        entity_type = st.selectbox(
            "Entity Level",
            options=["model", "sku"],
            format_func=lambda x: "Model (faster)" if x == "model" else "SKU (detailed)",
            key="ml_entity_type",
        )

        top_n = st.slider(
            "Top N entities by volume",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            key="ml_top_n",
        )

    return entity_type, top_n


def _render_forecast_settings() -> tuple[int, str]:
    _, col2 = st.columns(2)

    with col2:
        settings = get_settings()
        horizon = st.number_input(
            "Forecast Horizon (months)",
            min_value=1,
            max_value=12,
            value=int(settings.get("forecast_time", 3)),
            key="ml_horizon",
        )

        cv_metric = st.selectbox(
            "CV Metric",
            options=["mape", "mae", "rmse"],
            format_func=lambda x: {"mape": "MAPE (%)", "mae": "MAE", "rmse": "RMSE"}[x],
            key="ml_cv_metric",
        )

    return horizon, cv_metric


def _render_model_selection() -> tuple[list[str], bool]:
    st.markdown("**Models to Evaluate**")

    available_models = get_available_ml_models()
    col_ml, col_stat = st.columns(2)

    with col_ml:
        st.caption("ML Models")
        selected_ml = [
            model_key
            for model_key, config in available_models.items()
            if st.checkbox(config.name, value=True, key=f"ml_model_{model_key}")
        ]

    with col_stat:
        st.caption("Statistical Models")
        include_statistical = st.checkbox(
            "Include Statistical (Holt-Winters, SARIMA)",
            value=True,
            key="ml_include_stat",
        )

    return selected_ml, include_statistical


def _render_cv_settings() -> tuple[int, int]:
    col_cv1, col_cv2 = st.columns(2)

    with col_cv1:
        cv_splits = st.number_input(
            "CV Splits",
            min_value=2,
            max_value=5,
            value=3,
            key="ml_cv_splits",
        )

    with col_cv2:
        cv_test_size = st.number_input(
            "CV Test Size (months)",
            min_value=1,
            max_value=6,
            value=3,
            key="ml_cv_test_size",
        )

    return cv_splits, cv_test_size


def _run_training(params: dict) -> None:
    progress_bar = st.progress(0, text="Loading data...")

    try:
        monthly_agg, sku_stats, entities = _load_training_data(progress_bar, params)
        if entities is None:
            return

        st.info(f"Training models for {len(entities)} entities...")

        forecasts_df, stats, trained_models = _execute_training(
            progress_bar, monthly_agg, entities, sku_stats, params
        )

        saved_count = _save_trained_models(progress_bar, trained_models, params)

        _store_training_results(forecasts_df, stats, trained_models, params, saved_count)

    except Exception as e:
        logger.exception("Error during training")
        st.error(f"{Icons.ERROR} Training error: {str(e)}")


def _load_training_data(
        progress_bar, params: dict
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, list[dict] | None]:
    progress_bar.progress(5, text="Loading monthly aggregations...")

    monthly_agg = _load_monthly_aggregations_cached()
    if monthly_agg is None or monthly_agg.empty:
        st.error("No monthly aggregation data available")
        return None, None, None

    progress_bar.progress(15, text="Loading SKU statistics...")
    sku_stats = _load_sku_statistics_cached(params["entity_type"])

    progress_bar.progress(20, text="Preparing entities...")
    entities = _prepare_entity_list(monthly_agg, params)

    if not entities:
        st.warning("No entities found matching the criteria")
        return None, None, None

    return monthly_agg, sku_stats, entities


def _execute_training(
        progress_bar, monthly_agg: pd.DataFrame, entities: list[dict], sku_stats, params: dict
) -> tuple:
    def progress_callback(current, total, entity_id):
        pct = 20 + int((current / total) * 70)
        progress_bar.progress(pct, text=f"Training {current}/{total}: {entity_id}")

    progress_bar.progress(25, text="Training models...")

    return batch_train_and_forecast(
        monthly_agg=monthly_agg,
        entities=entities,
        horizon_months=params["horizon"],
        models_to_evaluate=params["models_to_evaluate"],
        include_statistical=params["include_statistical"],
        cv_splits=params["cv_splits"],
        cv_test_size=params["cv_test_size"],
        cv_metric=params["cv_metric"],
        sku_stats=sku_stats,
        progress_callback=progress_callback,
    )


def _save_trained_models(progress_bar, trained_models: dict, params: dict) -> int:
    progress_bar.progress(95, text="Saving models...")

    repo = create_ml_model_repository()
    saved_count = 0

    for entity_id, model_info in trained_models.items():
        try:
            repo.save_model(
                entity_id=entity_id,
                entity_type=params["entity_type"],
                trained_model_info=model_info,
                cv_metric=params["cv_metric"],
            )
            saved_count += 1
        except Exception as e:
            logger.warning("Failed to save model for %s: %s", entity_id, e)

    return saved_count


def _store_training_results(
        forecasts_df, stats: dict, trained_models: dict, params: dict, saved_count: int
) -> None:
    st.session_state[SessionKeys.ML_FORECAST_DATA] = forecasts_df
    st.session_state[SessionKeys.ML_TRAINED_MODELS] = trained_models
    st.session_state[SessionKeys.ML_TRAINING_STATS] = stats
    st.session_state[SessionKeys.ML_FORECAST_PARAMS] = params

    st.success(f"{Icons.SUCCESS} Training complete! {stats['success']} models trained, {saved_count} saved.")

    if stats["failed"] > 0:
        st.warning(f"{stats['failed']} entities failed")

    st.rerun()


def _prepare_entity_list(monthly_agg: pd.DataFrame, params: dict) -> list[dict]:
    entity_type = params["entity_type"]
    top_n = params["top_n"]

    id_col = _find_column(monthly_agg, ["entity_id", "sku", "SKU"])
    qty_col = _find_column(monthly_agg, ["total_quantity", "TOTAL_QUANTITY"])

    if id_col is None or qty_col is None:
        return []

    df = monthly_agg.copy()

    if entity_type == "model":
        df["_entity"] = df[id_col].astype(str).str[:5]
    else:
        df["_entity"] = df[id_col].astype(str)

    volume = df.groupby("_entity", observed=True)[qty_col].sum().reset_index()
    volume.columns = ["entity_id", "total_volume"]
    volume = volume.sort_values("total_volume", ascending=False).head(top_n)

    return [
        {"entity_id": row["entity_id"], "entity_type": entity_type}
        for _, row in volume.iterrows()
    ]


def _display_training_results() -> None:
    stats = st.session_state[SessionKeys.ML_TRAINING_STATS]
    forecasts_df = st.session_state.get(SessionKeys.ML_FORECAST_DATA)

    st.markdown("---")
    st.subheader("Training Results")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Entities", stats["total"])
    with col2:
        st.metric("Success", stats["success"])
    with col3:
        st.metric("Failed", stats["failed"])
    with col4:
        avg_score = stats.get("avg_cv_score", 0)
        st.metric("Avg CV Score", f"{avg_score:.1f}%")

    if stats.get("model_distribution"):
        st.markdown("#### Model Distribution")
        dist_df = pd.DataFrame([
            {"Model": k, "Count": v}
            for k, v in stats["model_distribution"].items()
        ])

        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            fig = px.pie(
                dist_df,
                values="Count",
                names="Model",
                title="Best Model Selection",
            )
            st.plotly_chart(fig, width='stretch')
        with col_table:
            st.dataframe(dist_df, width='stretch', hide_index=True)

    if forecasts_df is not None and not forecasts_df.empty:
        st.markdown("#### Forecast Preview")
        _display_forecast_table(forecasts_df)


def _display_forecast_table(forecasts_df: pd.DataFrame) -> None:
    entities = forecasts_df["entity_id"].unique()

    summary = []
    for entity in entities:
        entity_data = forecasts_df[forecasts_df["entity_id"] == entity]
        summary.append({
            "Entity": entity,
            "Model": entity_data["model_type"].iloc[0] if "model_type" in entity_data.columns else "N/A",
            "CV Score": f"{entity_data['cv_score'].iloc[0]:.1f}%" if "cv_score" in entity_data.columns and pd.notna(
                entity_data["cv_score"].iloc[0]) else "N/A",
            "Total Forecast": f"{entity_data['forecast'].sum():,.0f}",
        })

    summary_df = pd.DataFrame(summary)

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
    render_dataframe_with_aggrid(summary_df, height=300, pinned_columns=["Entity"])

    csv = forecasts_df.to_csv(index=False)
    st.download_button(
        "Download Forecasts (CSV)",
        csv,
        "ml_forecasts.csv",
        MimeTypes.TEXT_CSV,
        key="ml_download_forecasts",
    )


def _render_generate_tab() -> None:
    st.subheader("Generate Forecasts from Saved Models")

    repo = create_ml_model_repository()
    model_count = repo.get_model_count()

    if model_count == 0:
        st.info("No trained models found. Train models first in the 'Train Models' tab.")
        return

    st.write(f"**{model_count}** trained models available")

    col1, col2 = st.columns(2)
    with col1:
        settings = get_settings()
        horizon = st.number_input(
            "Forecast Horizon (months)",
            min_value=1,
            max_value=12,
            value=int(settings.get("forecast_time", 3)),
            key="ml_gen_horizon",
        )
    with col2:
        entity_filter = st.text_input(
            "Entity Filter (optional)",
            placeholder="e.g., CH031",
            key="ml_gen_filter",
        )

    if st.button("Generate Forecasts", type="primary", key="ml_gen_btn"):
        _generate_forecasts_from_models(horizon, entity_filter)

    if "ml_generated_forecasts" in st.session_state:
        st.markdown("---")
        forecasts_df = st.session_state["ml_generated_forecasts"]
        st.subheader("Generated Forecasts")
        _display_forecast_table(forecasts_df)

        st.markdown("---")
        _render_entity_detail_chart(forecasts_df)


def _generate_forecasts_from_models(horizon: int, entity_filter: str) -> None:
    repo = create_ml_model_repository()
    models = repo.list_models(limit=500)

    if entity_filter:
        entity_filter = entity_filter.upper()
        models = [m for m in models if entity_filter in m["entity_id"]]

    if not models:
        st.warning("No models found matching the filter")
        return

    monthly_agg = _load_monthly_aggregations_cached()
    if monthly_agg is None:
        st.error("Could not load monthly aggregations")
        return

    progress_bar = st.progress(0, text="Generating forecasts...")
    all_forecasts = []

    for i, model_meta in enumerate(models):
        entity_id = model_meta["entity_id"]
        entity_type = model_meta["entity_type"]

        progress_bar.progress(
            int((i + 1) / len(models) * 100),
            text=f"Generating {i + 1}/{len(models)}: {entity_id}"
        )

        model_info = repo.get_model(entity_id, entity_type)
        if model_info is None:
            continue

        result = generate_ml_forecast(monthly_agg, entity_id, model_info, horizon)

        if result["success"] and result["forecast_df"] is not None:
            forecast_df = result["forecast_df"].copy()
            forecast_df["entity_id"] = entity_id
            forecast_df["entity_type"] = entity_type
            forecast_df["model_type"] = model_info.get("model_type", "unknown")
            forecast_df["cv_score"] = model_info.get("cv_score")
            all_forecasts.append(forecast_df)

    if all_forecasts:
        combined_df = pd.concat(all_forecasts, ignore_index=True)
        st.session_state["ml_generated_forecasts"] = combined_df
        st.success(f"{Icons.SUCCESS} Generated forecasts for {len(all_forecasts)} entities")
        st.rerun()
    else:
        st.warning("No forecasts generated")


def _render_entity_detail_chart(forecasts_df: pd.DataFrame) -> None:
    with st.expander("Entity Detail Chart", expanded=False):
        entities = sorted(forecasts_df["entity_id"].unique())

        selected = st.selectbox(
            "Select Entity",
            options=entities,
            key="ml_chart_entity",
        )

        if selected:
            entity_data = forecasts_df.loc[forecasts_df["entity_id"] == selected].copy()  # type: ignore[assignment]

            if "period" in entity_data.columns:  # type: ignore[union-attr]
                entity_data = entity_data.sort_values(by="period")  # type: ignore[union-attr]
                x_col = "period"
            else:
                x_col = str(entity_data.columns[0])  # type: ignore[union-attr]

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=entity_data[x_col].astype(str),
                y=entity_data["forecast"],
                mode="lines+markers",
                name="Forecast",
                line={"color": "blue", "width": 2},
            ))

            if "lower_ci" in entity_data.columns and "upper_ci" in entity_data.columns:
                fig.add_trace(go.Scatter(
                    x=entity_data[x_col].astype(str),
                    y=entity_data["upper_ci"],
                    mode="lines",
                    name="Upper CI",
                    line={"color": "lightblue", "width": 1, "dash": "dash"},
                ))
                fig.add_trace(go.Scatter(
                    x=entity_data[x_col].astype(str),
                    y=entity_data["lower_ci"],
                    mode="lines",
                    name="Lower CI",
                    line={"color": "lightblue", "width": 1, "dash": "dash"},
                    fill="tonexty",
                    fillcolor="rgba(173, 216, 230, 0.3)",
                ))

            model_type = entity_data["model_type"].iloc[0] if "model_type" in entity_data.columns else "N/A"
            cv_score = entity_data["cv_score"].iloc[0] if "cv_score" in entity_data.columns else None
            title = f"Forecast: {selected} (Model: {model_type}"
            if cv_score and pd.notna(cv_score):
                title += f", CV: {cv_score:.1f}%"
            title += ")"

            fig.update_layout(
                title=title,
                xaxis_title="Period",
                yaxis_title="Quantity",
                hovermode="x unified",
                height=400,
            )

            st.plotly_chart(fig, width='stretch')


def _render_manage_tab() -> None:
    st.subheader("Manage Trained Models")

    repo = create_ml_model_repository()
    models = repo.list_models(limit=200)

    if not models:
        st.info("No trained models found.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Models", len(models))
    with col2:
        avg_cv = sum(m.get("cv_score", 0) or 0 for m in models) / len(models) if models else 0
        st.metric("Avg CV Score", f"{avg_cv:.1f}%")
    with col3:
        model_types = {}
        for m in models:
            mt = m.get("model_type", "unknown")
            model_types[mt] = model_types.get(mt, 0) + 1
        most_common = max(model_types, key=model_types.get) if model_types else "N/A"
        st.metric("Most Common Model", most_common)

    st.markdown("---")

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search = st.text_input("Search Entity", key="ml_manage_search")
    with col_filter:
        type_filter = st.selectbox(
            "Filter by Model Type",
            options=["All"] + list({m.get("model_type", "") for m in models}),
            key="ml_manage_type_filter",
        )

    filtered_models = models
    if search:
        search = search.upper()
        filtered_models = [m for m in filtered_models if search in m["entity_id"]]
    if type_filter != "All":
        filtered_models = [m for m in filtered_models if m.get("model_type") == type_filter]

    models_df = pd.DataFrame([
        {
            "Entity": m["entity_id"],
            "Type": m.get("entity_type", "model"),
            "Model": m.get("model_type", "N/A"),
            "CV Score": f"{m.get('cv_score', 0):.1f}%" if m.get("cv_score") else "N/A",
            "Trained": m.get("trained_at", "")[:10] if m.get("trained_at") else "N/A",
        }
        for m in filtered_models
    ])

    st.write(f"Showing {len(filtered_models)} models")

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
    render_dataframe_with_aggrid(models_df, height=400, pinned_columns=["Entity"])

    st.markdown("---")
    _render_model_detail(filtered_models, repo)

    st.markdown("---")
    st.subheader("Bulk Actions")
    col_del, col_export = st.columns(2)
    with col_del:
        if st.button("Delete All Models", type="secondary", key="ml_delete_all"):
            count = repo.delete_all_models()
            st.success(f"Deleted {count} models")
            st.rerun()
    with col_export:
        if st.button("Export Model Report", key="ml_export_report"):
            report_df = pd.DataFrame(models)
            csv = report_df.to_csv(index=False)
            st.download_button(
                "Download Report",
                csv,
                "ml_models_report.csv",
                MimeTypes.TEXT_CSV,
                key="ml_report_download",
            )


def _render_model_detail(models: list[dict], repo) -> None:
    with st.expander("Model Details", expanded=False):
        if not models:
            st.info("No models to display")
            return

        entity_options = [m["entity_id"] for m in models]
        selected_entity = st.selectbox(
            "Select Entity for Details",
            options=entity_options,
            key="ml_detail_entity",
        )

        if not selected_entity:
            return

        model_meta = next((m for m in models if m["entity_id"] == selected_entity), None)
        if not model_meta:
            return

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Entity:** {model_meta['entity_id']}")
            st.write(f"**Model Type:** {model_meta.get('model_type', 'N/A')}")
            st.write(f"**CV Score:** {model_meta.get('cv_score', 'N/A')}")
        with col2:
            st.write(f"**Trained At:** {model_meta.get('trained_at', 'N/A')}")
            st.write(f"**CV Metric:** {model_meta.get('cv_metric', 'N/A')}")
            st.write(f"**Product Type:** {model_meta.get('product_type', 'N/A')}")

        feature_importance = model_meta.get("feature_importance")
        if feature_importance:
            st.markdown("#### Feature Importance")
            importance_df = pd.DataFrame([
                {"Feature": k, "Importance": v}
                for k, v in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            ])

            fig = px.bar(
                importance_df.head(15),
                x="Importance",
                y="Feature",
                orientation="h",
                title="Top Features",
            )
            fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, width='stretch')

        if st.button(f"Delete Model for {selected_entity}", key="ml_delete_single"):
            entity_type = model_meta.get("entity_type", "model")
            if repo.delete_model(selected_entity, entity_type):
                st.success(f"Deleted model for {selected_entity}")
                st.rerun()
            else:
                st.error("Failed to delete model")


def _clear_session_data() -> None:
    keys_to_clear = [
        SessionKeys.ML_FORECAST_DATA,
        SessionKeys.ML_FORECAST_PARAMS,
        SessionKeys.ML_TRAINED_MODELS,
        SessionKeys.ML_TRAINING_STATS,
        "ml_generated_forecasts",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None
