import plotly.express as px
import streamlit as st

from pattern_optimizer_logic import (
    MIN_ORDER_PER_PATTERN,
    Pattern,
    PatternSet,
    load_pattern_sets,
    optimize_patterns,
    save_pattern_sets,
)
from sales_data import SalesAnalyzer, SalesDataLoader

st.set_page_config(page_title="Inventory & Pattern Optimizer", page_icon="📊", layout="wide")

tab1, tab2 = st.tabs(["📊 Sales & Inventory Analysis", "📦 Size Pattern Optimizer"])

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

    st.sidebar.subheader("Lead Time")
    lead_time = st.sidebar.number_input(
        "Lead time in months",
        label_visibility="collapsed",
        min_value=0.0,
        max_value=100.0,
        value=1.36,
        step=0.01,
        format="%.2f",
    )

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
            value=0.6,
            step=0.1,
            format="%.1f",
            key="basic_cv",
        )
    with basic_cols[2]:
        z_score_basic = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=2.05,
            step=0.001,
            format="%.3f",
            key="basic_z",
        )
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
            value=1.645,
            step=0.001,
            format="%.3f",
        )
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
            value=1.0,
            step=0.1,
            format="%.1f",
            key="seasonal_cv",
        )
    with seasonal_cols[2]:
        z_score_seasonal_1 = st.number_input(
            "Z-Score IN season",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=1.75,
            step=0.001,
            format="%.3f",
            key="seasonal_z1",
            placeholder="IN season",
        )
    with seasonal_cols[3]:
        z_score_seasonal_2 = st.number_input(
            "Z-Score OUT of season",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=1.6,
            step=0.001,
            format="%.3f",
            key="seasonal_z2",
            placeholder="OUT of season",
        )

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
            value=12,
            step=1,
            key="new_cv",
        )
    with new_cols[2]:
        z_score_new = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=1.8,
            step=0.001,
            format="%.3f",
            key="new_z",
        )
    with new_cols[3]:
        st.write("-")

    st.sidebar.markdown("---")
    st.sidebar.write("**Current Parameters:**")
    st.sidebar.write(f"Lead Time: {lead_time} months")
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

    @st.cache_data
    def load_data():
        loader = SalesDataLoader()
        return loader.get_aggregated_data()

    @st.cache_data
    def load_stock():
        loader = SalesDataLoader()
        stock_file = loader.get_latest_stock_file()
        if stock_file:
            return loader.load_stock_file(stock_file), stock_file.name
        return None, None

    @st.cache_data
    def load_forecast():
        loader = SalesDataLoader()
        forecast_result = loader.get_latest_forecast_file()
        if forecast_result:
            forecast_file, file_date = forecast_result
            df_forecast = loader.load_forecast_file(forecast_file)
            return df_forecast, file_date, forecast_file.name
        return None, None, None

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
        lead_time=lead_time,
        z_basic=z_score_basic,
        z_regular=z_score_regular,
        z_seasonal_in=z_score_seasonal_1,
        z_seasonal_out=z_score_seasonal_2,
        z_new=z_score_new,
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
            summary["OVERSTOCKED_%"] = (
                (summary["STOCK"] - summary["ROP"]) / summary["ROP"] * 100
            ).round(1)

            stock_loaded = True
        else:
            st.info("ℹ️ No stock file found. Stock-related columns will not be available.")

    if use_forecast:
        forecast_df, forecast_date, forecast_filename = load_forecast()
        if forecast_df is not None:
            try:
                forecast_metrics = SalesAnalyzer.calculate_forecast_metrics(forecast_df, forecast_date)

                if group_by_model:
                    forecast_metrics["MODEL"] = forecast_metrics["sku"].astype(str).str[:5]
                    forecast_agg = (
                        forecast_metrics.groupby("MODEL")
                        .agg({"FORECAST_8W": "sum", "FORECAST_16W": "sum"})
                        .reset_index()
                    )
                    summary = summary.merge(forecast_agg, on="MODEL", how="left")
                else:
                    forecast_metrics = forecast_metrics.rename(columns={"sku": "SKU"})
                    summary = summary.merge(
                        forecast_metrics[["SKU", "FORECAST_8W", "FORECAST_16W"]], on="SKU", how="left"
                    )

                summary["FORECAST_8W"] = summary["FORECAST_8W"].fillna(0)
                summary["FORECAST_16W"] = summary["FORECAST_16W"].fillna(0)

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
                "FORECAST_8W",
                "FORECAST_16W",
                "OVERSTOCKED_%",
                "DEFICIT",
                "MONTHS",
                "QUANTITY",
                "AVERAGE SALES",
                "LAST_2_YEARS_AVG",
                "CV",
                "SS",
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
                "FORECAST_8W",
                "FORECAST_16W",
                "OVERSTOCKED_%",
                "DEFICIT",
                "MONTHS",
                "QUANTITY",
                "AVERAGE SALES",
                "LAST_2_YEARS_AVG",
                "CV",
                "SS",
                "VALUE",
                "BELOW_ROP",
            ]
    else:
        column_order = [
            id_column,
            "TYPE",
            "MONTHS",
            "QUANTITY",
            "AVERAGE SALES",
            "LAST_2_YEARS_AVG",
            "SS",
            "CV",
            "ROP",
            "FORECAST_8W",
            "FORECAST_16W",
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
        if stock_loaded:
            show_only_below_rop = st.checkbox("Show only below ROP", value=False)
        else:
            show_only_below_rop = False
    with col3:
        if group_by_model:
            show_bestsellers = st.checkbox("Bestsellers (>300/mo)", value=False)
        else:
            show_bestsellers = False
            st.write("_Bestsellers (model view only)_")
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

    if stock_loaded and show_overstocked and "OVERSTOCKED_%" in filtered_summary.columns:
        filtered_summary = filtered_summary[
            filtered_summary["OVERSTOCKED_%"] >= overstock_threshold
        ]

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

    if stock_loaded:
        st.dataframe(filtered_summary, width="stretch", height=600)
    else:
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

            col1.metric("Below ROP", int(below_rop_count), delta=None, delta_color="inverse")
            col2.metric("Total Deficit (units)", f"{total_deficit:,.0f}")
            col3.metric(
                "% Below ROP",
                (
                    f"{(below_rop_count / valid_stock_count * 100):.1f}%"
                    if valid_stock_count > 0
                    else "0%"
                ),
            )

            overstocked_count = int((valid_stock["OVERSTOCKED_%"] >= overstock_threshold).sum())
            normal_count = valid_stock_count - below_rop_count - overstocked_count

            pie_data = {
                "Status": ["Below ROP", "Overstocked", "Normal"],
                "Count": [below_rop_count, overstocked_count, normal_count],
            }

            fig = px.pie(
                pie_data,
                values="Count",
                names="Status",
                title=f"Stock Status Distribution (Overstock threshold: {overstock_threshold}%)",
                color="Status",
                color_discrete_map={
                    "Below ROP": "#ff4b4b",
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
        download_label, display_data.to_csv(index=False), download_filename, "text/csv"
    )

# ========================================
# TAB 2: SIZE PATTERN OPTIMIZER
# ========================================

with tab2:
    st.title("Size Pattern Optimizer")

    # Initialize session state
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

        if st.button(
            "Run Optimization", type="primary", width="content", key="run_optimization"
        ):
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

                    met_col1, met_col2, met_col3 = st.columns(3)
                    with met_col1:
                        st.metric("Total Patterns", result["total_patterns"])
                    with met_col2:
                        st.metric("Total Excess", result["total_excess"])
                    with met_col3:
                        coverage_icon = "✅" if result["all_covered"] else "❌"
                        st.metric("Coverage", coverage_icon)

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
