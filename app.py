from __future__ import annotations

import streamlit as st

from utils.logging_config import setup_logging

setup_logging()

from ui import sidebar
from ui import tab_forecast_accuracy
from ui import tab_forecast_comparison
from ui import tab_monthly_analysis
from ui import tab_order_creation
from ui import tab_order_recommendations
from ui import tab_order_tracking
from ui import tab_pattern_optimizer
from ui import tab_sales_analysis
from ui import tab_weekly_analysis
from ui.shared.session_manager import initialize_session_state
from ui.shared.styles import RESPONSIVE_TABS_STYLE

st.set_page_config(page_title="Inventory & Pattern Optimizer", page_icon="📊", layout="wide")

st.markdown(RESPONSIVE_TABS_STYLE, unsafe_allow_html=True)

initialize_session_state()

tabs = st.tabs([
    "📊 Sales & Inventory Analysis",
    "✂️ Size Pattern Optimizer",
    "📋 Weekly Analysis",
    "📆 Monthly Analysis",
    "🎯 Order Recommendations",
    "🛒 Order Creation",
    "🚚 Order Tracking",
    "📈 Forecast Accuracy",
    "🔬 Forecast Comparison",
])

sidebar_options = sidebar.render_sidebar()

context = {
    "group_by_model": sidebar_options.get("group_by_model", False),
    "use_stock": sidebar_options.get("use_stock", True),
    "use_forecast": sidebar_options.get("use_forecast", True),
}

with tabs[0]:
    tab_sales_analysis.render(context)

with tabs[1]:
    tab_pattern_optimizer.render()

with tabs[2]:
    tab_weekly_analysis.render(context)

with tabs[3]:
    tab_monthly_analysis.render()

with tabs[4]:
    tab_order_recommendations.render(context)

with tabs[5]:
    tab_order_creation.render(context)

with tabs[6]:
    tab_order_tracking.render()

with tabs[7]:
    tab_forecast_accuracy.render(context)

with tabs[8]:
    tab_forecast_comparison.render()
