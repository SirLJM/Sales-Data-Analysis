from __future__ import annotations

import numpy as np
import pandas as pd


def optimize_dtypes(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    initial_mem = df.memory_usage(deep=True).sum()

    for col in df.columns:
        col_type = df[col].dtype

        if isinstance(col_type, pd.CategoricalDtype):
            continue
        elif col_type == "object":
            df = _optimize_object_column(df, col)
        elif np.issubdtype(col_type, np.integer):  # type: ignore[arg-type]
            df = _optimize_integer_column(df, col)
        elif np.issubdtype(col_type, np.floating):  # type: ignore[arg-type]
            df = _optimize_float_column(df, col)

    if verbose:
        final_mem = df.memory_usage(deep=True).sum()
        reduction = (1 - final_mem / initial_mem) * 100
        print(f"Memory reduced: {initial_mem / 1e6:.1f}MB -> {final_mem / 1e6:.1f}MB ({reduction:.1f}% reduction)")

    return df


def _optimize_object_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    num_unique = df[col].nunique()
    num_total = len(df[col])

    if num_unique / num_total < 0.5:
        df[col] = df[col].astype("category")

    return df


def _optimize_integer_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    col_min = df[col].min()
    col_max = df[col].max()

    if col_min >= 0:
        if col_max <= 255:
            df[col] = df[col].astype(np.uint8)
        elif col_max <= 65535:
            df[col] = df[col].astype(np.uint16)
        elif col_max <= 4294967295:
            df[col] = df[col].astype(np.uint32)
    else:
        if col_min >= -128 and col_max <= 127:
            df[col] = df[col].astype(np.int8)
        elif col_min >= -32768 and col_max <= 32767:
            df[col] = df[col].astype(np.int16)
        elif col_min >= -2147483648 and col_max <= 2147483647:
            df[col] = df[col].astype(np.int32)

    return df


def _optimize_float_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df[col] = df[col].astype(np.float32)
    return df


def get_optimal_sales_dtypes() -> dict[str, str]:
    return {
        "order_id": "category",
        "sku": "category",
        "ilosc": "int16",
        "cena": "float32",
        "razem": "float32",
    }


def get_optimal_stock_dtypes() -> dict[str, str]:
    return {
        "sku": "category",
        "nazwa": "category",
        "cena_netto": "float32",
        "available_stock": "int32",
    }


def get_optimal_forecast_dtypes() -> dict[str, str]:
    return {
        "sku": "category",
        "forecast": "int32",
    }
