from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from sales_data.analyzer import SalesAnalyzer
from sales_data.data_source_factory import DataSourceFactory
from utils.pattern_optimizer_logic import PatternSet, load_pattern_sets, get_min_order_per_pattern

TOTAL_PATTERNS = "Total Patterns"


@st.cache_data(ttl=3600)
def load_size_aliases() -> Dict[str, str]:
    data_source = DataSourceFactory.create_data_source()
    return data_source.load_size_aliases()


def render_order_creation_interface() -> None:
    selected_items = st.session_state.selected_order_items

    models = list({item["model"] for item in selected_items})

    if len(models) > 1:
        st.info(f"Selected items span {len(models)} models. Please select one model to process.")
        selected_model = st.selectbox("Select model to create order:", options=models)
    else:
        selected_model = models[0]

    if selected_model:
        items_for_model = [item for item in selected_items if item["model"] == selected_model]
        process_model_order(selected_model, items_for_model)


def process_model_order(model: str, selected_items: List[Dict]) -> None:
    st.subheader(f"Order for Model: {model}")

    pattern_set = lookup_pattern_set(model)
    if pattern_set is None:
        st.error(f"❌ Pattern set '{model}' not found")
        st.info("Please create a pattern set in the Pattern Optimizer tab with name matching the model code")
        if st.button("→ Go to Pattern Optimizer"):
            st.info("Please navigate to the 'Size Pattern Optimizer' tab manually")
        return

    st.success(f"✅ Found pattern set: {pattern_set.name}")

    metadata = load_model_metadata_for_model(model)
    display_model_metadata(metadata)

    urgent_colors = find_urgent_colors_for_model(model)
    selected_colors = [item["color"] for item in selected_items]
    all_colors = sorted(set(selected_colors + urgent_colors))

    if urgent_colors:
        st.info(f"**Urgent colors:** {', '.join(urgent_colors)}")

    pattern_results = {}
    for color in all_colors:
        result = optimize_color_pattern(model, color, pattern_set)
        pattern_results[color] = result

    sales_history = load_last_4_months_sales(model, all_colors)
    forecast_data = load_forecast_data_for_colors(model, all_colors)

    order_table = create_order_summary_table(
        model, all_colors, pattern_results, sales_history, forecast_data, pattern_set
    )

    st.markdown("---")
    st.subheader("Order Summary")
    st.dataframe(order_table, hide_index=True, height=400, width="stretch")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save to Database"):
            save_order_to_database(model, order_table, pattern_results, metadata)
    with col2:
        csv = order_table.to_csv(index=False)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        st.download_button(
            "📥 Download CSV",
            csv,
            f"order_{model}_{timestamp}.csv",
            "text/csv"
        )
    with col3:
        if st.button("❌ Cancel"):
            st.session_state.selected_order_items = []
            st.rerun()


def find_urgent_colors_for_model(model: str) -> List[str]:
    if "recommendations_data" not in st.session_state:
        return []

    recommendations_data = st.session_state.recommendations_data
    if recommendations_data is None:
        return []

    model_color_summary = recommendations_data.get("model_color_summary")
    if model_color_summary is None:
        return []

    return SalesAnalyzer.find_urgent_colors(model_color_summary, model)


def lookup_pattern_set(model: str) -> Optional[PatternSet]:
    pattern_sets = load_pattern_sets()
    for ps in pattern_sets:
        if ps.name == model:
            return ps
    return None


def optimize_color_pattern(model: str, color: str, pattern_set: PatternSet) -> Dict:
    recommendations_data = st.session_state.get("recommendations_data")
    if not recommendations_data:
        st.warning(f"No recommendations data available for {model}-{color}")
        return _get_empty_optimization_result()

    priority_skus = recommendations_data["priority_skus"]
    size_aliases = load_size_aliases()
    min_per_pattern = get_min_order_per_pattern()

    return SalesAnalyzer.optimize_pattern_with_aliases(
        priority_skus, model, color, pattern_set, size_aliases, min_per_pattern
    )


def _get_empty_optimization_result() -> Dict:
    return {
        "allocation": {},
        "produced": {},
        "excess": {},
        "total_patterns": 0,
        "total_excess": 0,
        "all_covered": False,
    }


def load_model_metadata_for_model(model: str) -> Dict:
    if "data_source" not in st.session_state:
        st.session_state.data_source = DataSourceFactory.create_data_source()

    metadata_df = st.session_state.data_source.load_model_metadata()

    if metadata_df is None or metadata_df.empty:
        return {}

    row = metadata_df[metadata_df["Model"] == model]
    if row.empty:
        return {}

    return {
        "szwalnia_glowna": row.iloc[0].get("SZWALNIA GŁÓWNA", ""),
        "szwalnia_druga": row.iloc[0].get("SZWALNIA DRUGA", ""),
        "rodzaj_materialu": row.iloc[0].get("RODZAJ MATERIAŁU", ""),
        "gramatura": row.iloc[0].get("GRAMATURA", ""),
    }


def display_model_metadata(metadata: Dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Primary Facility", metadata.get("szwalnia_glowna", "N/A") or "N/A")
    with col2:
        st.metric("Secondary Facility", metadata.get("szwalnia_druga", "N/A") or "N/A")
    with col3:
        st.metric("Material Type", metadata.get("rodzaj_materialu", "N/A") or "N/A")
    with col4:
        st.metric("Material Weight", metadata.get("gramatura", "N/A") or "N/A")


def load_last_4_months_sales(model: str, colors: List[str]) -> pd.DataFrame:
    try:
        if "data_source" not in st.session_state:
            st.session_state.data_source = DataSourceFactory.create_data_source()

        monthly_agg = st.session_state.data_source.get_monthly_aggregations(entity_type="sku")

        if monthly_agg is None or monthly_agg.empty:
            return pd.DataFrame()

        if "entity_id" in monthly_agg.columns:
            monthly_agg = monthly_agg.rename(columns={"entity_id": "SKU"})
        if "year_month" in monthly_agg.columns:
            monthly_agg = monthly_agg.rename(columns={"year_month": "YEAR_MONTH"})
        if "total_quantity" in monthly_agg.columns:
            monthly_agg = monthly_agg.rename(columns={"total_quantity": "TOTAL_QUANTITY"})

        monthly_agg["model"] = monthly_agg["SKU"].astype(str).str[:5]
        monthly_agg["color"] = monthly_agg["SKU"].astype(str).str[5:7]

        filtered = monthly_agg[
            (monthly_agg["model"] == model) &
            (monthly_agg["color"].isin(colors))
            ]

        if filtered.empty:
            return pd.DataFrame()

        filtered = filtered.sort_values("YEAR_MONTH")

        unique_months = filtered["YEAR_MONTH"].unique()
        last_4_months = sorted(unique_months)[-4:] if len(unique_months) >= 4 else sorted(unique_months)

        filtered_last_4 = filtered[filtered["YEAR_MONTH"].isin(last_4_months)]

        pivot_df = filtered_last_4.pivot_table(
            index="color",
            columns="YEAR_MONTH",
            values="TOTAL_QUANTITY",
            aggfunc="sum",
            fill_value=0
        )

        pivot_df = pivot_df.reset_index()

        return pivot_df

    except Exception as e:
        st.warning(f"Could not load sales history: {e}")
        return pd.DataFrame()


def load_forecast_data_for_colors(model: str, colors: List[str]) -> Dict:
    if "recommendations_data" not in st.session_state or st.session_state.recommendations_data is None:
        return {}

    model_color_summary = st.session_state.recommendations_data.get("model_color_summary")
    if model_color_summary is None:
        return {}

    forecast_dict = {}
    for color in colors:
        row = model_color_summary[
            (model_color_summary["MODEL"] == model) &
            (model_color_summary["COLOR"] == color)
            ]
        if not row.empty:
            forecast_dict[color] = {
                "priority_score": float(row.iloc[0].get("PRIORITY_SCORE", 0)),
                "forecast": int(row.iloc[0].get("FORECAST_LEADTIME", 0)),
                "deficit": int(row.iloc[0].get("DEFICIT", 0)),
                "coverage_gap": int(row.iloc[0].get("COVERAGE_GAP", 0)),
                "stock": int(row.iloc[0].get("STOCK", 0)),
                "safety_stock": int(row.iloc[0].get("SS", 0)),
                "reorder_point": int(row.iloc[0].get("ROP", 0)),
            }

    return forecast_dict


def _build_pattern_allocation_string(allocation: Dict, pattern_set: PatternSet) -> str:
    if not allocation:
        return ""

    pattern_parts = []
    for pattern_id, count in sorted(allocation.items()):
        if count > 0:
            pattern = next((p for p in pattern_set.patterns if p.id == pattern_id), None)
            if pattern:
                pattern_parts.append(f"{pattern.name}:{count}")
    return ", ".join(pattern_parts)


def _build_produced_string(produced: Dict) -> str:
    if not produced:
        return ""
    return ", ".join([f"{s}:{q}" for s, q in sorted(produced.items()) if q > 0])


def _format_month_label(year_month_str: str) -> str:
    if len(year_month_str) == 7 and "-" in year_month_str:
        year, month = year_month_str.split("-")
        return f"{month}-{year}"
    return year_month_str


def _add_sales_history_to_row(row: Dict, sales_history: pd.DataFrame, color: str) -> None:
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


def _create_base_row(model: str, color: str, pattern_res: Dict, forecast: Dict, pattern_allocation_str: str) -> Dict:
    return {
        "Model": model,
        "Color": color,
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


def create_order_summary_table(
        model: str,
        colors: List[str],
        pattern_results: Dict,
        sales_history: pd.DataFrame,
        forecast_data: Dict,
        pattern_set: PatternSet
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


def save_order_to_database(model: str, order_table: pd.DataFrame, pattern_results: Dict, metadata: Dict) -> None:
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
                "pattern_results": {k: {
                    "allocation": v.get("allocation", {}),
                    "produced": v.get("produced", {}),
                    "excess": v.get("excess", {}),
                    "total_patterns": v.get("total_patterns", 0),
                    "total_excess": v.get("total_excess", 0),
                } for k, v in pattern_results.items()},
                "order_table": order_table.to_dict(orient="records"),
            }
        }

        success = save_order(order_data)

        if success:
            st.success(f"✅ Order {order_id} saved successfully!")
            st.session_state.selected_order_items = []
        else:
            st.error("❌ Failed to save order")

    except Exception as e:
        st.error(f"❌ Error saving order: {e}")
        import traceback
        st.code(traceback.format_exc())
