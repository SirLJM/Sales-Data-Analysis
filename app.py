import streamlit as st

from sales_data import SalesDataLoader, SalesAnalyzer

st.markdown("""
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 380px;
        max-width: 380px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Sales Data Analysis")

st.sidebar.header("Parameters")

st.sidebar.subheader("Lead Time")
lead_time = st.sidebar.number_input(
    "Lead time in months",
    label_visibility="collapsed",
    min_value=0.0,
    max_value=100.0,
    value=1.36,
    step=0.01,
    format="%.2f"
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
        key="basic_cv"
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
        key="basic_z"
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
        format="%.3f"
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
        key="seasonal_cv"
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
        placeholder="IN season"
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
        placeholder="OUT of season"
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
        key="new_cv"
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
        key="new_z"
    )
with new_cols[3]:
    st.write("-")

st.sidebar.markdown("---")
st.sidebar.write("**Current Parameters:**")
st.sidebar.write(f"Lead Time: {lead_time} months")
st.sidebar.write(f"Basic: CV < {service_basic} : Z-Score = {z_score_basic}")
st.sidebar.write(f"Regular: {service_regular_min} ≤ CV ≤ {service_regular_max} : Z-Score = {z_score_regular}")
st.sidebar.write(
    f"Seasonal: CV > {service_seasonal} : Z-Score IN season = {z_score_seasonal_1}, Z-Score OUT of season = {z_score_seasonal_2}")
st.sidebar.write(f"New: months < {service_new} : Z-Score = {z_score_new}")

st.sidebar.markdown("---")
st.sidebar.subheader("View Options")
group_by_model = st.sidebar.checkbox("Group by Model (first 5 chars)", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("Stock Data")
use_stock = st.sidebar.checkbox("Load stock data from data directory", value=True)

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


df = load_data()
analyzer = SalesAnalyzer(df)

if group_by_model:
    summary = analyzer.aggregate_by_model()
    id_column = 'MODEL'
else:
    summary = analyzer.aggregate_by_sku()
    id_column = 'SKU'

summary = analyzer.classify_sku_type(
    summary,
    cv_basic=service_basic,
    cv_seasonal=service_seasonal
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
    z_new=z_score_new
)

current_year_avg = analyzer.calculate_current_year_avg_sales(by_model=group_by_model)
summary = summary.merge(current_year_avg, on=id_column, how='left')
summary['CURRENT_YEAR_AVG'] = summary['CURRENT_YEAR_AVG'].fillna(0)

stock_loaded = False
if use_stock:
    stock_df, stock_filename = load_stock()

    if stock_df is not None:
        stock_df = stock_df.rename(columns={
            'sku': 'SKU',
            'nazwa': 'DESCRIPTION',
            'available_stock': 'STOCK'
        })

        if group_by_model:
            stock_df['MODEL'] = stock_df['SKU'].astype(str).str[:5]
            stock_agg = stock_df.groupby('MODEL', as_index=False).agg({
                'STOCK': 'sum',
                'DESCRIPTION': 'first'
            })
            summary = summary.merge(stock_agg, on='MODEL', how='left')
        else:
            summary = summary.merge(stock_df, on='SKU', how='left')

        summary['BELOW_ROP'] = summary['STOCK'] < summary['ROP']
        summary['DEFICIT'] = summary['ROP'] - summary['STOCK']
        summary['DEFICIT'] = summary['DEFICIT'].apply(lambda x: max(0, x))
        summary['OVERSTOCKED_%'] = ((summary['STOCK'] - summary['ROP']) / summary['ROP'] * 100).round(1)

        stock_loaded = True
    else:
        st.warning("No stock file found in data directory. Expected format: YYYYMMDD.csv or YYYYMMDD.xlsx")

if stock_loaded:
    column_order = [id_column, 'DESCRIPTION', 'TYPE', 'STOCK', 'ROP', 'OVERSTOCKED_%', 'DEFICIT', 'MONTHS', 'QUANTITY',
                    'AVERAGE SALES', 'CURRENT_YEAR_AVG', 'SS', 'BELOW_ROP']
else:
    column_order = [id_column, 'TYPE', 'MONTHS', 'QUANTITY', 'AVERAGE SALES', 'CURRENT_YEAR_AVG', 'SS', 'ROP']

summary = summary[column_order]

col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    search_label = "Search for Model:" if group_by_model else "Search for SKU:"
    search_placeholder = "Enter Model or partial Model..." if group_by_model else "Enter SKU or partial SKU..."
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
    type_filter = st.multiselect("Filter by Type:", options=['basic', 'regular', 'seasonal', 'new'], default=[])

overstock_threshold = 20
show_overstocked = False

if stock_loaded:
    st.markdown("**Overstocked Filter:**")
    col_over1, col_over2 = st.columns([1, 3])
    with col_over1:
        show_overstocked = st.checkbox("Show overstocked items", value=False)
    with col_over2:
        if show_overstocked:
            overstock_threshold = st.slider("Overstocked by %:", min_value=0, max_value=200, value=20, step=5)

filtered_summary = summary.copy()

if search_term:
    filtered_summary = filtered_summary[
        filtered_summary[id_column].astype(str).str.contains(search_term, case=False, na=False)]

if show_only_below_rop and 'BELOW_ROP' in filtered_summary.columns:
    filtered_summary = filtered_summary[filtered_summary['BELOW_ROP'] == True]

if show_bestsellers:
    filtered_summary = filtered_summary[filtered_summary['CURRENT_YEAR_AVG'] > 300]

if stock_loaded and show_overstocked and 'OVERSTOCKED_%' in filtered_summary.columns:
    filtered_summary = filtered_summary[filtered_summary['OVERSTOCKED_%'] >= overstock_threshold]

if type_filter:
    filtered_summary = filtered_summary[filtered_summary['TYPE'].isin(type_filter)]

item_label = "Model(s)" if group_by_model else "SKU(s)"
st.write(f"Showing {len(filtered_summary)} of {len(summary)} {item_label}")

st.markdown("""
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
""", unsafe_allow_html=True)

if stock_loaded:
    st.dataframe(
        filtered_summary,
        width="stretch",
        height=600
    )
else:
    st.dataframe(
        filtered_summary,
        width="stretch",
        height=600
    )

st.subheader("TYPE")
display_data = filtered_summary
type_counts = display_data['TYPE'].value_counts()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Basic", type_counts.get('basic', 0))
col2.metric("Regular", type_counts.get('regular', 0))
col3.metric("Seasonal", type_counts.get('seasonal', 0))
col4.metric("New", type_counts.get('new', 0))

if stock_loaded:
    st.subheader("Stock Status")

    col1, col2, col3 = st.columns(3)
    below_rop_count = 0
    total_deficit = 0
    valid_stock_count = 0

    if 'STOCK' in display_data.columns and 'BELOW_ROP' in display_data.columns:
        valid_stock = display_data[display_data['STOCK'].notna()]
        valid_stock_count = len(valid_stock)
        below_rop_count = int(valid_stock['BELOW_ROP'].sum())

        items_below_rop = valid_stock[valid_stock['BELOW_ROP'] == True]
        total_deficit = items_below_rop['DEFICIT'].sum() if len(items_below_rop) > 0 else 0

    col1.metric("Below ROP", int(below_rop_count), delta=None, delta_color="inverse")
    col2.metric("Total Deficit (units)", f"{total_deficit:,.0f}")
    col3.metric("% Below ROP", f"{(below_rop_count / valid_stock_count * 100):.1f}%" if valid_stock_count > 0 else "0%")

col1, col2 = st.columns(2)
col1.metric("Total SKUs", len(display_data))
col2.metric("Total Quantity", f"{display_data['QUANTITY'].sum():,.0f}")

download_label = "Download Model Summary CSV" if group_by_model else "Download SKU Summary CSV"
download_filename = "model_summary.csv" if group_by_model else "sku_summary.csv"
st.download_button(
    download_label,
    display_data.to_csv(index=False),
    download_filename,
    "text/csv"
)
