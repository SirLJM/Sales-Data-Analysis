from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import ColumnNames, Config, Icons, MimeTypes
from ui.i18n import t, Keys
from ui.shared.data_loaders import load_data, load_forecast, load_stock, load_yearly_sales, load_yearly_forecast
from ui.shared.session_manager import get_settings
from ui.shared.sku_utils import extract_model
from ui.shared.styles import SIDEBAR_STYLE
from utils.logging_config import get_logger

YO_Y_ = "YoY %"

logger = get_logger("tab_sales_analysis")


def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        logger.exception("Error in Sales Analysis")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_SALES_ANALYSIS).format(error=str(e))}")


def _render_content(context: dict) -> None:
    st.markdown(SIDEBAR_STYLE, unsafe_allow_html=True)
    st.title(t(Keys.TITLE_SALES_DATA_ANALYSIS))

    settings = get_settings()
    group_by_model = context.get("group_by_model", False)
    use_stock = context.get("use_stock", True)
    use_forecast = context.get("use_forecast", True)

    df = load_data()
    logger.info("Sales data loaded: %d rows, group_by_model=%s", len(df) if df is not None else 0, group_by_model)
    analyzer = SalesAnalyzer(df)

    summary, id_column = _build_summary(analyzer, group_by_model, settings)
    seasonal_data = analyzer.determine_seasonal_months()

    stock_df, stock_df_sku_level, stock_loaded = _process_stock_data(
        summary, group_by_model, use_stock
    )

    forecast_df, forecast_date = _process_forecast_data(
        summary, group_by_model, use_forecast, settings
    )

    summary = _arrange_columns(summary, id_column, stock_loaded, group_by_model)

    filtered_summary = _render_filters(summary, id_column, group_by_model, stock_loaded)

    _render_data_table(filtered_summary, summary, group_by_model)
    _render_type_metrics(filtered_summary)
    _render_stock_metrics(filtered_summary, stock_df, stock_loaded)
    _render_download_button(filtered_summary, group_by_model)

    if stock_loaded and use_forecast and forecast_df is not None:
        _render_stock_projection(
            summary, forecast_df, forecast_date, id_column, group_by_model
        )

    _render_yearly_sales_trend()

    context["df"] = df
    context["analyzer"] = analyzer
    context["seasonal_data"] = seasonal_data
    context["stock_df"] = stock_df
    context["stock_df_sku_level"] = stock_df_sku_level
    context["stock_loaded"] = stock_loaded
    context["forecast_df"] = forecast_df
    context["forecast_date"] = forecast_date


def _build_summary(analyzer: SalesAnalyzer, group_by_model: bool, settings: dict) -> tuple[pd.DataFrame, str]:
    if group_by_model:
        summary = analyzer.aggregate_by_model()
        id_column = "MODEL"
    else:
        summary = analyzer.aggregate_by_sku()
        id_column = "SKU"

    summary = analyzer.classify_sku_type(
        summary,
        cv_basic=settings["cv_thresholds"]["basic"],
        cv_seasonal=settings["cv_thresholds"]["seasonal"],
    )

    seasonal_data = analyzer.determine_seasonal_months()
    summary = analyzer.calculate_safety_stock_and_rop(
        summary,
        seasonal_data,
        z_basic=settings["z_scores"]["basic"],
        z_regular=settings["z_scores"]["regular"],
        z_seasonal_in=settings["z_scores"]["seasonal_in"],
        z_seasonal_out=settings["z_scores"]["seasonal_out"],
        z_new=settings["z_scores"]["new"],
        lead_time_months=settings["lead_time"],
    )

    last_two_years_avg = analyzer.calculate_last_two_years_avg_sales(by_model=group_by_model)
    summary = summary.merge(last_two_years_avg, on=id_column, how="left")
    summary["LAST_2_YEARS_AVG"] = summary["LAST_2_YEARS_AVG"].fillna(0)

    return summary, id_column


def _process_stock_data(
        summary: pd.DataFrame,
        group_by_model: bool,
        use_stock: bool,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, bool]:
    if not use_stock:
        return None, None, False

    stock_df, _ = load_stock()
    if stock_df is None:
        st.info(f"{Icons.INFO} {t(Keys.MSG_NO_STOCK_FILE)}")
        return None, None, False

    stock_df = stock_df.rename(columns={
        "sku": "SKU",
        "nazwa": "DESCRIPTION",
        "available_stock": ColumnNames.STOCK,
        "cena_netto": "PRICE",
    })
    stock_df[ColumnNames.VALUE] = stock_df[ColumnNames.STOCK] * stock_df["PRICE"]

    stock_df_sku_level = stock_df[["SKU", "DESCRIPTION", ColumnNames.STOCK, "PRICE", ColumnNames.VALUE]].copy()

    if group_by_model:
        stock_df["MODEL"] = extract_model(stock_df["SKU"])
        stock_agg = stock_df.groupby("MODEL", as_index=False, observed=True).agg({
            ColumnNames.STOCK: "sum",
            ColumnNames.VALUE: "sum",
            "DESCRIPTION": "first",
        })
        summary_merged = summary.merge(stock_agg, on="MODEL", how="left")
    else:
        summary_merged = summary.merge(
            stock_df[["SKU", "DESCRIPTION", ColumnNames.STOCK, ColumnNames.VALUE]],
            on="SKU",
            how="left",
        )

    summary.update(summary_merged)
    for col in [ColumnNames.STOCK, ColumnNames.VALUE, "DESCRIPTION"]:
        if col in summary_merged.columns and col not in summary.columns:
            summary[col] = summary_merged[col]

    summary["BELOW_ROP"] = summary[ColumnNames.STOCK] < summary["ROP"]
    summary["DEFICIT"] = (summary["ROP"] - summary[ColumnNames.STOCK]).clip(lower=0)
    summary[ColumnNames.OVERSTOCKED_PCT] = (
            (summary[ColumnNames.STOCK] - summary["ROP"]) / summary["ROP"] * 100
    ).round(1)

    return stock_df, stock_df_sku_level, True


def _merge_forecast_by_model(summary: pd.DataFrame, forecast_metrics: pd.DataFrame) -> None:
    forecast_metrics["MODEL"] = extract_model(forecast_metrics["sku"])
    if "FORECAST_LEADTIME" not in forecast_metrics.columns:
        return
    forecast_agg = forecast_metrics.groupby("MODEL", observed=True).agg({"FORECAST_LEADTIME": "sum"}).reset_index()
    summary_merged = summary.merge(forecast_agg, on="MODEL", how="left")
    if "FORECAST_LEADTIME" in summary_merged.columns:
        summary["FORECAST_LEADTIME"] = summary_merged["FORECAST_LEADTIME"]


def _merge_forecast_by_sku(summary: pd.DataFrame, forecast_metrics: pd.DataFrame) -> None:
    forecast_metrics = forecast_metrics.rename(columns={"sku": "SKU"})
    if "FORECAST_LEADTIME" not in forecast_metrics.columns:
        return
    merge_cols = ["SKU", "FORECAST_LEADTIME"]
    summary_merged = summary.merge(forecast_metrics[merge_cols], on="SKU", how="left")
    if "FORECAST_LEADTIME" in summary_merged.columns:
        summary["FORECAST_LEADTIME"] = summary_merged["FORECAST_LEADTIME"]


def _process_forecast_data(
        summary: pd.DataFrame,
        group_by_model: bool,
        use_forecast: bool,
        settings: dict,
) -> tuple[pd.DataFrame | None, pd.Timestamp | None]:
    if not use_forecast:
        return None, None

    forecast_df, forecast_date, _ = load_forecast()
    if forecast_df is None:
        st.info(f"{Icons.INFO} {t(Keys.MSG_NO_FORECAST_FILE)}")
        return None, None

    try:
        forecast_metrics = SalesAnalyzer.calculate_forecast_metrics(
            forecast_df, forecast_time_months=settings["forecast_time"]
        )

        if group_by_model:
            _merge_forecast_by_model(summary, forecast_metrics)
        else:
            _merge_forecast_by_sku(summary, forecast_metrics)

        if "FORECAST_LEADTIME" in summary.columns:
            summary["FORECAST_LEADTIME"] = summary["FORECAST_LEADTIME"].fillna(0)

    except Exception as e:
        st.error(f"{Icons.ERROR} {t(Keys.MSG_ERROR_PROCESSING_FORECAST).format(error=e)}")

    return forecast_df, forecast_date


def _arrange_columns(
        summary: pd.DataFrame,
        id_column: str,
        stock_loaded: bool,
        group_by_model: bool,
) -> pd.DataFrame:
    if stock_loaded:
        if group_by_model:
            column_order = [
                id_column, "TYPE", ColumnNames.STOCK, "ROP", "SS", "FORECAST_LEADTIME",
                ColumnNames.OVERSTOCKED_PCT, "DEFICIT", "MONTHS", "QUANTITY",
                ColumnNames.AVERAGE_SALES, "LAST_2_YEARS_AVG", "CV", ColumnNames.VALUE, "BELOW_ROP",
            ]
        else:
            column_order = [
                id_column, "DESCRIPTION", "TYPE", ColumnNames.STOCK, "ROP", "SS",
                "FORECAST_LEADTIME", ColumnNames.OVERSTOCKED_PCT, "DEFICIT", "MONTHS",
                "QUANTITY", ColumnNames.AVERAGE_SALES, "LAST_2_YEARS_AVG", "CV",
                ColumnNames.VALUE, "BELOW_ROP",
            ]
    else:
        column_order = [
            id_column, "TYPE", "MONTHS", "QUANTITY", ColumnNames.AVERAGE_SALES,
            "LAST_2_YEARS_AVG", "SS", "CV", "ROP", "FORECAST_LEADTIME",
        ]

    column_order = [col for col in column_order if col in summary.columns]
    return summary[column_order]


def _render_filters(
        summary: pd.DataFrame,
        id_column: str,
        group_by_model: bool,
        stock_loaded: bool,
) -> pd.DataFrame:
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search_label = t(Keys.SEARCH_MODEL) if group_by_model else t(Keys.SEARCH_SKU)
        search_placeholder = t(Keys.SEARCH_MODEL_PLACEHOLDER) if group_by_model else t(Keys.SEARCH_SKU_PLACEHOLDER)
        with st.form("sales_search_form", clear_on_submit=False, border=False):
            form_col1, form_col2 = st.columns([4, 1])
            with form_col1:
                search_term = st.text_input(search_label, placeholder=search_placeholder, key="sales_analysis_search")
            with form_col2:
                st.form_submit_button(t(Keys.BTN_SEARCH), type="primary", use_container_width=True)

    with col2:
        st.write("")
        show_only_below_rop = st.checkbox(t(Keys.SHOW_ONLY_BELOW_ROP), value=False, key="show_below_rop") if stock_loaded else False

    with col3:
        if group_by_model:
            st.write("")
            show_bestsellers = st.checkbox(t(Keys.BESTSELLERS), value=False, key="show_bestsellers")
        else:
            show_bestsellers = False

    with col4:
        type_filter = st.multiselect(
            t(Keys.FILTER_BY_TYPE),
            options=["basic", "regular", "seasonal", "new"],
            default=[],
            key="type_filter",
        )

    overstock_threshold = Config.DEFAULT_OVERSTOCK_THRESHOLD
    show_overstocked = False

    if stock_loaded:
        st.markdown(t(Keys.OVERSTOCKED_FILTER))
        col_over1, col_over2 = st.columns([1, 3])
        with col_over1:
            show_overstocked = st.checkbox(t(Keys.SHOW_OVERSTOCKED), value=False, key="show_overstocked")
        with col_over2:
            if show_overstocked:
                overstock_threshold = st.slider(
                    t(Keys.OVERSTOCKED_BY_PCT), min_value=0, max_value=200, value=20, step=5,
                    key="overstock_threshold",
                )

    filtered = summary.copy()

    if search_term:
        filtered = filtered[
            filtered[id_column].astype(str).str.contains(search_term, case=False, na=False)
        ]

    if show_only_below_rop and "BELOW_ROP" in filtered.columns:
        filtered = filtered[filtered["BELOW_ROP"]]

    if show_bestsellers:
        filtered = filtered[filtered["LAST_2_YEARS_AVG"] > 300]

    if stock_loaded and show_overstocked and ColumnNames.OVERSTOCKED_PCT in filtered.columns:
        filtered = filtered[filtered[ColumnNames.OVERSTOCKED_PCT] >= overstock_threshold]

    if type_filter:
        filtered = filtered[filtered["TYPE"].isin(type_filter)]

    return filtered


def _render_data_table(
        filtered_summary: pd.DataFrame,
        summary: pd.DataFrame,
        group_by_model: bool,
) -> None:
    item_label = t(Keys.MODELS) if group_by_model else t(Keys.SKUS)
    st.write(t(Keys.SHOWING_N_OF_M).format(count=len(filtered_summary), total=len(summary), items=item_label))

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid

    id_col = "MODEL" if group_by_model else "SKU"
    pinned = [id_col] if id_col in filtered_summary.columns else None
    render_dataframe_with_aggrid(filtered_summary, height=Config.DATAFRAME_HEIGHT, pinned_columns=pinned)


def _render_type_metrics(display_data: pd.DataFrame) -> None:
    st.subheader(t(Keys.COL_TYPE))
    type_counts = display_data["TYPE"].value_counts()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t(Keys.TYPE_BASIC), type_counts.get("basic", 0))
    col2.metric(t(Keys.TYPE_REGULAR), type_counts.get("regular", 0))
    col3.metric(t(Keys.TYPE_SEASONAL), type_counts.get("seasonal", 0))
    col4.metric(t(Keys.TYPE_NEW), type_counts.get("new", 0))


def _render_stock_metrics(
        display_data: pd.DataFrame,
        stock_df: pd.DataFrame | None,
        stock_loaded: bool,
) -> None:
    if not stock_loaded:
        col1, col2 = st.columns(2)
        col1.metric(t(Keys.METRIC_TOTAL_SKUS), len(display_data))
        col2.metric(t(Keys.METRIC_TOTAL_QUANTITY), f"{display_data['QUANTITY'].sum():,.0f}")
        return

    st.subheader(t(Keys.TITLE_STOCK_STATUS))

    col1, col2, col3 = st.columns(3)

    if ColumnNames.STOCK in display_data.columns and "BELOW_ROP" in display_data.columns:
        valid_stock = display_data[display_data[ColumnNames.STOCK].notna()]
        valid_stock_count = len(valid_stock)
        below_rop_count = int(valid_stock["BELOW_ROP"].sum())

        items_below_rop = valid_stock[valid_stock["BELOW_ROP"]]
        total_deficit = items_below_rop["DEFICIT"].sum() if len(items_below_rop) > 0 else 0

        col1.metric(t(Keys.METRIC_BELOW_ROP), int(below_rop_count), delta=None, delta_color="inverse")
        col2.metric(t(Keys.METRIC_TOTAL_DEFICIT), f"{total_deficit:,.0f}")
        col3.metric(
            t(Keys.METRIC_PCT_BELOW_ROP),
            f"{(below_rop_count / valid_stock_count * 100):.1f}%" if valid_stock_count > 0 else "0%",
        )

        overstock_threshold = Config.DEFAULT_OVERSTOCK_THRESHOLD
        overstocked_count = int((valid_stock[ColumnNames.OVERSTOCKED_PCT] >= overstock_threshold).sum())
        normal_count = valid_stock_count - below_rop_count - overstocked_count

        pie_data = {
            "Status": [t(Keys.METRIC_BELOW_ROP), t(Keys.METRIC_OVERSTOCKED), t(Keys.METRIC_NORMAL)],
            "Count": [below_rop_count, overstocked_count, normal_count],
        }

        fig = px.pie(
            pie_data,
            values="Count",
            names="Status",
            title=t(Keys.STOCK_STATUS_DISTRIBUTION).format(threshold=overstock_threshold),
            color="Status",
            color_discrete_map={
                t(Keys.METRIC_BELOW_ROP): "#ff4b4b",
                t(Keys.METRIC_OVERSTOCKED): "#ffa500",
                t(Keys.METRIC_NORMAL): "#00cc00",
            },
        )
        fig.update_traces(textposition="inside", textinfo="percent+label+value")
        st.plotly_chart(fig)

    if stock_df is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric(t(Keys.METRIC_TOTAL_SKUS), len(display_data))
        total_stock = stock_df[ColumnNames.STOCK].sum()
        total_value = stock_df[ColumnNames.VALUE].sum()
        col2.metric(t(Keys.METRIC_TOTAL_STOCK), f"{total_stock:,.0f}")
        col3.metric(t(Keys.METRIC_TOTAL_STOCK_VALUE), f"{total_value:,.2f}")


def _render_download_button(display_data: pd.DataFrame, group_by_model: bool) -> None:
    download_label = t(Keys.DOWNLOAD_MODEL_SUMMARY) if group_by_model else t(Keys.DOWNLOAD_SKU_SUMMARY)
    download_filename = "model_summary.csv" if group_by_model else "sku_summary.csv"
    st.download_button(
        download_label,
        display_data.to_csv(index=False),
        download_filename,
        MimeTypes.TEXT_CSV,
        key="download_tab1_summary",
    )


def _get_available_ids_for_projection(
    summary: pd.DataFrame,
    forecast_df: pd.DataFrame,
    id_column: str,
    group_by_model: bool,
) -> list:
    if group_by_model:
        forecast_df_copy = forecast_df.copy()
        forecast_df_copy["model"] = extract_model(forecast_df_copy["sku"])
        forecast_ids = forecast_df_copy["model"].unique()
    else:
        forecast_ids = forecast_df["sku"].unique()

    valid_summary = summary[
        (summary[ColumnNames.STOCK].notna())
        & (summary["ROP"].notna())
        & (summary[id_column].isin(forecast_ids))
    ]
    return sorted(valid_summary[id_column].unique())


def _render_stock_projection(
        summary: pd.DataFrame,
        forecast_df: pd.DataFrame,
        forecast_date: pd.Timestamp,
        id_column: str,
        group_by_model: bool,
) -> None:
    st.markdown("---")
    st.subheader(t(Keys.TITLE_STOCK_PROJECTION))

    available_ids = _get_available_ids_for_projection(summary, forecast_df, id_column, group_by_model)
    entity_type = t(Keys.MODELS) if group_by_model else t(Keys.SKUS)

    if not available_ids:
        st.info(t(Keys.MSG_LOAD_BOTH_DATASETS).format(entity_type=entity_type))
        return

    col_input, col_months, _ = st.columns([1, 1, 2])

    with col_input:
        input_label = t(Keys.ENTER_MODEL_TO_ANALYZE) if group_by_model else t(Keys.ENTER_SKU_TO_ANALYZE)
        input_placeholder = t(Keys.SEARCH_MODEL_PLACEHOLDER) if group_by_model else t(Keys.SEARCH_SKU_PLACEHOLDER)
        with st.form("projection_search_form", clear_on_submit=False, border=False):
            form_col1, form_col2 = st.columns([3, 1])
            with form_col1:
                selected_id = st.text_input(input_label, placeholder=input_placeholder)
            with form_col2:
                st.form_submit_button(t(Keys.BTN_SEARCH), type="primary", use_container_width=True)

    with col_months:
        projection_months = st.slider(t(Keys.PROJECTION_MONTHS), min_value=1, max_value=12, value=6, step=1)

    st.caption(t(Keys.ITEMS_AVAILABLE).format(count=len(available_ids), entity_type=entity_type))

    if not selected_id:
        return

    if selected_id not in available_ids:
        st.warning(f"{Icons.WARNING} {t(Keys.MSG_NOT_FOUND).format(id=selected_id)}")
        return

    _render_projection_chart(
        summary, forecast_df, forecast_date, selected_id, id_column, group_by_model, projection_months
    )


def _render_projection_chart(
        summary: pd.DataFrame,
        forecast_df: pd.DataFrame,
        forecast_date: pd.Timestamp,
        selected_id: str,
        id_column: str,
        group_by_model: bool,
        projection_months: int,
) -> None:
    entity_data = summary[summary[id_column] == selected_id].iloc[0]
    current_stock = entity_data[ColumnNames.STOCK]
    rop = entity_data["ROP"]
    safety_stock = entity_data["SS"]
    avg_sales = entity_data[ColumnNames.AVERAGE_SALES]

    if group_by_model:
        projection_df = SalesAnalyzer.calculate_model_stock_projection(
            model=selected_id,
            current_stock=current_stock,
            rop=rop,
            safety_stock=safety_stock,
            forecast_df=forecast_df,
            start_date=forecast_date,
            projection_months=projection_months,
        )
    else:
        projection_df = SalesAnalyzer.calculate_stock_projection(
            sku=selected_id,
            current_stock=current_stock,
            rop=rop,
            safety_stock=safety_stock,
            forecast_df=forecast_df,
            start_date=forecast_date,
            projection_months=projection_months,
        )

    if projection_df.empty:
        entity_name = t(Keys.GROUP_MODEL) if group_by_model else "SKU"
        st.info(t(Keys.MSG_NO_FORECAST_DATA).format(entity=entity_name))
        return

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=projection_df["projected_stock"],
        mode="lines+markers",
        name=t(Keys.CHART_PROJECTED_STOCK),
        line={"color": "blue", "width": 3},
        marker={"size": 6},
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=projection_df["rop"],
        mode="lines",
        name=t(Keys.CHART_ROP).format(value=rop),
        line={"color": "orange", "width": 2, "dash": "dash"},
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=projection_df["safety_stock"],
        mode="lines",
        name=t(Keys.CHART_SAFETY_STOCK).format(value=safety_stock),
        line={"color": "yellow", "width": 2, "dash": "dot"},
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=[0] * len(projection_df),
        mode="lines",
        name=t(Keys.CHART_ZERO_STOCK),
        line={"color": "red", "width": 2, "dash": "dash"},
    ))

    rop_cross = projection_df[
        (projection_df["rop_reached"]) & (~projection_df["rop_reached"].shift(1, fill_value=False))
        ]
    zero_cross = projection_df[
        (projection_df["zero_reached"]) & (~projection_df["zero_reached"].shift(1, fill_value=False))
        ]

    if not rop_cross.empty:
        first_rop = rop_cross.iloc[0]
        fig.add_annotation(
            x=first_rop["date"],
            y=first_rop["projected_stock"],
            text=t(Keys.CHART_ROP_REACHED),
            showarrow=True,
            arrowhead=2,
            arrowcolor="orange",
            ax=0, ay=-40,
            bgcolor="orange",
            font={"color": "white"},
        )

    if not zero_cross.empty:
        first_zero = zero_cross.iloc[0]
        fig.add_annotation(
            x=first_zero["date"],
            y=first_zero["projected_stock"],
            text=t(Keys.CHART_STOCKOUT),
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            ax=0, ay=-40,
            bgcolor="red",
            font={"color": "white"},
        )

    entity_name = t(Keys.GROUP_MODEL) if group_by_model else "SKU"
    fig.update_layout(
        title=t(Keys.STOCK_PROJECTION_FOR).format(entity=entity_name, id=selected_id),
        xaxis_title=t(Keys.CHART_DATE),
        yaxis_title=t(Keys.CHART_QUANTITY),
        hovermode="x unified",
        height=500,
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig, width="stretch")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric(t(Keys.METRIC_CURRENT_STOCK), f"{current_stock:.0f}")
    with metric_col2:
        st.metric(t(Keys.METRIC_ROP), f"{rop:.0f}")
    with metric_col3:
        st.metric(t(Keys.METRIC_SAFETY_STOCK), f"{safety_stock:.0f}")
    with metric_col4:
        st.metric(t(Keys.METRIC_AVG_MONTHLY_SALES), f"{avg_sales:.0f}")

    if not rop_cross.empty:
        days_to_rop = (rop_cross.iloc[0]["date"] - forecast_date).days
        date_str = rop_cross.iloc[0]['date'].strftime('%Y-%m-%d')
        if days_to_rop <= 30:
            st.error(f"{Icons.WARNING} {t(Keys.WARN_ROP_IN_DAYS).format(days=days_to_rop, date=date_str)}")
        else:
            st.warning(t(Keys.WARN_ROP_IN_DAYS).format(days=days_to_rop, date=date_str))

    if not zero_cross.empty:
        days_to_zero = (zero_cross.iloc[0]["date"] - forecast_date).days
        date_str = zero_cross.iloc[0]['date'].strftime('%Y-%m-%d')
        st.error(t(Keys.ERR_STOCKOUT_IN_DAYS).format(days=days_to_zero, date=date_str))


def _render_yearly_sales_trend() -> None:
    st.markdown("---")
    st.subheader(t(Keys.TITLE_YEARLY_SALES_TREND))
    st.caption(t(Keys.YEARLY_CAPTION))

    col_mode, col_input = st.columns([1, 3])

    with col_mode:
        view_mode = st.radio(
            t(Keys.GROUP_BY),
            options=[t(Keys.GROUP_MODEL), t(Keys.GROUP_MODEL_COLOR)],
            horizontal=True,
            key="yearly_trend_view_mode"
        )

    include_color = view_mode == t(Keys.GROUP_MODEL_COLOR)
    id_col = "MODEL_COLOR" if include_color else "MODEL"

    yearly_sales = load_yearly_sales(include_color=include_color)
    yearly_forecast = load_yearly_forecast(include_color=include_color)

    available_ids = sorted(yearly_sales[id_col].unique())

    with col_input:
        input_label = t(Keys.INPUT_MODEL_COLOR) if include_color else t(Keys.INPUT_MODEL)
        with st.form("yearly_trend_form", clear_on_submit=False, border=False):
            form_col1, form_col2 = st.columns([4, 1])
            with form_col1:
                selected_id = st.text_input(
                    input_label,
                    placeholder=t(Keys.ENTER_CODE_PLACEHOLDER),
                    key="yearly_trend_input"
                )
            with form_col2:
                st.form_submit_button(t(Keys.BTN_SEARCH), type="primary", use_container_width=True)

    st.caption(t(Keys.ITEMS_AVAILABLE_SHORT).format(count=len(available_ids)))

    _render_yearly_summary_table(yearly_sales, yearly_forecast, id_col, include_color)

    if not selected_id:
        return

    selected_id = selected_id.upper()

    if selected_id not in available_ids:
        st.warning(f"{Icons.WARNING} {t(Keys.NOT_FOUND_IN_SALES).format(id=selected_id)}")
        return

    _render_yearly_trend_chart(yearly_sales, yearly_forecast, selected_id, id_col, include_color)


def _render_yearly_summary_table(
        yearly_sales: pd.DataFrame,
        yearly_forecast: pd.DataFrame | None,
        id_col: str,
        include_color: bool,
) -> None:
    from datetime import datetime
    current_year = datetime.now().year
    prev_year = current_year - 1
    prev_prev_year = current_year - 2

    summary_data = _build_yearly_summary_data(
        yearly_sales, yearly_forecast, id_col, current_year, prev_year, prev_prev_year
    )

    if summary_data.empty:
        st.info(t(Keys.NO_DATA_FOR_SUMMARY))
        return

    with st.expander(t(Keys.ALL_ITEMS_SUMMARY), expanded=False):
        col_filter, col_sort = st.columns([2, 2])

        with col_filter:
            with st.form("yearly_summary_filter_form", clear_on_submit=False, border=False):
                form_col1, form_col2 = st.columns([4, 1])
                with form_col1:
                    search_filter = st.text_input(
                        t(Keys.FILTER_BY_CODE),
                        placeholder=t(Keys.TYPE_TO_FILTER),
                        key="yearly_summary_filter"
                    )
                with form_col2:
                    st.form_submit_button(t(Keys.BTN_SEARCH), type="primary", use_container_width=True)

        with col_sort:
            sort_options = [
                f"{prev_year} Sales (desc)",
                f"{prev_year} Sales (asc)",
                "YoY Change % (desc)",
                "YoY Change % (asc)",
                "Forecast (desc)",
            ]
            sort_by = st.selectbox(t(Keys.SORT_BY), options=sort_options, key="yearly_summary_sort")

        filtered_data = summary_data.copy()
        if search_filter:
            filtered_data = filtered_data[
                filtered_data[id_col].str.contains(search_filter.upper(), na=False)
            ]

        filtered_data = _sort_yearly_summary(filtered_data, sort_by, prev_year)

        st.dataframe(
            filtered_data,
            width='stretch',
            hide_index=True,
            height=400,
        )

        csv_data = filtered_data.to_csv(index=False)
        entity_label = "model_color" if include_color else "model"
        st.download_button(
            label=t(Keys.BTN_DOWNLOAD_CSV),
            data=csv_data,
            file_name=f"yearly_sales_{entity_label}.csv",
            mime=MimeTypes.TEXT_CSV,
        )


def _get_year_column(pivot: pd.DataFrame, year: int) -> pd.Series:
    if year in pivot.columns:
        return pivot[year].astype(int)
    return pd.Series([0] * len(pivot), index=pivot.index)


def _add_forecast_column(summary: pd.DataFrame, yearly_forecast: pd.DataFrame | None, id_col: str) -> pd.DataFrame:
    if yearly_forecast is None or yearly_forecast.empty:
        summary["Forecast"] = 0
        return summary

    forecast_agg = yearly_forecast.groupby(id_col, observed=True)["QUANTITY"].sum().reset_index()
    forecast_agg.columns = [id_col, "Forecast"]
    forecast_agg["Forecast"] = forecast_agg["Forecast"].astype(int)
    summary = summary.merge(forecast_agg, on=id_col, how="left", validate="many_to_many")
    summary["Forecast"] = summary["Forecast"].fillna(0).astype(int)
    return summary


def _build_yearly_summary_data(
        yearly_sales: pd.DataFrame,
        yearly_forecast: pd.DataFrame | None,
        id_col: str,
        current_year: int,
        prev_year: int,
        prev_prev_year: int,
) -> pd.DataFrame:
    pivot = yearly_sales.pivot_table(
        index=id_col,
        columns="YEAR",
        values="QUANTITY",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    summary = pd.DataFrame({
        id_col: pivot[id_col],
        str(prev_prev_year): _get_year_column(pivot, prev_prev_year),
        str(prev_year): _get_year_column(pivot, prev_year),
        f"{current_year} YTD": _get_year_column(pivot, current_year),
    })

    summary[YO_Y_] = summary.apply(
        lambda row: _calc_yoy_change(row[str(prev_prev_year)], row[str(prev_year)]),
        axis=1
    )

    return _add_forecast_column(summary, yearly_forecast, id_col)


def _calc_yoy_change(prev_val: float, curr_val: float) -> float:
    if prev_val > 0:
        return round(((curr_val - prev_val) / prev_val) * 100, 1)
    return 100.0 if curr_val > 0 else 0.0


def _sort_yearly_summary(data: pd.DataFrame, sort_by: str, prev_year: int) -> pd.DataFrame:
    prev_year_col = str(prev_year)

    sort_configs = {
        "Sales (desc)": (prev_year_col, False),
        "Sales (asc)": (prev_year_col, True),
        "YoY Change % (desc)": (YO_Y_, False),
        "YoY Change % (asc)": (YO_Y_, True),
        "Forecast (desc)": ("Forecast", False),
    }

    for pattern, (col, ascending) in sort_configs.items():
        if pattern in sort_by:
            return data.sort_values(col, ascending=ascending)

    return data


def _render_yearly_trend_chart(
        yearly_sales: pd.DataFrame,
        yearly_forecast: pd.DataFrame | None,
        selected_id: str,
        id_col: str,
        include_color: bool,
) -> None:
    from datetime import datetime
    current_year = datetime.now().year

    sales_data = yearly_sales[yearly_sales[id_col] == selected_id].copy()
    sales_data = sales_data.sort_values("YEAR")

    if yearly_forecast is not None:
        forecast_data = yearly_forecast[yearly_forecast[id_col] == selected_id].copy()
        forecast_data = forecast_data[forecast_data["YEAR"] >= current_year]
        forecast_data = forecast_data.groupby("YEAR", as_index=False, observed=True).agg({"QUANTITY": "sum"})
    else:
        forecast_data = pd.DataFrame(columns=["YEAR", "QUANTITY"])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=sales_data["YEAR"],
        y=sales_data["QUANTITY"],
        name=t(Keys.CHART_HISTORICAL_SALES),
        marker={"color": "#1f77b4"},
        text=sales_data["QUANTITY"].round(0).astype(int),
        textposition="outside",
    ))

    if not forecast_data.empty:
        fig.add_trace(go.Bar(
            x=forecast_data["YEAR"],
            y=forecast_data["QUANTITY"],
            name=t(Keys.CHART_FORECAST),
            marker={"color": "#ff7f0e"},
            text=forecast_data["QUANTITY"].round(0).astype(int),
            textposition="outside",
            opacity=0.7,
        ))

    entity_label = t(Keys.GROUP_MODEL_COLOR) if include_color else t(Keys.GROUP_MODEL)
    fig.update_layout(
        title=t(Keys.YEARLY_SALES_TREND_FOR).format(entity=entity_label, id=selected_id),
        xaxis_title=t(Keys.CHART_YEAR),
        yaxis_title=t(Keys.CHART_QUANTITY_SOLD),
        barmode="group",
        hovermode="x unified",
        height=450,
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        xaxis={"tickmode": "linear", "dtick": 1},
    )

    st.plotly_chart(fig, width='stretch')

    _render_trend_metrics(sales_data, forecast_data)


def _render_trend_metrics(
        sales_data: pd.DataFrame,
        forecast_data: pd.DataFrame,
) -> None:
    col1, col2, col3, col4 = st.columns(4)

    first_year = int(sales_data["YEAR"].min()) if not sales_data.empty else None
    total_historical = int(sales_data["QUANTITY"].sum()) if not sales_data.empty else 0
    years_active = len(sales_data) if not sales_data.empty else 0

    with col1:
        st.metric(t(Keys.METRIC_FIRST_SALE_YEAR), first_year if first_year else "N/A")
    with col2:
        st.metric(t(Keys.METRIC_YEARS_ACTIVE), years_active)
    with col3:
        st.metric(t(Keys.METRIC_TOTAL_HISTORICAL_SALES), f"{total_historical:,}")

    if not forecast_data.empty:
        forecast_qty = int(forecast_data["QUANTITY"].sum())
        with col4:
            st.metric(t(Keys.METRIC_FORECAST_FUTURE), f"{forecast_qty:,}")

    if len(sales_data) >= 2:
        recent_years = sales_data.tail(2).reset_index(drop=True)
        prev_year = int(recent_years.loc[0, "YEAR"])
        last_year = int(recent_years.loc[1, "YEAR"])
        if last_year - prev_year == 1:
            prev_year_qty = float(recent_years.loc[0, "QUANTITY"])
            last_year_qty = float(recent_years.loc[1, "QUANTITY"])
            if prev_year_qty > 0:
                yoy_change = ((last_year_qty - prev_year_qty) / prev_year_qty) * 100
                trend_icon, trend_color = _get_trend_indicator(yoy_change)
                st.markdown(
                    f"**{t(Keys.YOY_TREND).format(prev=prev_year, curr=last_year)}** {trend_icon} "
                    f"<span style='color:{trend_color}'>{yoy_change:+.1f}%</span> "
                    f"({int(prev_year_qty):,} → {int(last_year_qty):,})",
                    unsafe_allow_html=True
                )


def _get_trend_indicator(yoy_change: float) -> tuple[str, str]:
    if yoy_change > 0:
        return "📈", "green"
    if yoy_change < 0:
        return "📉", "red"
    return "➡️", "gray"
