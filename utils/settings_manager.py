import json
import os
from typing import Any, Dict

SETTINGS_FILE = "../settings.json"

DEFAULT_SETTINGS = {
    "lead_time": 1.36,
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
    "optimizer": {"min_order_per_pattern": 5},
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
}


def load_settings() -> Dict[str, Any]:
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
        return _merge_with_defaults(settings)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load settings from {SETTINGS_FILE}: {e}")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except IOError as e:
        print(f"Error: Could not save settings to {SETTINGS_FILE}: {e}")
        return False


def reset_settings() -> Dict[str, Any]:
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()


def _merge_with_defaults(settings: Dict[str, Any]) -> Dict[str, Any]:
    merged = DEFAULT_SETTINGS.copy()

    for key in DEFAULT_SETTINGS:
        if key in settings:
            if isinstance(DEFAULT_SETTINGS[key], dict):
                merged[key] = DEFAULT_SETTINGS[key].copy()
                merged[key].update(settings[key])
            else:
                merged[key] = settings[key]

    return merged


def get_setting(key: str, settings: Dict[str, Any] | None = None) -> Any:
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


def update_setting(key: str, value: Any, settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
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
