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


NAV_INJECT_JS = """
<script>
(function() {
    if (window.parent.document.getElementById('nav-menu-injected')) return;

    var tabsContainer = window.parent.document.querySelector('div[data-testid="stTabs"]');
    if (!tabsContainer) return;

    var navHtml = `
    <div id="nav-menu-injected" style="position:absolute;left:-40px;top:0;z-index:1000;">
        <button id="nav-btn" style="background:transparent;border:none;font-size:20px;cursor:pointer;padding:4px 8px;border-radius:4px;">☰</button>
        <div id="nav-dropdown" style="display:none;position:absolute;top:100%;left:0;background:white;border:1px solid #ddd;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.15);min-width:220px;padding:4px;">
            """ + "".join([
                f'<button class="nav-item" data-idx="{i}" style="display:block;width:100%;padding:6px 10px;border:none;background:transparent;text-align:left;cursor:pointer;font-size:12px;border-radius:3px;">{name}</button>'
                for i, name in enumerate(TAB_NAMES)
            ]) + """
        </div>
    </div>`;

    tabsContainer.style.position = 'relative';
    tabsContainer.style.marginLeft = '45px';
    tabsContainer.insertAdjacentHTML('afterbegin', navHtml);

    var btn = window.parent.document.getElementById('nav-btn');
    var dropdown = window.parent.document.getElementById('nav-dropdown');

    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    });

    dropdown.querySelectorAll('.nav-item').forEach(function(item) {
        item.addEventListener('mouseover', function() { this.style.background = '#f5f5f5'; });
        item.addEventListener('mouseout', function() { this.style.background = 'transparent'; });
        item.addEventListener('click', function() {
            var idx = parseInt(this.getAttribute('data-idx'));
            var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
            if (tabs[idx]) tabs[idx].click();
            dropdown.style.display = 'none';
        });
    });

    window.parent.document.addEventListener('click', function(e) {
        if (!e.target.closest('#nav-menu-injected')) {
            dropdown.style.display = 'none';
        }
    });
})();
</script>
"""

import streamlit.components.v1 as components
components.html(NAV_INJECT_JS, height=0)

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
