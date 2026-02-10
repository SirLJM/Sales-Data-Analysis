from __future__ import annotations

import pandas as pd
import streamlit as st

from sales_data.analysis.material_planning import (
    calculate_material_gap,
    calculate_material_requirements,
    extract_production_quantities_from_orders,
)
from ui.constants import Config, Icons, MimeTypes, SessionKeys
from ui.i18n import Keys, t
from ui.shared.data_loaders import load_bom_data, load_material_catalog, load_material_stock
from utils.logging_config import get_logger
from utils.order_manager import get_active_orders

logger = get_logger("tab_material_planning")


@st.fragment
def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Material Planning")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_MATERIAL_PLANNING).format(error=str(e))}")


def _render_content() -> None:
    st.title(t(Keys.TITLE_MATERIAL_PLANNING))

    bom_data = load_bom_data()
    material_catalog = load_material_catalog()
    material_stock = load_material_stock()

    if bom_data is None or bom_data.empty:
        st.warning(t(Keys.MAT_NO_BOM))
        return

    st.markdown("---")
    _render_order_requirements(bom_data, material_catalog, material_stock)

    st.markdown("---")
    _render_manual_input(bom_data, material_catalog, material_stock)

    st.markdown("---")
    _render_stock_section(material_stock)


def _render_order_requirements(
        bom_data: pd.DataFrame,
        material_catalog: pd.DataFrame | None,
        material_stock: pd.DataFrame | None,
) -> None:
    st.subheader(t(Keys.MAT_SECTION_ORDERS))

    active_orders = get_active_orders()
    if not active_orders:
        st.info(t(Keys.MAT_NO_ORDERS))
        return

    production_qty = extract_production_quantities_from_orders(active_orders)
    if production_qty.empty:
        st.info(t(Keys.MAT_NO_ORDERS))
        return

    requirements = calculate_material_requirements(production_qty, bom_data)
    if requirements.empty:
        st.info(t(Keys.MAT_NO_REQUIREMENTS))
        return

    gap_df = calculate_material_gap(requirements, material_stock, material_catalog)
    _display_requirements_table(gap_df, "order_requirements")


def _get_manual_inputs() -> list[dict]:
    if SessionKeys.MATERIAL_MANUAL_INPUTS not in st.session_state:
        st.session_state[SessionKeys.MATERIAL_MANUAL_INPUTS] = []
    return st.session_state[SessionKeys.MATERIAL_MANUAL_INPUTS]


def _render_manual_input(
        bom_data: pd.DataFrame,
        material_catalog: pd.DataFrame | None,
        material_stock: pd.DataFrame | None,
) -> None:
    st.subheader(t(Keys.MAT_SECTION_MANUAL))

    available_models = sorted(bom_data["model"].unique().tolist())
    manual_inputs = _get_manual_inputs()

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        selected_model = st.selectbox(
            t(Keys.MAT_MODEL),
            options=available_models,
            key="mat_manual_model",
        )
    with col2:
        quantity = st.number_input(
            t(Keys.MAT_QUANTITY),
            min_value=1,
            value=100,
            step=10,
            key="mat_manual_qty",
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t(Keys.MAT_ADD_ENTRY), key="mat_add_btn"):
            manual_inputs.append({"model": selected_model, "quantity": quantity})
            st.session_state[SessionKeys.MATERIAL_MANUAL_INPUTS] = manual_inputs
            st.rerun()

    if manual_inputs:
        for i, entry in enumerate(manual_inputs):
            col_m, col_q, col_r = st.columns([3, 2, 1])
            with col_m:
                st.text(entry["model"])
            with col_q:
                st.text(str(entry["quantity"]))
            with col_r:
                if st.button(t(Keys.MAT_REMOVE), key=f"mat_remove_{i}"):
                    manual_inputs.pop(i)
                    st.session_state[SessionKeys.MATERIAL_MANUAL_INPUTS] = manual_inputs
                    st.rerun()

        manual_df = pd.DataFrame(manual_inputs)
        manual_qty = manual_df.groupby("model", as_index=False).agg(quantity=("quantity", "sum"))

        active_orders = get_active_orders()
        order_qty = extract_production_quantities_from_orders(active_orders)

        if not order_qty.empty:
            combined_qty = pd.concat([order_qty, manual_qty], ignore_index=True)
            combined_qty = combined_qty.groupby("model", as_index=False).agg(
                quantity=("quantity", "sum")
            )
        else:
            combined_qty = manual_qty

        st.subheader(t(Keys.MAT_COMBINED_REQUIREMENTS))
        requirements = calculate_material_requirements(combined_qty, bom_data)
        if not requirements.empty:
            gap_df = calculate_material_gap(requirements, material_stock, material_catalog)
            _display_requirements_table(gap_df, "combined_requirements")
        else:
            st.info(t(Keys.MAT_NO_REQUIREMENTS))


def _display_requirements_table(df: pd.DataFrame, key_prefix: str) -> None:
    display_columns = {
        "material_name": t(Keys.MAT_COL_MATERIAL),
        "component_type": t(Keys.MAT_COL_TYPE),
        "total_meters": t(Keys.MAT_COL_METERS),
        "total_kg": t(Keys.MAT_COL_KG),
        "model_count": t(Keys.MAT_COL_MODEL_COUNT),
        "contributing_models": t(Keys.MAT_COL_MODELS),
    }

    if "supplier" in df.columns:
        display_columns["supplier"] = t(Keys.MAT_COL_SUPPLIER)

    if "gap_meters" in df.columns:
        display_columns["quantity_meters"] = t(Keys.MAT_COL_STOCK_M)
        display_columns["quantity_kg"] = t(Keys.MAT_COL_STOCK_KG)
        display_columns["gap_meters"] = t(Keys.MAT_COL_GAP_M)
        display_columns["gap_kg"] = t(Keys.MAT_COL_GAP_KG)

    available_cols = [c for c in display_columns if c in df.columns]
    display_df = df[available_cols].copy()
    display_df = display_df.rename(columns={c: display_columns[c] for c in available_cols})

    for col in [t(Keys.MAT_COL_METERS), t(Keys.MAT_COL_KG),
                t(Keys.MAT_COL_STOCK_M), t(Keys.MAT_COL_STOCK_KG),
                t(Keys.MAT_COL_GAP_M), t(Keys.MAT_COL_GAP_KG)]:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)

    st.dataframe(display_df, width='stretch', height=Config.DATAFRAME_HEIGHT)

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=t(Keys.MAT_DOWNLOAD_CSV),
        data=csv_data,
        file_name="material_requirements.csv",
        mime=MimeTypes.TEXT_CSV,
        key=f"{key_prefix}_download",
    )


def _render_stock_section(material_stock: pd.DataFrame | None) -> None:
    st.subheader(t(Keys.MAT_SECTION_STOCK))

    if material_stock is None or material_stock.empty:
        st.info(t(Keys.MAT_NO_STOCK))
    else:
        st.dataframe(material_stock, width='stretch')
