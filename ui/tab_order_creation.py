from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from sales_data import SalesAnalyzer
from sales_data.analysis import apply_priority_scoring
from ui.constants import ColumnNames, Icons, MimeTypes, SessionKeys
from ui.i18n import Keys, t
from ui.shared.data_loaders import (
    load_color_aliases,
    load_model_metadata,
    load_size_aliases,
    load_size_aliases_reverse,
    merge_stock_into_summary,
)
from ui.shared.session_manager import get_data_source, get_session_value, get_settings, set_session_value
from ui.shared.sku_utils import extract_color, extract_model, extract_size, get_size_sort_key
from ui.shared.styles import ROTATED_TABLE_STYLE
from utils.logging_config import get_logger
from utils.pattern_optimizer import PatternSet, load_pattern_sets

TOTAL_PATTERNS = "Total Patterns"
_MSG_NO_RECOMMENDATIONS = "No recommendations data in session"

logger = get_logger("tab_order_creation")


@st.fragment
def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        logger.exception("Error in Order Creation")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_ORDER_CREATION).format(error=str(e))}")


def _render_content(context: dict) -> None:
    st.title(t(Keys.TITLE_ORDER_CREATION))

    st.markdown("---")
    _render_manual_order_input(context)

    st.markdown("---")
    _render_order_interface()


def _render_manual_order_input(context: dict) -> None:
    st.subheader(t(Keys.TITLE_MANUAL_ORDER_CREATION))

    with st.form("manual_order_creation_form"):
        manual_model = st.text_input(
            t(Keys.ENTER_MODEL_CODE),
            placeholder=t(Keys.ENTER_MODEL_PLACEHOLDER),
            help=t(Keys.ENTER_MODEL_CODE_HELP),
        )
        create_clicked = st.form_submit_button(t(Keys.BTN_CREATE_ORDER), type="primary")

    if create_clicked:
        _process_manual_order(manual_model, context)


def _process_manual_order(manual_model: str, context: dict) -> None:
    if not manual_model:
        st.warning(f"{Icons.WARNING} {t(Keys.MSG_ENTER_MODEL_CODE)}")
        return

    model_code = manual_model.upper().strip()
    df = context["df"]
    analyzer = context["analyzer"]
    settings = get_settings()

    model_skus = df[df["sku"].astype(str).str[:5] == model_code]

    if model_skus.empty:
        logger.warning("No SKUs found for model '%s'", model_code)
        st.error(f"{Icons.ERROR} {t(Keys.MODEL_NOT_FOUND).format(model=model_code)}")
        return

    with st.spinner(t(Keys.LOADING_DATA_FOR_MODEL).format(model=model_code)):  # type: ignore[attr-defined]
        sku_summary = _prepare_sku_summary(analyzer, context, settings)
        sku_summary = _add_sku_components(sku_summary)
        model_data = pd.DataFrame(sku_summary[sku_summary["MODEL"] == model_code]).copy()

        if model_data.empty:
            logger.warning("No data found for model '%s' after filtering", model_code)
            st.error(f"{Icons.ERROR} {t(Keys.NO_DATA_FOR_MODEL).format(model=model_code)}")
            return

        selected_items = _build_selected_items(model_data, model_code)

        if selected_items:
            logger.info("Order created for model '%s' with %d items", model_code, len(selected_items))
            _save_order_to_session(selected_items, model_data)
            st.success(f"{Icons.SUCCESS} {t(Keys.CREATED_ORDER).format(model=model_code, count=len(selected_items))}")
            st.rerun()
        else:
            logger.warning("No items with forecast/deficit found for model '%s'", model_code)
            st.warning(f"{Icons.WARNING} {t(Keys.NO_FORECAST_DEFICIT).format(model=model_code)}")


def _prepare_sku_summary(analyzer: SalesAnalyzer, context: dict, settings: dict) -> pd.DataFrame:
    seasonal_data = context["seasonal_data"]
    stock_df = context.get("stock_df")
    forecast_df = context.get("forecast_df")

    if stock_df is None or (hasattr(stock_df, 'empty') and stock_df.empty):
        stock_df = _load_stock_data()

    if forecast_df is None or (hasattr(forecast_df, 'empty') and forecast_df.empty):
        forecast_df = _load_forecast_data()

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

    sku_summary = merge_stock_into_summary(sku_summary, stock_df, ColumnNames.STOCK)
    sku_summary = _merge_forecast_data(sku_summary, forecast_df, settings["lead_time"])
    sku_summary = apply_priority_scoring(sku_summary, settings)

    monthly_agg = _load_monthly_aggregations_cached()
    if monthly_agg is not None and not monthly_agg.empty:
        period_sales = SalesAnalyzer.calculate_period_sales(monthly_agg, settings["lead_time"])
        sku_summary = sku_summary.merge(period_sales, on="SKU", how="left")
        sku_summary["PERIOD_SALES"] = sku_summary["PERIOD_SALES"].fillna(0).astype(int)
    else:
        sku_summary["PERIOD_SALES"] = 0

    return sku_summary


def _merge_forecast_data(
        sku_summary: pd.DataFrame, forecast_df: pd.DataFrame | None, lead_time: float
) -> pd.DataFrame:
    if forecast_df is None or forecast_df.empty:
        sku_summary["FORECAST_LEADTIME"] = 0
        return sku_summary

    return _add_forecast_data(sku_summary, forecast_df, lead_time)


@st.cache_data(ttl=3600)
def _load_cached_data(data_type: str) -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        if data_type == "stock":
            return data_source.load_stock_data()
        return data_source.load_forecast_data()
    except Exception as e:
        logger.warning("Could not load %s data: %s", data_type, e)
        return None


def _load_stock_data() -> pd.DataFrame | None:
    return _load_cached_data("stock")


def _load_forecast_data() -> pd.DataFrame | None:
    return _load_cached_data("forecast")


def _add_forecast_data(sku_summary: pd.DataFrame, forecast_df: pd.DataFrame, lead_time: float) -> pd.DataFrame:
    forecast_start, forecast_end = SalesAnalyzer.calculate_forecast_date_range(lead_time)
    forecast_window = forecast_df[
        (forecast_df["data"] >= forecast_start) & (forecast_df["data"] < forecast_end)
        ]
    forecast_agg = pd.DataFrame(forecast_window.groupby("sku", as_index=False, observed=True)["forecast"].sum())
    forecast_agg = forecast_agg.rename(columns={"sku": "SKU", "forecast": "FORECAST_LEADTIME"})
    sku_summary = sku_summary.merge(forecast_agg, on="SKU", how="left")
    sku_summary["FORECAST_LEADTIME"] = sku_summary["FORECAST_LEADTIME"].fillna(0)
    return sku_summary


def _add_sku_components(sku_summary: pd.DataFrame) -> pd.DataFrame:
    sku_col = pd.Series(sku_summary["SKU"])
    sku_summary["MODEL"] = extract_model(sku_col)
    sku_summary["COLOR"] = extract_color(sku_col)
    sku_summary["SIZE"] = extract_size(sku_col)
    sku_summary["DEFICIT"] = (sku_summary["ROP"] - sku_summary[ColumnNames.STOCK]).clip(lower=0)
    return sku_summary


def _calculate_order_qty_for_row(row: pd.Series) -> tuple[str, int]:
    size_code = str(row["SIZE"])
    period_sales = int(row.get("PERIOD_SALES", 0) or 0)
    if period_sales == 0:
        return size_code, 0
    stock_qty = int(row.get(ColumnNames.STOCK, 0) or 0)
    ss_value = row.get("SS", 0)
    ss = 0 if ss_value is None or (isinstance(ss_value, float) and pd.isna(ss_value)) else int(ss_value)
    order_qty = max(0, period_sales + ss - stock_qty)
    return size_code, order_qty


def _build_size_quantities(color_data: pd.DataFrame) -> dict[str, int]:
    size_quantities = {}
    for _, row in color_data.iterrows():
        size_code, order_qty = _calculate_order_qty_for_row(row)
        if order_qty > 0:
            size_quantities[size_code] = order_qty
    return size_quantities


def _create_color_item(color_data: pd.DataFrame, model_code: str, color: str, size_quantities: dict) -> dict:
    avg_priority = color_data["PRIORITY_SCORE"].mean() if "PRIORITY_SCORE" in color_data.columns else 0
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
        color_data = pd.DataFrame(model_data[model_data["COLOR"] == color])
        size_quantities = _build_size_quantities(color_data)
        if size_quantities:
            item = _create_color_item(color_data, model_code, str(color), size_quantities)
            selected_items.append(item)
    return selected_items


def _save_order_to_session(selected_items: list[dict], model_data: pd.DataFrame) -> None:
    set_session_value(SessionKeys.SELECTED_ORDER_ITEMS, selected_items)
    st.session_state[SessionKeys.PATTERN_RESULTS_CACHE] = {}

    if "PRIORITY_SCORE" not in model_data.columns:
        model_data["PRIORITY_SCORE"] = 0

    required_cols = [
        "SKU", "MODEL", "COLOR", "SIZE", "PRIORITY_SCORE", "DEFICIT",
        "FORECAST_LEADTIME", ColumnNames.STOCK, "ROP", "SS", "TYPE", "PERIOD_SALES"
    ]
    available_cols = [col for col in required_cols if col in model_data.columns]
    priority_skus = model_data[available_cols].copy()

    if "URGENT" not in priority_skus.columns:
        priority_skus["URGENT"] = (priority_skus[ColumnNames.STOCK] == 0) & (priority_skus["FORECAST_LEADTIME"] > 0)

    model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(pd.DataFrame(priority_skus))

    set_session_value(SessionKeys.RECOMMENDATIONS_DATA, {
        "priority_skus": priority_skus,
        "model_color_summary": model_color_summary,
    })


def _render_order_interface() -> None:
    selected_items = get_session_value(SessionKeys.SELECTED_ORDER_ITEMS)

    if not selected_items:
        st.info(f"{Icons.INFO} {t(Keys.NO_ITEMS_SELECTED)}")
        return

    models = list({item["model"] for item in selected_items})

    if len(models) > 1:
        st.info(t(Keys.SELECT_MODEL_TO_PROCESS).format(count=len(models)))
        selected_model = st.selectbox(t(Keys.SELECT_MODEL_LABEL), options=models)
    else:
        selected_model = models[0]

    if selected_model:
        items_for_model = [item for item in selected_items if item["model"] == selected_model]
        _process_model_order(selected_model, items_for_model)


def _process_model_order(model: str, selected_items: list[dict]) -> None:
    st.subheader(t(Keys.ORDER_FOR_MODEL).format(model=model))

    pattern_set = _lookup_pattern_set(model)
    if pattern_set is None:
        logger.warning("Pattern set not found for model '%s'", model)
        st.error(f"{Icons.ERROR} {t(Keys.PATTERN_SET_NOT_FOUND).format(model=model)}")
        st.info(t(Keys.CREATE_PATTERN_SET_HINT))
        return

    st.success(f"{Icons.SUCCESS} {t(Keys.FOUND_PATTERN_SET).format(name=pattern_set.name)}")

    metadata = _load_model_metadata_for_model(model)

    col_meta, col_img = st.columns([3, 1])
    with col_meta:
        _display_model_metadata(metadata)
    with col_img:
        _display_model_image(model)

    urgent_colors = _find_urgent_colors_for_model(model)
    selected_colors = [item["color"] for item in selected_items]
    all_colors = sorted(set(selected_colors + urgent_colors))

    if urgent_colors:
        st.info(t(Keys.URGENT_COLORS).format(colors=', '.join(urgent_colors)))

    monthly_agg = _load_monthly_aggregations_cached()

    pattern_results = _get_cached_pattern_results(model, all_colors, pattern_set, monthly_agg)

    sales_history = _load_last_4_months_sales(model, all_colors, monthly_agg)

    forecast_data = _load_forecast_data_for_colors(model, all_colors)

    order_table = _create_order_summary_table(
        model, all_colors, pattern_results, sales_history, forecast_data, pattern_set
    )

    st.markdown("---")
    st.subheader(t(Keys.TITLE_ORDER_SUMMARY))

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
    render_dataframe_with_aggrid(order_table, height=400, pinned_columns=["Model", "Color"])

    _render_order_actions(model, order_table, pattern_results, metadata)

    st.markdown("---")
    _render_size_distribution_table(pattern_results, model, monthly_agg)

    st.markdown("---")
    st.subheader(t(Keys.TITLE_SIZE_COLOR_TABLE))
    stock_by_color_size = _get_stock_by_color_size(model)
    _render_size_color_table(pattern_results, pattern_set, stock_by_color_size, all_colors)

    _render_zero_stock_production_table(pattern_results, stock_by_color_size)


def _render_zero_stock_production_table(
    pattern_results: dict, stock_by_color_size: dict[tuple[str, str], int]
) -> None:
    color_aliases = load_color_aliases()
    size_alias_to_code = load_size_aliases_reverse()

    zero_stock_items = _collect_zero_stock_items(pattern_results, stock_by_color_size, color_aliases)

    if not zero_stock_items:
        return

    zero_stock_items.sort(
        key=lambda x: (x["color"], get_size_sort_key(x["size"], size_alias_to_code))
    )

    st.markdown("---")
    st.subheader(t(Keys.TITLE_ZERO_STOCK_PRODUCTION))

    df = pd.DataFrame(zero_stock_items)
    df = df.rename(columns={
        "color": "Color Code",
        "color_name": "Color",
        "size": "Size",
        "produced": "Produced Qty",
    })

    col1, _ = st.columns([1, 2])
    with col1:
        st.dataframe(df[["Color Code", "Color", "Size", "Produced Qty"]], hide_index=True)


def _collect_zero_stock_items(
    pattern_results: dict, stock_by_color_size: dict[tuple[str, str], int], color_aliases: dict
) -> list[dict]:
    items = []
    for color, result in pattern_results.items():
        for size_alias, qty in result.get("produced", {}).items():
            if qty > 0 and stock_by_color_size.get((color, size_alias), -1) == 0:
                items.append({
                    "color": color,
                    "color_name": color_aliases.get(color, color),
                    "size": size_alias,
                    "produced": qty,
                })
    return items


def _render_order_actions(model: str, order_table: pd.DataFrame, pattern_results: dict, metadata: dict) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(t(Keys.BTN_SAVE_TO_DB)):
            _save_order_to_database(model, order_table, pattern_results, metadata)
    with col2:
        csv = order_table.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            t(Keys.BTN_DOWNLOAD_ORDER_CSV),
            csv,
            f"order_{model}_{timestamp}.csv",
            MimeTypes.TEXT_CSV,
            key=f"download_order_{model}",
        )
    with col3:
        if st.button(f"{Icons.ERROR} {t(Keys.BTN_CANCEL)}"):
            st.session_state[SessionKeys.SELECTED_ORDER_ITEMS] = []
            st.session_state[SessionKeys.PATTERN_RESULTS_CACHE] = {}
            st.rerun()


def _render_size_color_table(
        pattern_results: dict, pattern_set: PatternSet, stock_by_color_size: dict[tuple[str, str], int],
        model_colors: list[str]
) -> None:
    col1, _, col3 = st.columns([2, 1, 1])
    with col1:
        filter_options = {
            "all": t(Keys.COLOR_FILTER_ALL),
            "model": t(Keys.COLOR_FILTER_MODEL),
            "active": t(Keys.COLOR_FILTER_ACTIVE),
        }
        color_filter = st.radio(
            "Colors",
            options=list(filter_options.keys()),
            format_func=lambda x: filter_options[x],
            horizontal=True,
            key="color_filter_radio"
        )
    with col3:
        scale = st.slider("Scale %", min_value=50, max_value=100, value=100, step=10, key="size_color_scale")

    active_colors = list(pattern_results.keys())
    size_color_table = _build_color_size_table(pattern_results, pattern_set, color_filter, model_colors, active_colors)

    tsv_data = size_color_table.to_csv(sep="\t", index=False)
    _render_copy_button(tsv_data)

    scale_style = f"""
    <style>
    .scaled-table {{ transform: scale({scale / 100}); transform-origin: top left; }}
    .scaled-table-container {{ overflow: auto; }}
    </style>
    """
    st.markdown(scale_style, unsafe_allow_html=True)
    st.markdown(ROTATED_TABLE_STYLE, unsafe_allow_html=True)
    html_table = _build_styled_html_table(size_color_table, stock_by_color_size)
    st.markdown(f'<div class="scaled-table-container"><div class="rotated-table scaled-table">{html_table}</div></div>', unsafe_allow_html=True)


def _render_size_distribution_table(
    pattern_results: dict,
    model: str,
    monthly_agg: pd.DataFrame | None,
) -> None:
    size_totals = _aggregate_size_totals(pattern_results)
    total_qty = sum(size_totals.values())
    if total_qty == 0:
        return

    size_alias_to_code = load_size_aliases_reverse()
    size_aliases = load_size_aliases()
    sorted_sizes = sorted(size_totals.keys(), key=lambda s: get_size_sort_key(s, size_alias_to_code))

    sales_by_month = {}
    if monthly_agg is not None:
        sales_by_month = SalesAnalyzer.get_size_sales_by_month_for_model(
            monthly_agg, model, size_aliases, months=3
        )

    df, total_pct = _build_distribution_dataframe(size_totals, sorted_sizes, total_qty, sales_by_month)

    st.subheader(t(Keys.TITLE_SIZE_DISTRIBUTION))
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(t(Keys.CAPTION_SIZE_DISTRIBUTION))
        st.dataframe(df, hide_index=True)
    with col2:
        st.metric(t(Keys.LABEL_TOTAL_QTY), total_qty)
        check_color = "green" if abs(total_pct - 100.0) < 0.1 else "red"
        st.markdown(f"**Sum: <span style='color:{check_color}'>{total_pct:.1f}%</span>**", unsafe_allow_html=True)


def _aggregate_size_totals(pattern_results: dict) -> dict[str, int]:
    size_totals: dict[str, int] = {}
    for result in pattern_results.values():
        for size, qty in result.get("produced", {}).items():
            size_totals[size] = size_totals.get(size, 0) + qty
    return size_totals


def _build_distribution_dataframe(
    size_totals: dict[str, int], sorted_sizes: list[str], total_qty: int, sales_by_month: dict
) -> tuple[pd.DataFrame, float]:
    data: dict[str, list] = {"": []}
    for size in sorted_sizes:
        data[size] = []

    data[""].append("Produced")
    for size in sorted_sizes:
        data[size].append(str(size_totals[size]))

    total_pct = 0.0
    data[""].append("%")
    for size in sorted_sizes:
        qty = size_totals[size]
        pct = (qty / total_qty) * 100
        total_pct += pct
        data[size].append(f"{pct:.1f}%")

    sorted_months = sorted(sales_by_month.keys(), reverse=True) if sales_by_month else []
    for month in sorted_months:
        month_sales = sales_by_month.get(month, {})
        data[""].append(month)
        for size in sorted_sizes:
            data[size].append(str(month_sales.get(size, 0)))

    return pd.DataFrame(data), total_pct


def _get_stock_by_color_size(model: str) -> dict[tuple[str, str], int]:
    recommendations_data = st.session_state.get(SessionKeys.RECOMMENDATIONS_DATA)
    if not recommendations_data:
        return {}

    priority_skus = recommendations_data.get("priority_skus")
    if priority_skus is None or priority_skus.empty:
        return {}

    model_skus = priority_skus[priority_skus["MODEL"] == model]
    if model_skus.empty:
        return {}

    size_aliases = load_size_aliases()
    result: dict[tuple[str, str], int] = {}
    for _, row in model_skus.iterrows():
        color = str(row.get("COLOR") or "")
        size_code = str(row.get("SIZE") or "")
        size = size_aliases.get(size_code, size_code)
        stock = int(row.get(ColumnNames.STOCK, 0) or 0)
        result[(color, size)] = stock
    return result


def _get_cell_style(
        col: str, size: str, cell_value: str,
        color_name_to_code: dict, stock_by_color_size: dict[tuple[str, str], int]
) -> str:
    if col == "Size" or not size or str(cell_value) == "":
        return ""
    color_code = color_name_to_code.get(col, col)
    stock = stock_by_color_size.get((color_code, size), -1)
    if stock == 0:
        return ' style="background-color: #ffcccc;"'
    return ""


def _build_header_row(columns: pd.Index) -> str:
    header_cells = [
        f'<th>{col}</th>' if i == 0 else f'<th><span>{col}</span></th>'
        for i, col in enumerate(columns)
    ]
    return f'<tr>{"".join(header_cells)}</tr>'


def _build_body_row(
    row: pd.Series,
    columns: pd.Index,
    color_name_to_code: dict,
    stock_by_color_size: dict[tuple[str, str], int],
) -> str:
    size = str(row.get("Size", ""))
    cells = [
        f'<td{_get_cell_style(str(col), size, str(row[col]), color_name_to_code, stock_by_color_size)}>{row[col]}</td>'
        for col in columns
    ]
    return f'<tr>{"".join(cells)}</tr>'


def _build_styled_html_table(
        df: pd.DataFrame, stock_by_color_size: dict[tuple[str, str], int]
) -> str:
    color_aliases = load_color_aliases()
    color_name_to_code = {v: k for k, v in color_aliases.items()} if color_aliases else {}

    header = _build_header_row(df.columns)
    body_rows = [
        _build_body_row(row, df.columns, color_name_to_code, stock_by_color_size)
        for _, row in df.iterrows()
    ]

    return f'<table class="rotated-table" border="0"><thead>{header}</thead><tbody>{"".join(body_rows)}</tbody></table>'


def _render_copy_button(tsv_data: str) -> None:
    from st_copy_to_clipboard import st_copy_to_clipboard
    st_copy_to_clipboard(tsv_data, t(Keys.BTN_COPY_TABLE))


def _lookup_pattern_set(model: str) -> PatternSet | None:
    pattern_sets = load_pattern_sets()
    return next((ps for ps in pattern_sets if ps.name == model), None)


def _find_urgent_colors_for_model(model: str) -> list[str]:
    recommendations_data = st.session_state.get(SessionKeys.RECOMMENDATIONS_DATA)
    if recommendations_data is None:
        return []

    model_color_summary = recommendations_data.get("model_color_summary")
    if model_color_summary is None:
        return []

    return SalesAnalyzer.find_urgent_colors(model_color_summary, model)


@st.cache_data(ttl=3600)
def _load_monthly_aggregations_cached() -> pd.DataFrame | None:
    try:
        data_source = get_data_source()
        return data_source.get_monthly_aggregations(entity_type="sku")
    except Exception as e:
        logger.warning("Could not load monthly aggregations: %s", e)
        return None


def _get_cached_pattern_results(
        model: str, colors: list[str], pattern_set: PatternSet, monthly_agg: pd.DataFrame | None
) -> dict:
    cache_key = f"{model}:{','.join(sorted(colors))}"
    cache = st.session_state.get(SessionKeys.PATTERN_RESULTS_CACHE, {})

    if cache.get("key") == cache_key and cache.get("results"):
        logger.debug("Using cached pattern results for model='%s'", model)
        return cache["results"]

    logger.info("Computing pattern results for model='%s', colors=%d", model, len(colors))
    pattern_results = {}
    for color in colors:
        result = _optimize_color_pattern(model, color, pattern_set, monthly_agg)
        pattern_results[color] = result

    st.session_state[SessionKeys.PATTERN_RESULTS_CACHE] = {
        "key": cache_key,
        "results": pattern_results,
    }
    return pattern_results


def _get_effective_min_order_for_pattern_set(pattern_set: PatternSet) -> int:
    if SessionKeys.MIN_ORDER_OVERRIDE in st.session_state:
        override = st.session_state[SessionKeys.MIN_ORDER_OVERRIDE]
        if override is not None:
            return override
    return pattern_set.get_min_order()


def _get_order_creation_size_quantities(
        priority_skus: pd.DataFrame, model: str, color: str, size_aliases: dict[str, str]
) -> dict[str, int]:
    model_color = pd.DataFrame(
        priority_skus[(priority_skus["MODEL"] == model) & (priority_skus["COLOR"] == color)]
    )
    if model_color.empty:
        return {}

    result: dict[str, int] = {}
    for _, row in model_color.iterrows():
        period_sales = int(row.get("PERIOD_SALES", 0) or 0)
        if period_sales == 0:
            continue
        stock_qty = int(row.get(ColumnNames.STOCK, 0) or 0)
        ss_value = row.get("SS", 0)
        ss = 0 if ss_value is None or (isinstance(ss_value, float) and pd.isna(ss_value)) else int(ss_value)
        order_qty = max(0, period_sales + ss - stock_qty)
        if order_qty > 0:
            size_code = str(row["SIZE"])
            alias = size_aliases.get(size_code, size_code)
            result[alias] = result.get(alias, 0) + order_qty
    return result


def _optimize_color_pattern(
        model: str, color: str, pattern_set: PatternSet, monthly_agg: pd.DataFrame | None
) -> dict:
    recommendations_data = st.session_state.get(SessionKeys.RECOMMENDATIONS_DATA)
    if not recommendations_data:
        logger.warning("No recommendations data found for model='%s', color='%s'", model, color)
        st.warning(t(Keys.NO_RECOMMENDATIONS_DATA).format(model=model, color=color))
        return _get_empty_optimization_result()

    priority_skus = recommendations_data["priority_skus"]
    size_aliases = load_size_aliases()
    min_per_pattern = _get_effective_min_order_for_pattern_set(pattern_set)
    settings = get_settings()
    algorithm_mode = settings.get("optimizer", {}).get("algorithm_mode", "greedy_overshoot")

    size_quantities_override = _get_order_creation_size_quantities(priority_skus, model, color, size_aliases)

    size_sales_history = None
    if monthly_agg is not None and not monthly_agg.empty:
        size_sales_history = SalesAnalyzer.calculate_size_sales_history(
            monthly_agg, model, color, size_aliases, months=2
        )

    return SalesAnalyzer.optimize_pattern_with_aliases(
        priority_skus, model, color, pattern_set, size_aliases, min_per_pattern, algorithm_mode,
        size_sales_history, size_quantities_override, min_sales_threshold=2,
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
    na_value = t(Keys.NA)
    labels = [
        (Keys.LABEL_PRIMARY_FACILITY, "szwalnia_glowna"),
        (Keys.LABEL_SECONDARY_FACILITY, "szwalnia_druga"),
        (Keys.LABEL_MATERIAL_TYPE, "rodzaj_materialu"),
        (Keys.LABEL_MATERIAL_WEIGHT, "gramatura"),
    ]
    cols = st.columns(len(labels))
    for col, (label_key, field) in zip(cols, labels):
        with col:
            st.metric(t(label_key), metadata.get(field, na_value) or na_value)


def _load_last_4_months_sales(
        model: str, colors: list[str], monthly_agg: pd.DataFrame | None = None
) -> pd.DataFrame:
    try:
        if monthly_agg is None:
            monthly_agg = _load_monthly_aggregations_cached()
        if monthly_agg is None or monthly_agg.empty:
            return pd.DataFrame()
        return SalesAnalyzer.get_last_n_months_sales_by_color(monthly_agg, model, colors, months=4)
    except Exception as e:
        logger.warning("Error loading sales history: %s", e)
        st.warning(t(Keys.MSG_COULD_NOT_LOAD_SALES).format(error=str(e)))
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

    pattern_lookup = {p.id: p.name for p in pattern_set.patterns}
    return ", ".join(
        f"{pattern_lookup[pid]}:{count}"
        for pid, count in sorted(allocation.items())
        if count > 0 and pid in pattern_lookup
    )


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


def _build_color_size_table(
    pattern_results: dict,
    pattern_set: PatternSet,
    color_filter: str,
    model_colors: list[str],
    active_colors: list[str]
) -> pd.DataFrame:
    color_aliases = load_color_aliases()
    size_alias_to_code = load_size_aliases_reverse()

    colors_to_show = _get_filtered_colors(color_filter, model_colors, active_colors)
    data = []

    for pattern in pattern_set.patterns:
        pattern_sizes = sorted(
            pattern.sizes.keys(),
            key=lambda s: get_size_sort_key(s, size_alias_to_code)
        )

        for size in pattern_sizes:
            row = _create_pattern_row(size, colors_to_show, color_aliases, pattern_results, pattern.id)
            data.append(row)

        empty_row = _create_empty_row(colors_to_show, color_aliases)
        data.append(empty_row)

    if data and data[-1]["Size"] == "":
        data.pop()

    return pd.DataFrame(data)


def _get_filtered_colors(color_filter: str, model_colors: list[str], active_colors: list[str]) -> list[str]:
    if color_filter == "active":
        return sorted(active_colors)
    if color_filter == "model":
        return sorted(model_colors)
    color_aliases = load_color_aliases()
    return sorted(color_aliases.keys()) if color_aliases else []


def _create_pattern_row(size: str, all_model_colors: list[str], color_aliases: dict, pattern_results: dict,
                        pattern_id: int) -> dict[str, str | int]:
    row: dict[str, str | int] = {"Size": size}
    for color in all_model_colors:
        color_name = color_aliases.get(color, color)
        pattern_count = _get_pattern_count_for_color(pattern_results, color, pattern_id)
        row[color_name] = pattern_count
    return row


def _get_pattern_count_for_color(pattern_results: dict, color: str, pattern_id: int) -> int:
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


def _build_pattern_results_data(pattern_results: dict) -> dict:
    return {
        k: {
            "allocation": v.get("allocation", {}),
            "produced": v.get("produced", {}),
            "excess": v.get("excess", {}),
            "total_patterns": v.get("total_patterns", 0),
            "total_excess": v.get("total_excess", 0),
        }
        for k, v in pattern_results.items()
    }


def _build_order_data(
    order_id: str,
    model: str,
    order_table: pd.DataFrame,
    pattern_results: dict,
    metadata: dict,
) -> dict:
    return {
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
            "pattern_results": _build_pattern_results_data(pattern_results),
            "order_table": order_table.to_dict(orient="records"),
        },
    }


def _save_order_to_database(model: str, order_table: pd.DataFrame, pattern_results: dict, metadata: dict) -> None:
    from utils.order_manager import save_order

    try:
        order_id = f"ORD_{model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        order_data = _build_order_data(order_id, model, order_table, pattern_results, metadata)
        success = save_order(order_data)

        if success:
            logger.info("Order saved: order_id='%s', model='%s'", order_id, model)
            st.success(f"{Icons.SUCCESS} {t(Keys.MSG_ORDER_SAVED).format(order_id=order_id)}")
            st.session_state[SessionKeys.SELECTED_ORDER_ITEMS] = []
            st.session_state[SessionKeys.PATTERN_RESULTS_CACHE] = {}
        else:
            logger.error("Failed to save order: order_id='%s', model='%s'", order_id, model)
            st.error(f"{Icons.ERROR} {t(Keys.MSG_ORDER_SAVE_FAILED)}")

    except Exception as e:
        logger.exception("Error saving order")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_SAVING_ORDER).format(error=str(e))}")


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_product_image_data(model: str) -> tuple[str | None, str | None]:
    from utils.product_image_fetcher import get_product_image_and_url

    return get_product_image_and_url(model)


def _display_model_image(model: str) -> None:
    image_url, product_url = _fetch_product_image_data(model)

    if image_url and product_url:
        st.markdown(
            f'<a href="{product_url}" target="_blank">'
            f'<img src="{image_url}" width="220" style="border-radius: 8px; cursor: pointer;">'
            f"</a>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("Brak obrazka")
