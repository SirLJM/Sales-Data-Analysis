from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

if TYPE_CHECKING:
    from st_aggrid import AgGridReturn

ROW_HEIGHT = 35
HEADER_HEIGHT = 40
MIN_HEIGHT = 100
MAX_HEIGHT = 600


def _calculate_height(df: pd.DataFrame, max_height: int) -> int:
    content_height = len(df) * ROW_HEIGHT + HEADER_HEIGHT
    return max(MIN_HEIGHT, min(content_height, max_height))


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
        width = _calculate_column_width(df[col])
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

    actual_height = height if height is not None else _calculate_height(df, max_height)

    return AgGrid(
        df,
        gridOptions=grid_options,
        height=actual_height,
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True,
        theme="streamlit",
    )
