from __future__ import annotations

import pandas as pd
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import ColumnNames, Config, Icons, MimeTypes, SessionKeys
from ui.shared.data_loaders import load_color_aliases, load_model_metadata
from ui.shared.session_manager import get_session_value, get_settings, set_session_value
from utils.logging_config import get_logger

logger = get_logger("tab_order_recommendations")


def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        logger.exception("Error in Order Recommendations")
        st.error(f"{Icons.ERROR} Error in Order Recommendations: {str(e)}")


def _render_content(context: dict) -> None:
    st.title("🎯 Order Recommendations")
    st.write(
        "Automatically prioritize which models and colors to order based on stock levels, forecasts, and ROP thresholds."
    )

    _initialize_tab_session_state()

    stock_loaded = context.get("stock_loaded", False)
    use_forecast = context.get("use_forecast", False)
    forecast_df = context.get("forecast_df")

    if not stock_loaded or not use_forecast or forecast_df is None:
        st.warning(f"{Icons.WARNING} Please load both stock and forecast data in Tab 1 to use this feature.")
        return

    _render_parameters_expander()
    _render_facility_filters()
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


@st.fragment
def _render_parameters_expander() -> None:
    settings = get_settings()

    with st.expander("⚙️ Recommendation Parameters", expanded=False):
        st.caption("Adjust these parameters to tune the priority scoring algorithm")

        _render_priority_weights(settings)
        _render_type_multipliers(settings)
        _render_stockout_parameters(settings)


def _render_priority_weights(settings: dict) -> None:
    st.write("**Priority Weights** (contribution to final score)")
    w_col1, w_col2, w_col3 = st.columns(3)

    with w_col1:
        weight_stockout = st.slider(
            "Stockout Risk",
            0.0, 1.0,
            settings["order_recommendations"]["priority_weights"]["stockout_risk"],
            0.05,
            key="weight_stockout",
            help="Weight for stockout risk factor in priority calculation. Higher values prioritize items at risk of stockout.",
        )
    with w_col2:
        weight_revenue = st.slider(
            "Revenue Impact",
            0.0, 1.0,
            settings["order_recommendations"]["priority_weights"]["revenue_impact"],
            0.05,
            key="weight_revenue",
            help="Weight for revenue impact in priority calculation. Higher values prioritize high-revenue items.",
        )
    with w_col3:
        weight_demand = st.slider(
            "Demand Forecast",
            0.0, 1.0,
            settings["order_recommendations"]["priority_weights"]["demand_forecast"],
            0.05,
            key="weight_demand",
            help="Weight for demand forecast in priority calculation. Higher values prioritize items with high forecasted demand.",
        )

    st.caption(f"Current weights sum: {weight_stockout + weight_revenue + weight_demand:.2f} (ideally 1.0)")

    settings["order_recommendations"]["priority_weights"]["stockout_risk"] = weight_stockout
    settings["order_recommendations"]["priority_weights"]["revenue_impact"] = weight_revenue
    settings["order_recommendations"]["priority_weights"]["demand_forecast"] = weight_demand


def _render_type_multipliers(settings: dict) -> None:
    st.write("**Type Multipliers** (priority boost by product type)")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        mult_new = st.slider(
            "New Products", 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["new"],
            0.1, key="mult_new",
            help="Multiplier for new products (< 12 months). Values > 1.0 increase priority.",
        )
    with m_col2:
        mult_seasonal = st.slider(
            "Seasonal", 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["seasonal"],
            0.1, key="mult_seasonal",
            help="Multiplier for seasonal products (CV > 1.0).",
        )
    with m_col3:
        mult_regular = st.slider(
            "Regular", 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["regular"],
            0.1, key="mult_regular",
            help="Multiplier for regular products (0.6 < CV < 1.0).",
        )
    with m_col4:
        mult_basic = st.slider(
            "Basic", 0.5, 2.0,
            settings["order_recommendations"]["type_multipliers"]["basic"],
            0.1, key="mult_basic",
            help="Multiplier for basic products (CV < 0.6).",
        )

    settings["order_recommendations"]["type_multipliers"]["new"] = mult_new
    settings["order_recommendations"]["type_multipliers"]["seasonal"] = mult_seasonal
    settings["order_recommendations"]["type_multipliers"]["regular"] = mult_regular
    settings["order_recommendations"]["type_multipliers"]["basic"] = mult_basic


def _render_stockout_parameters(settings: dict) -> None:
    st.write("**Stockout Risk & Other Parameters**")
    o_col1, o_col2, o_col3 = st.columns(3)

    with o_col1:
        zero_penalty = st.slider(
            "Zero Stock Penalty", 50, 150,
            settings["order_recommendations"]["stockout_risk"]["zero_stock_penalty"],
            5, key="zero_penalty",
            help="Risk score for SKUs with zero stock AND forecasted demand.",
        )
    with o_col2:
        below_rop_penalty = st.slider(
            "Below ROP Max Penalty", 40, 100,
            settings["order_recommendations"]["stockout_risk"]["below_rop_max_penalty"],
            5, key="below_rop_penalty",
            help="Maximum risk score for items below Reorder Point (ROP).",
        )
    with o_col3:
        demand_cap = st.slider(
            "Demand Cap", 50, 300,
            settings["order_recommendations"]["demand_cap"],
            10, key="demand_cap",
            help="Maximum forecast value used in priority calculation.",
        )

    settings["order_recommendations"]["stockout_risk"]["zero_stock_penalty"] = zero_penalty
    settings["order_recommendations"]["stockout_risk"]["below_rop_max_penalty"] = below_rop_penalty
    settings["order_recommendations"]["demand_cap"] = demand_cap


def _render_facility_filters() -> None:
    st.write("**Filter by Production Facility**")
    model_metadata_df = load_model_metadata()

    if model_metadata_df is None or ColumnNames.SZWALNIA_G not in model_metadata_df.columns:
        st.info("Model metadata not available. Showing all items.")
        return

    unique_facilities = sorted(
        model_metadata_df[ColumnNames.SZWALNIA_G].dropna().str.strip().unique().tolist()
    )
    col_include, col_exclude = st.columns(2)

    with col_include:
        st.session_state[SessionKeys.SZWALNIA_INCLUDE_FILTER] = st.multiselect(
            "Include Facilities:",
            options=unique_facilities,
            default=st.session_state[SessionKeys.SZWALNIA_INCLUDE_FILTER],
            help="Select facilities to INCLUDE. Empty = include all.",
        )

    with col_exclude:
        st.session_state[SessionKeys.SZWALNIA_EXCLUDE_FILTER] = st.multiselect(
            "Exclude Facilities:",
            options=unique_facilities,
            default=st.session_state[SessionKeys.SZWALNIA_EXCLUDE_FILTER],
            help="Select facilities to EXCLUDE. Takes precedence over include.",
        )


def _render_controls_row() -> None:
    col_top_n, col_calc, col_clear = st.columns([3, 1, 1])

    with col_top_n:
        top_n = st.slider(
            "Number of top priority items to show:",
            min_value=5, max_value=50,
            value=st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N],
            step=5,
        )
        st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N] = top_n

    with col_calc:
        st.write("")
        st.write("")
        if st.button("Generate Recommendations", type="primary"):
            st.session_state["_generate_recommendations"] = True

    with col_clear:
        st.write("")
        st.write("")
        if st.button("Clear", type="secondary"):
            st.session_state[SessionKeys.RECOMMENDATIONS_DATA] = None
            st.rerun()


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

    st.subheader("Top Priority Items to Order")
    st.caption(f"Showing top {len(top_model_colors)} MODEL+COLOR combinations by priority")

    _render_order_selection_table(top_model_colors, recommendations, model_metadata_df)
    _render_selected_items_actions()

    st.markdown("---")
    _render_full_summary(recommendations, model_metadata_df)


def _generate_recommendations(context: dict) -> None:
    analyzer = context["analyzer"]
    seasonal_data = context["seasonal_data"]
    stock_df = context.get("stock_df")
    forecast_df = context.get("forecast_df")
    settings = get_settings()

    # noinspection PyTypeChecker
    with st.spinner("Calculating order priorities..."):
        try:
            sku_summary = _build_sku_summary(analyzer, seasonal_data, stock_df, settings)

            forecast_time = settings["lead_time"]
            recommendations = SalesAnalyzer.generate_order_recommendations(
                summary_df=sku_summary,
                forecast_df=forecast_df,
                forecast_time_months=forecast_time,
                top_n=st.session_state[SessionKeys.RECOMMENDATIONS_TOP_N],
                settings=settings,
            )

            recommendations = _filter_active_orders(recommendations)
            recommendations = _apply_facility_filters(recommendations)

            set_session_value(SessionKeys.RECOMMENDATIONS_DATA, recommendations)
            st.success(
                f"{Icons.SUCCESS} Analyzed {len(recommendations['priority_skus'])} SKUs - scroll down to view results")

        except Exception as e:
            logger.exception("Error generating recommendations")
            st.error(f"Error generating recommendations: {e}")


def _build_sku_summary(analyzer: SalesAnalyzer, seasonal_data: dict, stock_df: pd.DataFrame | None,
                       settings: dict) -> pd.DataFrame:
    sku_summary = analyzer.aggregate_by_sku()
    sku_summary = analyzer.classify_sku_type(
        sku_summary,
        cv_basic=settings["cv_thresholds"]["basic"],
        cv_seasonal=settings["cv_thresholds"]["seasonal"],
    )
    # noinspection PyTypeChecker
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

    sku_summary = _merge_stock_data(sku_summary, stock_df)
    return sku_summary


def _merge_stock_data(sku_summary: pd.DataFrame, stock_df: pd.DataFrame | None) -> pd.DataFrame:
    if stock_df is None or stock_df.empty:
        if ColumnNames.STOCK not in sku_summary.columns:
            sku_summary[ColumnNames.STOCK] = 0
        if "PRICE" not in sku_summary.columns:
            sku_summary["PRICE"] = 0
        return sku_summary

    stock_df_copy = stock_df.copy()
    if "sku" in stock_df_copy.columns:
        stock_df_copy = stock_df_copy.rename(columns={"sku": "SKU"})
    if "available_stock" in stock_df_copy.columns:
        stock_df_copy[ColumnNames.STOCK] = stock_df_copy["available_stock"]
    elif "stock" in stock_df_copy.columns:
        stock_df_copy[ColumnNames.STOCK] = stock_df_copy["stock"]
    if "cena_netto" in stock_df_copy.columns:
        stock_df_copy["PRICE"] = stock_df_copy["cena_netto"]

    stock_cols = ["SKU", ColumnNames.STOCK]
    if "PRICE" in stock_df_copy.columns:
        stock_cols.append("PRICE")

    sku_stock = stock_df_copy[stock_cols].copy()
    sku_summary = sku_summary.merge(sku_stock, on="SKU", how="left")
    sku_summary[ColumnNames.STOCK] = sku_summary[ColumnNames.STOCK].astype(float).fillna(0)
    if "PRICE" in stock_cols:
        sku_summary["PRICE"] = sku_summary["PRICE"].astype(float).fillna(0)

    return sku_summary


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


def _render_order_selection_table(top_model_colors: pd.DataFrame, recommendations: dict,
                                  model_metadata_df: pd.DataFrame | None) -> None:
    order_list = []
    color_aliases = load_color_aliases()

    for idx, (_, row) in enumerate(top_model_colors.iterrows(), 1):
        model = row["MODEL"]
        color = row["COLOR"]

        size_quantities = SalesAnalyzer.get_size_quantities_for_model_color(
            recommendations["priority_skus"],
            model,
            color,
        )

        sizes_str = (
            ", ".join([f"{size}:{qty}" for size, qty in sorted(size_quantities.items())])
            if size_quantities
            else "No data"
        )

        color_name = color_aliases.get(color, color)

        order_item = {
            "#": idx,
            "Model": model,
            "Color": color,
            "Color Name": color_name,
            "Priority": f"{row['PRIORITY_SCORE']:.1f}",
            "Deficit": int(row["DEFICIT"]),
            "Forecast": int(row.get("FORECAST_LEADTIME", 0)),
            ColumnNames.SIZE_QTY: sizes_str,
        }

        if model_metadata_df is not None:
            metadata_row = model_metadata_df[model_metadata_df["Model"] == model]
            if not metadata_row.empty:
                order_item[ColumnNames.SZWALNIA_G] = metadata_row.iloc[0][ColumnNames.SZWALNIA_G]

        order_list.append(order_item)

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
                "Select",
                help="Select items to create order",
                default=False,
            )
        },
        height=min(Config.DATAFRAME_HEIGHT, len(order_list) * 35 + 38),
    )

    _process_selections(edited_df)


def _process_selections(edited_df: pd.DataFrame) -> None:
    selected_rows = edited_df[edited_df["Select"] == True]

    if selected_rows.empty:
        return

    selected_items = []
    for _, row in selected_rows.iterrows():
        sizes_str = row[ColumnNames.SIZE_QTY]
        size_quantities = {}
        if sizes_str and sizes_str != "No data":
            for pair in sizes_str.split(", "):
                if ":" in pair:
                    size, qty = pair.split(":")
                    size_quantities[size] = int(qty)

        selected_items.append({
            "model": row["Model"],
            "color": row["Color"],
            "priority_score": float(row["Priority"]),
            "deficit": int(row["Deficit"]),
            "forecast": int(row["Forecast"]),
            "sizes": size_quantities,
        })

    set_session_value(SessionKeys.SELECTED_ORDER_ITEMS, selected_items)


def _render_selected_items_actions() -> None:
    selected_items = get_session_value(SessionKeys.SELECTED_ORDER_ITEMS)

    if selected_items:
        st.success(f"✓ {len(selected_items)} items selected")
        if st.button("📋 Create Order", type="primary"):
            st.info("Please navigate to the 'Order Creation' tab to complete the order")
    else:
        st.info("Select items above to create an order")


def _render_full_summary(recommendations: dict, model_metadata_df: pd.DataFrame | None) -> None:
    st.subheader("Full Model+Color Priority Summary")

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
        "📥 Download Full Priority Report (SKU level)",
        recommendations["priority_skus"].to_csv(index=False),
        "order_priority_report.csv",
        MimeTypes.TEXT_CSV,
        key="download_tab5_priority_report",
    )
