from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from ui.constants import ColumnNames, Config, Icons, SessionKeys
from ui.i18n import Keys, t
from utils.logging_config import get_logger

ORDER_COUNT = "Order Count"

MONTHLY_CAPACITY = "Monthly Capacity"

TOTAL_QUANTITY = "Total Quantity"

logger = get_logger("tab_order_tracking")


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Order Tracking")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_ORDER_TRACKING).format(error=str(e))}")


def _render_content() -> None:
    st.title(t(Keys.TITLE_ORDER_TRACKING))

    _init_pdf_parser_lookup_data()

    st.markdown("---")
    _render_pdf_upload()

    st.markdown("---")
    _render_manual_order_form()

    st.markdown("---")
    _render_active_orders()

    st.markdown("---")
    _render_facility_capacity()


def _init_pdf_parser_lookup_data() -> None:
    if st.session_state.get("_pdf_parser_initialized"):
        return
    from ui.shared import load_unique_categories, load_unique_facilities
    from utils.pdf_parser import set_lookup_data

    facilities = load_unique_facilities()
    categories = load_unique_categories()
    set_lookup_data(facilities, categories)
    st.session_state["_pdf_parser_initialized"] = True


@st.fragment
def _render_pdf_upload() -> None:
    from utils.order_manager import add_manual_order
    from utils.pdf_parser import parse_order_pdf

    st.subheader(t(Keys.TITLE_IMPORT_PDF))

    uploaded_file = st.file_uploader(
        t(Keys.UPLOAD_PDF),
        type=["pdf"],
        help=t(Keys.HELP_UPLOAD_PDF),
        key="pdf_upload",
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.info(f"{Icons.INFO} {t(Keys.FILE_UPLOADED).format(filename=uploaded_file.name)}")

        with col2:
            if st.button(t(Keys.BTN_PARSE_PDF), key="parse_pdf_btn", type="primary"):
                # noinspection PyTypeChecker
                with st.spinner(t(Keys.LABEL_PARSING_PDF)):
                    order_data = parse_order_pdf(uploaded_file)
                    if order_data:
                        st.session_state["parsed_order_data"] = order_data
                    else:
                        st.error(f"{Icons.ERROR} {t(Keys.FAILED_PARSE_PDF)}")

    if "parsed_order_data" in st.session_state:
        order_data = st.session_state["parsed_order_data"]
        st.success(f"{Icons.SUCCESS} {t(Keys.PDF_PARSED)}")
        _display_parsed_order(order_data)

        if st.button(t(Keys.BTN_CREATE_FROM_PDF), key="create_from_pdf_btn", type="primary"):
            order_id = f"ORD_{order_data.get('model', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if add_manual_order(order_id, order_data):
                st.success(f"{Icons.SUCCESS} {t(Keys.ORDER_CREATED_PDF).format(order_id=order_id)}")
                del st.session_state["parsed_order_data"]
                _invalidate_orders_cache()
                st.rerun()
            else:
                st.error(f"{Icons.ERROR} {t(Keys.FAILED_CREATE_ORDER)}")


def _display_parsed_order(order_data: dict) -> None:
    order_date = order_data.get('order_date')
    na_value = t(Keys.NA)
    date_str = order_date.strftime('%Y-%m-%d') if order_date else na_value

    parsed_df = pd.DataFrame([{
        t(Keys.ORDER_DATE): date_str,
        t(Keys.MODEL): order_data.get('model', na_value),
        t(Keys.PRODUCT): order_data.get('product_name', na_value),
        t(Keys.QUANTITY): order_data.get('total_quantity', na_value),
        t(Keys.FACILITY): order_data.get('facility', na_value),
        t(Keys.OPERATION): order_data.get('operation', na_value),
        t(Keys.MATERIAL): order_data.get('material', na_value),
    }])

    st.dataframe(parsed_df, hide_index=True)


@st.fragment
def _render_manual_order_form() -> None:
    from utils.order_manager import add_manual_order

    st.subheader(t(Keys.TITLE_MANUAL_ORDER))

    with st.form("manual_order_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            manual_order_date = st.date_input(
                t(Keys.ORDER_DATE),
                value=datetime.today(),
                help=t(Keys.HELP_ORDER_DATE),
            )
        with col2:
            manual_order_model = st.text_input(
                t(Keys.LABEL_MODEL_CODE),
                placeholder=t(Keys.PLACEHOLDER_MODEL_CODE),
            )
        with col3:
            manual_product_name = st.text_input(
                t(Keys.LABEL_PRODUCT_NAME),
                placeholder=t(Keys.PLACEHOLDER_PRODUCT_NAME),
            )
        with col4:
            manual_quantity = st.number_input(
                t(Keys.QUANTITY),
                min_value=0,
                value=0,
            )

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            manual_facility = st.text_input(
                t(Keys.FACILITY),
                placeholder=t(Keys.PLACEHOLDER_FACILITY),
            )
        with col6:
            manual_operation = st.text_input(
                t(Keys.OPERATION),
                placeholder=t(Keys.PLACEHOLDER_OPERATION),
            )
        with col7:
            manual_material = st.text_input(
                t(Keys.MATERIAL),
                placeholder=t(Keys.PLACEHOLDER_MATERIAL),
            )
        with col8:
            st.write("")

        submitted = st.form_submit_button(t(Keys.BTN_ADD_ORDER), type="primary")
        if submitted:
            if not manual_order_model:
                st.warning(f"{Icons.WARNING} {t(Keys.MSG_ENTER_MODEL_CODE)}")
            else:
                order_id = f"ORD_{manual_order_model.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                order_data = {
                    "order_date": manual_order_date,
                    "model": manual_order_model.upper(),
                    "product_name": manual_product_name or None,
                    "total_quantity": manual_quantity,
                    "facility": manual_facility or None,
                    "operation": manual_operation or None,
                    "material": manual_material or None,
                }
                if add_manual_order(order_id, order_data):
                    st.success(f"{Icons.SUCCESS} {t(Keys.ORDER_ADDED).format(order_id=order_id)}")
                    _invalidate_orders_cache()
                    st.rerun()
                else:
                    st.error(f"{Icons.ERROR} {t(Keys.FAILED_ADD_ORDER)}")


def _get_cached_active_orders() -> list[dict]:
    from utils.order_manager import get_active_orders

    cache_key = "cached_active_orders"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = get_active_orders()
    return st.session_state[cache_key]


def _invalidate_orders_cache() -> None:
    if "cached_active_orders" in st.session_state:
        del st.session_state["cached_active_orders"]


@st.fragment
def _render_active_orders() -> None:
    from ui.shared import render_dataframe_with_aggrid

    st.subheader(t(Keys.TITLE_ACTIVE_ORDERS))

    active_orders = _get_cached_active_orders()

    if not active_orders:
        st.info(f"{Icons.INFO} {t(Keys.NO_ACTIVE_ORDERS)}")
        return

    order_list = _build_order_list(active_orders)
    orders_df = pd.DataFrame(order_list)

    grid_response = render_dataframe_with_aggrid(
        orders_df,
        selection_mode="multiple",
        pinned_columns=[ColumnNames.ORDER_ID],
        max_height=Config.DATAFRAME_HEIGHT,
    )

    selected_rows = grid_response.selected_rows
    _handle_aggrid_archive_selection(selected_rows)

    st.caption(t(Keys.TOTAL_ACTIVE_ORDERS).format(count=len(active_orders)))
    ready_count = len([o for o in order_list if o["Days Elapsed"] >= Config.DELIVERY_THRESHOLD_DAYS])
    st.caption(t(Keys.ORDERS_READY).format(threshold=Config.DELIVERY_THRESHOLD_DAYS, count=ready_count))


def _build_order_list(active_orders: list[dict]) -> list[dict]:
    today = datetime.today()
    order_list = []

    for order in active_orders:
        order_date = _parse_order_date(order.get("order_date"))
        days_elapsed = (today - order_date).days
        is_ready = days_elapsed >= Config.DELIVERY_THRESHOLD_DAYS

        order_list.append({
            ColumnNames.ORDER_ID: order["order_id"],
            ColumnNames.ORDER_DATE: order_date.strftime("%Y-%m-%d"),
            "Model": order["model"],
            "Product": order.get("product_name") or "",
            "Quantity": order.get("total_quantity") or 0,
            "Facility": order.get("facility") or "",
            "Operation": order.get("operation") or "",
            "Material": order.get("material") or "",
            ColumnNames.DAYS_ELAPSED: days_elapsed,
            "Status": (
                t(Keys.STATUS_READY)
                if is_ready
                else t(Keys.STATUS_PENDING).format(days=Config.DELIVERY_THRESHOLD_DAYS - days_elapsed)
            ),
        })

    return order_list


def _parse_order_date(order_date) -> datetime:
    if isinstance(order_date, str):
        return datetime.fromisoformat(order_date.replace("Z", "+00:00"))
    if isinstance(order_date, datetime):
        return order_date
    return datetime.combine(order_date, datetime.min.time())


def _handle_aggrid_archive_selection(selected_rows) -> None:
    from utils.order_manager import archive_order

    if selected_rows is None or len(selected_rows) == 0:
        return

    selected_df = pd.DataFrame(selected_rows) if not isinstance(selected_rows, pd.DataFrame) else selected_rows

    if selected_df.empty:
        return

    if st.button(t(Keys.BTN_ARCHIVE_N_ORDERS).format(count=len(selected_df)), type="secondary"):
        for _, row in selected_df.iterrows():
            order_id = row[ColumnNames.ORDER_ID]
            if archive_order(order_id):
                st.success(f"{Icons.SUCCESS} {t(Keys.ORDER_ARCHIVED).format(order_id=order_id)}")
            else:
                st.error(f"{Icons.ERROR} {t(Keys.FAILED_ARCHIVE_ORDER).format(order_id=order_id)}")
        _invalidate_orders_cache()
        st.rerun()


def _render_facility_capacity() -> None:
    st.subheader(t(Keys.TITLE_FACILITY_CAPACITY))

    active_orders = _get_cached_active_orders()

    if not active_orders:
        st.info(f"{Icons.INFO} {t(Keys.MSG_NO_CAPACITY_DATA)}")
        return

    capacity_data = _calculate_facility_capacity(active_orders)

    if not capacity_data:
        st.info(f"{Icons.INFO} {t(Keys.MSG_NO_FACILITY_DATA)}")
        return

    facility_capacities = _get_facility_capacities()

    capacity_df = pd.DataFrame(capacity_data)
    capacity_df[MONTHLY_CAPACITY] = capacity_df["Facility"].map(
        lambda f: facility_capacities.get(f, 0)
    )
    capacity_df["Utilization %"] = capacity_df.apply(
        lambda row: _calculate_utilization(row[TOTAL_QUANTITY], row[MONTHLY_CAPACITY]),
        axis=1,
    )
    capacity_df = capacity_df.sort_values(TOTAL_QUANTITY, ascending=False)

    st.dataframe(
        capacity_df,
        hide_index=True,
        column_config={
            "Facility": st.column_config.TextColumn(t(Keys.FACILITY), width="medium"),
            ORDER_COUNT: st.column_config.NumberColumn(t(Keys.LABEL_ORDERS), format="%d"),
            TOTAL_QUANTITY: st.column_config.NumberColumn(t(Keys.LABEL_TOTAL_QTY), format="%d"),
            MONTHLY_CAPACITY: st.column_config.NumberColumn(t(Keys.LABEL_CAPACITY), format="%d"),
            "Utilization %": st.column_config.ProgressColumn(
                t(Keys.LABEL_UTILIZATION),
                format="%.0f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )

    total_qty = capacity_df[TOTAL_QUANTITY].sum()
    st.caption(t(Keys.CAPTION_TOTAL_QTY_FACILITIES).format(total=total_qty))

    _render_capacity_editor(capacity_df["Facility"].tolist(), facility_capacities)


def _calculate_facility_capacity(active_orders: list[dict]) -> list[dict]:
    facility_totals: dict[str, dict] = {}

    for order in active_orders:
        facility = order.get("facility") or "Unknown"
        quantity = order.get("total_quantity") or 0

        if facility not in facility_totals:
            facility_totals[facility] = {ORDER_COUNT: 0, TOTAL_QUANTITY: 0}

        facility_totals[facility][ORDER_COUNT] += 1
        facility_totals[facility][TOTAL_QUANTITY] += quantity

    return [{"Facility": facility, **data} for facility, data in facility_totals.items()]


def _get_facility_capacities() -> dict[str, int]:
    from utils.settings_manager import get_setting, load_settings

    if SessionKeys.FACILITY_CAPACITY not in st.session_state:
        settings = load_settings()
        st.session_state[SessionKeys.FACILITY_CAPACITY] = get_setting(
            "facility_capacity", settings
        ) or {}
    return st.session_state[SessionKeys.FACILITY_CAPACITY]


def _save_facility_capacities(capacities: dict[str, int]) -> None:
    from utils.settings_manager import load_settings, save_settings, update_setting

    st.session_state[SessionKeys.FACILITY_CAPACITY] = capacities
    settings = load_settings()
    settings = update_setting("facility_capacity", capacities, settings)
    save_settings(settings)


def _calculate_utilization(total_qty: int, capacity: int) -> float:
    return min((total_qty / capacity) * 100, 100.0) if capacity > 0 else 0.0


@st.fragment
def _render_capacity_editor(facilities: list[str], current_capacities: dict[str, int]) -> None:
    with st.expander(t(Keys.TITLE_EDIT_CAPACITY), expanded=False):
        st.caption(t(Keys.HELP_CAPACITY_EDITOR))

        cols_per_row = 3
        edited_capacities = current_capacities.copy()
        has_changes = False

        for i in range(0, len(facilities), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(facilities):
                    facility = facilities[i + j]
                    current_value = current_capacities.get(facility, 0)
                    with col:
                        new_value = st.number_input(
                            facility,
                            min_value=0,
                            value=current_value,
                            step=100,
                            key=f"capacity_{facility}",
                        )
                        if new_value != current_value:
                            edited_capacities[facility] = new_value
                            has_changes = True

        if has_changes and st.button(t(Keys.BTN_SAVE_CAPACITY), type="primary"):
            _save_facility_capacities(edited_capacities)
            st.success(f"{Icons.SUCCESS} {t(Keys.MSG_CAPACITY_SAVED)}")
            st.rerun()
