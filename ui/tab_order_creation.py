from __future__ import annotations

import traceback
from datetime import datetime

import pandas as pd
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import ColumnNames, Icons, MimeTypes, SessionKeys
from ui.shared.data_loaders import load_color_aliases, load_model_metadata, load_size_aliases
from ui.shared.session_manager import get_data_source, get_session_value, get_settings, set_session_value
from ui.shared.sku_utils import extract_color, extract_model, extract_size
from ui.shared.styles import ROTATED_TABLE_STYLE
from utils.pattern_optimizer import PatternSet, get_min_order_per_pattern, load_pattern_sets

TOTAL_PATTERNS = "Total Patterns"


def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        st.error(f"{Icons.ERROR} Error in Order Creation: {str(e)}")
        st.code(traceback.format_exc())


def _render_content(context: dict) -> None:
    st.title("📋 Order Creation")

    st.markdown("---")
    _render_manual_order_input(context)

    st.markdown("---")
    _render_order_interface()


def _render_manual_order_input(context: dict) -> None:
    st.subheader("📝 Manual Order Creation")

    col_input, col_button = st.columns([3, 1])
    with col_input:
        manual_model = st.text_input(
            "Enter Model Code",
            placeholder="e.g., CH031",
            help="Enter any model code (5 characters) to create an order.",
            key="manual_model_input",
        )
    with col_button:
        st.write("")
        st.write("")
        create_clicked = st.button("Create Order", key="create_manual_order", type="primary")

    if create_clicked:
        _process_manual_order(manual_model, context)


def _process_manual_order(manual_model: str, context: dict) -> None:
    if not manual_model:
        st.warning(f"{Icons.WARNING} Please enter a model code")
        return

    model_code = manual_model.upper().strip()
    df = context["df"]
    analyzer = context["analyzer"]
    settings = get_settings()

    model_skus = df[df["sku"].astype(str).str[:5] == model_code]

    if model_skus.empty:
        st.error(f"{Icons.ERROR} Model '{model_code}' not found in sales data.")
        return

    # noinspection PyTypeChecker
    with st.spinner(f"Loading data for model {model_code}..."):
        sku_summary = _prepare_sku_summary(analyzer, context, settings)
        sku_summary = _add_sku_components(sku_summary)
        model_data = sku_summary[sku_summary["MODEL"] == model_code].copy()

        if model_data.empty:
            st.error(f"{Icons.ERROR} No data found for model '{model_code}'")
            return

        selected_items = _build_selected_items(model_data, model_code)

        if selected_items:
            _save_order_to_session(selected_items, model_data)
            st.success(f"{Icons.SUCCESS} Created order for model {model_code} with {len(selected_items)} colors")
            st.rerun()
        else:
            st.warning(f"{Icons.WARNING} No items with positive forecast or deficit found for model '{model_code}'")


def _prepare_sku_summary(analyzer: SalesAnalyzer, context: dict, settings: dict) -> pd.DataFrame:
    seasonal_data = context["seasonal_data"]
    stock_df = context.get("stock_df")
    forecast_df = context.get("forecast_df")
    use_stock = context.get("use_stock", False)
    use_forecast = context.get("use_forecast", False)

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

    if use_stock and stock_df is not None:
        stock_df_sku_level = _prepare_stock_df(stock_df)
        if stock_df_sku_level is not None:
            stock_cols = ["SKU", ColumnNames.STOCK]
            if "PRICE" in stock_df_sku_level.columns:
                stock_cols.append("PRICE")
            sku_stock = stock_df_sku_level[stock_cols].copy()
            sku_summary = sku_summary.merge(sku_stock, on="SKU", how="left")
            sku_summary[ColumnNames.STOCK] = sku_summary[ColumnNames.STOCK].fillna(0)
            if "PRICE" in stock_cols:
                sku_summary["PRICE"] = sku_summary["PRICE"].fillna(0)
        else:
            _add_default_stock_columns(sku_summary)
    else:
        _add_default_stock_columns(sku_summary)

    if use_forecast and forecast_df is not None:
        sku_summary = _add_forecast_data(sku_summary, forecast_df, settings["lead_time"])
    else:
        sku_summary["FORECAST_LEADTIME"] = 0

    return sku_summary


def _prepare_stock_df(stock_df: pd.DataFrame) -> pd.DataFrame | None:
    if stock_df is None or stock_df.empty:
        return None

    stock_copy = stock_df.copy()
    if "sku" in stock_copy.columns:
        stock_copy = stock_copy.rename(columns={"sku": "SKU"})
    if "available_stock" in stock_copy.columns:
        stock_copy[ColumnNames.STOCK] = stock_copy["available_stock"]
    elif "stock" in stock_copy.columns:
        stock_copy[ColumnNames.STOCK] = stock_copy["stock"]

    if "cena_netto" in stock_copy.columns:
        stock_copy["PRICE"] = stock_copy["cena_netto"]

    return stock_copy


def _add_default_stock_columns(sku_summary: pd.DataFrame) -> None:
    if ColumnNames.STOCK not in sku_summary.columns:
        sku_summary[ColumnNames.STOCK] = 0
    if "PRICE" not in sku_summary.columns:
        sku_summary["PRICE"] = 0


def _add_forecast_data(sku_summary: pd.DataFrame, forecast_df: pd.DataFrame, lead_time: float) -> pd.DataFrame:
    forecast_start, forecast_end = SalesAnalyzer.calculate_forecast_date_range(lead_time)
    forecast_window = forecast_df[
        (forecast_df["data"] >= forecast_start) & (forecast_df["data"] < forecast_end)
        ]
    forecast_agg = forecast_window.groupby("sku", as_index=False)["forecast"].sum()
    # noinspection PyArgumentList
    forecast_agg = forecast_agg.rename(columns={"sku": "SKU", "forecast": "FORECAST_LEADTIME"})
    sku_summary = sku_summary.merge(forecast_agg, on="SKU", how="left")
    sku_summary["FORECAST_LEADTIME"] = sku_summary["FORECAST_LEADTIME"].fillna(0)
    return sku_summary


def _add_sku_components(sku_summary: pd.DataFrame) -> pd.DataFrame:
    sku_summary["MODEL"] = extract_model(sku_summary["SKU"])
    sku_summary["COLOR"] = extract_color(sku_summary["SKU"])
    sku_summary["SIZE"] = extract_size(sku_summary["SKU"])
    sku_summary["DEFICIT"] = (sku_summary["ROP"] - sku_summary[ColumnNames.STOCK]).clip(lower=0)
    return sku_summary


def _calculate_order_qty_for_row(row: pd.Series) -> tuple[str, int]:
    size_code = row["SIZE"]
    forecast_qty = int(row.get("FORECAST_LEADTIME", 0) or 0)
    stock_qty = int(row.get(ColumnNames.STOCK, 0) or 0)
    rop_value = row.get("ROP", 0)
    rop = 0 if pd.isna(rop_value) else int(rop_value)
    deficit = max(0, rop - stock_qty)
    order_qty = max(forecast_qty, deficit)
    return size_code, order_qty


def _build_size_quantities(color_data: pd.DataFrame) -> dict[str, int]:
    size_quantities = {}
    for _, row in color_data.iterrows():
        size_code, order_qty = _calculate_order_qty_for_row(row)
        if order_qty > 0:
            size_quantities[size_code] = order_qty
    return size_quantities


def _create_color_item(color_data: pd.DataFrame, model_code: str, color: str, size_quantities: dict) -> dict:
    avg_priority = color_data["PRIORITY"].mean() if "PRIORITY" in color_data.columns else 0
    total_deficit = int(color_data["DEFICIT"].sum()) if "DEFICIT" in color_data.columns else 0
    total_forecast = int(color_data["FORECAST_LEADTIME"].sum())
    return {
        "model": model_code,
        "color": color,
        "priority_score": float(avg_priority),
        "deficit": total_deficit,
        "forecast": total_forecast,
        "sizes": size_quantities,
    }


def _build_selected_items(model_data: pd.DataFrame, model_code: str) -> list[dict]:
    selected_items = []
    for color in model_data["COLOR"].unique():
        # noinspection PyTypeChecker
        color_data: pd.DataFrame = model_data[model_data["COLOR"] == color]
        size_quantities = _build_size_quantities(color_data)
        if size_quantities:
            selected_items.append(_create_color_item(color_data, model_code, color, size_quantities))
    return selected_items


def _save_order_to_session(selected_items: list[dict], model_data: pd.DataFrame) -> None:
    set_session_value(SessionKeys.SELECTED_ORDER_ITEMS, selected_items)

    if "PRIORITY" not in model_data.columns:
        model_data["PRIORITY"] = 0

    required_cols = [
        "SKU", "MODEL", "COLOR", "SIZE", "PRIORITY", "DEFICIT",
        "FORECAST_LEADTIME", ColumnNames.STOCK, "ROP", "SS", "TYPE"
    ]
    available_cols = [col for col in required_cols if col in model_data.columns]
    priority_skus = model_data[available_cols].copy()

    priority_skus["PRIORITY_SCORE"] = priority_skus["PRIORITY"]
    priority_skus["URGENT"] = (priority_skus[ColumnNames.STOCK] == 0) & (priority_skus["FORECAST_LEADTIME"] > 0)

    model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(priority_skus)

    set_session_value(SessionKeys.RECOMMENDATIONS_DATA, {
        "priority_skus": priority_skus,
        "model_color_summary": model_color_summary,
    })


def _render_order_interface() -> None:
    selected_items = get_session_value(SessionKeys.SELECTED_ORDER_ITEMS)

    if not selected_items:
        st.info(f"{Icons.INFO} No items selected. Use the manual input above or go to Order Recommendations tab.")
        return

    models = list({item["model"] for item in selected_items})

    if len(models) > 1:
        st.info(f"Selected items span {len(models)} models. Please select one model to process.")
        selected_model = st.selectbox("Select model to create order:", options=models)
    else:
        selected_model = models[0]

    if selected_model:
        items_for_model = [item for item in selected_items if item["model"] == selected_model]
        _process_model_order(selected_model, items_for_model)


def _process_model_order(model: str, selected_items: list[dict]) -> None:
    st.subheader(f"Order for Model: {model}")

    pattern_set = _lookup_pattern_set(model)
    if pattern_set is None:
        st.error(f"{Icons.ERROR} Pattern set '{model}' not found")
        st.info("Please create a pattern set in the Pattern Optimizer tab with name matching the model code")
        return

    st.success(f"{Icons.SUCCESS} Found pattern set: {pattern_set.name}")

    metadata = _load_model_metadata_for_model(model)
    _display_model_metadata(metadata)

    urgent_colors = _find_urgent_colors_for_model(model)
    selected_colors = [item["color"] for item in selected_items]
    all_colors = sorted(set(selected_colors + urgent_colors))

    if urgent_colors:
        st.info(f"**Urgent colors:** {', '.join(urgent_colors)}")

    pattern_results = {}
    for color in all_colors:
        result = _optimize_color_pattern(model, color, pattern_set)
        pattern_results[color] = result

    sales_history = _load_last_4_months_sales(model, all_colors)
    forecast_data = _load_forecast_data_for_colors(model, all_colors)

    order_table = _create_order_summary_table(
        model, all_colors, pattern_results, sales_history, forecast_data, pattern_set
    )

    st.markdown("---")
    st.subheader("Order Summary")
    st.dataframe(order_table, hide_index=True, height=400, width="stretch")

    _render_order_actions(model, order_table, pattern_results, metadata)

    st.markdown("---")
    st.subheader("Size × Color Production Table")
    _render_size_color_table(pattern_results, pattern_set)


def _render_order_actions(model: str, order_table: pd.DataFrame, pattern_results: dict, metadata: dict) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save to Database"):
            _save_order_to_database(model, order_table, pattern_results, metadata)
    with col2:
        csv = order_table.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 Download CSV",
            csv,
            f"order_{model}_{timestamp}.csv",
            MimeTypes.TEXT_CSV,
            key=f"download_order_{model}",
        )
    with col3:
        if st.button(f"{Icons.ERROR} Cancel"):
            st.session_state[SessionKeys.SELECTED_ORDER_ITEMS] = []
            st.rerun()


def _render_size_color_table(pattern_results: dict, pattern_set: PatternSet) -> None:
    size_color_table = _build_color_size_table(pattern_results, pattern_set)
    st.markdown(ROTATED_TABLE_STYLE, unsafe_allow_html=True)
    html_table = size_color_table.to_html(index=False, classes="rotated-table", border=0)
    st.markdown(f'<div class="rotated-table">{html_table}</div>', unsafe_allow_html=True)


def _lookup_pattern_set(model: str) -> PatternSet | None:
    pattern_sets = load_pattern_sets()
    for ps in pattern_sets:
        if ps.name == model:
            return ps
    return None


def _find_urgent_colors_for_model(model: str) -> list[str]:
    recommendations_data = st.session_state.get(SessionKeys.RECOMMENDATIONS_DATA)
    if recommendations_data is None:
        return []

    model_color_summary = recommendations_data.get("model_color_summary")
    if model_color_summary is None:
        return []

    return SalesAnalyzer.find_urgent_colors(model_color_summary, model)


def _optimize_color_pattern(model: str, color: str, pattern_set: PatternSet) -> dict:
    recommendations_data = st.session_state.get(SessionKeys.RECOMMENDATIONS_DATA)
    if not recommendations_data:
        st.warning(f"No recommendations data available for {model}-{color}")
        return _get_empty_optimization_result()

    priority_skus = recommendations_data["priority_skus"]
    size_aliases = load_size_aliases()
    min_per_pattern = get_min_order_per_pattern()
    settings = get_settings()
    algorithm_mode = settings.get("optimizer", {}).get("algorithm_mode", "greedy_overshoot")

    return SalesAnalyzer.optimize_pattern_with_aliases(
        priority_skus, model, color, pattern_set, size_aliases, min_per_pattern, algorithm_mode
    )


def _get_empty_optimization_result() -> dict:
    return {
        "allocation": {},
        "produced": {},
        "excess": {},
        "total_patterns": 0,
        "total_excess": 0,
        "all_covered": False,
    }


def _load_model_metadata_for_model(model: str) -> dict:
    metadata_df = load_model_metadata()

    if metadata_df is None or metadata_df.empty:
        return {}

    row = metadata_df[metadata_df["Model"] == model]
    if row.empty:
        return {}

    return {
        "szwalnia_glowna": row.iloc[0].get(ColumnNames.SZWALNIA_G, ""),
        "szwalnia_druga": row.iloc[0].get(ColumnNames.SZWALNIA_D, ""),
        "rodzaj_materialu": row.iloc[0].get(ColumnNames.MATERIAL, ""),
        "gramatura": row.iloc[0].get(ColumnNames.GRAMATURA, ""),
    }


def _display_model_metadata(metadata: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Primary Facility", metadata.get("szwalnia_glowna", "N/A") or "N/A")
    with col2:
        st.metric("Secondary Facility", metadata.get("szwalnia_druga", "N/A") or "N/A")
    with col3:
        st.metric("Material Type", metadata.get("rodzaj_materialu", "N/A") or "N/A")
    with col4:
        st.metric("Material Weight", metadata.get("gramatura", "N/A") or "N/A")


def _load_last_4_months_sales(model: str, colors: list[str]) -> pd.DataFrame:
    try:
        data_source = get_data_source()
        monthly_agg = data_source.get_monthly_aggregations(entity_type="sku")
        return SalesAnalyzer.get_last_n_months_sales_by_color(monthly_agg, model, colors, months=4)
    except Exception as e:
        st.warning(f"Could not load sales history: {e}")
        return pd.DataFrame()


def _load_forecast_data_for_colors(model: str, colors: list[str]) -> dict:
    recommendations_data = st.session_state.get(SessionKeys.RECOMMENDATIONS_DATA)
    if recommendations_data is None:
        return {}

    model_color_summary = recommendations_data.get("model_color_summary")
    if model_color_summary is None:
        return {}

    forecast_dict = {}
    for color in colors:
        row = model_color_summary[
            (model_color_summary["MODEL"] == model) & (model_color_summary["COLOR"] == color)
            ]
        if not row.empty:
            forecast_dict[color] = {
                "priority_score": float(row.iloc[0].get("PRIORITY_SCORE", 0)),
                "forecast": int(row.iloc[0].get("FORECAST_LEADTIME", 0)),
                "deficit": int(row.iloc[0].get("DEFICIT", 0)),
                "coverage_gap": int(row.iloc[0].get("COVERAGE_GAP", 0)),
                "stock": int(row.iloc[0].get(ColumnNames.STOCK, 0)),
                "safety_stock": int(row.iloc[0].get("SS", 0)),
                "reorder_point": int(row.iloc[0].get("ROP", 0)),
            }

    return forecast_dict


def _create_order_summary_table(
        model: str,
        colors: list[str],
        pattern_results: dict,
        sales_history: pd.DataFrame,
        forecast_data: dict,
        pattern_set: PatternSet,
) -> pd.DataFrame:
    rows = []
    for color in colors:
        pattern_res = pattern_results.get(color, {})
        forecast = forecast_data.get(color, {})

        pattern_allocation_str = _build_pattern_allocation_string(pattern_res.get("allocation", {}), pattern_set)
        produced_str = _build_produced_string(pattern_res.get("produced", {}))

        row = _create_base_row(model, color, pattern_res, forecast, pattern_allocation_str)
        _add_sales_history_to_row(row, sales_history, color)
        row["Produced (Size:Qty)"] = produced_str

        rows.append(row)

    return pd.DataFrame(rows)


def _create_base_row(model: str, color: str, pattern_res: dict, forecast: dict, pattern_allocation_str: str) -> dict:
    color_aliases = load_color_aliases()
    color_name = color_aliases.get(color, color)

    return {
        "Model": model,
        "Color": color,
        "Color Name": color_name,
        "Priority": round(forecast.get("priority_score", 0), 1),
        "Patterns": pattern_allocation_str,
        TOTAL_PATTERNS: pattern_res.get("total_patterns", 0),
        "Total Excess": pattern_res.get("total_excess", 0),
        "Stock": forecast.get("stock", 0),
        "Safety Stock": forecast.get("safety_stock", 0),
        "ROP": forecast.get("reorder_point", 0),
        "Forecast": forecast.get("forecast", 0),
        "Deficit": forecast.get("deficit", 0),
        "Coverage Gap": forecast.get("coverage_gap", 0),
    }


def _build_pattern_allocation_string(allocation: dict, pattern_set: PatternSet) -> str:
    if not allocation:
        return ""

    pattern_parts = []
    for pattern_id, count in sorted(allocation.items()):
        if count > 0:
            pattern = next((p for p in pattern_set.patterns if p.id == pattern_id), None)
            if pattern:
                pattern_parts.append(f"{pattern.name}:{count}")
    return ", ".join(pattern_parts)


def _build_produced_string(produced: dict) -> str:
    if not produced:
        return ""
    return ", ".join([f"{s}:{q}" for s, q in sorted(produced.items()) if q > 0])


def _add_sales_history_to_row(row: dict, sales_history: pd.DataFrame, color: str) -> None:
    if sales_history.empty or "color" not in sales_history.columns:
        return

    sales_row = sales_history[sales_history["color"] == color]
    if sales_row.empty:
        return

    month_cols = [col for col in sales_history.columns if col != "color"]
    for col in sorted(month_cols):
        try:
            month_label = _format_month_label(str(col))
            row[month_label] = int(sales_row.iloc[0][col])
        except (KeyError, ValueError, IndexError):
            pass


def _format_month_label(year_month_str: str) -> str:
    if len(year_month_str) == 7 and "-" in year_month_str:
        year, month = year_month_str.split("-")
        return f"{month}-{year}"
    return year_month_str


def _build_color_size_table(pattern_results: dict, pattern_set: PatternSet) -> pd.DataFrame:
    color_aliases = load_color_aliases()
    size_alias_to_code = _load_size_aliases_reverse()

    def get_size_sort_key(size_str: str) -> int:
        size_code = size_alias_to_code.get(size_str, size_str)
        try:
            return int(size_code)
        except (ValueError, TypeError):
            return 999

    all_model_colors = _get_all_model_colors(pattern_results)
    data = []

    for pattern in pattern_set.patterns:
        pattern_sizes = sorted(pattern.sizes.keys(), key=get_size_sort_key)

        for size in pattern_sizes:
            # noinspection PyTypeChecker
            row = _create_pattern_row(size, all_model_colors, color_aliases, pattern_results, pattern.id)
            data.append(row)

        empty_row = _create_empty_row(all_model_colors, color_aliases)
        data.append(empty_row)

    if data and data[-1]["Size"] == "":
        data.pop()

    return pd.DataFrame(data)


@st.cache_data(ttl=3600)
def _load_size_aliases_reverse() -> dict[str, str]:
    size_aliases = load_size_aliases()
    return {v: k for k, v in size_aliases.items()}


def _get_all_model_colors(pattern_results: dict) -> list[str]:
    ordered_colors = sorted(pattern_results.keys())
    data_source = get_data_source()
    sales_df = data_source.load_sales_data()

    if sales_df is None or sales_df.empty:
        return ordered_colors

    selected_items = st.session_state.get(SessionKeys.SELECTED_ORDER_ITEMS, [])
    if not selected_items:
        return ordered_colors

    model_code = selected_items[0]["model"]
    model_skus = sales_df[sales_df["sku"].astype(str).str[:5] == model_code]
    return sorted(model_skus["sku"].astype(str).str[5:7].unique())


def _create_pattern_row(size: str, all_model_colors: list[str], color_aliases: dict, pattern_results: dict,
                        pattern_id: str) -> dict:
    row = {"Size": size}
    for color in all_model_colors:
        color_name = color_aliases.get(color, color)
        pattern_count = _get_pattern_count_for_color(pattern_results, color, pattern_id)
        # noinspection PyTypeChecker
        row[color_name] = pattern_count
    return row


def _get_pattern_count_for_color(pattern_results: dict, color: str, pattern_id: str) -> int:
    if color not in pattern_results:
        return 0
    allocation = pattern_results[color].get("allocation", {})
    return allocation.get(pattern_id, 0)


def _create_empty_row(all_model_colors: list[str], color_aliases: dict) -> dict:
    empty_row = {"Size": ""}
    for color in all_model_colors:
        color_name = color_aliases.get(color, color)
        empty_row[color_name] = ""
    return empty_row


def _save_order_to_database(model: str, order_table: pd.DataFrame, pattern_results: dict, metadata: dict) -> None:
    from utils.order_manager import save_order

    try:
        order_id = f"ORD_{model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        order_data = {
            "order_id": order_id,
            "model": model,
            "status": "draft",
            "szwalnia_glowna": metadata.get("szwalnia_glowna"),
            "szwalnia_druga": metadata.get("szwalnia_druga"),
            "rodzaj_materialu": metadata.get("rodzaj_materialu"),
            "gramatura": metadata.get("gramatura"),
            "total_colors": len(order_table),
            "total_patterns": int(order_table[TOTAL_PATTERNS].sum()),
            "total_excess": int(order_table["Total Excess"].sum()),
            "total_quantity": int(order_table[TOTAL_PATTERNS].sum()),
            "order_data": {
                "pattern_results": {
                    k: {
                        "allocation": v.get("allocation", {}),
                        "produced": v.get("produced", {}),
                        "excess": v.get("excess", {}),
                        "total_patterns": v.get("total_patterns", 0),
                        "total_excess": v.get("total_excess", 0),
                    }
                    for k, v in pattern_results.items()
                },
                "order_table": order_table.to_dict(orient="records"),
            },
        }

        success = save_order(order_data)

        if success:
            st.success(f"{Icons.SUCCESS} Order {order_id} saved successfully!")
            st.session_state[SessionKeys.SELECTED_ORDER_ITEMS] = []
        else:
            st.error(f"{Icons.ERROR} Failed to save order")

    except Exception as e:
        st.error(f"{Icons.ERROR} Error saving order: {e}")
        st.code(traceback.format_exc())
