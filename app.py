import sys

import streamlit as st

sys.path.insert(0, 'src')
from sales_data import SalesDataLoader, SalesAnalyzer

st.title("Sales Data Analysis")

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

st.metric("Total SKUs", len(sku_summary))
st.metric("Total Quantity", f"{sku_summary['total_quantity'].sum():,}")