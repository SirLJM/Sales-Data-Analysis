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
# st.sidebar.markdown("**Configuration:**")
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
st.sidebar.write(f"Seasonal: CV > {service_seasonal} : Z-Score IN season = {z_score_seasonal_1}, Z-Score OUT of season = {z_score_seasonal_2}")
st.sidebar.write(f"New: months < {service_new} : Z-Score = {z_score_new}")

@st.cache_data
def load_data():
    loader = SalesDataLoader()
    return loader.get_aggregated_data()


df = load_data()
analyzer = SalesAnalyzer(df)

st.header("SKU Aggregation")
sku_summary = analyzer.aggregate_by_sku()

sku_summary = analyzer.classify_sku_type(
    sku_summary,
    cv_basic=service_basic,
    cv_seasonal=service_seasonal,
    months_new=service_new)

seasonal_data = analyzer.determine_seasonal_months()

sku_summary = analyzer.calculate_safety_stock_and_rop(
    sku_summary,
    seasonal_data,
    lead_time=lead_time,
    z_basic=z_score_basic,
    z_regular=z_score_regular,
    z_seasonal_in=z_score_seasonal_1,
    z_seasonal_out=z_score_seasonal_2,
    z_new=z_score_new
)

column_order = ['SKU', 'TYPE', 'MONTHS', 'QUANTITY', 'AVERAGE SALES', 'SD', 'CV', 'SS', 'ROP']
sku_summary = sku_summary[column_order]

st.subheader("SKU SEARCH")
search_term = st.text_input("Search SKU", placeholder="Enter SKU or partial SKU...")
if search_term:
    filtered_summary = sku_summary[sku_summary['SKU'].astype(str).str.contains(search_term, case=False, na=False)]
    st.write(f"Found {len(filtered_summary)} SKUs matching '{search_term}':")
    st.dataframe(filtered_summary, width="stretch", height=600)
else:
    st.dataframe(sku_summary, width="stretch", height=600)


st.subheader("TYPE")
type_counts = sku_summary['TYPE'].value_counts()
display_data = filtered_summary if search_term else sku_summary
type_counts = display_data['TYPE'].value_counts()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Basic", type_counts.get('basic', 0))
col2.metric("Regular", type_counts.get('regular', 0))
col3.metric("Seasonal", type_counts.get('seasonal', 0))
col4.metric("New", type_counts.get('new', 0))

col1, col2 = st.columns(2)
col1.metric("Total SKUs", len(display_data))
col2.metric("Total Quantity", f"{display_data['QUANTITY'].sum():,.0f}")

st.download_button(
    "Download SKU Summary CSV",
    display_data.to_csv(index=False),
    "sku_summary.csv",
    "text/csv"
)

