from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from ui.constants import ColumnNames, Config, Icons
from utils.logging_config import get_logger

TOTAL_QUANTITY = "Total Quantity"

logger = get_logger("tab_order_tracking")


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Order Tracking")
        st.error(f"{Icons.ERROR} Error in Order Tracking: {str(e)}")


def _render_content() -> None:
    st.title("📦 Order Tracking")

    st.markdown("---")
    _render_pdf_upload()

    st.markdown("---")
    _render_manual_order_form()

    st.markdown("---")
    _render_active_orders()

    st.markdown("---")
    _render_facility_capacity()


@st.fragment
def _render_pdf_upload() -> None:
    from ui.shared import load_unique_categories, load_unique_facilities
    from utils.order_manager import add_manual_order
    from utils.pdf_parser import parse_order_pdf, set_lookup_data

    facilities = load_unique_facilities()
    categories = load_unique_categories()
    set_lookup_data(facilities, categories)

    st.subheader("📄 Import Order from PDF")

    uploaded_file = st.file_uploader(
        "Upload order PDF file",
        type=["pdf"],
        help="Upload a PDF file containing order details",
        key="pdf_upload",
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.info(f"{Icons.INFO} File uploaded: {uploaded_file.name}")

        with col2:
            if st.button("Parse PDF", key="parse_pdf_btn", type="primary"):
                # noinspection PyTypeChecker
                with st.spinner("Parsing PDF..."):
                    order_data = parse_order_pdf(uploaded_file)
                    if order_data:
                        st.session_state["parsed_order_data"] = order_data
                    else:
                        st.error(f"{Icons.ERROR} Failed to parse PDF. Please check the file format.")

    if "parsed_order_data" in st.session_state:
        order_data = st.session_state["parsed_order_data"]
        st.success(f"{Icons.SUCCESS} PDF parsed successfully")
        _display_parsed_order(order_data)

        if st.button("Create Order from PDF", key="create_from_pdf_btn", type="primary"):
            order_id = f"ORD_{order_data.get('model', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if add_manual_order(order_id, order_data):
                st.success(f"{Icons.SUCCESS} Order {order_id} created from PDF")
                del st.session_state["parsed_order_data"]
                _invalidate_orders_cache()
                st.rerun()
            else:
                st.error(f"{Icons.ERROR} Failed to create order")


def _display_parsed_order(order_data: dict) -> None:
    order_date = order_data.get('order_date')
    date_str = order_date.strftime('%Y-%m-%d') if order_date else 'N/A'

    parsed_df = pd.DataFrame([{
        "Order Date": date_str,
        "Model": order_data.get('model', 'N/A'),
        "Product": order_data.get('product_name', 'N/A'),
        "Quantity": order_data.get('total_quantity', 'N/A'),
        "Facility": order_data.get('facility', 'N/A'),
        "Operation": order_data.get('operation', 'N/A'),
        "Material": order_data.get('material', 'N/A'),
    }])

    st.dataframe(parsed_df, hide_index=True)


@st.fragment
def _render_manual_order_form() -> None:
    from utils.order_manager import add_manual_order

    st.subheader("📝 Add Manual Order")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        manual_order_date = st.date_input(
            ColumnNames.ORDER_DATE,
            value=datetime.today(),
            help="Date when the order was placed",
            key="manual_order_date_input",
        )
    with col2:
        manual_order_model = st.text_input(
            "Model Code",
            placeholder="e.g., ABC12",
            key="manual_order_model_input",
        )
    with col3:
        manual_product_name = st.text_input(
            "Product Name",
            placeholder="e.g., Bluza",
            key="manual_product_name_input",
        )
    with col4:
        manual_quantity = st.number_input(
            "Quantity",
            min_value=0,
            value=0,
            key="manual_quantity_input",
        )

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        manual_facility = st.text_input(
            "Facility",
            placeholder="e.g., Sieradz",
            key="manual_facility_input",
        )
    with col6:
        manual_operation = st.text_input(
            "Operation",
            placeholder="e.g., szycie i składanie",
            key="manual_operation_input",
        )
    with col7:
        manual_material = st.text_input(
            "Material",
            placeholder="e.g., DRES PĘTELKA 280 GSM",
            key="manual_material_input",
        )
    with col8:
        st.write("")
        st.write("")
        if st.button("Add Order", key="add_manual_order_btn", type="primary"):
            if not manual_order_model:
                st.warning(f"{Icons.WARNING} Please enter a model code")
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
                    st.success(f"{Icons.SUCCESS} Order {order_id} added to active orders")
                    _invalidate_orders_cache()
                    st.rerun()
                else:
                    st.error(f"{Icons.ERROR} Failed to add order")


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
    st.subheader("📋 Active Orders")

    active_orders = _get_cached_active_orders()

    if not active_orders:
        st.info(f"{Icons.INFO} No active orders. Create orders in Tab 5 or add manual orders above.")
        return

    order_list = _build_order_list(active_orders)
    orders_df = pd.DataFrame(order_list)

    edited_orders = st.data_editor(
        orders_df,
        hide_index=True,
        disabled=[
            ColumnNames.ORDER_ID, ColumnNames.ORDER_DATE, "Model", "Product",
            "Quantity", "Facility", "Operation", "Material",
            ColumnNames.DAYS_ELAPSED, "Status"
        ],
        column_config={
            "Archive": st.column_config.CheckboxColumn(
                "Archive",
                help="Check to archive this order",
                default=False,
            )
        },
        height=min(Config.DATAFRAME_HEIGHT, len(order_list) * 35 + 38),
    )

    _handle_archive_selection(edited_orders)

    st.caption(f"📦 Total active orders: {len(active_orders)}")
    ready_count = len([o for o in order_list if o["Days Elapsed"] >= Config.DELIVERY_THRESHOLD_DAYS])
    st.caption(
        f"🚚 Orders ready for delivery (should be in stock now) (>= {Config.DELIVERY_THRESHOLD_DAYS} days): {ready_count}"
    )


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
                "🚚 Ready"
                if is_ready
                else f"⏳ {Config.DELIVERY_THRESHOLD_DAYS - days_elapsed}d"
            ),
            "Archive": False,
        })

    return order_list


def _parse_order_date(order_date) -> datetime:
    if isinstance(order_date, str):
        return datetime.fromisoformat(order_date.replace("Z", "+00:00"))
    elif not isinstance(order_date, datetime):
        return datetime.combine(order_date, datetime.min.time())
    return order_date


def _handle_archive_selection(edited_orders: pd.DataFrame) -> None:
    from utils.order_manager import archive_order

    selected_to_archive = edited_orders[edited_orders["Archive"] == True]

    if not selected_to_archive.empty:
        if st.button(f"Archive {len(selected_to_archive)} Order(s)", type="secondary"):
            for _, row in selected_to_archive.iterrows():
                if archive_order(row[ColumnNames.ORDER_ID]):
                    st.success(f"{Icons.SUCCESS} Archived order {row[ColumnNames.ORDER_ID]}")
                else:
                    st.error(f"{Icons.ERROR} Failed to archive order {row[ColumnNames.ORDER_ID]}")
            _invalidate_orders_cache()
            st.rerun()


def _render_facility_capacity() -> None:
    st.subheader("🏭 Facility Capacity")

    active_orders = _get_cached_active_orders()

    if not active_orders:
        st.info(f"{Icons.INFO} No active orders to calculate facility capacity.")
        return

    capacity_data = _calculate_facility_capacity(active_orders)

    if not capacity_data:
        st.info(f"{Icons.INFO} No facility data available in active orders.")
        return

    capacity_df = pd.DataFrame(capacity_data)
    capacity_df = capacity_df.sort_values(TOTAL_QUANTITY, ascending=False)

    st.dataframe(
        capacity_df,
        hide_index=True,
        column_config={
            "Facility": st.column_config.TextColumn("Facility", width="medium"),
            "Order Count": st.column_config.NumberColumn("Orders", format="%d"),
            TOTAL_QUANTITY: st.column_config.NumberColumn("Total Qty", format="%d"),
        },
    )

    total_qty = capacity_df[TOTAL_QUANTITY].sum()
    st.caption(f"📊 Total quantity across all facilities: {total_qty:,}")


def _calculate_facility_capacity(active_orders: list[dict]) -> list[dict]:
    facility_totals: dict[str, dict] = {}

    for order in active_orders:
        facility = order.get("facility") or "Unknown"
        quantity = order.get("total_quantity") or 0

        if facility not in facility_totals:
            facility_totals[facility] = {"order_count": 0, "total_quantity": 0}

        facility_totals[facility]["order_count"] += 1
        facility_totals[facility]["total_quantity"] += quantity

    return [
        {
            "Facility": facility,
            "Order Count": data["order_count"],
            "Total Quantity": data["total_quantity"],
        }
        for facility, data in facility_totals.items()
    ]
