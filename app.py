from __future__ import annotations

import streamlit as st

from ui import sidebar
from ui import tab_forecast_accuracy
from ui import tab_monthly_analysis
from ui import tab_order_creation
from ui import tab_order_recommendations
from ui import tab_order_tracking
from ui import tab_pattern_optimizer
from ui import tab_sales_analysis
from ui import tab_weekly_analysis
from ui.shared.session_manager import initialize_session_state

st.set_page_config(page_title="Inventory & Pattern Optimizer", page_icon="📊", layout="wide")

initialize_session_state()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Sales & Inventory Analysis",
    "📦 Size Pattern Optimizer",
    "📅 Weekly Analysis",
    "📆 Monthly Analysis",
    "🎯 Order Recommendations",
    "📋 Order Creation",
    "📦 Order Tracking",
    "🎯 Forecast Accuracy",
])

sidebar_options = sidebar.render_sidebar()

context = {
    "group_by_model": sidebar_options.get("group_by_model", False),
    "use_stock": sidebar_options.get("use_stock", True),
    "use_forecast": sidebar_options.get("use_forecast", True),
}

with tab1:
    tab_sales_analysis.render(context)

with tab2:
    tab_pattern_optimizer.render()

with tab3:
    tab_weekly_analysis.render(context)

with tab4:
    tab_monthly_analysis.render()

with tab5:
    tab_order_recommendations.render(context)

with tab6:
    tab_order_creation.render(context)

with tab7:
    tab_order_tracking.render()

with tab8:
    tab_forecast_accuracy.render(context)
