from __future__ import annotations

import streamlit as st

from ui.constants import SessionKeys
from ui.i18n import t, Keys, set_language, get_language
from ui.shared.session_manager import get_settings, set_session_value
from utils.logging_config import get_logger
from utils.settings_manager import reset_settings, save_settings

logger = get_logger("sidebar")


def render_sidebar() -> dict:
    settings = get_settings()

    _render_language_selector()
    st.sidebar.header(t(Keys.SIDEBAR_PARAMETERS))

    _render_save_reset_buttons(settings)
    _render_lead_time_section(settings)
    params = _render_service_levels_section(settings)
    _render_optimizer_section(settings)
    _render_current_parameters_summary(settings, params)
    view_options = _render_view_options()
    data_options = _render_data_options()

    return {
        "group_by_model": view_options["group_by_model"],
        "use_stock": data_options["use_stock"],
        "use_forecast": data_options["use_forecast"],
    }


def _render_language_selector() -> None:
    languages = {"en": "🇬🇧 English", "pl": "🇵🇱 Polski"}

    if "app_language" not in st.session_state:
        st.session_state["app_language"] = get_language()
    else:
        set_language(st.session_state["app_language"])

    selected = st.sidebar.selectbox(
        "🌐 Language / Język",
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(st.session_state["app_language"]),
        key="language_selector",
    )

    if selected != st.session_state["app_language"]:
        logger.info("Language changed from %s to %s", st.session_state["app_language"], selected)
        st.session_state["app_language"] = selected
        set_language(selected)
        st.rerun()


def _render_save_reset_buttons(settings: dict) -> None:
    col_save, col_reset = st.sidebar.columns(2)
    with col_save:
        if st.button(t(Keys.BTN_SAVE), key="save_settings", help="Save current parameters to settings.json"):
            logger.info("Save settings button clicked")
            if save_settings(settings):
                logger.info("Settings saved successfully")
                st.success(f"✅ {t(Keys.MSG_SAVED)}")
            else:
                logger.error("Failed to save settings")
                st.error(f"❌ {t(Keys.MSG_SAVE_FAILED)}")
    with col_reset:
        if st.button(t(Keys.BTN_RESET), key="reset_settings", help="Reset to default values"):
            logger.info("Reset settings button clicked")
            set_session_value(SessionKeys.SETTINGS, reset_settings())
            st.rerun()


def _render_lead_time_section(settings: dict) -> None:
    st.sidebar.subheader(t(Keys.SIDEBAR_LEAD_TIME_FORECAST))

    old_lead_time = settings["lead_time"]
    lead_time = st.sidebar.number_input(
        t(Keys.LEAD_TIME_MONTHS),
        min_value=0.0,
        max_value=100.0,
        value=settings["lead_time"],
        step=0.01,
        format="%.2f",
        key="lead_time_input",
        help=t(Keys.LEAD_TIME_HELP),
    )
    if lead_time != old_lead_time:
        logger.info("Lead time changed from %.2f to %.2f months", old_lead_time, lead_time)
    settings["lead_time"] = lead_time

    sync_forecast = st.sidebar.checkbox(
        t(Keys.SYNC_FORECAST),
        value=settings["sync_forecast_with_lead_time"],
        key="sync_forecast_checkbox",
        help=t(Keys.SYNC_FORECAST_HELP),
    )
    settings["sync_forecast_with_lead_time"] = sync_forecast

    if sync_forecast:
        settings["forecast_time"] = lead_time
    else:
        forecast_time = st.sidebar.number_input(
            t(Keys.FORECAST_TIME_MONTHS),
            min_value=0.0,
            max_value=100.0,
            value=float(settings["forecast_time"]),
            step=0.01,
            format="%.2f",
            key="forecast_time_input",
            help=t(Keys.FORECAST_TIME_HELP),
        )
        settings["forecast_time"] = forecast_time


def _render_service_levels_section(settings: dict) -> dict:
    st.sidebar.subheader(t(Keys.SIDEBAR_SERVICE_LEVELS))

    header_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with header_cols[0]:
        st.write(t(Keys.COL_TYPE))
    with header_cols[1]:
        st.write(t(Keys.COL_CV))
    with header_cols[2]:
        st.write(t(Keys.COL_ZSCORE))
    with header_cols[3]:
        st.write(t(Keys.COL_ZSCORE))

    service_basic = _render_basic_row(settings)
    z_score_regular = _render_regular_row(settings)
    service_seasonal, z_score_seasonal_1, z_score_seasonal_2 = _render_seasonal_row(
        settings, service_basic
    )
    service_new, z_score_new = _render_new_row(settings)

    return {
        "service_basic": service_basic,
        "z_score_regular": z_score_regular,
        "service_seasonal": service_seasonal,
        "z_score_seasonal_1": z_score_seasonal_1,
        "z_score_seasonal_2": z_score_seasonal_2,
        "service_new": service_new,
        "z_score_new": z_score_new,
    }


def _render_basic_row(settings: dict) -> float:
    basic_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with basic_cols[0]:
        st.write(t(Keys.TYPE_BASIC))
    with basic_cols[1]:
        service_basic = st.number_input(
            "CV",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=1.0,
            value=settings["cv_thresholds"]["basic"],
            step=0.1,
            format="%.1f",
            key="basic_cv",
        )
        settings["cv_thresholds"]["basic"] = service_basic
    with basic_cols[2]:
        z_score_basic = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=settings["z_scores"]["basic"],
            step=0.001,
            format="%.3f",
            key="basic_z",
        )
        settings["z_scores"]["basic"] = z_score_basic
    with basic_cols[3]:
        st.write("-")
    return service_basic


def _render_regular_row(settings: dict) -> float:
    regular_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with regular_cols[0]:
        st.write(t(Keys.TYPE_REGULAR))
    with regular_cols[1]:
        st.write("-")
    with regular_cols[2]:
        z_score_regular = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=settings["z_scores"]["regular"],
            step=0.001,
            format="%.3f",
        )
        settings["z_scores"]["regular"] = z_score_regular
    with regular_cols[3]:
        st.write("-")
    return z_score_regular


def _render_seasonal_row(settings: dict, service_basic: float) -> tuple[float, float, float]:
    seasonal_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with seasonal_cols[0]:
        st.write(t(Keys.TYPE_SEASONAL))
    with seasonal_cols[1]:
        service_seasonal = st.number_input(
            "CV",
            label_visibility="collapsed",
            min_value=service_basic,
            max_value=10.0,
            value=settings["cv_thresholds"]["seasonal"],
            step=0.1,
            format="%.1f",
            key="seasonal_cv",
        )
        settings["cv_thresholds"]["seasonal"] = service_seasonal
    with seasonal_cols[2]:
        z_score_seasonal_1 = st.number_input(
            "Z-Score IN season",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=settings["z_scores"]["seasonal_in"],
            step=0.001,
            format="%.3f",
            key="seasonal_z1",
            placeholder="IN season",
        )
        settings["z_scores"]["seasonal_in"] = z_score_seasonal_1
    with seasonal_cols[3]:
        z_score_seasonal_2 = st.number_input(
            "Z-Score OUT of season",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=settings["z_scores"]["seasonal_out"],
            step=0.001,
            format="%.3f",
            key="seasonal_z2",
            placeholder="OUT of season",
        )
        settings["z_scores"]["seasonal_out"] = z_score_seasonal_2
    return service_seasonal, z_score_seasonal_1, z_score_seasonal_2


def _render_new_row(settings: dict) -> tuple[int, float]:
    new_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with new_cols[0]:
        st.write(t(Keys.TYPE_NEW))
    with new_cols[1]:
        service_new = st.number_input(
            "CV",
            label_visibility="collapsed",
            min_value=12,
            max_value=24,
            value=settings["new_product_threshold_months"],
            step=1,
            key="new_cv",
        )
        settings["new_product_threshold_months"] = service_new
    with new_cols[2]:
        z_score_new = st.number_input(
            "Z-Score",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=10.0,
            value=settings["z_scores"]["new"],
            step=0.001,
            format="%.3f",
            key="new_z",
        )
        settings["z_scores"]["new"] = z_score_new
    with new_cols[3]:
        st.write("-")
    return service_new, z_score_new


def _render_optimizer_section(settings: dict) -> None:
    st.sidebar.subheader(t(Keys.SIDEBAR_PATTERN_OPTIMIZER))

    algorithm_mode = st.sidebar.radio(
        t(Keys.COL_ALGORITHM),
        options=["greedy_overshoot", "greedy_classic"],
        format_func=lambda x: (
            t(Keys.ALG_GREEDY_OVERSHOOT) if x == "greedy_overshoot" else t(Keys.ALG_CLASSIC_GREEDY)
        ),
        index=(
            0
            if settings.get("optimizer", {}).get("algorithm_mode", "greedy_overshoot")
               == "greedy_overshoot"
            else 1
        ),
        key="sidebar_algorithm_mode",
        help=t(Keys.ALG_HELP),
    )
    if "optimizer" not in settings:
        settings["optimizer"] = {}
    settings["optimizer"]["algorithm_mode"] = algorithm_mode


def _render_current_parameters_summary(settings: dict, params: dict) -> None:
    st.sidebar.markdown("---")
    st.sidebar.write(f"**{t(Keys.SIDEBAR_CURRENT_PARAMS)}**")

    lead_time = settings["lead_time"]
    forecast_time = settings["forecast_time"]
    sync_forecast = settings["sync_forecast_with_lead_time"]

    st.sidebar.write(f"{t(Keys.LEAD_TIME_MONTHS)}: {lead_time}")
    if sync_forecast:
        st.sidebar.write(f"{t(Keys.FORECAST_TIME_MONTHS)}: {forecast_time} ({t(Keys.SYNC_FORECAST).lower()})")
    else:
        st.sidebar.write(f"{t(Keys.FORECAST_TIME_MONTHS)}: {forecast_time}")

    service_basic = params["service_basic"]
    z_score_basic = settings["z_scores"]["basic"]
    z_score_regular = params["z_score_regular"]
    service_seasonal = params["service_seasonal"]
    z_score_seasonal_1 = params["z_score_seasonal_1"]
    z_score_seasonal_2 = params["z_score_seasonal_2"]
    service_new = params["service_new"]
    z_score_new = params["z_score_new"]

    st.sidebar.write(f"{t(Keys.TYPE_BASIC)}: CV < {service_basic} : Z-Score = {z_score_basic}")
    st.sidebar.write(
        f"{t(Keys.TYPE_REGULAR)}: {service_basic} ≤ CV ≤ {service_seasonal} : Z-Score = {z_score_regular}"
    )
    st.sidebar.write(
        f"{t(Keys.TYPE_SEASONAL)}: CV > {service_seasonal} : Z IN = {z_score_seasonal_1}, Z OUT = {z_score_seasonal_2}"
    )
    st.sidebar.write(f"{t(Keys.TYPE_NEW)}: months < {service_new} : Z-Score = {z_score_new}")

    algorithm_mode = settings.get("optimizer", {}).get("algorithm_mode", "greedy_overshoot")
    algorithm_display = (
        t(Keys.ALG_GREEDY_OVERSHOOT)
        if algorithm_mode == "greedy_overshoot"
        else t(Keys.ALG_CLASSIC_GREEDY)
    )
    st.sidebar.write(f"{t(Keys.COL_ALGORITHM)}: {algorithm_display}")


def _render_view_options() -> dict:
    st.sidebar.markdown("---")
    st.sidebar.subheader(t(Keys.SIDEBAR_VIEW_OPTIONS))
    group_by_model = st.sidebar.checkbox(t(Keys.GROUP_BY_MODEL), value=False)
    return {"group_by_model": group_by_model}


def _render_data_options() -> dict:
    st.sidebar.markdown("---")
    st.sidebar.subheader(t(Keys.SIDEBAR_LOAD_DATA))
    use_stock = st.sidebar.checkbox(t(Keys.LOAD_STOCK_DATA), value=True)
    use_forecast = st.sidebar.checkbox(t(Keys.LOAD_FORECAST_DATA), value=True)
    return {"use_stock": use_stock, "use_forecast": use_forecast}
