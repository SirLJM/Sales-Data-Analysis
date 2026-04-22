from __future__ import annotations

from collections.abc import Collection

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


def filter_excluded_skus(
    df: pd.DataFrame,
    excluded_skus: Collection[str],
    sku_column: str = "SKU",
) -> pd.DataFrame:
    if not excluded_skus or df.empty:
        return df
    col = _resolve_sku_column(df, sku_column)
    if col is None:
        return df
    return pd.DataFrame(df[~df[col].isin(list(excluded_skus))])


def _resolve_sku_column(df: pd.DataFrame, sku_column: str) -> str | None:
    if sku_column in df.columns:
        return sku_column
    if "sku" in df.columns:
        return "sku"
    return None


def filter_excluded_models(
    df: pd.DataFrame,
    excluded_skus: Collection[str],
    sku_column: str = "sku",
) -> pd.DataFrame:
    if not excluded_skus or df.empty:
        return df
    col = _resolve_sku_column(df, sku_column)
    if col is None:
        return df
    excluded_models = list({sku[:5] for sku in excluded_skus})
    return pd.DataFrame(df[~df[col].astype(str).str[:5].isin(excluded_models)])


def filter_excluded_model_colors(
    df: pd.DataFrame,
    excluded_skus: Collection[str],
    sku_column: str = "sku",
) -> pd.DataFrame:
    if not excluded_skus or df.empty:
        return df
    col = _resolve_sku_column(df, sku_column)
    if col is None:
        return df
    excluded_mc = list({sku[:7] for sku in excluded_skus})
    return pd.DataFrame(df[~df[col].astype(str).str[:7].isin(excluded_mc)])


def filter_by_active_skus(
    df: pd.DataFrame,
    active_skus: set[str] | None,
    sku_column: str = "sku",
) -> pd.DataFrame:
    if active_skus is None or df.empty:
        return df
    col = sku_column if sku_column in df.columns else "sku"
    if col not in df.columns:
        return df
    return pd.DataFrame(df[df[col].isin(active_skus)])


def get_size_sort_key(size_alias: str, size_alias_to_code: dict[str, str]) -> int:
    size_code = size_alias_to_code.get(size_alias, size_alias)
    try:
        return int(size_code)
    except (ValueError, TypeError):
        return 999
