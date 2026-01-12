from __future__ import annotations

import streamlit as st

from utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("app")

logger.info("Application startup initiated")

from ui import sidebar
from ui import tab_forecast_accuracy
from ui import tab_forecast_comparison
from ui import tab_ml_forecast
from ui import tab_monthly_analysis
from ui import tab_nlq
from ui import tab_order_creation
from ui import tab_order_recommendations
from ui import tab_order_tracking
from ui import tab_pattern_optimizer
from ui import tab_sales_analysis
from ui import tab_task_planner
from ui import tab_weekly_analysis
from ui.i18n import t, Keys, get_tab_names
from ui.shared.session_manager import initialize_session_state
from ui.shared.styles import INPUT_FIELD_STYLE, RESPONSIVE_TABS_STYLE

logger.info("Configuring Streamlit page")

st.set_page_config(page_title=t(Keys.PAGE_TITLE), page_icon="📊", layout="wide")

st.markdown(RESPONSIVE_TABS_STYLE + INPUT_FIELD_STYLE, unsafe_allow_html=True)

initialize_session_state()

TAB_NAMES = get_tab_names()
logger.info("Application configured with %d tabs: %s", len(TAB_NAMES), TAB_NAMES)


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

logger.info("Rendering sidebar")
sidebar_options = sidebar.render_sidebar()

context = {
    "group_by_model": sidebar_options.get("group_by_model", False),
    "use_stock": sidebar_options.get("use_stock", True),
    "use_forecast": sidebar_options.get("use_forecast", True),
}

TAB_RENDERERS = [
    (tab_task_planner.render, False),
    (tab_sales_analysis.render, True),
    (tab_pattern_optimizer.render, False),
    (tab_weekly_analysis.render, True),
    (tab_monthly_analysis.render, False),
    (tab_order_recommendations.render, True),
    (tab_order_creation.render, True),
    (tab_order_tracking.render, False),
    (tab_forecast_accuracy.render, True),
    (tab_forecast_comparison.render, False),
    (tab_ml_forecast.render, False),
    (tab_nlq.render, True),
]

for i, (renderer, needs_context) in enumerate(TAB_RENDERERS):
    with tabs[i]:
        renderer(context) if needs_context else renderer()

logger.info("Application render cycle completed")
