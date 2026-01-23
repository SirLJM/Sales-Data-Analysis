from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Pattern:
    name: str
    keywords: list[str]
    regex: str | None = None
    extractor: Callable[[re.Match[str]], Any] | None = None
    priority: int = 1


ENTITY_PATTERNS = [
    Pattern(
        name="sales",
        keywords=["sales", "sold", "selling", "revenue", "orders"],
        priority=2,
    ),
    Pattern(
        name="stock",
        keywords=["stock", "inventory", "available", "warehouse", "quantity"],
        priority=2,
    ),
    Pattern(
        name="forecast",
        keywords=["forecast", "prediction", "predicted", "expected", "prognosis"],
        priority=2,
    ),
]

IDENTIFIER_PATTERNS = [
    Pattern(
        name="model",
        keywords=["model"],
        regex=r"model\s+([A-Za-z]{2}\d{3}|[A-Za-z0-9]{5})",
        extractor=lambda m: m.group(1).upper() if m else None,
        priority=3,
    ),
    Pattern(
        name="model_direct",
        keywords=[],
        regex=r"\b([A-Za-z]{2}\d{3})\b",
        extractor=lambda m: m.group(1).upper() if m else None,
        priority=1,
    ),
    Pattern(
        name="sku",
        keywords=["sku"],
        regex=r"sku\s+([A-Za-z0-9]{9})",
        extractor=lambda m: m.group(1).upper() if m else None,
        priority=3,
    ),
    Pattern(
        name="sku_direct",
        keywords=[],
        regex=r"\b([A-Za-z]{2}\d{3}[A-Za-z0-9]{4})\b",
        extractor=lambda m: m.group(1).upper() if m else None,
        priority=1,
    ),
    Pattern(
        name="color",
        keywords=["color", "colour"],
        regex=r"colou?r\s+([A-Za-z]{2})",
        extractor=lambda m: m.group(1).upper() if m else None,
        priority=3,
    ),
]

TIME_PATTERNS = [
    Pattern(
        name="last_n_years",
        keywords=["last", "past"],
        regex=r"last\s+(\d+)\s+years?",
        extractor=lambda m: (int(m.group(1)), "years") if m else None,
        priority=3,
    ),
    Pattern(
        name="last_n_months",
        keywords=["last", "past"],
        regex=r"last\s+(\d+)\s+months?",
        extractor=lambda m: (int(m.group(1)), "months") if m else None,
        priority=3,
    ),
    Pattern(
        name="last_n_weeks",
        keywords=["last", "past"],
        regex=r"last\s+(\d+)\s+weeks?",
        extractor=lambda m: (int(m.group(1)), "weeks") if m else None,
        priority=3,
    ),
    Pattern(
        name="last_n_days",
        keywords=["last", "past"],
        regex=r"last\s+(\d+)\s+days?",
        extractor=lambda m: (int(m.group(1)), "days") if m else None,
        priority=3,
    ),
    Pattern(
        name="year_range",
        keywords=[],
        regex=r"(\d{4})\s*[-–to]+\s*(\d{4})",
        extractor=lambda m: (int(m.group(1)), int(m.group(2))) if m else None,
        priority=2,
    ),
    Pattern(
        name="single_year",
        keywords=["year", "in"],
        regex=r"(?:year|in)\s+(\d{4})",
        extractor=lambda m: (int(m.group(1)), int(m.group(1))) if m else None,
        priority=2,
    ),
    Pattern(
        name="year_direct",
        keywords=[],
        regex=r"\b(20[12]\d)\b",
        extractor=lambda m: (int(m.group(1)), int(m.group(1))) if m else None,
        priority=1,
    ),
]

FILTER_PATTERNS = [
    Pattern(
        name="below_rop",
        keywords=["below rop", "under rop", "reorder", "need reorder"],
        priority=2,
    ),
    Pattern(
        name="zero_stock",
        keywords=["zero stock", "no stock", "out of stock", "stockout"],
        priority=2,
    ),
    Pattern(
        name="type_seasonal",
        keywords=["seasonal", "season"],
        priority=2,
    ),
    Pattern(
        name="type_basic",
        keywords=["basic", "stable"],
        priority=2,
    ),
    Pattern(
        name="type_regular",
        keywords=["regular"],
        priority=2,
    ),
    Pattern(
        name="type_new",
        keywords=["new products", "new items", "new"],
        priority=2,
    ),
    Pattern(
        name="bestseller",
        keywords=["bestseller", "bestsellers", "best seller", "top selling"],
        priority=2,
    ),
    Pattern(
        name="overstock",
        keywords=["overstock", "overstocked", "excess", "surplus"],
        priority=2,
    ),
    Pattern(
        name="stock_condition",
        keywords=[],
        regex=r"stock\s*(>|<|>=|<=|=)\s*(\d+)",
        extractor=lambda m: ("stock", m.group(1), int(m.group(2))) if m else None,
        priority=3,
    ),
    Pattern(
        name="facility",
        keywords=["facility", "szwalnia"],
        regex=r"(?:facility|szwalnia)\s+([A-Za-z\s]+?)(?:\s+|$)",
        extractor=lambda m: ("facility", "=", m.group(1).strip()) if m else None,
        priority=2,
    ),
]

AGGREGATION_PATTERNS = [
    Pattern(
        name="by_month",
        keywords=["by month", "monthly", "per month"],
        priority=2,
    ),
    Pattern(
        name="by_year",
        keywords=["by year", "yearly", "per year", "annual"],
        priority=2,
    ),
    Pattern(
        name="by_model",
        keywords=["by model", "per model", "grouped by model", "models by"],
        priority=2,
    ),
    Pattern(
        name="by_color",
        keywords=["by color", "per color", "grouped by color", "colors by"],
        priority=2,
    ),
    Pattern(
        name="by_size",
        keywords=["by size", "per size", "grouped by size", "sizes by"],
        priority=2,
    ),
]

LIMIT_PATTERNS = [
    Pattern(
        name="top_n",
        keywords=["top"],
        regex=r"top\s+(\d+)",
        extractor=lambda m: int(m.group(1)) if m else None,
        priority=3,
    ),
    Pattern(
        name="first_n",
        keywords=["first"],
        regex=r"first\s+(\d+)",
        extractor=lambda m: int(m.group(1)) if m else None,
        priority=2,
    ),
    Pattern(
        name="limit_n",
        keywords=["limit"],
        regex=r"limit\s+(\d+)",
        extractor=lambda m: int(m.group(1)) if m else None,
        priority=2,
    ),
]

METRIC_PATTERNS = [
    Pattern(
        name="quantity",
        keywords=["quantity", "count", "pieces", "units", "how many"],
        priority=1,
    ),
    Pattern(
        name="value",
        keywords=["value", "revenue", "amount", "worth", "total"],
        priority=1,
    ),
    Pattern(
        name="average",
        keywords=["average", "avg", "mean"],
        priority=2,
    ),
    Pattern(
        name="sum",
        keywords=["sum", "total"],
        priority=2,
    ),
]

ALL_PATTERNS = {
    "entity": ENTITY_PATTERNS,
    "identifier": IDENTIFIER_PATTERNS,
    "time": TIME_PATTERNS,
    "filter": FILTER_PATTERNS,
    "aggregation": AGGREGATION_PATTERNS,
    "limit": LIMIT_PATTERNS,
    "metric": METRIC_PATTERNS,
}
