import pandas as pd
import plotly.express as px
import streamlit as st

from sales_data import SalesAnalyzer
from sales_data.data_source_factory import DataSourceFactory
from utils.pattern_optimizer_logic import (
    Pattern,
    PatternSet,
    get_min_order_per_pattern,
    load_pattern_sets,
    optimize_patterns,
    save_pattern_sets,
)
from utils.settings_manager import load_settings, reset_settings, save_settings

SIZE_QTY = "Sizes (Size:Qty)"

MODEL_COLOR = "MODEL+COLOR"

LAST_WEEK = "Last Week"

TEXT_CSV = "text/csv"

MATERIAL = "RODZAJ MATERIAŁU"

SZWALNIA_D = "SZWALNIA DRUGA"

SZWALNIA_G = "SZWALNIA GŁÓWNA"

BELOW_ROP = "Below ROP"

AVERAGE_SALES = "AVERAGE SALES"

OVERSTOCKED__ = "OVERSTOCKED_%"

st.set_page_config(page_title="Inventory & Pattern Optimizer", page_icon="📊", layout="wide")

if "settings" not in st.session_state:
    st.session_state.settings = load_settings()


def display_optimization_metrics(optimization_result: dict):
    met_col1, met_col2, met_col3 = st.columns(3)
    with met_col1:
        st.metric("Total Patterns", optimization_result["total_patterns"])
    with met_col2:
        st.metric("Total Excess", optimization_result["total_excess"])
    with met_col3:
        coverage_icon = "✅" if optimization_result["all_covered"] else "❌"
        st.metric("Coverage", coverage_icon)


def display_star_product(star: dict, stock_data: pd.DataFrame, is_rising: bool):
    product_model = star["model"]

    desc = ""
    if stock_data is not None:
        stock_df_copy = stock_data.copy()
        stock_df_copy["model"] = stock_df_copy["sku"].astype(str).str[:5]
        model_desc = stock_df_copy[stock_df_copy["model"] == product_model]
        if not model_desc.empty:
            desc = model_desc.iloc[0]["nazwa"]

    st.markdown(f"**Model:** {product_model}")
    if desc:
        st.caption(desc)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(LAST_WEEK, f"{int(star['current_week_sales']):,}")
    with m2:
        st.metric("Last Year", f"{int(star['prev_year_sales']):,}")
    with m3:
        sign = "+" if is_rising else ""
        st.metric(
            "Change",
            f"{sign}{int(star['difference']):,}",
            delta=f"{sign}{star['percent_change']:.1f}%",
        )


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Sales & Inventory Analysis",
        "📦 Size Pattern Optimizer",
        "🎯 Order Recommendations",
        "📅 Weekly Analysis",
        "📋 Order Creation",
    ]
)

# ========================================
# TAB 1: SALES & INVENTORY ANALYSIS
# ========================================

with tab1:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 380px;
            max-width: 380px;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Sales Data Analysis")

    # -----------SIDEBAR-------------

    st.sidebar.header("Parameters")

    col_save, col_reset = st.sidebar.columns(2)
    with col_save:
        if st.button(
                "💾 Save", key="save_settings", help="Save current parameters to settings.json"
        ):
            if save_settings(st.session_state.settings):
                st.success("✅ Saved!")
            else:
                st.error("❌ Save failed")
    with col_reset:
        if st.button("🔄 Reset", key="reset_settings", help="Reset to default values"):
            st.session_state.settings = reset_settings()
            st.rerun()

    st.sidebar.subheader("Lead Time & Forecast")

    lead_time = st.sidebar.number_input(
        "Lead time in months",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.settings["lead_time"],
        step=0.01,
        format="%.2f",
        key="lead_time_input",
        help="Time between order placement and receipt (used in ROP and SS calculations)"
    )
    st.session_state.settings["lead_time"] = lead_time

    sync_forecast = st.sidebar.checkbox(
        "Sync forecast time with lead time",
        value=st.session_state.settings["sync_forecast_with_lead_time"],
        key="sync_forecast_checkbox",
        help="When enabled, forecast time automatically matches lead time"
    )
    st.session_state.settings["sync_forecast_with_lead_time"] = sync_forecast

    if sync_forecast:
        forecast_time = lead_time
        st.session_state.settings["forecast_time"] = lead_time
    else:
        forecast_time = st.sidebar.number_input(
            "Forecast time in months",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.settings["forecast_time"]),
            step=0.01,
            format="%.2f",
            key="forecast_time_input",
            help="Time period for forecast calculations (independent of lead time when sync is off)"
        )
        st.session_state.settings["forecast_time"] = forecast_time

    st.sidebar.subheader("Service Levels")
    header_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with header_cols[0]:
        st.write("Type")
    with header_cols[1]:
        st.write("CV")
    with header_cols[2]:
        st.write("Z-Score")
    with header_cols[3]:
        st.write("Z-Score")

    basic_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with basic_cols[0]:
        st.write("Basic")
    with basic_cols[1]:
        service_basic = st.number_input(
            "CV",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.settings["cv_thresholds"]["basic"],
            step=0.1,
            format="%.1f",
            key="basic_cv",
        )
        st.session_state.settings["cv_thresholds"]["basic"] = service_basic
    with basic_cols[2]:
        z_score_basic = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state.settings["z_scores"]["basic"],
            step=0.001,
            format="%.3f",
            key="basic_z",
        )
        st.session_state.settings["z_scores"]["basic"] = z_score_basic
    with basic_cols[3]:
        st.write("-")

    regular_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with regular_cols[0]:
        st.write("Regular")
    with regular_cols[1]:
        st.write("-")
    with regular_cols[2]:
        z_score_regular = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state.settings["z_scores"]["regular"],
            step=0.001,
            format="%.3f",
        )
        st.session_state.settings["z_scores"]["regular"] = z_score_regular
    with regular_cols[3]:
        st.write("-")

    seasonal_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with seasonal_cols[0]:
        st.write("Seasonal")
    with seasonal_cols[1]:
        service_seasonal = st.number_input(
            "CV",
            label_visibility="collapsed",
            min_value=service_basic,
            max_value=10.0,
            value=st.session_state.settings["cv_thresholds"]["seasonal"],
            step=0.1,
            format="%.1f",
            key="seasonal_cv",
        )
        st.session_state.settings["cv_thresholds"]["seasonal"] = service_seasonal
    with seasonal_cols[2]:
        z_score_seasonal_1 = st.number_input(
            "Z-Score IN season",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state.settings["z_scores"]["seasonal_in"],
            step=0.001,
            format="%.3f",
            key="seasonal_z1",
            placeholder="IN season",
        )
        st.session_state.settings["z_scores"]["seasonal_in"] = z_score_seasonal_1
    with seasonal_cols[3]:
        z_score_seasonal_2 = st.number_input(
            "Z-Score OUT of season",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state.settings["z_scores"]["seasonal_out"],
            step=0.001,
            format="%.3f",
            key="seasonal_z2",
            placeholder="OUT of season",
        )
        st.session_state.settings["z_scores"]["seasonal_out"] = z_score_seasonal_2

    service_regular_min = service_basic
    service_regular_max = service_seasonal

    new_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with new_cols[0]:
        st.write("New")
    with new_cols[1]:
        service_new = st.number_input(
            "CV",
            label_visibility="collapsed",
            min_value=12,
            max_value=24,
            value=st.session_state.settings["new_product_threshold_months"],
            step=1,
            key="new_cv",
        )
        st.session_state.settings["new_product_threshold_months"] = service_new
    with new_cols[2]:
        z_score_new = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state.settings["z_scores"]["new"],
            step=0.001,
            format="%.3f",
            key="new_z",
        )
        st.session_state.settings["z_scores"]["new"] = z_score_new
    with new_cols[3]:
        st.write("-")

    st.sidebar.markdown("---")
    st.sidebar.write("**Current Parameters:**")
    st.sidebar.write(f"Lead Time: {lead_time} months")
    if sync_forecast:
        st.sidebar.write(f"Forecast Time: {forecast_time} months (synced with lead time)")
    else:
        st.sidebar.write(f"Forecast Time: {forecast_time} months")
    st.sidebar.write(f"Basic: CV < {service_basic} : Z-Score = {z_score_basic}")
    st.sidebar.write(
        f"Regular: {service_regular_min} ≤ CV ≤ {service_regular_max} : Z-Score = {z_score_regular}"
    )
    st.sidebar.write(
        f"Seasonal: CV > {service_seasonal} : Z-Score IN season = {z_score_seasonal_1}, Z-Score OUT of season = {z_score_seasonal_2}"
    )
    st.sidebar.write(f"New: months < {service_new} : Z-Score = {z_score_new}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("View Options")
    group_by_model = st.sidebar.checkbox("Group by Model (first 5 chars)", value=False)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Load additional data")
    use_stock = st.sidebar.checkbox("Load stock data from data directory", value=True)
    use_forecast = st.sidebar.checkbox("Load forecast data from data directory", value=True)


    # -----------END OF SIDEBAR-------------

    def get_data_source():
        if "data_source" not in st.session_state:
            st.session_state.data_source = DataSourceFactory.create_data_source()
        return st.session_state.data_source


    @st.cache_data
    def load_data():
        data_source = get_data_source()
        return data_source.load_sales_data()


    @st.cache_data
    def load_stock():
        data_source = get_data_source()
        stock_dataframe = data_source.load_stock_data()
        if stock_dataframe is not None and not stock_dataframe.empty:
            return stock_dataframe, (
                "database" if data_source.get_data_source_type() == "database" else "file"
            )
        return None, None


    @st.cache_data
    def load_forecast():
        data_source = get_data_source()
        forecast_dataframe = data_source.load_forecast_data()
        if forecast_dataframe is not None and not forecast_dataframe.empty:
            if "generated_date" in forecast_dataframe.columns:
                loaded_forecast_date = forecast_dataframe["generated_date"].iloc[0]
                if loaded_forecast_date is not None and not isinstance(
                        loaded_forecast_date, pd.Timestamp
                ):
                    loaded_forecast_date = pd.Timestamp(loaded_forecast_date)
            else:
                loaded_forecast_date = None
            source_name = "database" if data_source.get_data_source_type() == "database" else "file"
            return forecast_dataframe, loaded_forecast_date, source_name
        return None, None, None


    @st.cache_data
    def load_model_metadata():
        data_source = get_data_source()
        return data_source.load_model_metadata()


    df = load_data()
    analyzer = SalesAnalyzer(df)

    if group_by_model:
        summary = analyzer.aggregate_by_model()
        id_column = "MODEL"
    else:
        summary = analyzer.aggregate_by_sku()
        id_column = "SKU"

    summary = analyzer.classify_sku_type(
        summary, cv_basic=service_basic, cv_seasonal=service_seasonal
    )

    seasonal_data = analyzer.determine_seasonal_months()

    summary = analyzer.calculate_safety_stock_and_rop(
        summary,
        seasonal_data,
        z_basic=z_score_basic,
        z_regular=z_score_regular,
        z_seasonal_in=z_score_seasonal_1,
        z_seasonal_out=z_score_seasonal_2,
        z_new=z_score_new,
        lead_time_months=lead_time,
    )

    last_two_years_avg = analyzer.calculate_last_two_years_avg_sales(by_model=group_by_model)
    summary = summary.merge(last_two_years_avg, on=id_column, how="left")
    summary["LAST_2_YEARS_AVG"] = summary["LAST_2_YEARS_AVG"].fillna(0)

    stock_loaded = False
    stock_df = None
    if use_stock:
        stock_df, stock_filename = load_stock()

        if stock_df is not None:
            stock_df = stock_df.rename(
                columns={
                    "sku": "SKU",
                    "nazwa": "DESCRIPTION",
                    "available_stock": "STOCK",
                    "cena_netto": "PRICE",
                }
            )

            stock_df["VALUE"] = stock_df["STOCK"] * stock_df["PRICE"]

            if group_by_model:
                stock_df["MODEL"] = stock_df["SKU"].astype(str).str[:5]
                stock_agg = stock_df.groupby("MODEL", as_index=False).agg(
                    {"STOCK": "sum", "VALUE": "sum", "DESCRIPTION": "first"}
                )
                summary = summary.merge(stock_agg, on="MODEL", how="left")
            else:
                summary = summary.merge(
                    stock_df[["SKU", "DESCRIPTION", "STOCK", "VALUE"]], on="SKU", how="left"
                )

            summary["BELOW_ROP"] = summary["STOCK"] < summary["ROP"]
            summary["DEFICIT"] = summary["ROP"] - summary["STOCK"]
            summary["DEFICIT"] = summary["DEFICIT"].apply(lambda x: max(0, x))
            summary[OVERSTOCKED__] = (
                    (summary["STOCK"] - summary["ROP"]) / summary["ROP"] * 100
            ).round(1)

            stock_loaded = True
        else:
            st.info("ℹ️ No stock file found. Stock-related columns will not be available.")

    if use_forecast:
        forecast_df, forecast_date, forecast_filename = load_forecast()
        if forecast_df is not None:
            try:
                forecast_metrics = SalesAnalyzer.calculate_forecast_metrics(
                    forecast_df, forecast_time_months=st.session_state.settings["forecast_time"]
                )

                if group_by_model:
                    forecast_metrics["MODEL"] = forecast_metrics["sku"].astype(str).str[:5]
                    agg_dict = {}
                    if "FORECAST_LEADTIME" in forecast_metrics.columns:
                        agg_dict["FORECAST_LEADTIME"] = "sum"
                    if agg_dict:
                        forecast_agg = (
                            forecast_metrics.groupby("MODEL")
                            .agg(agg_dict)
                            .reset_index()
                        )
                        summary = summary.merge(forecast_agg, on="MODEL", how="left")
                else:
                    forecast_metrics = forecast_metrics.rename(columns={"sku": "SKU"})
                    merge_cols = ["SKU"]
                    if "FORECAST_LEADTIME" in forecast_metrics.columns:
                        merge_cols.append("FORECAST_LEADTIME")
                    summary = summary.merge(
                        forecast_metrics[merge_cols],
                        on="SKU",
                        how="left",
                    )

                if "FORECAST_LEADTIME" in summary.columns:
                    summary["FORECAST_LEADTIME"] = summary["FORECAST_LEADTIME"].fillna(0)

            except Exception as e:
                st.error(f"❌ Error processing forecast data: {e}")
        else:
            st.info("ℹ️ No forecast file found. Forecast columns will not be available.")

    if stock_loaded:
        if group_by_model:
            column_order = [
                id_column,
                "TYPE",
                "STOCK",
                "ROP",
                "SS",
                "FORECAST_LEADTIME",
                OVERSTOCKED__,
                "DEFICIT",
                "MONTHS",
                "QUANTITY",
                AVERAGE_SALES,
                "LAST_2_YEARS_AVG",
                "CV",
                "VALUE",
                "BELOW_ROP",
            ]
        else:
            column_order = [
                id_column,
                "DESCRIPTION",
                "TYPE",
                "STOCK",
                "ROP",
                "SS",
                "FORECAST_LEADTIME",
                OVERSTOCKED__,
                "DEFICIT",
                "MONTHS",
                "QUANTITY",
                AVERAGE_SALES,
                "LAST_2_YEARS_AVG",
                "CV",
                "VALUE",
                "BELOW_ROP",
            ]
    else:
        column_order = [
            id_column,
            "TYPE",
            "MONTHS",
            "QUANTITY",
            AVERAGE_SALES,
            "LAST_2_YEARS_AVG",
            "SS",
            "CV",
            "ROP",
            "FORECAST_LEADTIME",
        ]

    column_order = [col for col in column_order if col in summary.columns]
    summary = summary[column_order]

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search_label = "Search for Model:" if group_by_model else "Search for SKU:"
        search_placeholder = (
            "Enter Model or partial Model..." if group_by_model else "Enter SKU or partial SKU..."
        )
        search_term = st.text_input(search_label, placeholder=search_placeholder)
    with col2:
        st.space("small")
        if stock_loaded:
            show_only_below_rop = st.checkbox("Show only below ROP", value=False)
        else:
            show_only_below_rop = False
    with col3:
        if group_by_model:
            st.space("small")
            show_bestsellers = st.checkbox("Bestsellers (>300/mo)", value=False)
        else:
            show_bestsellers = False
    with col4:
        type_filter = st.multiselect(
            "Filter by Type:", options=["basic", "regular", "seasonal", "new"], default=[]
        )

    overstock_threshold = 20
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

    filtered_summary = summary.copy()

    if search_term:
        filtered_summary = filtered_summary[
            filtered_summary[id_column].astype(str).str.contains(search_term, case=False, na=False)
        ]

    if show_only_below_rop and "BELOW_ROP" in filtered_summary.columns:
        filtered_summary = filtered_summary[filtered_summary["BELOW_ROP"]]

    if show_bestsellers:
        filtered_summary = filtered_summary[filtered_summary["LAST_2_YEARS_AVG"] > 300]

    if stock_loaded and show_overstocked and OVERSTOCKED__ in filtered_summary.columns:
        filtered_summary = filtered_summary[filtered_summary[OVERSTOCKED__] >= overstock_threshold]

    if type_filter:
        filtered_summary = filtered_summary[filtered_summary["TYPE"].isin(type_filter)]

    item_label = "Model(s)" if group_by_model else "SKU(s)"
    st.write(f"Showing {len(filtered_summary)} of {len(summary)} {item_label}")

    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 95%; !important;
            padding-left: 2rem; !important;
            padding-right: 2rem; !important;
        }
        section[data-testid="stDataFrame"] {
            width: 100%; !important;
        }
        div[data-testid="stDataFrame"] > div {
            width: 100%; !important;
            max-width: 100%; !important;
        }
        div[data-testid="stDataFrame"] iframe {
            width: 100%; !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.dataframe(filtered_summary, width="stretch", height=600)

    st.subheader("TYPE")
    display_data = filtered_summary
    type_counts = display_data["TYPE"].value_counts()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Basic", type_counts.get("basic", 0))
    col2.metric("Regular", type_counts.get("regular", 0))
    col3.metric("Seasonal", type_counts.get("seasonal", 0))
    col4.metric("New", type_counts.get("new", 0))

    if stock_loaded:
        st.subheader("Stock Status")

        col1, col2, col3 = st.columns(3)
        below_rop_count = 0
        total_deficit = 0
        valid_stock_count = 0

        if "STOCK" in display_data.columns and "BELOW_ROP" in display_data.columns:
            valid_stock = display_data[display_data["STOCK"].notna()]
            valid_stock_count = len(valid_stock)
            below_rop_count = int(valid_stock["BELOW_ROP"].sum())

            items_below_rop = valid_stock[valid_stock["BELOW_ROP"]]
            total_deficit = items_below_rop["DEFICIT"].sum() if len(items_below_rop) > 0 else 0

            col1.metric(BELOW_ROP, int(below_rop_count), delta=None, delta_color="inverse")
            col2.metric("Total Deficit (units)", f"{total_deficit:,.0f}")
            col3.metric(
                "% Below ROP",
                (
                    f"{(below_rop_count / valid_stock_count * 100):.1f}%"
                    if valid_stock_count > 0
                    else "0%"
                ),
            )

            overstocked_count = int((valid_stock[OVERSTOCKED__] >= overstock_threshold).sum())
            normal_count = valid_stock_count - below_rop_count - overstocked_count

            pie_data = {
                "Status": [BELOW_ROP, "Overstocked", "Normal"],
                "Count": [below_rop_count, overstocked_count, normal_count],
            }

            fig = px.pie(
                pie_data,
                values="Count",
                names="Status",
                title=f"Stock Status Distribution (Overstock threshold: {overstock_threshold}%)",
                color="Status",
                color_discrete_map={
                    BELOW_ROP: "#ff4b4b",
                    "Overstocked": "#ffa500",
                    "Normal": "#00cc00",
                },
            )
            fig.update_traces(textposition="inside", textinfo="percent+label+value")
            st.plotly_chart(fig, width="stretch")

    if stock_loaded and stock_df is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total SKUs", len(display_data))
        total_stock = stock_df["STOCK"].sum()
        total_value = stock_df["VALUE"].sum()
        col2.metric("Total STOCK", f"{total_stock:,.0f}")
        col3.metric("Total Stock Value", f"{total_value:,.2f}")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Total SKUs", len(display_data))
        col2.metric("Total Quantity", f"{display_data['QUANTITY'].sum():,.0f}")

    download_label = "Download Model Summary CSV" if group_by_model else "Download SKU Summary CSV"
    download_filename = "model_summary.csv" if group_by_model else "sku_summary.csv"
    st.download_button(
        download_label,
        display_data.to_csv(index=False),
        download_filename,
        TEXT_CSV,
        key="download_tab1_summary"
    )

    if stock_loaded and use_forecast and forecast_df is not None:
        st.markdown("---")
        st.subheader("📈 Stock Projection Analysis")

        if group_by_model:
            forecast_df_copy = forecast_df.copy()
            forecast_df_copy["model"] = forecast_df_copy["sku"].astype(str).str[:5]
            available_ids = sorted(
                summary[
                    (summary["STOCK"].notna())
                    & (summary["ROP"].notna())
                    & (summary[id_column].isin(forecast_df_copy["model"].unique()))
                    ][id_column].unique()
            )
        else:
            available_ids = sorted(
                summary[
                    (summary["STOCK"].notna())
                    & (summary["ROP"].notna())
                    & (summary[id_column].isin(forecast_df["sku"].unique()))
                    ][id_column].unique()
            )

        if len(available_ids) > 0:
            col_input, col_months = st.columns([3, 1])

            with col_input:
                input_label = "Enter Model to analyze:" if group_by_model else "Enter SKU to analyze:"
                input_placeholder = "Type Model..." if group_by_model else "Type SKU..."
                input_help = f"Enter a {'model' if group_by_model else 'SKU'} with both stock and forecast data available"

                selected_id = st.text_input(
                    input_label,
                    placeholder=input_placeholder,
                    help=input_help,
                )

            with col_months:
                projection_months = st.slider(
                    "Projection months:", min_value=1, max_value=12, value=6, step=1
                )

            entity_type = "Models" if group_by_model else "SKUs"
            st.caption(f"📦 {len(available_ids)} {entity_type} available with complete data")

            if selected_id:
                if selected_id not in available_ids:
                    entity_name = "Model" if group_by_model else "SKU"
                    st.warning(f"⚠️ {entity_name} '{selected_id}' not found or missing stock/forecast data.")
                else:
                    entity_data = summary[summary[id_column] == selected_id].iloc[0]
                    current_stock = entity_data["STOCK"]
                    rop = entity_data["ROP"]
                    safety_stock = entity_data["SS"]
                    avg_sales = entity_data[AVERAGE_SALES]

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

                    if not projection_df.empty:
                        import plotly.graph_objects as go

                        fig = go.Figure()

                        fig.add_trace(
                            go.Scatter(
                                x=projection_df["date"],
                                y=projection_df["projected_stock"],
                                mode="lines+markers",
                                name="Projected Stock",
                                line={"color": "blue", "width": 3},
                                marker={"size": 6},
                            )
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=projection_df["date"],
                                y=projection_df["rop"],
                                mode="lines",
                                name=f"ROP ({rop:.0f})",
                                line={"color": "orange", "width": 2, "dash": "dash"},
                            )
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=projection_df["date"],
                                y=projection_df["safety_stock"],
                                mode="lines",
                                name=f"Safety Stock ({safety_stock:.0f})",
                                line={"color": "yellow", "width": 2, "dash": "dot"},
                            )
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=projection_df["date"],
                                y=[0] * len(projection_df),
                                mode="lines",
                                name="Zero Stock",
                                line={"color": "red", "width": 2, "dash": "dash"},
                            )
                        )

                        rop_cross = projection_df[
                            (projection_df["rop_reached"])
                            & (~projection_df["rop_reached"].shift(1, fill_value=False))
                            ]
                        zero_cross = projection_df[
                            (projection_df["zero_reached"])
                            & (~projection_df["zero_reached"].shift(1, fill_value=False))
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
                                ax=0,
                                ay=-40,
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
                                ax=0,
                                ay=-40,
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
                            legend={
                                "orientation": "h",
                                "yanchor": "bottom",
                                "y": 1.02,
                                "xanchor": "right",
                                "x": 1,
                            },
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
                                    f"⚠️ Stock will reach ROP in {days_to_rop} days ({rop_cross.iloc[0]['date'].strftime('%Y-%m-%d')})"
                                )
                            else:
                                st.warning(
                                    f"Stock will reach ROP in {days_to_rop} days ({rop_cross.iloc[0]['date'].strftime('%Y-%m-%d')})"
                                )

                        if not zero_cross.empty:
                            days_to_zero = (zero_cross.iloc[0]["date"] - forecast_date).days
                            st.error(
                                f"🚨 Stockout predicted in {days_to_zero} days ({zero_cross.iloc[0]['date'].strftime('%Y-%m-%d')})"
                            )

                    else:
                        entity_name = "Model" if group_by_model else "SKU"
                        st.info(f"No forecast data available for this {entity_name} in the projection window.")
        else:
            entity_type = "Models" if group_by_model else "SKUs"
            st.info(
                f"No {entity_type} have both stock and forecast data available. Load both datasets to use this feature."
            )

# ========================================
# TAB 2: SIZE PATTERN OPTIMIZER
# ========================================

with tab2:
    st.title("Size Pattern Optimizer")

    if "pattern_sets" not in st.session_state:
        st.session_state.pattern_sets = load_pattern_sets()

    if "active_set_id" not in st.session_state:
        st.session_state.active_set_id = (
            st.session_state.pattern_sets[0].id if st.session_state.pattern_sets else None
        )

    if "show_add_pattern_set" not in st.session_state:
        st.session_state.show_add_pattern_set = False

    if "edit_set_id" not in st.session_state:
        st.session_state.edit_set_id = None

    if "num_patterns" not in st.session_state:
        st.session_state.num_patterns = 6

    if "num_sizes" not in st.session_state:
        st.session_state.num_sizes = 5

    st.markdown(
        """
    <style>
        .section-header {
            font-size: 1.5rem;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
        }
        .success-box {
            border-left: 4px solid #28a745;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .warning-box {
            border-left: 4px solid #ffc107;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .info-box {
            border-left: 4px solid #17a2b8;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    MIN_ORDER_PER_PATTERN = get_min_order_per_pattern()
    st.markdown(
        f'<div class="info-box">Minimum order per pattern: {MIN_ORDER_PER_PATTERN} units</div>',
        unsafe_allow_html=True,
    )

    active_set = None
    if st.session_state.active_set_id:
        active_set = next(
            (ps for ps in st.session_state.pattern_sets if ps.id == st.session_state.active_set_id),
            None,
        )

    sizes = active_set.size_names if active_set else ["XL", "L", "M", "S", "XS"]

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-header">Quantities</div>', unsafe_allow_html=True)

        if active_set:
            st.info(f"Using sizes from: {active_set.name}")

        quantities = {}

        num_cols = min(len(sizes), 5)
        cols = st.columns(num_cols)

        for i, size in enumerate(sizes):
            col_idx = i % num_cols
            with cols[col_idx]:
                quantities[size] = st.number_input(
                    size, min_value=0, value=0, step=1, key=f"qty_{size}"
                )

        st.markdown('<div class="section-header">Pattern Sets</div>', unsafe_allow_html=True)

        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("New Set", width="content", key="new_set_btn"):
                st.session_state.show_add_pattern_set = True
                st.session_state.edit_set_id = None
                st.session_state.num_patterns = 6
                st.session_state.num_sizes = 5
        with btn_col2:
            if st.button("Save All", width="content", key="save_all_btn"):
                save_pattern_sets(st.session_state.pattern_sets)
                st.success("Pattern sets saved!")
        with btn_col3:
            if st.button("Reload", width="content", key="reload_btn"):
                st.session_state.pattern_sets = load_pattern_sets()
                st.session_state.active_set_id = (
                    st.session_state.pattern_sets[0].id if st.session_state.pattern_sets else None
                )
                st.rerun()

        if st.session_state.pattern_sets:
            set_options = {ps.name: ps.id for ps in st.session_state.pattern_sets}

            current_index = 0
            if st.session_state.active_set_id:
                for idx, (name, ps_id) in enumerate(set_options.items()):
                    if ps_id == st.session_state.active_set_id:
                        current_index = idx
                        break

            selected_set_name = st.selectbox(
                "Select Active Pattern Set:",
                options=list(set_options.keys()),
                index=current_index,
                key="pattern_set_selector",
            )

            new_active_id = set_options[selected_set_name]
            if new_active_id != st.session_state.active_set_id:
                st.session_state.active_set_id = new_active_id
                st.rerun()

            active_set = next(
                (
                    ps
                    for ps in st.session_state.pattern_sets
                    if ps.id == st.session_state.active_set_id
                ),
                None,
            )

            if active_set:
                st.write(f"**{active_set.name}**")
                st.write(f"Sizes: {', '.join(active_set.size_names)}")
                st.write(f"Patterns: {len(active_set.patterns)}")

                for pattern in active_set.patterns:
                    sizes_str = " + ".join(
                        [f"{count} × {size}" for size, count in pattern.sizes.items()]
                    )
                    st.markdown(f"  • **{pattern.name}** : *{sizes_str}*")

                btn_edit, btn_delete = st.columns(2)
                with btn_edit:
                    if st.button("Edit Set", key="edit_set", width="content"):
                        st.session_state.show_add_pattern_set = True
                        st.session_state.edit_set_id = st.session_state.active_set_id
                        st.session_state.num_patterns = len(active_set.patterns)
                        st.session_state.num_sizes = len(active_set.size_names)
                        st.rerun()
                with btn_delete:
                    if st.button("Delete Set", key="delete_set", width="content"):
                        st.session_state.pattern_sets = [
                            ps
                            for ps in st.session_state.pattern_sets
                            if ps.id != st.session_state.active_set_id
                        ]
                        st.session_state.active_set_id = (
                            st.session_state.pattern_sets[0].id
                            if st.session_state.pattern_sets
                            else None
                        )
                        st.rerun()
        else:
            st.info("No pattern sets defined. Create a pattern set to get started!")

        if st.session_state.show_add_pattern_set:
            editing_set = None
            if st.session_state.edit_set_id:
                editing_set = next(
                    (
                        ps
                        for ps in st.session_state.pattern_sets
                        if ps.id == st.session_state.edit_set_id
                    ),
                    None,
                )

            st.markdown("---")
            st.subheader("Create/Edit Pattern Set")

            set_name = st.text_input(
                "Set Name",
                placeholder="e.g., Kids Collection",
                value=editing_set.name if editing_set else "",
                key="set_name_input",
            )

            num_sizes = st.number_input(
                "Number of size categories",
                min_value=1,
                max_value=20,
                value=len(editing_set.size_names) if editing_set else st.session_state.num_sizes,
                step=1,
                key="num_sizes_input",
            )

            if num_sizes != st.session_state.num_sizes:
                st.session_state.num_sizes = int(num_sizes)
                st.rerun()

            st.write("**Define size categories:**")
            size_names = []  # type: list[str]
            size_cols = st.columns(min(int(num_sizes), 5))
            for i in range(int(num_sizes)):
                col_idx = i % len(size_cols)
                with size_cols[col_idx]:
                    default_name = (
                        editing_set.size_names[i]
                        if editing_set and i < len(editing_set.size_names)
                        else f"size_{i + 1}"
                    )
                    size_name = st.text_input(
                        f"Size {i + 1}", value=default_name, key=f"size_name_{i}"
                    )
                    if size_name:
                        size_names.append(size_name)

            num_patterns = st.number_input(
                "Number of patterns in this set",
                min_value=1,
                max_value=20,
                value=len(editing_set.patterns) if editing_set else st.session_state.num_patterns,
                step=1,
                key="num_patterns_input",
            )

            if num_patterns != st.session_state.num_patterns:
                st.session_state.num_patterns = int(num_patterns)
                st.rerun()

            patterns = []
            for i in range(int(num_patterns)):
                with st.expander(f"Pattern {i + 1}", expanded=(i < 3)):
                    existing_pattern = (
                        editing_set.patterns[i]
                        if editing_set and i < len(editing_set.patterns)
                        else None
                    )

                    # noinspection PyTypeHints
                    placeholder_text = f"e.g., {size_names[0] if size_names else 'Size1'} + {size_names[1] if len(size_names) > 1 else 'Size2'}"
                    pattern_name = st.text_input(
                        "Pattern Name",
                        placeholder=placeholder_text,
                        key=f"pname_{i}",
                        value=existing_pattern.name if existing_pattern else "",
                    )

                    st.write("Quantities per size:")
                    pattern_sizes = {}
                    p_cols = st.columns(min(len(size_names), 5))
                    for j, size in enumerate(size_names):
                        col_idx = j % len(p_cols)
                        with p_cols[col_idx]:
                            default_val = (
                                existing_pattern.sizes.get(size, 0) if existing_pattern else 0
                            )
                            qty = st.number_input(
                                size,
                                min_value=0,
                                value=default_val,
                                key=f"p{i}_{size}",
                                label_visibility="visible",
                            )
                            if qty > 0:
                                pattern_sizes[size] = qty

                    if pattern_name and pattern_sizes:
                        patterns.append(Pattern(i + 1, pattern_name, pattern_sizes))

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.button("Save Pattern Set", width="content", key="submit_set"):
                    if set_name and len(size_names) == num_sizes and len(patterns) == num_patterns:
                        if editing_set:
                            editing_set.name = set_name
                            editing_set.size_names = size_names
                            editing_set.patterns = patterns
                        else:
                            new_id = (
                                    max([ps.id for ps in st.session_state.pattern_sets], default=0) + 1
                            )
                            st.session_state.pattern_sets.append(
                                PatternSet(new_id, set_name, size_names, patterns)
                            )
                            st.session_state.active_set_id = new_id

                        st.session_state.show_add_pattern_set = False
                        st.session_state.edit_set_id = None
                        st.rerun()
                    else:
                        st.error(
                            f"Please complete all fields: set name, {int(num_sizes)} size names, and {int(num_patterns)} patterns!"
                        )

            with col_cancel:
                if st.button("Cancel", width="content", key="cancel_set"):
                    st.session_state.show_add_pattern_set = False
                    st.session_state.edit_set_id = None
                    st.rerun()

    with col2:
        st.markdown('<div class="section-header">Optimization</div>', unsafe_allow_html=True)

        if st.button("Run Optimization", type="primary", width="content", key="run_optimization"):
            if not st.session_state.pattern_sets:
                st.error("Please add at least one pattern set before optimizing!")
            elif st.session_state.active_set_id is None:
                st.error("Please select an active pattern set!")
            elif not any(quantities.values()):
                st.warning("Please enter quantities to optimize!")
            else:
                active_set = next(
                    (
                        ps
                        for ps in st.session_state.pattern_sets
                        if ps.id == st.session_state.active_set_id
                    ),
                    None,
                )

                if active_set:
                    result = optimize_patterns(
                        quantities, active_set.patterns, MIN_ORDER_PER_PATTERN
                    )

                    display_optimization_metrics(result)

                    has_violations = len(result["min_order_violations"]) > 0

                    if result["all_covered"] and not has_violations:
                        st.markdown(
                            '<div class="success-box">All requirements covered and minimum orders met!</div>',
                            unsafe_allow_html=True,
                        )
                    elif has_violations:
                        violation_text = ", ".join(
                            [f"{name} ({count})" for name, count in result["min_order_violations"]]
                        )
                        st.markdown(
                            f'<div class="warning-box">Minimum order violations (need {MIN_ORDER_PER_PATTERN} per pattern): {violation_text}</div>',
                            unsafe_allow_html=True,
                        )
                    elif not result["all_covered"]:
                        st.markdown(
                            '<div class="warning-box">Some requirements not covered</div>',
                            unsafe_allow_html=True,
                        )

                    st.markdown("### Pattern Allocation")
                    allocation_data = []
                    for pattern in active_set.patterns:
                        count = result["allocation"].get(pattern.id, 0)
                        if count > 0:
                            sizes_str = " + ".join([f"{c}×{s}" for s, c in pattern.sizes.items()])
                            status = "⚠️" if count < MIN_ORDER_PER_PATTERN else "✅"
                            allocation_data.append(
                                {
                                    "Pattern": pattern.name,
                                    "Count": count,
                                    "Composition": sizes_str,
                                    "Status": status,
                                }
                            )

                    if allocation_data:
                        st.dataframe(allocation_data, width="content", hide_index=True)
                    else:
                        st.info("No patterns allocated")

                    st.markdown("### Production vs Required")
                    production_data = []
                    for size in sizes:
                        produced = result["produced"][size]
                        required = quantities[size]
                        excess = result["excess"][size]
                        status = "✅" if produced >= required else "❌"
                        production_data.append(
                            {
                                "Size": size,
                                "Required": required,
                                "Produced": produced,
                                "Excess": f"{excess:+d}",
                                "Status": status,
                            }
                        )

                    total_required = sum(quantities[size] for size in sizes)
                    total_produced = sum(result["produced"][size] for size in sizes)
                    total_excess = sum(result["excess"][size] for size in sizes)
                    production_data.append(
                        {
                            "Size": "**TOTAL**",
                            "Required": total_required,
                            "Produced": total_produced,
                            "Excess": f"{total_excess:+d}",
                            "Status": "",
                        }
                    )

                    st.dataframe(production_data, width="content", hide_index=True)

# ========================================
# TAB 3: ORDER RECOMMENDATIONS
# ========================================

with tab3:
    st.title("🎯 Order Recommendations")
    st.write(
        "Automatically prioritize which models and colors to order based on stock levels, forecasts, and ROP thresholds."
    )

    if "recommendations_data" not in st.session_state:
        st.session_state.recommendations_data = None
    if "recommendations_top_n" not in st.session_state:
        st.session_state.recommendations_top_n = 10
    if "selected_order_items" not in st.session_state:
        st.session_state.selected_order_items = []
    if "szwalnia_include_filter" not in st.session_state:
        st.session_state.szwalnia_include_filter = []
    if "szwalnia_exclude_filter" not in st.session_state:
        st.session_state.szwalnia_exclude_filter = []

    if not stock_loaded or not use_forecast or forecast_df is None:
        st.warning("⚠️ Please load both stock and forecast data in Tab 1 to use this feature.")
    else:
        with st.expander("⚙️ Recommendation Parameters", expanded=False):
            st.caption("Adjust these parameters to tune the priority scoring algorithm")

            st.write("**Priority Weights** (contribution to final score)")
            w_col1, w_col2, w_col3 = st.columns(3)
            with w_col1:
                weight_stockout = st.slider(
                    "Stockout Risk",
                    0.0,
                    1.0,
                    st.session_state.settings["order_recommendations"]["priority_weights"][
                        "stockout_risk"
                    ],
                    0.05,
                    key="weight_stockout",
                    help="Weight for stockout risk factor in priority calculation. Higher values prioritize items at risk of stockout (zero stock or below ROP).",
                )
            with w_col2:
                weight_revenue = st.slider(
                    "Revenue Impact",
                    0.0,
                    1.0,
                    st.session_state.settings["order_recommendations"]["priority_weights"][
                        "revenue_impact"
                    ],
                    0.05,
                    key="weight_revenue",
                    help="Weight for revenue impact in priority calculation. Higher values prioritize high-revenue items (forecast × price).",
                )
            with w_col3:
                weight_demand = st.slider(
                    "Demand Forecast",
                    0.0,
                    1.0,
                    st.session_state.settings["order_recommendations"]["priority_weights"][
                        "demand_forecast"
                    ],
                    0.05,
                    key="weight_demand",
                    help="Weight for demand forecast in priority calculation. Higher values prioritize items with high forecasted demand during lead time.",
                )

            st.caption(
                f"Current weights sum: {weight_stockout + weight_revenue + weight_demand:.2f} (ideally 1.0)"
            )

            st.write("**Type Multipliers** (priority boost by product type)")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                mult_new = st.slider(
                    "New Products",
                    0.5,
                    2.0,
                    st.session_state.settings["order_recommendations"]["type_multipliers"]["new"],
                    0.1,
                    key="mult_new",
                    help="Multiplier applied to new products (< 12 months since first sale). Values > 1.0 increase priority, < 1.0 decrease priority.",
                )
            with m_col2:
                mult_seasonal = st.slider(
                    "Seasonal",
                    0.5,
                    2.0,
                    st.session_state.settings["order_recommendations"]["type_multipliers"][
                        "seasonal"
                    ],
                    0.1,
                    key="mult_seasonal",
                    help="Multiplier for seasonal products (high variability, CV > 1.0). Higher values prioritize seasonal items during peak season.",
                )
            with m_col3:
                mult_regular = st.slider(
                    "Regular",
                    0.5,
                    2.0,
                    st.session_state.settings["order_recommendations"]["type_multipliers"][
                        "regular"
                    ],
                    0.1,
                    key="mult_regular",
                    help="Multiplier for regular products (moderate variability, 0.6 < CV < 1.0). Typically set to 1.0 as baseline.",
                )
            with m_col4:
                mult_basic = st.slider(
                    "Basic",
                    0.5,
                    2.0,
                    st.session_state.settings["order_recommendations"]["type_multipliers"]["basic"],
                    0.1,
                    key="mult_basic",
                    help="Multiplier for basic products (stable demand, CV < 0.6). Lower values reduce priority for consistently available items.",
                )

            st.write("**Stockout Risk & Other Parameters**")
            o_col1, o_col2, o_col3 = st.columns(3)
            with o_col1:
                zero_penalty = st.slider(
                    "Zero Stock Penalty",
                    50,
                    150,
                    st.session_state.settings["order_recommendations"]["stockout_risk"][
                        "zero_stock_penalty"
                    ],
                    5,
                    key="zero_penalty",
                    help="Risk score assigned to SKUs with zero stock AND forecasted demand. Higher values = maximum urgency for out-of-stock items.",
                )
            with o_col2:
                below_rop_penalty = st.slider(
                    "Below ROP Max Penalty",
                    40,
                    100,
                    st.session_state.settings["order_recommendations"]["stockout_risk"][
                        "below_rop_max_penalty"
                    ],
                    5,
                    key="below_rop_penalty",
                    help="Maximum risk score for items below Reorder Point (ROP). Actual score scales proportionally based on how far below ROP.",
                )
            with o_col3:
                demand_cap = st.slider(
                    "Demand Cap",
                    50,
                    300,
                    st.session_state.settings["order_recommendations"]["demand_cap"],
                    10,
                    key="demand_cap",
                    help="Maximum forecast value used in priority calculation. Prevents extremely high forecasts from dominating the score. Values are clipped to this maximum.",
                )

            st.session_state.settings["order_recommendations"]["priority_weights"][
                "stockout_risk"
            ] = weight_stockout
            st.session_state.settings["order_recommendations"]["priority_weights"][
                "revenue_impact"
            ] = weight_revenue
            st.session_state.settings["order_recommendations"]["priority_weights"][
                "demand_forecast"
            ] = weight_demand
            st.session_state.settings["order_recommendations"]["type_multipliers"]["new"] = mult_new
            st.session_state.settings["order_recommendations"]["type_multipliers"][
                "seasonal"
            ] = mult_seasonal
            st.session_state.settings["order_recommendations"]["type_multipliers"][
                "regular"
            ] = mult_regular
            st.session_state.settings["order_recommendations"]["type_multipliers"][
                "basic"
            ] = mult_basic
            st.session_state.settings["order_recommendations"]["stockout_risk"][
                "zero_stock_penalty"
            ] = zero_penalty
            st.session_state.settings["order_recommendations"]["stockout_risk"][
                "below_rop_max_penalty"
            ] = below_rop_penalty
            st.session_state.settings["order_recommendations"]["demand_cap"] = demand_cap

        st.write("**Filter by Production Facility**")
        model_metadata_df_filter = load_model_metadata()
        if model_metadata_df_filter is not None and SZWALNIA_G in model_metadata_df_filter.columns:
            unique_facilities = sorted(
                model_metadata_df_filter[SZWALNIA_G].dropna().unique().tolist()
            )

            col_include, col_exclude = st.columns(2)

            with col_include:
                st.session_state.szwalnia_include_filter = st.multiselect(
                    "Include Facilities:",
                    options=unique_facilities,
                    default=st.session_state.szwalnia_include_filter,
                    help="Select facilities to INCLUDE. Empty = include all.",
                )

            with col_exclude:
                st.session_state.szwalnia_exclude_filter = st.multiselect(
                    "Exclude Facilities:",
                    options=unique_facilities,
                    default=st.session_state.szwalnia_exclude_filter,
                    help="Select facilities to EXCLUDE. Takes precedence over include.",
                )
        else:
            st.info("Model metadata not available. Showing all items.")

        col_top_n, col_calc, col_clear = st.columns([3, 1, 1])
        with col_top_n:
            top_n_recommendations = st.slider(
                "Number of top priority items to show:",
                min_value=5,
                max_value=50,
                value=st.session_state.recommendations_top_n,
                step=5,
            )
            st.session_state.recommendations_top_n = top_n_recommendations
        with col_calc:
            st.write("")
            st.write("")
            calculate_recommendations = st.button("Generate Recommendations", type="primary")
        with col_clear:
            st.write("")
            st.write("")
            if st.button("Clear", type="secondary"):
                st.session_state.recommendations_data = None
                st.rerun()

        if calculate_recommendations:
            with st.spinner("Calculating order priorities..."):
                try:
                    sku_summary = analyzer.aggregate_by_sku()
                    sku_summary = analyzer.classify_sku_type(
                        sku_summary,
                        cv_basic=st.session_state.settings["cv_thresholds"]["basic"],
                        cv_seasonal=st.session_state.settings["cv_thresholds"]["seasonal"]
                    )
                    sku_summary = analyzer.calculate_safety_stock_and_rop(
                        sku_summary,
                        seasonal_data,
                        z_basic=st.session_state.settings["z_scores"]["basic"],
                        z_regular=st.session_state.settings["z_scores"]["regular"],
                        z_seasonal_in=st.session_state.settings["z_scores"]["seasonal_in"],
                        z_seasonal_out=st.session_state.settings["z_scores"]["seasonal_out"],
                        z_new=st.session_state.settings["z_scores"]["new"],
                        lead_time_months=st.session_state.settings["lead_time"],
                    )
                    sku_last_two_years = analyzer.calculate_last_two_years_avg_sales(by_model=False)
                    sku_summary = sku_summary.merge(sku_last_two_years, on="SKU", how="left")
                    sku_summary["LAST_2_YEARS_AVG"] = sku_summary["LAST_2_YEARS_AVG"].fillna(0)

                    if stock_loaded:
                        sku_stock = stock_df.copy()
                        sku_summary = sku_summary.merge(sku_stock, on="SKU", how="left")
                        sku_summary["STOCK"] = sku_summary["STOCK"].fillna(0)
                        if "PRICE" in sku_stock.columns:
                            sku_summary["PRICE"] = sku_summary["PRICE"].fillna(0)

                    recommendations = SalesAnalyzer.generate_order_recommendations(
                        summary_df=sku_summary,
                        forecast_df=forecast_df,
                        forecast_time_months=forecast_time,
                        top_n=top_n_recommendations,
                        settings=st.session_state.settings,
                    )

                    include_filter = st.session_state.szwalnia_include_filter
                    exclude_filter = st.session_state.szwalnia_exclude_filter

                    if include_filter or exclude_filter:
                        model_metadata_df = load_model_metadata()
                        if model_metadata_df is not None and SZWALNIA_G in model_metadata_df.columns:
                            priority_skus = recommendations["priority_skus"].copy()
                            priority_skus = priority_skus.merge(
                                model_metadata_df[["Model", SZWALNIA_G]],
                                left_on="MODEL",
                                right_on="Model",
                                how="left",
                            )

                            if include_filter:
                                priority_skus = priority_skus[
                                    priority_skus[SZWALNIA_G].isin(include_filter)
                                ]

                            if exclude_filter:
                                priority_skus = priority_skus[
                                    ~priority_skus[SZWALNIA_G].isin(exclude_filter)
                                ]

                            priority_skus = priority_skus.drop(columns=["Model", SZWALNIA_G])

                            model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(
                                priority_skus
                            )

                            recommendations["priority_skus"] = priority_skus
                            recommendations["model_color_summary"] = model_color_summary

                    st.session_state.recommendations_data = recommendations

                    st.success(
                        f"✅ Analyzed {len(recommendations['priority_skus'])} SKUs - scroll down to view results"
                    )

                except Exception as e:
                    st.error(f"Error generating recommendations: {e}")
                    import traceback

                    st.code(traceback.format_exc())

        if st.session_state.recommendations_data is not None:
            recommendations = st.session_state.recommendations_data

            model_metadata_df = load_model_metadata()

            top_model_colors = (
                recommendations["model_color_summary"]  # type: ignore[index]
                .sort_values("PRIORITY_SCORE", ascending=False)
                .head(st.session_state.recommendations_top_n)
            )

            st.subheader("Top Priority Items to Order")
            st.caption(f"Showing top {len(top_model_colors)} MODEL+COLOR combinations by priority")

            order_list = []
            for idx, (_, row) in enumerate(top_model_colors.iterrows(), 1):
                model = row["MODEL"]
                color = row["COLOR"]

                size_quantities = SalesAnalyzer.get_size_quantities_for_model_color(
                    recommendations["priority_skus"],  # type: ignore[index]
                    model,
                    color,
                )

                sizes_str = (
                    ", ".join([f"{size}:{qty}" for size, qty in sorted(size_quantities.items())])
                    if size_quantities
                    else "No data"
                )

                urgent_mark = "🚨" if row.get("URGENT", False) else ""

                order_item = {
                    "#": idx,
                    "Model": model,
                    "Color": color,
                    "Priority": f"{row['PRIORITY_SCORE']:.1f}",
                    "Deficit": int(row["DEFICIT"]),
                    "Forecast": int(row.get("FORECAST_LEADTIME", 0)),
                    SIZE_QTY: sizes_str,
                }

                if model_metadata_df is not None:
                    metadata_row = model_metadata_df[model_metadata_df["Model"] == model]
                    if not metadata_row.empty:
                        order_item[SZWALNIA_G] = metadata_row.iloc[0][SZWALNIA_G]

                order_list.append(order_item)

            order_df = pd.DataFrame(order_list)
            order_df.insert(0, "Select", False)

            edited_df = st.data_editor(
                order_df,
                hide_index=True,
                disabled=["#", "Model", "Color", "Priority", "Deficit", "Forecast", SIZE_QTY]
                         + ([SZWALNIA_G] if SZWALNIA_G in order_df.columns else []),
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select items to create order",
                        default=False,
                    )
                },
                height=min(600, len(order_list) * 35 + 38),
            )

            selected_rows = edited_df[edited_df["Select"] == True]

            if not selected_rows.empty:
                selected_items = []
                for _, row in selected_rows.iterrows():
                    sizes_str = row[SIZE_QTY]
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

                st.session_state.selected_order_items = selected_items

            if st.session_state.selected_order_items:
                st.success(f"✓ {len(st.session_state.selected_order_items)} items selected")

                if st.button("📋 Create Order", type="primary"):
                    st.info("Please navigate to the 'Order Creation' tab to complete the order")
            else:
                st.info("Select items above to create an order")

            st.markdown("---")
            st.subheader("Full Model+Color Priority Summary")

            model_color_summary = recommendations["model_color_summary"].copy()  # type: ignore[index]

            if model_metadata_df is not None:
                model_color_summary = model_color_summary.merge(
                    model_metadata_df, left_on="MODEL", right_on="Model", how="left"
                )
                if "Model" in model_color_summary.columns:
                    model_color_summary = model_color_summary.drop(columns=["Model"])

            display_cols = [
                "MODEL",
                "COLOR",
                "PRIORITY_SCORE",
                "DEFICIT",
                "FORECAST_LEADTIME",
                "COVERAGE_GAP",
                "URGENT",
            ]

            if model_metadata_df is not None:
                display_cols.extend([SZWALNIA_G, SZWALNIA_D, MATERIAL, "GRAMATURA"])

            available_cols = [col for col in display_cols if col in model_color_summary.columns]
            st.dataframe(
                model_color_summary[available_cols],
                hide_index=True,
                height=400,
            )

            st.download_button(
                "📥 Download Full Priority Report (SKU level)",
                recommendations["priority_skus"].to_csv(index=False),  # type: ignore[index]
                "order_priority_report.csv",
                TEXT_CSV,
                key="download_tab3_priority_report"
            )

# ========================================
# TAB 4: WEEKLY ANALYSIS
# ========================================

with tab4:
    st.title("📅 Weekly Analysis")

    if st.button("Refresh Analysis", type="primary"):
        st.cache_data.clear()
        st.rerun()

    df = load_data()
    stock_df = None
    if stock_loaded:
        stock_df, _ = load_stock()

    st.markdown("---")
    st.header("⭐ Top Sales Report")
    st.caption("Compare previous week's sales to same week last year (Monday-Sunday)")

    try:
        from datetime import datetime

        top_sales = SalesAnalyzer.calculate_top_sales_report(
            sales_df=df, reference_date=datetime.today()
        )

        col_dates1, col_dates2 = st.columns(2)
        with col_dates1:
            st.metric(
                LAST_WEEK,
                f"{top_sales['last_week_start'].strftime('%d-%m-%Y')} - {top_sales['last_week_end'].strftime('%d-%m-%Y')}",
            )
        with col_dates2:
            st.metric(
                "Same Week Last Year",
                f"{top_sales['prev_year_start'].strftime('%d-%m-%Y')} - {top_sales['prev_year_end'].strftime('%d-%m-%Y')}",
            )

        col_rising, col_falling = st.columns(2)

        with col_rising:
            st.subheader("🚀 RISING STAR")
            if top_sales["rising_star"] is not None:
                display_star_product(top_sales["rising_star"], stock_df, is_rising=True)
            else:
                st.info("No rising products found")

        with col_falling:
            st.subheader("📉 FALLING STAR")
            if top_sales["falling_star"] is not None:
                display_star_product(top_sales["falling_star"], stock_df, is_rising=False)
            else:
                st.info("No falling products found")

    except Exception as e:
        st.error(f"❌ Error generating TOP SALES REPORT: {e}")
        import traceback

        st.code(traceback.format_exc())

    st.markdown("---")
    st.header("🏆 Top 5 Products by Type")
    st.caption("Best sellers from last week by product category")

    try:
        cv_basic = st.session_state.settings["cv_thresholds"]["basic"]
        cv_seasonal = st.session_state.settings["cv_thresholds"]["seasonal"]

        top_products = SalesAnalyzer.calculate_top_products_by_type(
            sales_df=df, cv_basic=cv_basic, cv_seasonal=cv_seasonal, reference_date=datetime.today()
        )

        col_new, col_seasonal = st.columns(2)
        col_regular, col_basic = st.columns(2)


        def display_top_5(column, type_name, emoji, df_top):
            with column:
                st.subheader(f"{emoji} {type_name.upper()}")
                if not df_top.empty:
                    top_products_df = df_top.copy()
                    top_products_df[MODEL_COLOR] = (
                            top_products_df["model"] + top_products_df["color"]
                    )

                    if stock_df is not None:
                        stock_df_copy = stock_df.copy()
                        stock_df_copy["model"] = stock_df_copy["sku"].astype(str).str[:5]
                        stock_df_copy["color"] = stock_df_copy["sku"].astype(str).str[5:7]
                        descriptions = (
                            stock_df_copy.groupby(["model", "color"])["nazwa"].first().reset_index()
                        )
                        top_products_df = top_products_df.merge(
                            descriptions, on=["model", "color"], how="left"
                        )
                        top_products_df["nazwa"] = top_products_df["nazwa"].fillna("")
                        final_cols = [MODEL_COLOR, "nazwa", "color", "sales"]
                        col_names = {"nazwa": "DESCRIPTION", "color": "COLOR", "sales": "SALES"}
                    else:
                        final_cols = [MODEL_COLOR, "color", "sales"]
                        col_names = {"color": "COLOR", "sales": "SALES"}

                    top_products_df = top_products_df[final_cols].rename(columns=col_names)

                    st.dataframe(top_products_df, hide_index=True, width="stretch")
                else:
                    st.info(f"No {type_name} products found")


        display_top_5(col_new, "New", "🆕", top_products["top_by_type"]["new"])
        display_top_5(col_seasonal, "Seasonal", "🌸", top_products["top_by_type"]["seasonal"])
        display_top_5(col_regular, "Regular", "📦", top_products["top_by_type"]["regular"])
        display_top_5(col_basic, "Basic", "⚙️", top_products["top_by_type"]["basic"])

    except Exception as e:
        st.error(f"❌ Error generating Top 5 by Type: {e}")
        import traceback

        st.code(traceback.format_exc())

    st.markdown("---")
    st.header("📊 New Products Launch Monitoring")
    st.caption(
        "Track weekly sales for products launched in the last 2 months (Weeks aligned to calendar Wednesdays)"
    )

    lookback_days = st.session_state.settings.get("weekly_analysis", {}).get("lookback_days", 60)

    with st.spinner("Generating weekly analysis..."):
        try:
            from datetime import datetime

            weekly_df = SalesAnalyzer.generate_weekly_new_products_analysis(
                sales_df=df,
                stock_df=stock_df,
                lookback_days=lookback_days,
                reference_date=datetime.today(),
            )

            if weekly_df.empty:
                st.info(f"ℹ️ No new products found with first sale in the last {lookback_days} days")
            else:
                col1, col2, col3 = st.columns(3)
                week_cols = [
                    col
                    for col in weekly_df.columns
                    if col not in ["SALES_START_DATE", "MODEL", "DESCRIPTION"]
                ]

                with col1:
                    st.metric("New Products", len(weekly_df))
                with col2:
                    st.metric("Weeks Tracked", len(week_cols))
                with col3:
                    total_sales = weekly_df[week_cols].sum().sum() if week_cols else 0
                    st.metric("Total Sales", f"{int(total_sales):,}")

                st.subheader("Weekly Sales by Model")
                st.dataframe(weekly_df, hide_index=True, height=600, width="stretch")

                csv = weekly_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Weekly Analysis (CSV)",
                    csv,
                    f"weekly_new_products_{datetime.today().strftime('%Y%m%d')}.csv",
                    TEXT_CSV,
                    key="download_tab4_weekly_analysis"
                )

                weekly_df["TOTAL_SALES"] = weekly_df[week_cols].sum(axis=1)
                zero_sales = weekly_df[weekly_df["TOTAL_SALES"] == 0]

                if not zero_sales.empty:
                    st.warning(f"⚠️ {len(zero_sales)} product(s) with ZERO sales in tracked period")
                    with st.expander("View zero-sales products", expanded=False):
                        display_cols = ["SALES_START_DATE", "MODEL"]
                        if "DESCRIPTION" in zero_sales.columns:
                            display_cols.append("DESCRIPTION")
                        st.dataframe(zero_sales[display_cols], hide_index=True)

        except Exception as e:
            st.error(f"❌ Error generating weekly analysis: {e}")
            import traceback

            st.code(traceback.format_exc())

# ========================================
# TAB 5: ORDER CREATION
# ========================================

with tab5:
    st.title("📋 Order Creation")

    st.markdown("---")
    st.subheader("📝 Manual Order Creation")

    col_input, col_button = st.columns([3, 1])
    with col_input:
        manual_model = st.text_input(
            "Enter Model Code",
            placeholder="e.g., ABC12",
            help="Enter a model code to create an order. Data will be pulled from Order Recommendations.",
            key="manual_model_input"
        )
    with col_button:
        st.write("")
        st.write("")
        create_clicked = st.button("Create Order", key="create_manual_order", type="primary")

    if create_clicked:
        if not manual_model:
            st.warning("⚠️ Please enter a model code")
        elif not st.session_state.get("recommendations_data"):
            st.error("❌ No recommendations data available. Please generate recommendations in Tab 3 first.")
        else:
            recommendations = st.session_state.recommendations_data
            priority_skus = recommendations.get("priority_skus")

            if priority_skus is None:
                st.error("❌ Priority SKUs data not found. Please regenerate recommendations in Tab 3.")
            else:
                model_color_summary = recommendations.get("model_color_summary")
                if model_color_summary is None:
                    st.error("❌ Model+Color summary data not found. Please regenerate recommendations in Tab 3.")
                else:
                    model_color_summary_copy = model_color_summary.copy()
                    model_data = model_color_summary_copy[model_color_summary_copy["MODEL"] == manual_model.upper()]

                    if model_data.empty:
                        st.error(
                            f"❌ Model '{manual_model.upper()}' not found in Order Recommendations. Please generate recommendations first.")
                    else:
                        selected_items = []
                        for _, row in model_data.iterrows():
                            size_str = row.get(SIZE_QTY, "")
                            size_quantities = {}
                            if size_str and pd.notna(size_str):
                                for item in str(size_str).split(", "):
                                    if ":" in item:
                                        size_code, qty = item.split(":")
                                        size_quantities[size_code.strip()] = int(qty.strip())

                            selected_items.append({
                                "model": row["MODEL"],
                                "color": row["COLOR"],
                                "priority_score": float(row.get("PRIORITY", 0)),
                                "deficit": int(row.get("DEFICIT", 0)),
                                "forecast": int(row.get("FORECAST", 0)),
                                "sizes": size_quantities,
                            })

                        st.session_state.selected_order_items = selected_items
                        st.success(
                            f"✅ Created order for model {manual_model.upper()} with {len(selected_items)} colors")
                        st.rerun()

    st.markdown("---")

    if not st.session_state.get("selected_order_items"):
        st.info("ℹ️ No items selected. Use the manual input above or go to Order Recommendations tab to select items.")
    else:
        from utils.order_creation_ui import render_order_creation_interface

        render_order_creation_interface()
