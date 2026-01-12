from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.logging_config import get_logger

logger = get_logger("settings_manager")

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"

DEFAULT_SETTINGS = {
    "data_source": {
        "mode": "file",
        "fallback_to_file": True,
        "pool_size": 10,
        "pool_recycle": 3600,
        "echo_sql": False,
    },
    "lead_time": 1.36,
    "forecast_time": 5,
    "sync_forecast_with_lead_time": False,
    "cv_thresholds": {"basic": 0.6, "seasonal": 1.0},
    "z_scores": {
        "basic": 2.5,
        "regular": 1.645,
        "seasonal_in": 1.85,
        "seasonal_out": 1.5,
        "new": 1.8,
    },
    "new_product_threshold_months": 12,
    "weekly_analysis": {"lookback_days": 60},
    "optimizer": {"min_order_per_pattern": 5, "algorithm_mode": "greedy_overshoot"},
    "order_recommendations": {
        "stockout_risk": {
            "zero_stock_penalty": 100,
            "below_rop_max_penalty": 80,
        },
        "priority_weights": {
            "stockout_risk": 0.5,
            "revenue_impact": 0.3,
            "demand_forecast": 0.2,
        },
        "type_multipliers": {
            "new": 1.2,
            "seasonal": 1.3,
            "regular": 1.0,
            "basic": 0.9,
        },
        "demand_cap": 100,
    },
    "forecast_accuracy": {
        "default_analysis_months": 3,
        "forecast_lookback_months": 4,
        "mape_threshold_good": 20.0,
        "mape_threshold_acceptable": 40.0,
    },
    "ml_forecast": {
        "default_models": ["lightgbm", "random_forest"],
        "cv_splits": 3,
        "cv_test_size": 3,
        "cv_metric": "mape",
        "include_statistical": True,
        "confidence_level": 0.95,
    },
    "facility_capacity": {},
}


def load_settings() -> dict[str, Any]:
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
        return _merge_with_defaults(settings)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Could not load settings from %s: %s", SETTINGS_FILE, e)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict[str, Any]) -> bool:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except IOError as e:
        logger.error("Could not save settings to %s: %s", SETTINGS_FILE, e)
        return False


def reset_settings() -> dict[str, Any]:
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()


def _merge_with_defaults(settings: dict[str, Any]) -> dict[str, Any]:
    merged = DEFAULT_SETTINGS.copy()

    for key, default_value in DEFAULT_SETTINGS.items():
        if key not in settings:
            continue

        if isinstance(default_value, dict):
            merged[key] = {**default_value, **settings[key]}
        else:
            merged[key] = settings[key]

    return merged


def get_setting(key: str, settings: dict[str, Any] | None = None) -> Any:
    if settings is None:
        settings = load_settings()

    keys = key.split(".")
    value = settings

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None

    return value


def update_setting(key: str, value: Any, settings: dict[str, Any] | None = None) -> dict[str, Any]:
    if settings is None:
        settings = load_settings()

    keys = key.split(".")
    current = settings

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value

    return settings
