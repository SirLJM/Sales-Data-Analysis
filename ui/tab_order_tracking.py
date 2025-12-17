from __future__ import annotations

import traceback
from datetime import datetime

import pandas as pd
import streamlit as st

from ui.constants import ColumnNames, Config, Icons


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        st.error(f"{Icons.ERROR} Error in Order Tracking: {str(e)}")
        st.code(traceback.format_exc())


def _render_content() -> None:
    st.title("📦 Order Tracking")

    st.markdown("---")
    _render_manual_order_form()

    st.markdown("---")
    _render_active_orders()


def _render_manual_order_form() -> None:
    from utils.order_manager import add_manual_order

    st.subheader("📝 Add Manual Order")

    col_model, col_date, col_button = st.columns([2, 2, 1])
    with col_model:
        manual_order_model = st.text_input(
            "Model Code",
            placeholder="e.g., ABC12",
            help="Enter the model code for manual order entry",
            key="manual_order_model_input",
        )
    with col_date:
        manual_order_date = st.date_input(
            ColumnNames.ORDER_DATE,
            value=datetime.today(),
            help="Date when the order was placed",
            key="manual_order_date_input",
        )
    with col_button:
        st.write("")
        st.write("")
        if st.button("Add Order", key="add_manual_order_btn", type="primary"):
            if not manual_order_model:
                st.warning(f"{Icons.WARNING} Please enter a model code")
            else:
                order_id = f"ORD_{manual_order_model.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if add_manual_order(order_id, manual_order_model.upper(), manual_order_date):
                    st.success(f"{Icons.SUCCESS} Order {order_id} added to active orders")
                    st.rerun()
                else:
                    st.error(f"{Icons.ERROR} Failed to add order")


def _render_active_orders() -> None:
    from utils.order_manager import get_active_orders

    st.subheader("📋 Active Orders")

    active_orders = get_active_orders()

    if not active_orders:
        st.info(f"{Icons.INFO} No active orders. Create orders in Tab 5 or add manual orders above.")
        return

    order_list = _build_order_list(active_orders)
    orders_df = pd.DataFrame(order_list)

    edited_orders = st.data_editor(
        orders_df,
        hide_index=True,
        disabled=[ColumnNames.ORDER_ID, "Model", ColumnNames.ORDER_DATE, ColumnNames.DAYS_ELAPSED, "Status"],
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
            "Model": order["model"],
            ColumnNames.ORDER_DATE: order_date.strftime("%Y-%m-%d"),
            ColumnNames.DAYS_ELAPSED: days_elapsed,
            "Status": (
                "🚚 Ready for Delivery"
                if is_ready
                else f"⏳ {Config.DELIVERY_THRESHOLD_DAYS - days_elapsed} days left"
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
            st.rerun()
