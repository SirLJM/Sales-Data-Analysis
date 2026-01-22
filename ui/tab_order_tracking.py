from __future__ import annotations

import base64
from datetime import datetime

import pandas as pd
import streamlit as st

from ui.constants import ColumnNames, Config, Icons, SessionKeys
from ui.i18n import Keys, t
from utils.logging_config import get_logger

UTILIZATION_ = "Utilization %"

ORDER_COUNT = "Order Count"

MONTHLY_CAPACITY = "Monthly Capacity"

TOTAL_QUANTITY = "Total Quantity"

OTHER_OPTION = "(Other)"

logger = get_logger("tab_order_tracking")


@st.fragment
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


def _get_available_facilities() -> list[str]:
    from ui.shared import load_unique_facilities
    return load_unique_facilities()


def _get_available_materials() -> list[str]:
    from ui.shared import load_unique_materials
    return load_unique_materials()


@st.fragment
def _render_pdf_upload() -> None:
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
                with st.spinner(t(Keys.LABEL_PARSING_PDF)):  # type: ignore[arg-type]
                    pdf_bytes = uploaded_file.getvalue()
                    order_data = parse_order_pdf(uploaded_file)
                    if order_data:
                        st.session_state["parsed_order_data"] = order_data
                        st.session_state["parsed_pdf_bytes"] = pdf_bytes
                        st.session_state["parsed_pdf_filename"] = uploaded_file.name
                        st.rerun()
                    else:
                        st.error(f"{Icons.ERROR} {t(Keys.FAILED_PARSE_PDF)}")

    if "parsed_order_data" in st.session_state:
        st.success(f"{Icons.SUCCESS} {t(Keys.PDF_PARSED)}")
        _render_editable_parsed_order()


def _render_editable_parsed_order() -> None:
    order_data = st.session_state["parsed_order_data"]
    facilities = _get_available_facilities()
    materials = _get_available_materials()

    order_date = order_data.get("order_date")
    default_date = order_date if order_date else datetime.today()

    with st.form("pdf_order_form"):
        form_values = _render_pdf_form_fields(order_data, default_date, facilities, materials)
        submitted, cancelled = _render_form_buttons()

        if submitted:
            _handle_pdf_order_submit(form_values)
        if cancelled:
            _clear_parsed_order_state()
            st.rerun()


def _render_pdf_form_fields(
        order_data: dict,
        default_date: datetime,
        facilities: list[str],
        materials: list[str],
) -> dict:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        edit_order_date = st.date_input(
            t(Keys.ORDER_DATE),
            value=default_date,
            help=t(Keys.HELP_ORDER_DATE),
        )
    with col2:
        edit_model = st.text_input(
            t(Keys.LABEL_MODEL_CODE),
            value=order_data.get("model") or "",
        )
    with col3:
        edit_product_name = st.text_input(
            t(Keys.LABEL_PRODUCT_NAME),
            value=order_data.get("product_name") or "",
        )
    with col4:
        edit_quantity = st.number_input(
            t(Keys.QUANTITY),
            min_value=0,
            value=order_data.get("total_quantity") or 0,
        )

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        edit_facility, edit_facility_other = _render_dropdown_with_other(
            label=t(Keys.FACILITY),
            options=facilities,
            default_value=order_data.get("facility"),
            key_prefix="pdf_facility",
        )
    with col6:
        edit_operation = st.text_input(
            t(Keys.OPERATION),
            value=order_data.get("operation") or "",
        )
    with col7:
        edit_material, edit_material_other = _render_dropdown_with_other(
            label=t(Keys.MATERIAL),
            options=materials,
            default_value=order_data.get("material"),
            key_prefix="pdf_material",
        )
    with col8:
        st.write("")

    return {
        "order_date": edit_order_date,
        "model": edit_model,
        "product_name": edit_product_name,
        "quantity": edit_quantity,
        "facility": edit_facility,
        "facility_other": edit_facility_other,
        "operation": edit_operation,
        "material": edit_material,
        "material_other": edit_material_other,
    }


def _render_form_buttons() -> tuple[bool, bool]:
    col_submit, col_cancel = st.columns([1, 1])
    with col_submit:
        submitted = st.form_submit_button(t(Keys.BTN_CREATE_FROM_PDF), type="primary")
    with col_cancel:
        cancelled = st.form_submit_button(t(Keys.BTN_CANCEL))
    return submitted, cancelled


def _handle_pdf_order_submit(form_values: dict) -> None:
    from utils.order_manager import add_manual_order

    final_facility = (
        form_values["facility_other"]
        if form_values["facility"] == OTHER_OPTION
        else form_values["facility"]
    )
    final_material = (
        form_values["material_other"]
        if form_values["material"] == OTHER_OPTION
        else form_values["material"]
    )

    final_order_data = {
        "order_date": form_values["order_date"],
        "model": form_values["model"].upper() if form_values["model"] else None,
        "product_name": form_values["product_name"] or None,
        "total_quantity": form_values["quantity"],
        "facility": final_facility or None,
        "operation": form_values["operation"] or None,
        "material": final_material or None,
    }

    if st.session_state.get("parsed_pdf_bytes"):
        final_order_data["pdf_data"] = base64.b64encode(
            st.session_state["parsed_pdf_bytes"]
        ).decode("utf-8")
        final_order_data["pdf_filename"] = st.session_state.get("parsed_pdf_filename")

    order_id = f"ORD_{final_order_data.get('model', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if add_manual_order(order_id, final_order_data):
        st.success(f"{Icons.SUCCESS} {t(Keys.ORDER_CREATED_PDF).format(order_id=order_id)}")
        _clear_parsed_order_state()
        _invalidate_orders_cache()
        st.rerun()
    else:
        st.error(f"{Icons.ERROR} {t(Keys.FAILED_CREATE_ORDER)}")


def _render_dropdown_with_other(
        label: str,
        options: list[str],
        default_value: str | None,
        key_prefix: str,
) -> tuple[str, str]:
    options_with_other = options + [OTHER_OPTION] if options else [OTHER_OPTION]

    if default_value and default_value in options:
        default_index = options.index(default_value)
    elif default_value:
        default_index = len(options_with_other) - 1
    else:
        default_index = 0

    selected = st.selectbox(
        label,
        options=options_with_other,
        index=default_index,
        key=f"{key_prefix}_select",
    )

    other_value = ""
    if selected == OTHER_OPTION:
        other_value = st.text_input(
            f"{label} ({t(Keys.PLACEHOLDER_SPECIFY)})",
            value=default_value if default_value and default_value not in options else "",
            key=f"{key_prefix}_other",
        )

    return selected, other_value


def _clear_parsed_order_state() -> None:
    keys_to_clear = ["parsed_order_data", "parsed_pdf_bytes", "parsed_pdf_filename"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


@st.fragment
def _render_manual_order_form() -> None:
    st.subheader(t(Keys.TITLE_MANUAL_ORDER))

    facilities = _get_available_facilities()
    materials = _get_available_materials()

    with st.form("manual_order_form"):
        form_values = _render_manual_form_fields(facilities, materials)
        submitted = st.form_submit_button(t(Keys.BTN_ADD_ORDER), type="primary")
        if submitted:
            _handle_manual_order_submit(form_values)


def _render_manual_form_fields(facilities: list[str], materials: list[str]) -> dict:
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
        manual_facility, manual_facility_other = _render_dropdown_with_other(
            label=t(Keys.FACILITY),
            options=facilities,
            default_value=None,
            key_prefix="manual_facility",
        )
    with col6:
        manual_operation = st.text_input(
            t(Keys.OPERATION),
            placeholder=t(Keys.PLACEHOLDER_OPERATION),
        )
    with col7:
        manual_material, manual_material_other = _render_dropdown_with_other(
            label=t(Keys.MATERIAL),
            options=materials,
            default_value=None,
            key_prefix="manual_material",
        )
    with col8:
        st.write("")

    return {
        "order_date": manual_order_date,
        "model": manual_order_model,
        "product_name": manual_product_name,
        "quantity": manual_quantity,
        "facility": manual_facility,
        "facility_other": manual_facility_other,
        "operation": manual_operation,
        "material": manual_material,
        "material_other": manual_material_other,
    }


def _handle_manual_order_submit(form_values: dict) -> None:
    from utils.order_manager import add_manual_order

    if not form_values["model"]:
        st.warning(f"{Icons.WARNING} {t(Keys.MSG_ENTER_MODEL_CODE)}")
        return

    final_facility = (
        form_values["facility_other"]
        if form_values["facility"] == OTHER_OPTION
        else form_values["facility"]
    )
    final_material = (
        form_values["material_other"]
        if form_values["material"] == OTHER_OPTION
        else form_values["material"]
    )

    order_id = f"ORD_{form_values['model'].upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    order_data = {
        "order_date": form_values["order_date"],
        "model": form_values["model"].upper(),
        "product_name": form_values["product_name"] or None,
        "total_quantity": form_values["quantity"],
        "facility": final_facility or None,
        "operation": form_values["operation"] or None,
        "material": final_material or None,
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


def _render_active_orders() -> None:
    st.subheader(t(Keys.TITLE_ACTIVE_ORDERS))

    active_orders = _get_cached_active_orders()

    if not active_orders:
        st.info(f"{Icons.INFO} {t(Keys.NO_ACTIVE_ORDERS)}")
        return

    order_list = _build_order_list(active_orders)
    orders_df = pd.DataFrame(order_list)

    row_height = 35
    header_height = 40
    table_height = min(header_height + len(orders_df) * row_height, 400)

    selected_indices = []
    with st.container():
        event = st.dataframe(
            orders_df,
            hide_index=True,
            width='stretch',
            height=table_height,
            selection_mode="multi-row",
            on_select="rerun",
            key="active_orders_df",
        )
        if event and event.selection and event.selection.rows:
            selected_indices = event.selection.rows

    if selected_indices:
        selected_df: pd.DataFrame = orders_df.iloc[selected_indices]  # type: ignore[assignment]
        _handle_dataframe_archive_selection(selected_df)

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


def _handle_dataframe_archive_selection(selected_df: pd.DataFrame) -> None:
    from utils.order_manager import archive_order

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
    capacity_df[UTILIZATION_] = capacity_df.apply(
        lambda row: _calculate_utilization(row[TOTAL_QUANTITY], row[MONTHLY_CAPACITY]),
        axis=1,
    )
    capacity_df["Weeks Ahead"] = capacity_df.apply(
        lambda row: _calculate_weeks_ahead(row[TOTAL_QUANTITY], row[MONTHLY_CAPACITY]),
        axis=1,
    )
    capacity_df["Capacity Status"] = capacity_df[UTILIZATION_].apply(_get_capacity_status)
    capacity_df = capacity_df.sort_values(TOTAL_QUANTITY, ascending=False)

    max_utilization = max(capacity_df[UTILIZATION_].max(), 100)
    progress_max = max(int(max_utilization * 1.2), 200)

    st.dataframe(
        capacity_df,
        hide_index=True,
        column_config={
            "Facility": st.column_config.TextColumn(t(Keys.FACILITY), width="medium"),
            ORDER_COUNT: st.column_config.NumberColumn(t(Keys.LABEL_ORDERS), format="%d"),
            TOTAL_QUANTITY: st.column_config.NumberColumn(t(Keys.LABEL_TOTAL_QTY), format="%d"),
            MONTHLY_CAPACITY: st.column_config.NumberColumn(t(Keys.LABEL_CAPACITY), format="%d"),
            UTILIZATION_: st.column_config.ProgressColumn(
                t(Keys.LABEL_UTILIZATION),
                format="%.0f%%",
                min_value=0,
                max_value=progress_max,
            ),
            "Weeks Ahead": st.column_config.NumberColumn(
                t(Keys.LABEL_WEEKS_AHEAD),
                format="%.1f",
                help=t(Keys.HELP_WEEKS_AHEAD),
            ),
            "Capacity Status": st.column_config.TextColumn(
                t(Keys.LABEL_STATUS),
                width="small",
            ),
        },
    )

    total_qty = capacity_df[TOTAL_QUANTITY].sum()
    st.caption(t(Keys.CAPTION_TOTAL_QTY_FACILITIES).format(total=total_qty))
    st.caption(t(Keys.CAPTION_CAPACITY_LEGEND))

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
    return (total_qty / capacity) * 100 if capacity > 0 else 0.0


def _calculate_weeks_ahead(total_qty: int, capacity: int) -> float:
    if capacity <= 0:
        return 0.0
    weekly_capacity = capacity / 4.0
    return total_qty / weekly_capacity if weekly_capacity > 0 else 0.0


def _get_capacity_status(utilization: float) -> str:
    if utilization >= 200:
        return f"🔴 {t(Keys.STATUS_2_PLUS_WEEKS)}"
    if utilization >= 150:
        return f"🟠 {t(Keys.STATUS_1_5_PLUS_WEEKS)}"
    if utilization >= 100:
        return f"🟡 {t(Keys.STATUS_1_PLUS_WEEK)}"
    if utilization >= 75:
        return f"🟢 {t(Keys.STATUS_OK)}"
    return f"⚪ {t(Keys.STATUS_LOW)}"


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
