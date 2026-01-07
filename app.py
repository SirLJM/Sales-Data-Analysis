from __future__ import annotations

import streamlit as st

from utils.logging_config import setup_logging

setup_logging()

from ui import sidebar
from ui import tab_forecast_accuracy
from ui import tab_forecast_comparison
from ui import tab_ml_forecast
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

TAB_NAMES = [
    "📊 Sales & Inventory Analysis",
    "✂️ Size Pattern Optimizer",
    "📋 Weekly Analysis",
    "📆 Monthly Analysis",
    "🎯 Order Recommendations",
    "🛒 Order Creation",
    "🚚 Order Tracking",
    "📈 Forecast Accuracy",
    "🔬 Forecast Comparison",
    "🤖 ML Forecast",
]


def _render_nav_buttons():
    import streamlit.components.v1 as components
    for i, name in enumerate(TAB_NAMES):
        components.html(f"""
        <button onclick="
            var tabs = window.parent.document.querySelectorAll('button[data-baseweb=&quot;tab&quot;]');
            if (tabs && tabs[{i}]) tabs[{i}].click();
            var popoverBtn = window.parent.document.querySelector('button[data-testid=&quot;stPopoverButton&quot;]');
            if (popoverBtn) popoverBtn.click();
        " style="
            display: block;
            width: 100%;
            padding: 10px 14px;
            margin: 2px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            cursor: pointer;
            text-align: left;
            font-size: 13px;
        ">{name}</button>
        """, height=42)


col_nav, col_spacer = st.columns([0.08, 0.92])
with col_nav:
    with st.popover("☰"):
        _render_nav_buttons()

tabs = st.tabs(TAB_NAMES)

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

with tabs[9]:
    tab_ml_forecast.render()
