from __future__ import annotations

import streamlit as st

from ui.constants import AlgorithmModes, SessionKeys
from ui.shared.session_manager import get_settings, set_session_value
from utils.settings_manager import reset_settings, save_settings


def render_sidebar() -> dict:
    settings = get_settings()

    st.sidebar.header("Parameters")

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


def _render_save_reset_buttons(settings: dict) -> None:
    col_save, col_reset = st.sidebar.columns(2)
    with col_save:
        if st.button(
            "💾 Save", key="save_settings", help="Save current parameters to settings.json"
        ):
            if save_settings(settings):
                st.success("✅ Saved!")
            else:
                st.error("❌ Save failed")
    with col_reset:
        if st.button("🔄 Reset", key="reset_settings", help="Reset to default values"):
            set_session_value(SessionKeys.SETTINGS, reset_settings())
            st.rerun()


def _render_lead_time_section(settings: dict) -> None:
    st.sidebar.subheader("Lead Time & Forecast")

    lead_time = st.sidebar.number_input(
        "Lead time in months",
        min_value=0.0,
        max_value=100.0,
        value=settings["lead_time"],
        step=0.01,
        format="%.2f",
        key="lead_time_input",
        help="Time between order placement and receipt (used in ROP and SS calculations)",
    )
    settings["lead_time"] = lead_time

    sync_forecast = st.sidebar.checkbox(
        "Sync forecast time with lead time",
        value=settings["sync_forecast_with_lead_time"],
        key="sync_forecast_checkbox",
        help="When enabled, forecast time automatically matches lead time",
    )
    settings["sync_forecast_with_lead_time"] = sync_forecast

    if sync_forecast:
        settings["forecast_time"] = lead_time
    else:
        forecast_time = st.sidebar.number_input(
            "Forecast time in months",
            min_value=0.0,
            max_value=100.0,
            value=float(settings["forecast_time"]),
            step=0.01,
            format="%.2f",
            key="forecast_time_input",
            help="Time period for forecast calculations (independent of lead time when sync is off)",
        )
        settings["forecast_time"] = forecast_time


def _render_service_levels_section(settings: dict) -> dict:
    st.sidebar.subheader("Service Levels")

    header_cols = st.sidebar.columns([2, 1.5, 1.5, 1.5])
    with header_cols[0]:
        st.write("Type")
    with header_cols[1]:
        st.write("CV")
    with header_cols[2]:
        st.write("Z-Score")
    with header_cols[3]:
        st.write("Z-Score")

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
        st.write("Basic")
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
        st.write("Regular")
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
        st.write("Seasonal")
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
        st.write("New")
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
    st.sidebar.subheader("Pattern Optimizer")

    algorithm_mode = st.sidebar.radio(
        "Algorithm",
        options=["greedy_overshoot", "greedy_classic"],
        format_func=lambda x: (
            AlgorithmModes.GREEDY_OVERSHOOT if x == "greedy_overshoot" else AlgorithmModes.CLASSIC_GREEDY
        ),
        index=(
            0
            if settings.get("optimizer", {}).get("algorithm_mode", "greedy_overshoot")
            == "greedy_overshoot"
            else 1
        ),
        key="sidebar_algorithm_mode",
        help="Greedy Overshoot: Better coverage with slightly higher excess. Classic Greedy: Minimal excess but may undercover.",
    )
    if "optimizer" not in settings:
        settings["optimizer"] = {}
    settings["optimizer"]["algorithm_mode"] = algorithm_mode


def _render_current_parameters_summary(settings: dict, params: dict) -> None:
    st.sidebar.markdown("---")
    st.sidebar.write("**Current Parameters:**")

    lead_time = settings["lead_time"]
    forecast_time = settings["forecast_time"]
    sync_forecast = settings["sync_forecast_with_lead_time"]

    st.sidebar.write(f"Lead Time: {lead_time} months")
    if sync_forecast:
        st.sidebar.write(f"Forecast Time: {forecast_time} months (synced with lead time)")
    else:
        st.sidebar.write(f"Forecast Time: {forecast_time} months")

    service_basic = params["service_basic"]
    z_score_basic = settings["z_scores"]["basic"]
    z_score_regular = params["z_score_regular"]
    service_seasonal = params["service_seasonal"]
    z_score_seasonal_1 = params["z_score_seasonal_1"]
    z_score_seasonal_2 = params["z_score_seasonal_2"]
    service_new = params["service_new"]
    z_score_new = params["z_score_new"]

    st.sidebar.write(f"Basic: CV < {service_basic} : Z-Score = {z_score_basic}")
    st.sidebar.write(
        f"Regular: {service_basic} ≤ CV ≤ {service_seasonal} : Z-Score = {z_score_regular}"
    )
    st.sidebar.write(
        f"Seasonal: CV > {service_seasonal} : Z-Score IN season = {z_score_seasonal_1}, Z-Score OUT of season = {z_score_seasonal_2}"
    )
    st.sidebar.write(f"New: months < {service_new} : Z-Score = {z_score_new}")

    algorithm_mode = settings.get("optimizer", {}).get("algorithm_mode", "greedy_overshoot")
    algorithm_display = (
        AlgorithmModes.GREEDY_OVERSHOOT
        if algorithm_mode == "greedy_overshoot"
        else AlgorithmModes.CLASSIC_GREEDY
    )
    st.sidebar.write(f"Optimizer Algorithm: {algorithm_display}")


def _render_view_options() -> dict:
    st.sidebar.markdown("---")
    st.sidebar.subheader("View Options")
    group_by_model = st.sidebar.checkbox("Group by Model (first 5 chars)", value=False)
    return {"group_by_model": group_by_model}


def _render_data_options() -> dict:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Load additional data")
    use_stock = st.sidebar.checkbox("Load stock data from data directory", value=True)
    use_forecast = st.sidebar.checkbox("Load forecast data from data directory", value=True)
    return {"use_stock": use_stock, "use_forecast": use_forecast}
