from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

if TYPE_CHECKING:
    from st_aggrid import AgGridReturn

ROW_HEIGHT = 35
HEADER_HEIGHT = 40
MAX_HEIGHT = 600

AGGRID_FIT_CONTENT_STYLE = """
<style>
.ag-root-wrapper {
    min-height: auto !important;
    width: fit-content !important;
    min-width: 100% !important;
}
.ag-body-viewport {
    min-height: auto !important;
}
.ag-header, .ag-body-horizontal-scroll {
    width: fit-content !important;
    min-width: 100% !important;
}
iframe[title="st_aggrid.agGrid"] {
    height: auto !important;
    min-height: 100px;
    width: fit-content !important;
    min-width: 100% !important;
}
div[data-testid="stCustomComponentV1"] {
    width: fit-content !important;
    min-width: 0 !important;
}
div[data-testid="stCustomComponentV1"] > div {
    height: auto !important;
    width: fit-content !important;
}
</style>
"""


def _calculate_column_width(series: pd.Series) -> int:
    char_width = 9
    padding = 30
    max_val_len = series.astype(str).str.len().max()
    header_len = len(str(series.name))
    content_len = max(max_val_len, header_len)
    return int(content_len * char_width + padding)


def render_dataframe_with_aggrid(
        df: pd.DataFrame,
        height: int | None = None,
        max_height: int = MAX_HEIGHT,
        selection_mode: str | None = None,
        pinned_columns: list[str] | None = None,
        fit_columns_on_grid_load: bool = False,
) -> AgGridReturn:
    df = df.copy()
    for col in df.select_dtypes(include=["float"]).columns:
        df[col] = df[col].round(2)
    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        minWidth=80,
    )

    for col in df.columns:
        width = _calculate_column_width(pd.Series(df[col]))
        gb.configure_column(col, width=width, maxWidth=max(width, 200))

    if pinned_columns:
        for col in pinned_columns:
            if col in df.columns:
                gb.configure_column(col, pinned="left")

    if selection_mode:
        gb.configure_selection(
            selection_mode=selection_mode,
            use_checkbox=True,
        )

    grid_options = gb.build()
    grid_options["enableRangeSelection"] = True
    grid_options["enableCellTextSelection"] = True
    grid_options["ensureDomOrder"] = True
    grid_options["autoSizeStrategy"] = {
        "type": "fitCellContents",
        "skipHeader": True,
    }

    content_height = len(df) * ROW_HEIGHT + HEADER_HEIGHT
    target_height = height if height is not None else max_height
    use_auto_height = content_height <= target_height

    if use_auto_height:
        grid_options["domLayout"] = "autoHeight"
        st.markdown(AGGRID_FIT_CONTENT_STYLE, unsafe_allow_html=True)
        actual_height = None
    else:
        actual_height = target_height

    return AgGrid(
        df,
        gridOptions=grid_options,
        height=actual_height if actual_height is not None else 400,
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True,
        theme="streamlit",
    )
