from __future__ import annotations

import pandas as pd
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import ColumnNames, Config, Icons, MimeTypes, SessionKeys
from ui.i18n import t, Keys
from ui.shared.data_loaders import load_color_aliases, load_model_metadata, merge_stock_into_summary
from ui.shared.session_manager import get_session_value, get_settings, set_session_value
from utils.logging_config import get_logger

logger = get_logger("tab_order_recommendations")

DEFAULT_EXCLUDED_MATERIALS = ["30% KASZMIR, 70% MERINO", "WEŁNA 100% MERINO", "MUŚLIN"]


@st.fragment
def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        logger.exception("Error in Order Recommendations")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_ORDER_RECOMMENDATIONS).format(error=str(e))}")


def _render_content(context: dict) -> None:
    st.title(t(Keys.TITLE_ORDER_RECOMMENDATIONS))
    st.write(t(Keys.ORDER_RECOMMENDATIONS_DESC))

    _initialize_tab_session_state()

    stock_loaded = context.get("stock_loaded", False)
    use_forecast = context.get("use_forecast", False)
    forecast_df = context.get("forecast_df")

    if not stock_loaded or not use_forecast or forecast_df is None:
        logger.warning("Required data not loaded: stock_loaded=%s, use_forecast=%s, forecast_df=%s",
                       stock_loaded, use_forecast, forecast_df is not None)
        st.warning(f"{Icons.WARNING} {t(Keys.LOAD_STOCK_AND_FORECAST)}")
        return

    _render_parameters_expander()
    _render_facility_filters()
    _render_material_filters()
    _render_controls_row()
    _render_results(context)


def _initialize_tab_session_state() -> None:
    if SessionKeys.RECOMMENDATIONS_DATA not in st.session_state:
        st.session_state[SessionKeys.RECOMMENDATIONS_DATA] = None
    if SessionKeys.RECOMMENDATIONS_TOP_N not in st.session_state:
        st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N] = 10
    if SessionKeys.SELECTED_ORDER_ITEMS not in st.session_state:
        st.session_state[SessionKeys.SELECTED_ORDER_ITEMS] = []
    if SessionKeys.SZWALNIA_INCLUDE_FILTER not in st.session_state:
        st.session_state[SessionKeys.SZWALNIA_INCLUDE_FILTER] = []
    if SessionKeys.SZWALNIA_EXCLUDE_FILTER not in st.session_state:
        st.session_state[SessionKeys.SZWALNIA_EXCLUDE_FILTER] = []
    if SessionKeys.MATERIAL_INCLUDE_FILTER not in st.session_state:
        st.session_state[SessionKeys.MATERIAL_INCLUDE_FILTER] = []
    if SessionKeys.MATERIAL_EXCLUDE_FILTER not in st.session_state:
        st.session_state[SessionKeys.MATERIAL_EXCLUDE_FILTER] = []
    if "forecast_source" not in st.session_state:
        st.session_state["forecast_source"] = "External"


@st.fragment
def _render_parameters_expander() -> None:
    settings = get_settings()

    with st.expander(t(Keys.TITLE_RECOMMENDATION_PARAMS), expanded=False):
        st.caption(t(Keys.RECOMMENDATION_PARAMS_HELP))

        _render_priority_weights(settings)
        _render_type_multipliers(settings)
        _render_stockout_parameters(settings)


def _render_priority_weights(settings: dict) -> None:
    st.write(f"**{t(Keys.PRIORITY_WEIGHTS)}**")
    w_col1, w_col2, w_col3 = st.columns(3)

    with w_col1:
        weight_stockout = st.slider(
            t(Keys.STOCKOUT_RISK),
            0.0, 1.0,
            settings["order_recommendations"]["priority_weights"]["stockout_risk"],
            0.05,
            key="weight_stockout",
            help=t(Keys.HELP_WEIGHT_STOCKOUT),
        )
    with w_col2:
        weight_revenue = st.slider(
            t(Keys.REVENUE_IMPACT),
            0.0, 1.0,
            settings["order_recommendations"]["priority_weights"]["revenue_impact"],
            0.05,
            key="weight_revenue",
            help=t(Keys.HELP_WEIGHT_REVENUE),
        )
    with w_col3:
        weight_demand = st.slider(
            t(Keys.DEMAND_FORECAST),
            0.0, 1.0,
            settings["order_recommendations"]["priority_weights"]["demand_forecast"],
            0.05,
            key="weight_demand",
            help=t(Keys.HELP_WEIGHT_DEMAND),
        )

    st.caption(t(Keys.CURRENT_WEIGHTS_SUM).format(sum=weight_stockout + weight_revenue + weight_demand))

    settings["order_recommendations"]["priority_weights"]["stockout_risk"] = weight_stockout
    settings["order_recommendations"]["priority_weights"]["revenue_impact"] = weight_revenue
    settings["order_recommendations"]["priority_weights"]["demand_forecast"] = weight_demand


def _render_type_multipliers(settings: dict) -> None:
    st.write(f"**{t(Keys.TYPE_MULTIPLIERS)}**")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        mult_new = st.slider(
            t(Keys.NEW_PRODUCTS), 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["new"],
            0.1, key="mult_new",
            help=t(Keys.HELP_MULT_NEW),
        )
    with m_col2:
        mult_seasonal = st.slider(
            t(Keys.TYPE_SEASONAL), 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["seasonal"],
            0.1, key="mult_seasonal",
            help=t(Keys.HELP_MULT_SEASONAL),
        )
    with m_col3:
        mult_regular = st.slider(
            t(Keys.TYPE_REGULAR), 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["regular"],
            0.1, key="mult_regular",
            help=t(Keys.HELP_MULT_REGULAR),
        )
    with m_col4:
        mult_basic = st.slider(
            t(Keys.TYPE_BASIC), 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["basic"],
            0.1, key="mult_basic",
            help=t(Keys.HELP_MULT_BASIC),
        )

    settings["order_recommendations"]["type_multipliers"]["new"] = mult_new
    settings["order_recommendations"]["type_multipliers"]["seasonal"] = mult_seasonal
    settings["order_recommendations"]["type_multipliers"]["regular"] = mult_regular
    settings["order_recommendations"]["type_multipliers"]["basic"] = mult_basic


def _render_stockout_parameters(settings: dict) -> None:
    st.write(f"**{t(Keys.STOCKOUT_RISK_PARAMS)}**")
    o_col1, o_col2, o_col3 = st.columns(3)

    with o_col1:
        zero_penalty = st.slider(
            t(Keys.ZERO_STOCK_PENALTY), 50, 150,
            settings["order_recommendations"]["stockout_risk"]["zero_stock_penalty"],
            5, key="zero_penalty",
            help=t(Keys.HELP_ZERO_PENALTY),
        )
    with o_col2:
        below_rop_penalty = st.slider(
            t(Keys.BELOW_ROP_PENALTY), 40, 100,
            settings["order_recommendations"]["stockout_risk"]["below_rop_max_penalty"],
            5, key="below_rop_penalty",
            help=t(Keys.HELP_BELOW_ROP_PENALTY),
        )
    with o_col3:
        demand_cap = st.slider(
            t(Keys.DEMAND_CAP), 50, 300,
            settings["order_recommendations"]["demand_cap"],
            10, key="demand_cap",
            help=t(Keys.HELP_DEMAND_CAP),
        )

    settings["order_recommendations"]["stockout_risk"]["zero_stock_penalty"] = zero_penalty
    settings["order_recommendations"]["stockout_risk"]["below_rop_max_penalty"] = below_rop_penalty
    settings["order_recommendations"]["demand_cap"] = demand_cap


def _render_facility_filters() -> None:
    st.write(f"**{t(Keys.FILTER_BY_FACILITY)}**")
    model_metadata_df = load_model_metadata()

    if model_metadata_df is None or ColumnNames.SZWALNIA_G not in model_metadata_df.columns:
        st.info(t(Keys.MODEL_METADATA_NOT_AVAILABLE))
        return

    unique_facilities = sorted(
        model_metadata_df[ColumnNames.SZWALNIA_G].dropna().str.strip().unique().tolist()
    )
    col_include, col_exclude = st.columns(2)

    with col_include:
        st.session_state[SessionKeys.SZWALNIA_INCLUDE_FILTER] = st.multiselect(
            t(Keys.INCLUDE_FACILITIES),
            options=unique_facilities,
            default=st.session_state[SessionKeys.SZWALNIA_INCLUDE_FILTER],
            help=t(Keys.HELP_INCLUDE_FACILITIES),
        )

    with col_exclude:
        st.session_state[SessionKeys.SZWALNIA_EXCLUDE_FILTER] = st.multiselect(
            t(Keys.EXCLUDE_FACILITIES),
            options=unique_facilities,
            default=st.session_state[SessionKeys.SZWALNIA_EXCLUDE_FILTER],
            help=t(Keys.HELP_EXCLUDE_FACILITIES),
        )


def _render_material_filters() -> None:
    st.write(f"**{t(Keys.FILTER_BY_MATERIAL)}**")
    model_metadata_df = load_model_metadata()

    if model_metadata_df is None or ColumnNames.MATERIAL not in model_metadata_df.columns:
        st.info(t(Keys.MODEL_METADATA_NOT_AVAILABLE))
        return

    unique_materials = sorted(
        model_metadata_df[ColumnNames.MATERIAL].dropna().str.strip().unique().tolist()
    )
    col_include, col_exclude = st.columns(2)

    with col_include:
        st.session_state[SessionKeys.MATERIAL_INCLUDE_FILTER] = st.multiselect(
            t(Keys.INCLUDE_MATERIALS),
            options=unique_materials,
            default=st.session_state[SessionKeys.MATERIAL_INCLUDE_FILTER],
            help=t(Keys.HELP_INCLUDE_MATERIALS),
        )

    with col_exclude:
        current_exclude = st.session_state[SessionKeys.MATERIAL_EXCLUDE_FILTER]
        if not current_exclude:
            current_exclude = [m for m in DEFAULT_EXCLUDED_MATERIALS if m in unique_materials]
        st.session_state[SessionKeys.MATERIAL_EXCLUDE_FILTER] = st.multiselect(
            t(Keys.EXCLUDE_MATERIALS_REC),
            options=unique_materials,
            default=current_exclude,
            help=t(Keys.HELP_EXCLUDE_MATERIALS),
        )


def _render_controls_row() -> None:
    col_source, col_top_n, col_calc, col_clear = st.columns([2, 2, 1, 1])

    with col_source:
        ml_models_count = _get_ml_models_count()
        source_options = ["External"]
        if ml_models_count > 0:
            source_options.append(f"ML ({ml_models_count} models)")

        st.session_state["forecast_source"] = st.selectbox(
            t(Keys.FORECAST_SOURCE),
            options=source_options,
            index=0,
            key="forecast_source_select",
            help=t(Keys.HELP_FORECAST_SOURCE),
        )

    with col_top_n:
        top_n = st.slider(
            t(Keys.TOP_PRIORITY_ITEMS),
            min_value=5, max_value=50,
            value=st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N],
            step=5,
        )
        st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N] = top_n

    with col_calc:
        st.write("")
        st.write("")
        if st.button(t(Keys.BTN_GENERATE_RECOMMENDATIONS), type="primary"):
            logger.info("Generate Recommendations button clicked, top_n=%d", top_n)
            st.session_state["_generate_recommendations"] = True

    with col_clear:
        st.write("")
        st.write("")
        if st.button(t(Keys.BTN_CLEAR), type="secondary"):
            logger.info("Clear recommendations button clicked")
            st.session_state[SessionKeys.RECOMMENDATIONS_DATA] = None
            st.rerun()


def _get_ml_models_count() -> int:
    try:
        from utils.ml_model_repository import create_ml_model_repository
        repo = create_ml_model_repository()
        return repo.get_model_count()
    except (ImportError, AttributeError, OSError):
        return 0


def _render_results(context: dict) -> None:
    if st.session_state.get("_generate_recommendations"):
        st.session_state["_generate_recommendations"] = False
        _generate_recommendations(context)

    recommendations = get_session_value(SessionKeys.RECOMMENDATIONS_DATA)
    if recommendations is None:
        return

    model_metadata_df = load_model_metadata()
    top_n = st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N]

    top_model_colors = (
        recommendations["model_color_summary"]
        .sort_values("PRIORITY_SCORE", ascending=False)
        .head(top_n)
    )

    st.subheader(t(Keys.TOP_PRIORITY_TO_ORDER))
    st.caption(t(Keys.SHOWING_TOP_MODEL_COLOR).format(count=len(top_model_colors)))

    _render_order_selection_table(top_model_colors, recommendations, model_metadata_df)
    _render_selected_items_actions()

    st.markdown("---")
    _render_full_summary(recommendations, model_metadata_df)


def _generate_recommendations(context: dict) -> None:
    logger.info("Starting recommendation generation")
    analyzer: SalesAnalyzer = context["analyzer"]
    seasonal_data: pd.DataFrame = context["seasonal_data"]
    stock_df = context.get("stock_df")
    forecast_df = context.get("forecast_df")
    settings = get_settings()

    forecast_source = st.session_state.get("forecast_source", "External")
    use_ml = forecast_source.startswith("ML")

    with st.spinner(t(Keys.CALCULATING_PRIORITIES)):  # type: ignore[attr-defined]
        try:
            sku_summary = _build_sku_summary(analyzer, seasonal_data, stock_df, settings)

            if use_ml:
                logger.info("Loading ML forecast data")
                forecast_df = _load_ml_forecast(settings)
                if forecast_df is None or forecast_df.empty:
                    logger.warning("No ML forecasts available")
                    st.error(t(Keys.NO_ML_FORECASTS))
                    return
                logger.info("ML forecast loaded: %d rows", len(forecast_df))

            if forecast_df is None:
                st.error(t(Keys.LOAD_STOCK_AND_FORECAST))
                return

            forecast_time = settings["lead_time"]
            recommendations = SalesAnalyzer.generate_order_recommendations(
                summary_df=sku_summary,
                forecast_df=forecast_df,
                forecast_time_months=forecast_time,
                top_n=st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N],
                settings=settings,
            )
            logger.info("Recommendations generated: %d priority SKUs, %d model-color combinations",
                        len(recommendations['priority_skus']), len(recommendations['model_color_summary']))

            recommendations = _filter_active_orders(recommendations)
            recommendations = _apply_facility_filters(recommendations)
            recommendations = _apply_material_filters(recommendations)

            set_session_value(SessionKeys.RECOMMENDATIONS_DATA, recommendations)
            source_label = "ML" if use_ml else "External"
            logger.info("Recommendations finalized: %d SKUs from %s source",
                        len(recommendations['priority_skus']), source_label)
            st.success(
                f"{Icons.SUCCESS} {t(Keys.ANALYZED_N_SKUS).format(count=len(recommendations['priority_skus']), source=source_label)}")

        except Exception as e:
            logger.exception("Error generating recommendations")
            st.error(t(Keys.ERR_GENERATING_RECOMMENDATIONS).format(error=e))


def _build_sku_summary(analyzer: SalesAnalyzer, seasonal_data: pd.DataFrame, stock_df: pd.DataFrame | None,
                       settings: dict) -> pd.DataFrame:
    sku_summary = analyzer.aggregate_by_sku()
    sku_summary = analyzer.classify_sku_type(
        sku_summary,
        cv_basic=settings["cv_thresholds"]["basic"],
        cv_seasonal=settings["cv_thresholds"]["seasonal"],
    )
    sku_summary = analyzer.calculate_safety_stock_and_rop(
        sku_summary,
        seasonal_data,
        z_basic=settings["z_scores"]["basic"],
        z_regular=settings["z_scores"]["regular"],
        z_seasonal_in=settings["z_scores"]["seasonal_in"],
        z_seasonal_out=settings["z_scores"]["seasonal_out"],
        z_new=settings["z_scores"]["new"],
        lead_time_months=settings["lead_time"],
    )

    sku_last_two_years = analyzer.calculate_last_two_years_avg_sales(by_model=False)
    sku_summary = sku_summary.merge(sku_last_two_years, on="SKU", how="left")
    sku_summary["LAST_2_YEARS_AVG"] = sku_summary["LAST_2_YEARS_AVG"].fillna(0)

    return merge_stock_into_summary(sku_summary, stock_df, ColumnNames.STOCK)


def _period_to_timestamp(p) -> pd.Timestamp:
    if hasattr(p, "to_timestamp"):
        result = p.to_timestamp()
        return pd.Timestamp(result) if not pd.isna(result) else pd.Timestamp.now()
    return pd.Timestamp(str(p))


def _process_single_forecast(
        monthly_agg: pd.DataFrame,
        model_meta: dict,
        repo,
        horizon: int,
) -> pd.DataFrame | None:
    from sales_data.analysis.ml_forecast import generate_ml_forecast

    entity_id = model_meta["entity_id"]
    entity_type = model_meta["entity_type"]

    model_info = repo.get_model(entity_id, entity_type)
    if model_info is None:
        return None

    result = generate_ml_forecast(monthly_agg, entity_id, model_info, horizon)

    if not result["success"] or result["forecast_df"] is None:
        return None

    forecast_df = result["forecast_df"].copy()
    forecast_df["sku"] = f"{entity_id}0000" if entity_type == "model" else entity_id
    forecast_df["data"] = forecast_df["period"].apply(_period_to_timestamp)

    return forecast_df[["sku", "data", "forecast"]]


def _load_ml_forecast(settings: dict) -> pd.DataFrame | None:
    from utils.ml_model_repository import create_ml_model_repository
    from ui.shared.session_manager import get_data_source

    try:
        repo = create_ml_model_repository()
        models = repo.list_models(limit=500)

        if not models:
            return None

        data_source = get_data_source()
        monthly_agg = data_source.get_monthly_aggregations()

        if monthly_agg is None or monthly_agg.empty:
            return None

        horizon = int(settings.get("lead_time", 3))
        all_forecasts = []

        for model_meta in models:
            forecast_df = _process_single_forecast(monthly_agg, model_meta, repo, horizon)
            if forecast_df is not None:
                all_forecasts.append(forecast_df)

        if all_forecasts:
            return pd.concat(all_forecasts, ignore_index=True)

        return None

    except (ImportError, AttributeError, KeyError) as e:
        logger.warning("Error loading ML forecast: %s", e)
        return None


def _filter_active_orders(recommendations: dict) -> dict:
    from utils.order_manager import get_active_orders

    active_orders = get_active_orders()
    active_models = {order["model"] for order in active_orders}

    if not active_models:
        return recommendations

    priority_skus = recommendations["priority_skus"].copy()
    priority_skus = priority_skus[~priority_skus["MODEL"].isin(active_models)]

    model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(priority_skus)

    recommendations["priority_skus"] = priority_skus
    recommendations["model_color_summary"] = model_color_summary

    st.info(f"ℹ️ Filtered out {len(active_models)} model(s) with active orders: {', '.join(sorted(active_models))}")
    return recommendations


def _apply_facility_filters(recommendations: dict) -> dict:
    include_filter = st.session_state[SessionKeys.SZWALNIA_INCLUDE_FILTER]
    exclude_filter = st.session_state[SessionKeys.SZWALNIA_EXCLUDE_FILTER]

    if not include_filter and not exclude_filter:
        return recommendations

    model_metadata_df = load_model_metadata()
    if model_metadata_df is None or ColumnNames.SZWALNIA_G not in model_metadata_df.columns:
        return recommendations

    priority_skus = recommendations["priority_skus"].copy()
    priority_skus = priority_skus.merge(
        model_metadata_df[["Model", ColumnNames.SZWALNIA_G]],
        left_on="MODEL",
        right_on="Model",
        how="left",
    )

    priority_skus[ColumnNames.SZWALNIA_G] = priority_skus[ColumnNames.SZWALNIA_G].str.strip()

    if include_filter:
        priority_skus = priority_skus[priority_skus[ColumnNames.SZWALNIA_G].isin(include_filter)]

    if exclude_filter:
        priority_skus = priority_skus[~priority_skus[ColumnNames.SZWALNIA_G].isin(exclude_filter)]

    priority_skus = priority_skus.drop(columns=["Model", ColumnNames.SZWALNIA_G])

    model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(priority_skus)

    recommendations["priority_skus"] = priority_skus
    recommendations["model_color_summary"] = model_color_summary

    return recommendations


def _apply_material_filters(recommendations: dict) -> dict:
    include_filter = st.session_state[SessionKeys.MATERIAL_INCLUDE_FILTER]
    exclude_filter = st.session_state[SessionKeys.MATERIAL_EXCLUDE_FILTER]

    if not include_filter and not exclude_filter:
        return recommendations

    model_metadata_df = load_model_metadata()
    if model_metadata_df is None or ColumnNames.MATERIAL not in model_metadata_df.columns:
        return recommendations

    priority_skus = recommendations["priority_skus"].copy()
    priority_skus = priority_skus.merge(
        model_metadata_df[["Model", ColumnNames.MATERIAL]],
        left_on="MODEL",
        right_on="Model",
        how="left",
    )

    priority_skus[ColumnNames.MATERIAL] = priority_skus[ColumnNames.MATERIAL].str.strip()

    if include_filter:
        priority_skus = priority_skus[priority_skus[ColumnNames.MATERIAL].isin(include_filter)]

    if exclude_filter:
        priority_skus = priority_skus[~priority_skus[ColumnNames.MATERIAL].isin(exclude_filter)]

    priority_skus = priority_skus.drop(columns=["Model", ColumnNames.MATERIAL])

    model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(priority_skus)

    recommendations["priority_skus"] = priority_skus
    recommendations["model_color_summary"] = model_color_summary

    return recommendations


def _build_order_item(
        idx: int,
        row: pd.Series,
        recommendations: dict,
        color_aliases: dict,
        model_metadata_df: pd.DataFrame | None,
) -> dict:
    model = str(row["MODEL"])
    color = str(row["COLOR"])

    size_quantities = SalesAnalyzer.get_size_quantities_for_model_color(
        recommendations["priority_skus"], model, color
    )

    sizes_str = (
        ", ".join([f"{size}:{qty}" for size, qty in sorted(size_quantities.items())])
        if size_quantities
        else t(Keys.NO_DATA)
    )

    order_item = {
        "#": idx,
        "Model": model,
        "Color": color,
        "Color Name": color_aliases.get(color, color),
        "Priority": f"{row['PRIORITY_SCORE']:.1f}",
        "Deficit": int(row["DEFICIT"]),
        "Forecast": int(row.get("FORECAST_LEADTIME") or 0),
        ColumnNames.SIZE_QTY: sizes_str,
    }

    if model_metadata_df is not None:
        metadata_row = model_metadata_df[model_metadata_df["Model"] == model]
        if not metadata_row.empty:
            order_item[ColumnNames.SZWALNIA_G] = metadata_row.iloc[0][ColumnNames.SZWALNIA_G]

    return order_item


def _render_order_selection_table(
        top_model_colors: pd.DataFrame,
        recommendations: dict,
        model_metadata_df: pd.DataFrame | None,
) -> None:
    color_aliases = load_color_aliases()

    order_list = [
        _build_order_item(idx, row, recommendations, color_aliases, model_metadata_df)
        for idx, (_, row) in enumerate(top_model_colors.iterrows(), 1)
    ]

    order_df = pd.DataFrame(order_list)
    order_df.insert(0, "Select", False)

    disabled_cols = ["#", "Model", "Color", "Color Name", "Priority", "Deficit", "Forecast", ColumnNames.SIZE_QTY]
    if ColumnNames.SZWALNIA_G in order_df.columns:
        disabled_cols.append(ColumnNames.SZWALNIA_G)

    edited_df = st.data_editor(
        order_df,
        hide_index=True,
        disabled=disabled_cols,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                t(Keys.SELECT),
                help=t(Keys.HELP_SELECT_ITEMS),
                default=False,
            )
        },
        height=min(Config.DATAFRAME_HEIGHT, len(order_list) * 35 + 38),
    )

    _process_selections(edited_df)


def _parse_size_quantities(sizes_str: str) -> dict[str, int]:
    if not sizes_str or sizes_str == "No data":
        return {}
    result = {}
    for pair in sizes_str.split(", "):
        if ":" in pair:
            size, qty = pair.split(":")
            result[size] = int(qty)
    return result


def _process_selections(edited_df: pd.DataFrame) -> None:
    selected_rows = edited_df[edited_df["Select"].fillna(False)]

    if selected_rows.empty:
        return

    selected_items = [
        {
            "model": row["Model"],
            "color": row["Color"],
            "priority_score": float(row["Priority"]),
            "deficit": int(row["Deficit"]),
            "forecast": int(row["Forecast"]),
            "sizes": _parse_size_quantities(str(row[ColumnNames.SIZE_QTY])),
        }
        for _, row in selected_rows.iterrows()
    ]

    set_session_value(SessionKeys.SELECTED_ORDER_ITEMS, selected_items)
    st.session_state[SessionKeys.PATTERN_RESULTS_CACHE] = {}


def _render_selected_items_actions() -> None:
    selected_items = get_session_value(SessionKeys.SELECTED_ORDER_ITEMS)

    if selected_items:
        st.success(f"✓ {t(Keys.ITEMS_SELECTED).format(count=len(selected_items))}")
        if st.button(t(Keys.BTN_CREATE_ORDER), type="primary"):
            st.info(t(Keys.NAVIGATE_ORDER_CREATION))
    else:
        st.info(t(Keys.SELECT_ITEMS_TO_ORDER))


def _render_full_summary(recommendations: dict, model_metadata_df: pd.DataFrame | None) -> None:
    st.subheader(t(Keys.FULL_MODEL_COLOR_SUMMARY))

    model_color_summary = recommendations["model_color_summary"].copy()

    color_aliases = load_color_aliases()

    if color_aliases:
        model_color_summary["COLOR_NAME"] = model_color_summary["COLOR"].map(color_aliases).fillna(
            model_color_summary["COLOR"]
        )
    else:
        model_color_summary["COLOR_NAME"] = model_color_summary["COLOR"]

    if model_metadata_df is not None:
        model_color_summary = model_color_summary.merge(
            model_metadata_df, left_on="MODEL", right_on="Model", how="left"
        )
        if "Model" in model_color_summary.columns:
            model_color_summary = model_color_summary.drop(columns=["Model"])

    display_cols = [
        "MODEL", "COLOR", "COLOR_NAME", "PRIORITY_SCORE",
        "DEFICIT", "FORECAST_LEADTIME", "URGENT",
    ]

    if model_metadata_df is not None:
        display_cols.extend([
            ColumnNames.SZWALNIA_G,
            ColumnNames.SZWALNIA_D,
            ColumnNames.MATERIAL,
            "GRAMATURA",
        ])

    available_cols = [col for col in display_cols if col in model_color_summary.columns]

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
    render_dataframe_with_aggrid(
        model_color_summary[available_cols], height=400, pinned_columns=["Model", "Color"]
    )

    st.download_button(
        t(Keys.DOWNLOAD_PRIORITY_REPORT),
        recommendations["priority_skus"].to_csv(index=False),
        "order_priority_report.csv",
        MimeTypes.TEXT_CSV,
        key="download_tab5_priority_report",
    )
