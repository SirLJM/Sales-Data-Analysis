from __future__ import annotations

from typing import Final


class SessionKeys:
    SETTINGS: Final[str] = "settings"
    DATA_SOURCE: Final[str] = "data_source"
    PATTERN_SETS: Final[str] = "pattern_sets"
    ACTIVE_SET_ID: Final[str] = "active_set_id"
    SHOW_ADD_PATTERN_SET: Final[str] = "show_add_pattern_set"
    EDIT_SET_ID: Final[str] = "edit_set_id"
    NUM_PATTERNS: Final[str] = "num_patterns"
    NUM_SIZES: Final[str] = "num_sizes"
    RECOMMENDATIONS_DATA: Final[str] = "recommendations_data"
    RECOMMENDATIONS_TOP_N: Final[str] = "recommendations_top_n"
    SELECTED_ORDER_ITEMS: Final[str] = "selected_order_items"
    SZWALNIA_INCLUDE_FILTER: Final[str] = "szwalnia_include_filter"
    SZWALNIA_EXCLUDE_FILTER: Final[str] = "szwalnia_exclude_filter"
    MONTHLY_YOY_PODGRUPA: Final[str] = "monthly_yoy_podgrupa"
    MONTHLY_YOY_KATEGORIA: Final[str] = "monthly_yoy_kategoria"
    MONTHLY_YOY_METADATA: Final[str] = "monthly_yoy_metadata"
    FORECAST_COMPARISON_DATA: Final[str] = "forecast_comparison_data"
    FORECAST_COMPARISON_PARAMS: Final[str] = "forecast_comparison_params"
    ML_FORECAST_DATA: Final[str] = "ml_forecast_data"
    ML_FORECAST_PARAMS: Final[str] = "ml_forecast_params"
    ML_TRAINED_MODELS: Final[str] = "ml_trained_models"
    ML_TRAINING_STATS: Final[str] = "ml_training_stats"


class ColumnNames:
    SKU: Final[str] = "SKU"
    MODEL: Final[str] = "MODEL"
    COLOR: Final[str] = "COLOR"
    SIZE: Final[str] = "SIZE"
    STOCK: Final[str] = "STOCK"
    VALUE: Final[str] = "VALUE"
    DESCRIPTION: Final[str] = "DESCRIPTION"
    PRICE: Final[str] = "PRICE"
    ROP: Final[str] = "ROP"
    SS: Final[str] = "SS"
    DEFICIT: Final[str] = "DEFICIT"
    FORECAST_LEADTIME: Final[str] = "FORECAST_LEADTIME"
    AVERAGE_SALES: Final[str] = "AVERAGE SALES"
    OVERSTOCKED_PCT: Final[str] = "OVERSTOCKED_%"
    BELOW_ROP: Final[str] = "Below ROP"
    PRIORITY_SCORE: Final[str] = "PRIORITY_SCORE"
    TYPE: Final[str] = "TYPE"
    CV: Final[str] = "CV"
    SZWALNIA_G: Final[str] = "SZWALNIA GŁÓWNA"
    SZWALNIA_D: Final[str] = "SZWALNIA DRUGA"
    MATERIAL: Final[str] = "RODZAJ MATERIAŁU"
    GRAMATURA: Final[str] = "GRAMATURA"
    MODEL_COLOR: Final[str] = "MODEL+COLOR"
    SIZE_QTY: Final[str] = "Sizes (Size:Qty)"
    ORDER_ID: Final[str] = "Order ID"
    ORDER_DATE: Final[str] = "Order Date"
    CURRENT_SALES: Final[str] = "Current Sales"
    PRIOR_YEAR_SALES: Final[str] = "Prior Year Sales"
    CHANGE_PCT: Final[str] = "Change %"
    CURRENT_PERIOD: Final[str] = "Current Period"
    LAST_WEEK: Final[str] = "Last Week"
    DAYS_ELAPSED: Final[str] = "Days Elapsed"


class Icons:
    SUCCESS: Final[str] = "✅"
    ERROR: Final[str] = "❌"
    WARNING: Final[str] = "⚠️"
    URGENT: Final[str] = "🚨"
    NEW: Final[str] = "🆕"
    SEASONAL: Final[str] = "🌸"
    BASIC: Final[str] = "⚙️"
    REGULAR: Final[str] = "📦"
    RISING: Final[str] = "📈"
    FALLING: Final[str] = "📉"
    ROCKET: Final[str] = "🚀"
    INFO: Final[str] = "ℹ️"


class AlgorithmModes:
    CLASSIC_GREEDY: Final[str] = "Classic Greedy"
    GREEDY_OVERSHOOT: Final[str] = "Greedy Overshoot"


class Config:
    MAX_ITERATIONS: Final[int] = 200
    DELIVERY_THRESHOLD_DAYS: Final[int] = 42
    DEFAULT_TOP_N: Final[int] = 10
    DATAFRAME_HEIGHT: Final[int] = 600
    CHART_HEIGHT: Final[int] = 500
    CACHE_TTL: Final[int] = 3600
    DEFAULT_NUM_PATTERNS: Final[int] = 6
    DEFAULT_NUM_SIZES: Final[int] = 5
    RECOMMENDATIONS_MIN: Final[int] = 5
    RECOMMENDATIONS_MAX: Final[int] = 50
    RECOMMENDATIONS_STEP: Final[int] = 5
    WEEKLY_LOOKBACK_DAYS: Final[int] = 60
    DEFAULT_OVERSTOCK_THRESHOLD: Final[int] = 20


class MimeTypes:
    TEXT_CSV: Final[str] = "text/csv"
