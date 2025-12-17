from __future__ import annotations

import traceback

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sales_data import SalesAnalyzer
from ui.constants import ColumnNames, Config, Icons, MimeTypes
from ui.shared.data_loaders import load_data, load_forecast, load_stock
from ui.shared.session_manager import get_settings
from ui.shared.sku_utils import extract_model
from ui.shared.styles import DATAFRAME_STYLE, SIDEBAR_STYLE


def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        st.error(f"{Icons.ERROR} Error in Sales Analysis: {str(e)}")
        st.code(traceback.format_exc())


def _render_content(context: dict) -> None:
    st.markdown(SIDEBAR_STYLE, unsafe_allow_html=True)
    st.title("Sales Data Analysis")

    settings = get_settings()
    group_by_model = context.get("group_by_model", False)
    use_stock = context.get("use_stock", True)
    use_forecast = context.get("use_forecast", True)

    df = load_data()
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
        st.info(f"{Icons.INFO} No stock file found. Stock-related columns will not be available.")
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
        stock_agg = stock_df.groupby("MODEL", as_index=False).agg({
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
    forecast_agg = forecast_metrics.groupby("MODEL").agg({"FORECAST_LEADTIME": "sum"}).reset_index()
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
        st.info(f"{Icons.INFO} No forecast file found. Forecast columns will not be available.")
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
        st.error(f"{Icons.ERROR} Error processing forecast data: {e}")

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
        search_label = "Search for Model:" if group_by_model else "Search for SKU:"
        search_placeholder = "Enter Model or partial Model..." if group_by_model else "Enter SKU or partial SKU..."
        search_term = st.text_input(search_label, placeholder=search_placeholder)

    with col2:
        st.write("")
        show_only_below_rop = st.checkbox("Show only below ROP", value=False) if stock_loaded else False

    with col3:
        if group_by_model:
            st.write("")
            show_bestsellers = st.checkbox("Bestsellers (>300/mo)", value=False)
        else:
            show_bestsellers = False

    with col4:
        type_filter = st.multiselect(
            "Filter by Type:",
            options=["basic", "regular", "seasonal", "new"],
            default=[],
        )

    overstock_threshold = Config.DEFAULT_OVERSTOCK_THRESHOLD
    show_overstocked = False

    if stock_loaded:
        st.markdown("**Overstocked Filter:**")
        col_over1, col_over2 = st.columns([1, 3])
        with col_over1:
            show_overstocked = st.checkbox("Show overstocked items", value=False)
        with col_over2:
            if show_overstocked:
                overstock_threshold = st.slider(
                    "Overstocked by %:", min_value=0, max_value=200, value=20, step=5
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
    item_label = "Model(s)" if group_by_model else "SKU(s)"
    st.write(f"Showing {len(filtered_summary)} of {len(summary)} {item_label}")

    st.markdown(DATAFRAME_STYLE, unsafe_allow_html=True)
    st.dataframe(filtered_summary, width="stretch", height=Config.DATAFRAME_HEIGHT)


def _render_type_metrics(display_data: pd.DataFrame) -> None:
    st.subheader("TYPE")
    type_counts = display_data["TYPE"].value_counts()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Basic", type_counts.get("basic", 0))
    col2.metric("Regular", type_counts.get("regular", 0))
    col3.metric("Seasonal", type_counts.get("seasonal", 0))
    col4.metric("New", type_counts.get("new", 0))


def _render_stock_metrics(
        display_data: pd.DataFrame,
        stock_df: pd.DataFrame | None,
        stock_loaded: bool,
) -> None:
    if not stock_loaded:
        col1, col2 = st.columns(2)
        col1.metric("Total SKUs", len(display_data))
        col2.metric("Total Quantity", f"{display_data['QUANTITY'].sum():,.0f}")
        return

    st.subheader("Stock Status")

    col1, col2, col3 = st.columns(3)

    if ColumnNames.STOCK in display_data.columns and "BELOW_ROP" in display_data.columns:
        valid_stock = display_data[display_data[ColumnNames.STOCK].notna()]
        valid_stock_count = len(valid_stock)
        below_rop_count = int(valid_stock["BELOW_ROP"].sum())

        items_below_rop = valid_stock[valid_stock["BELOW_ROP"]]
        total_deficit = items_below_rop["DEFICIT"].sum() if len(items_below_rop) > 0 else 0

        col1.metric(ColumnNames.BELOW_ROP, int(below_rop_count), delta=None, delta_color="inverse")
        col2.metric("Total Deficit (units)", f"{total_deficit:,.0f}")
        col3.metric(
            "% Below ROP",
            f"{(below_rop_count / valid_stock_count * 100):.1f}%" if valid_stock_count > 0 else "0%",
        )

        overstock_threshold = Config.DEFAULT_OVERSTOCK_THRESHOLD
        overstocked_count = int((valid_stock[ColumnNames.OVERSTOCKED_PCT] >= overstock_threshold).sum())
        normal_count = valid_stock_count - below_rop_count - overstocked_count

        pie_data = {
            "Status": [ColumnNames.BELOW_ROP, "Overstocked", "Normal"],
            "Count": [below_rop_count, overstocked_count, normal_count],
        }

        fig = px.pie(
            pie_data,
            values="Count",
            names="Status",
            title=f"Stock Status Distribution (Overstock threshold: {overstock_threshold}%)",
            color="Status",
            color_discrete_map={
                ColumnNames.BELOW_ROP: "#ff4b4b",
                "Overstocked": "#ffa500",
                "Normal": "#00cc00",
            },
        )
        fig.update_traces(textposition="inside", textinfo="percent+label+value")
        st.plotly_chart(fig, width="stretch")

    if stock_df is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total SKUs", len(display_data))
        total_stock = stock_df[ColumnNames.STOCK].sum()
        total_value = stock_df[ColumnNames.VALUE].sum()
        col2.metric("Total STOCK", f"{total_stock:,.0f}")
        col3.metric("Total Stock Value", f"{total_value:,.2f}")


def _render_download_button(display_data: pd.DataFrame, group_by_model: bool) -> None:
    download_label = "Download Model Summary CSV" if group_by_model else "Download SKU Summary CSV"
    download_filename = "model_summary.csv" if group_by_model else "sku_summary.csv"
    st.download_button(
        download_label,
        display_data.to_csv(index=False),
        download_filename,
        MimeTypes.TEXT_CSV,
        key="download_tab1_summary",
    )


def _render_stock_projection(
        summary: pd.DataFrame,
        forecast_df: pd.DataFrame,
        forecast_date: pd.Timestamp,
        id_column: str,
        group_by_model: bool,
) -> None:
    st.markdown("---")
    st.subheader("📈 Stock Projection Analysis")

    if group_by_model:
        forecast_df_copy = forecast_df.copy()
        forecast_df_copy["model"] = extract_model(forecast_df_copy["sku"])
        available_ids = sorted(
            summary[
                (summary[ColumnNames.STOCK].notna())
                & (summary["ROP"].notna())
                & (summary[id_column].isin(forecast_df_copy["model"].unique()))
                ][id_column].unique()
        )
    else:
        available_ids = sorted(
            summary[
                (summary[ColumnNames.STOCK].notna())
                & (summary["ROP"].notna())
                & (summary[id_column].isin(forecast_df["sku"].unique()))
                ][id_column].unique()
        )

    if len(available_ids) == 0:
        entity_type = "Models" if group_by_model else "SKUs"
        st.info(
            f"No {entity_type} have both stock and forecast data available. Load both datasets to use this feature."
        )
        return

    col_input, col_months = st.columns([3, 1])

    with col_input:
        input_label = "Enter Model to analyze:" if group_by_model else "Enter SKU to analyze:"
        input_placeholder = "Type Model..." if group_by_model else "Type SKU..."
        input_help = f"Enter a {'model' if group_by_model else 'SKU'} with both stock and forecast data available"
        selected_id = st.text_input(input_label, placeholder=input_placeholder, help=input_help)

    with col_months:
        projection_months = st.slider("Projection months:", min_value=1, max_value=12, value=6, step=1)

    entity_type = "Models" if group_by_model else "SKUs"
    st.caption(f"📦 {len(available_ids)} {entity_type} available with complete data")

    if not selected_id:
        return

    if selected_id not in available_ids:
        entity_name = "Model" if group_by_model else "SKU"
        st.warning(f"{Icons.WARNING} {entity_name} '{selected_id}' not found or missing stock/forecast data.")
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
        entity_name = "Model" if group_by_model else "SKU"
        st.info(f"No forecast data available for this {entity_name} in the projection window.")
        return

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=projection_df["projected_stock"],
        mode="lines+markers",
        name="Projected Stock",
        line={"color": "blue", "width": 3},
        marker={"size": 6},
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=projection_df["rop"],
        mode="lines",
        name=f"ROP ({rop:.0f})",
        line={"color": "orange", "width": 2, "dash": "dash"},
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=projection_df["safety_stock"],
        mode="lines",
        name=f"Safety Stock ({safety_stock:.0f})",
        line={"color": "yellow", "width": 2, "dash": "dot"},
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["date"],
        y=[0] * len(projection_df),
        mode="lines",
        name="Zero Stock",
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
            text="ROP Reached",
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
            text="Stockout!",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            ax=0, ay=-40,
            bgcolor="red",
            font={"color": "white"},
        )

    entity_name = "Model" if group_by_model else "SKU"
    fig.update_layout(
        title=f"Stock Projection for {entity_name} {selected_id}",
        xaxis_title="Date",
        yaxis_title="Quantity",
        hovermode="x unified",
        height=500,
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig, width="stretch")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric("Current Stock", f"{current_stock:.0f}")
    with metric_col2:
        st.metric("ROP", f"{rop:.0f}")
    with metric_col3:
        st.metric("Safety Stock", f"{safety_stock:.0f}")
    with metric_col4:
        st.metric("Avg Monthly Sales", f"{avg_sales:.0f}")

    if not rop_cross.empty:
        days_to_rop = (rop_cross.iloc[0]["date"] - forecast_date).days
        if days_to_rop <= 30:
            st.error(
                f"{Icons.WARNING} Stock will reach ROP in {days_to_rop} days ({rop_cross.iloc[0]['date'].strftime('%Y-%m-%d')})")
        else:
            st.warning(f"Stock will reach ROP in {days_to_rop} days ({rop_cross.iloc[0]['date'].strftime('%Y-%m-%d')})")

    if not zero_cross.empty:
        days_to_zero = (zero_cross.iloc[0]["date"] - forecast_date).days
        st.error(f"🚨 Stockout predicted in {days_to_zero} days ({zero_cross.iloc[0]['date'].strftime('%Y-%m-%d')})")
