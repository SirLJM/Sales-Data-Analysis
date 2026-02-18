from __future__ import annotations

import pandas as pd

CHILDREN_PREFIXES = ("ch", "ni", "dz")
ADULT_PREFIXES = ("do", "ju")


def get_sku_age_category(sku: str) -> str | None:
    prefix = sku[:2].lower()
    if prefix in CHILDREN_PREFIXES:
        return "children"
    if prefix in ADULT_PREFIXES:
        return "adult"
    return None


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
    df["MODEL"] = extract_model(pd.Series(df[sku_col]))
    df["COLOR"] = extract_color(pd.Series(df[sku_col]))
    df["SIZE"] = extract_size(pd.Series(df[sku_col]))
    return df


def get_size_sort_key(size_alias: str, size_alias_to_code: dict[str, str]) -> int:
    size_code = size_alias_to_code.get(size_alias, size_alias)
    try:
        return int(size_code)
    except (ValueError, TypeError):
        return 999
