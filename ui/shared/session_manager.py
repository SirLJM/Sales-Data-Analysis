from __future__ import annotations

from typing import Any

import streamlit as st

from ui.constants import Config, SessionKeys


def initialize_session_state() -> None:
    from sales_data.data_source_factory import DataSourceFactory
    from utils.pattern_optimizer import load_pattern_sets
    from utils.settings_manager import load_settings
    from utils.task_manager import load_tasks

    defaults: dict[str, Any] = {
        SessionKeys.SETTINGS: load_settings,
        SessionKeys.DATA_SOURCE: DataSourceFactory.create_data_source,
        SessionKeys.PATTERN_SETS: load_pattern_sets,
        SessionKeys.ACTIVE_SET_ID: None,
        SessionKeys.SHOW_ADD_PATTERN_SET: False,
        SessionKeys.EDIT_SET_ID: None,
        SessionKeys.NUM_PATTERNS: Config.DEFAULT_NUM_PATTERNS,
        SessionKeys.NUM_SIZES: Config.DEFAULT_NUM_SIZES,
        SessionKeys.RECOMMENDATIONS_DATA: None,
        SessionKeys.RECOMMENDATIONS_TOP_N: Config.DEFAULT_TOP_N,
        SessionKeys.SELECTED_ORDER_ITEMS: [],
        SessionKeys.SZWALNIA_INCLUDE_FILTER: [],
        SessionKeys.SZWALNIA_EXCLUDE_FILTER: [],
        SessionKeys.MONTHLY_YOY_PODGRUPA: None,
        SessionKeys.MONTHLY_YOY_KATEGORIA: None,
        SessionKeys.MONTHLY_YOY_METADATA: None,
        SessionKeys.TASKS: load_tasks,
        SessionKeys.TASK_FILTER_STATUS: "all",
        SessionKeys.TASK_FILTER_PRIORITY: "all",
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default() if callable(default) else default

    if st.session_state.get(SessionKeys.ACTIVE_SET_ID) is None:
        pattern_sets = st.session_state.get(SessionKeys.PATTERN_SETS, [])
        if pattern_sets:
            st.session_state[SessionKeys.ACTIVE_SET_ID] = pattern_sets[0].id


def get_settings() -> dict:
    return st.session_state[SessionKeys.SETTINGS]


def get_data_source():
    return st.session_state[SessionKeys.DATA_SOURCE]


def get_session_value(key: str, default: Any = None) -> Any:
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any) -> None:
    st.session_state[key] = value


def get_pattern_sets() -> list:
    return st.session_state.get(SessionKeys.PATTERN_SETS, [])


def get_active_pattern_set():
    active_id = st.session_state.get(SessionKeys.ACTIVE_SET_ID)
    if active_id is None:
        return None
    pattern_sets = get_pattern_sets()
    for ps in pattern_sets:
        if ps.id == active_id:
            return ps
    return None
