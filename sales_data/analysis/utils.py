from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd


def get_week_start_monday(date: datetime) -> datetime:
    days_since_mon = date.weekday()
    week_start = date - timedelta(days=days_since_mon)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)


def get_completed_last_week_range(reference_date: datetime) -> tuple[datetime, datetime]:
    current_week_start = get_week_start_monday(reference_date)
    last_week_start = current_week_start - timedelta(days=7)
    last_week_end = last_week_start + timedelta(days=6)
    last_week_end = last_week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
    return last_week_start, last_week_end


def get_last_week_range(reference_date: datetime) -> tuple[datetime, datetime]:
    if reference_date.weekday() >= 2:
        last_week_start = get_week_start_monday(reference_date)
    else:
        last_week_start = get_week_start_monday(reference_date - timedelta(days=7))

    last_week_end = last_week_start + timedelta(days=6)
    last_week_end = last_week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
    return last_week_start, last_week_end


def parse_sku_components(sku: str) -> dict[str, str]:
    sku_str = str(sku)
    return {
        "model": sku_str[:5] if len(sku_str) >= 5 else sku_str,
        "color": sku_str[5:7] if len(sku_str) >= 7 else "",
        "size": sku_str[7:9] if len(sku_str) >= 9 else "",
    }


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((col for col in candidates if col in df.columns), None)
