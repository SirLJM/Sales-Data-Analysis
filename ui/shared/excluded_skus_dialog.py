from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.constants import SessionKeys
from ui.i18n import t, Keys
from ui.shared.data_loaders import load_stock
from utils.sku_exclude_manager import save_excluded_skus


@st.dialog("Excluded SKUs", width="large")
def show_excluded_skus_dialog() -> None:
    st.subheader(t(Keys.EXCLUDED_SKUS_TITLE))

    excluded: list[str] = list(st.session_state.get(SessionKeys.EXCLUDED_SKUS, []))

    all_skus_df = _build_sku_list(excluded)

    search = st.text_input(
        t(Keys.EXCLUDED_SKUS_SEARCH),
        key="excluded_skus_search_input",
        label_visibility="collapsed",
        placeholder=t(Keys.EXCLUDED_SKUS_SEARCH),
    )

    if search:
        search_lower = search.lower()
        mask = (
            all_skus_df["SKU"].str.lower().str.contains(search_lower, na=False)
            | all_skus_df["Description"].str.lower().str.contains(search_lower, na=False)
        )
        display_df = pd.DataFrame(all_skus_df[mask])
    else:
        display_df = all_skus_df

    st.caption(t(Keys.EXCLUDED_SKUS_COUNT).format(count=len(excluded)))

    edited = st.data_editor(
        display_df,
        column_config={
            "Excluded": st.column_config.CheckboxColumn(
                "Excluded",
                default=False,
            ),
            "SKU": st.column_config.TextColumn("SKU", disabled=True),
            "Description": st.column_config.TextColumn("Description", disabled=True),
        },
        use_container_width=True,
        hide_index=True,
        key="excluded_skus_editor",
        height=500,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t(Keys.EXCLUDED_SKUS_CLEAR_ALL), use_container_width=True):
            st.session_state[SessionKeys.EXCLUDED_SKUS] = []
            save_excluded_skus([])
            st.rerun()

    with col2:
        if st.button(t(Keys.EXCLUDED_SKUS_SAVE), type="primary", use_container_width=True):
            if not isinstance(edited, pd.DataFrame):
                return
            new_excluded: list[str] = edited.loc[edited["Excluded"] == True, "SKU"].tolist()  # noqa: E712
            st.session_state[SessionKeys.EXCLUDED_SKUS] = new_excluded
            save_excluded_skus(new_excluded)
            st.rerun()


def _build_sku_list(excluded: list[str]) -> pd.DataFrame:
    stock_result = load_stock()
    stock_df = stock_result[0] if stock_result else None
    excluded_set = set(excluded)

    rows = _rows_from_stock(stock_df, excluded_set)

    seen_skus = {str(r["SKU"]) for r in rows}
    for sku in excluded:
        if sku not in seen_skus:
            rows.append({"Excluded": True, "SKU": sku, "Description": ""})

    if not rows:
        return pd.DataFrame(columns=pd.Index(["Excluded", "SKU", "Description"]))

    result = pd.DataFrame(rows)
    result = result.sort_values(by=["Excluded", "SKU"], ascending=[False, True])
    return result.reset_index(drop=True)


def _rows_from_stock(
    stock_df: pd.DataFrame | None, excluded_set: set[str]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if stock_df is None or stock_df.empty:
        return rows
    sku_col = "SKU" if "SKU" in stock_df.columns else "sku"
    desc_col = "nazwa" if "nazwa" in stock_df.columns else None
    for _, row in stock_df.iterrows():
        sku = str(row[sku_col])
        description = str(row[desc_col]) if desc_col else ""
        rows.append({"Excluded": sku in excluded_set, "SKU": sku, "Description": description})
    return rows
