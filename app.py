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
from ui import tab_material_planning
from ui import tab_order_tracking
from ui import tab_pattern_optimizer
from ui import tab_sales_analysis
from ui import tab_task_planner
from ui import tab_weekly_analysis
from ui.i18n import t, Keys, get_tab_names
from ui.shared.data_loaders import load_all_data_with_progress
from ui.shared.navigation import render_navigation_menu
from ui.shared.session_manager import initialize_session_state
from ui.shared.styles import INPUT_FIELD_STYLE, RESPONSIVE_TABS_STYLE

logger.info("Configuring Streamlit page")

st.set_page_config(page_title=t(Keys.PAGE_TITLE), page_icon="📊", layout="wide")
st.markdown(RESPONSIVE_TABS_STYLE + INPUT_FIELD_STYLE, unsafe_allow_html=True)

initialize_session_state()
load_all_data_with_progress()

TAB_NAMES = get_tab_names()
render_navigation_menu(TAB_NAMES)

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
    (tab_material_planning.render, False),
    (tab_forecast_accuracy.render, True),
    (tab_forecast_comparison.render, False),
    (tab_ml_forecast.render, False),
    (tab_nlq.render, True),
]

for i, (renderer, needs_context) in enumerate(TAB_RENDERERS):
    with tabs[i]:
        renderer(context) if needs_context else renderer()
