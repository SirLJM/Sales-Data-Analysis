from __future__ import annotations

import pandas as pd


def extract_model(sku_series: pd.Series) -> pd.Series:
    return sku_series.astype(str).str[:5]


def extract_color(sku_series: pd.Series) -> pd.Series:
    return sku_series.astype(str).str[5:7]


def extract_size(sku_series: pd.Series) -> pd.Series:
    return sku_series.astype(str).str[7:9]


def parse_sku(sku: str) -> dict[str, str]:
    return {
        "model": sku[:5],
        "color": sku[5:7],
        "size": sku[7:9],
    }


def add_sku_components(df: pd.DataFrame, sku_col: str = "SKU") -> pd.DataFrame:
    df = df.copy()
    df["MODEL"] = extract_model(df[sku_col])
    df["COLOR"] = extract_color(df[sku_col])
    df["SIZE"] = extract_size(df[sku_col])
    return df
