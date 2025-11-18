import streamlit as st

from sales_data import SalesDataLoader, SalesAnalyzer

st.title("Sales Data Analysis")

st.sidebar.header("Parameters")

st.sidebar.subheader("Lead Time")
lead_time = st.sidebar.number_input(
    "Lead time in months",
    min_value=0.0,
    max_value=100.0,
    value=1.36,
    step=0.01,
    format="%.2f"
)

st.sidebar.subheader("Service Levels")
st.sidebar.write("**Basic**")
col1, col2 = st.sidebar.columns(2)
with col1:
    service_basic = st.sidebar.number_input(
        "CV",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.1,
        format="%.1f",
        key="basic_cv",
        help="Products with coefficient of variation below this value"
    )
with col2:
    z_score_basic = st.sidebar.number_input(
        "Z-Score",
        min_value=0.0,
        max_value=10.0,
        value=2.05,
        step=0.001,
        format="%.3f",
        key="basic_z",
        help="Products with Z-Score"
    )

st.sidebar.write("**Regular**")
z_score_regular = st.sidebar.number_input(
    "Z-Score",
    min_value=0.0,
    max_value=10.0,
    value=1.645,
    step=0.001,
    format="%.3f",
    help="Products with Z-Score"
)

st.sidebar.write("**Seasonal**")
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    service_seasonal = st.sidebar.number_input(
        "CV",
        min_value=service_basic,
        max_value=10.0,
        value=1.0,
        step=0.1,
        format="%.1f",
        key="seasonal_cv",
        help="Products with coefficient of variation above this value"
    )
with col2:
    z_score_seasonal_1 = st.sidebar.number_input(
        "Z-Score IN season",
        min_value=0.0,
        max_value=10.0,
        value=1.75,
        step=0.001,
        format="%.3f",
        key="seasonal_z1",
        help="Products with Z-Score"
    )
with col3:
    z_score_seasonal_2 = st.sidebar.number_input(
        "Z-Score OUT of season",
        min_value=0.0,
        max_value=10.0,
        value=1.6,
        step=0.001,
        format="%.3f",
        key="seasonal_z2",
        help="Products with Z-Score"
    )

service_regular_min = service_basic
service_regular_max = service_seasonal

st.sidebar.write("**New**")
col1, col2 = st.sidebar.columns(2)
with col1:
    service_new = st.sidebar.number_input(
        "CV",
        min_value=12,
        max_value=24,
        value=12,
        step=1,
        key="new_cv",
        help="Products active for fewer than this many months"
    )
with col2:
    z_score_new = st.sidebar.number_input(
        "Z-Score",
        min_value=0.0,
        max_value=10.0,
        value=1.8,
        step=0.001,
        format="%.3f",
        key="new_z",
        help="Products with Z-Score"
    )

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

st.dataframe(sku_summary, use_container_width=True, height=600)

st.download_button(
    "Download SKU Summary CSV",
    sku_summary.to_csv(index=False),
    "sku_summary.csv",
    "text/csv"
)
