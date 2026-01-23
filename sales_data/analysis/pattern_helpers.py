from __future__ import annotations

import pandas as pd

from utils.logging_config import get_logger
from .order_priority import get_size_quantities_for_model_color
from .utils import find_column

logger = get_logger(__name__)


def calculate_size_priorities(
        sales_df: pd.DataFrame,
        model: str | None = None,
        size_aliases: dict[str, str] | None = None
) -> dict[str, float]:
    if sales_df is None or sales_df.empty:
        return {}

    df = sales_df.copy()
    if "SKU" not in df.columns:
        return {}

    df["size"] = df["SKU"].astype(str).str[7:9]

    if model:
        df["model"] = df["SKU"].astype(str).str[:5]
        df = df[df["model"] == model]

    size_col = "FORECAST_QTY" if "FORECAST_QTY" in df.columns else "TOTAL_QUANTITY"
    if size_col not in df.columns:
        return {}

    size_sales = df.groupby("size", observed=True)[size_col].sum()

    if size_aliases:
        aliased_sales: dict[str, float] = {}
        for size, sales in size_sales.items():
            size_str = str(size)
            alias = size_aliases.get(size_str, size_str)
            aliased_sales[alias] = aliased_sales.get(alias, 0) + sales
        size_sales = pd.Series(aliased_sales)

    if size_sales.empty or size_sales.max() == 0:
        return {}

    normalized = size_sales / size_sales.max()
    result = normalized.to_dict()
    return result


def calculate_size_sales_history(
        monthly_agg: pd.DataFrame,
        model: str,
        color: str,
        size_aliases: dict[str, str] | None = None,
        months: int = 4,
) -> dict[str, int]:
    if monthly_agg is None or monthly_agg.empty:
        return {}

    df = monthly_agg.copy()

    sku_col = find_column(df, ["sku", "SKU", "entity_id"])
    if sku_col is None:
        return {}

    df["_model"] = df[sku_col].astype(str).str[:5]
    df["_color"] = df[sku_col].astype(str).str[5:7]
    df["_size"] = df[sku_col].astype(str).str[7:9]

    filtered = pd.DataFrame(df[(df["_model"] == model) & (df["_color"] == color)])
    if filtered.empty:
        return {}

    month_col = find_column(filtered, ["year_month", "month", "MONTH"])
    qty_col = find_column(filtered, ["total_quantity", "TOTAL_QUANTITY", "ilosc"])

    if month_col is None or qty_col is None:
        return {}

    sorted_months = sorted(pd.Series(filtered[month_col]).unique(), reverse=True)[:months]
    recent = pd.DataFrame(filtered[pd.Series(filtered[month_col]).isin(sorted_months)])

    size_sales = recent.groupby("_size", observed=True)[qty_col].sum().to_dict()  # type: ignore[call-overload]
    return _apply_size_aliases(size_sales, size_aliases)


def _apply_size_aliases(size_sales: dict, size_aliases: dict[str, str] | None) -> dict[str, int]:
    if not size_aliases:
        return {str(k): int(v) for k, v in size_sales.items()}

    aliased = {}
    for size_code, sales in size_sales.items():
        alias = size_aliases.get(str(size_code), str(size_code))
        aliased[alias] = aliased.get(alias, 0) + int(sales)
    return aliased


def get_size_sales_by_month_for_model(
        monthly_agg: pd.DataFrame,
        model: str,
        size_aliases: dict[str, str] | None = None,
        months: int = 3,
) -> dict[str, dict[str, int]]:
    if monthly_agg is None or monthly_agg.empty:
        return {}

    df = monthly_agg.copy()

    sku_col = find_column(df, ["sku", "SKU", "entity_id"])
    if sku_col is None:
        return {}

    df["_model"] = df[sku_col].astype(str).str[:5]
    df["_size"] = df[sku_col].astype(str).str[7:9]

    filtered = pd.DataFrame(df[df["_model"] == model])
    if filtered.empty:
        return {}

    month_col = find_column(filtered, ["year_month", "month", "MONTH"])
    qty_col = find_column(filtered, ["total_quantity", "TOTAL_QUANTITY", "ilosc"])

    if month_col is None or qty_col is None:
        return {}

    sorted_months = sorted(pd.Series(filtered[month_col]).unique(), reverse=True)[:months]

    result = {}
    for month in sorted_months:
        month_data = filtered[filtered[month_col] == month]
        size_sales = month_data.groupby("_size", observed=True)[qty_col].sum().to_dict()  # type: ignore
        result[str(month)] = _apply_size_aliases(size_sales, size_aliases)

    return result


def optimize_pattern_with_aliases(
        priority_skus: pd.DataFrame,
        model: str,
        color: str,
        pattern_set,
        size_aliases: dict[str, str],
        min_per_pattern: int,
        algorithm_mode: str = "greedy_overshoot",
        size_sales_history: dict[str, int] | None = None,
) -> dict:
    from utils.pattern_optimizer import optimize_patterns

    size_quantities = get_size_quantities_for_model_color(priority_skus, model, color)

    if not size_quantities:
        return {
            "allocation": {},
            "produced": {},
            "excess": {},
            "total_patterns": 0,
            "total_excess": 0,
            "all_covered": False,
        }

    size_quantities_with_aliases = {}
    for size_code, quantity in size_quantities.items():
        alias = size_aliases.get(size_code, size_code)
        size_quantities_with_aliases[alias] = size_quantities_with_aliases.get(alias, 0) + quantity

    pattern_sizes = set()
    for p in pattern_set.patterns:
        pattern_sizes.update(p.sizes.keys())

    logger.info(
        "Model=%s, color=%s: size_quantities=%s, size_quantities_with_aliases=%s, pattern_sizes=%s",
        model, color, size_quantities, size_quantities_with_aliases, pattern_sizes
    )

    size_priorities = calculate_size_priorities(priority_skus, model, size_aliases)

    result = optimize_patterns(
        size_quantities_with_aliases,
        pattern_set.patterns,
        min_per_pattern,
        algorithm_mode,
        size_priorities,
        size_sales_history,
    )

    return result
