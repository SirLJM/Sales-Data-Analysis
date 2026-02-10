from __future__ import annotations

from .aggregation import (
    AVERAGE_SALES,
    aggregate_by_model,
    aggregate_by_sku,
    aggregate_forecast_yearly,
    aggregate_yearly_sales,
    calculate_last_two_years_avg_sales,
)
from .classification import classify_sku_type, determine_seasonal_months
from .inventory_metrics import (
    calculate_forecast_date_range,
    calculate_forecast_metrics,
    calculate_safety_stock_and_rop,
)
from .order_priority import (
    aggregate_order_by_model_color,
    apply_priority_scoring,
    calculate_order_priority,
    find_urgent_colors,
    generate_order_recommendations,
    get_size_quantities_for_model_color,
)
from .pattern_helpers import (
    calculate_size_priorities,
    calculate_size_sales_history,
    get_size_sales_by_month_for_model,
    optimize_pattern_with_aliases,
)
from .projection import (
    calculate_model_stock_projection,
    calculate_stock_projection,
)
from .reports import (
    calculate_monthly_yoy_by_category,
    calculate_top_products_by_type,
    calculate_top_sales_report,
    calculate_worst_models_12m,
    calculate_worst_rotating_models,
    generate_weekly_new_products_analysis,
    get_last_n_months_sales_by_color,
)
from .utils import (
    get_completed_last_week_range,
    get_last_week_range,
    get_week_start_monday,
    parse_sku_components,
)
from .forecast_comparison import (
    align_forecasts,
    calculate_comparison_metrics,
    aggregate_comparison_by_type,
    calculate_overall_summary,
)
from .internal_forecast import (
    batch_generate_forecasts,
    generate_internal_forecast,
    prepare_monthly_series,
    select_forecast_method,
)
from .material_planning import (
    calculate_material_gap,
    calculate_material_requirements,
    extract_production_quantities_from_orders,
    map_ribbing_type_to_material,
)

__all__ = [
    "AVERAGE_SALES",
    "aggregate_by_model",
    "aggregate_by_sku",
    "aggregate_forecast_yearly",
    "aggregate_order_by_model_color",
    "aggregate_yearly_sales",
    "calculate_forecast_date_range",
    "calculate_forecast_metrics",
    "calculate_last_two_years_avg_sales",
    "calculate_model_stock_projection",
    "calculate_monthly_yoy_by_category",
    "calculate_order_priority",
    "calculate_safety_stock_and_rop",
    "calculate_size_priorities",
    "calculate_size_sales_history",
    "calculate_stock_projection",
    "calculate_top_products_by_type",
    "calculate_top_sales_report",
    "calculate_worst_models_12m",
    "calculate_worst_rotating_models",
    "classify_sku_type",
    "determine_seasonal_months",
    "apply_priority_scoring",
    "find_urgent_colors",
    "generate_order_recommendations",
    "generate_weekly_new_products_analysis",
    "get_completed_last_week_range",
    "get_last_n_months_sales_by_color",
    "get_last_week_range",
    "get_size_quantities_for_model_color",
    "get_size_sales_by_month_for_model",
    "get_week_start_monday",
    "optimize_pattern_with_aliases",
    "parse_sku_components",
    "align_forecasts",
    "calculate_comparison_metrics",
    "aggregate_comparison_by_type",
    "calculate_overall_summary",
    "batch_generate_forecasts",
    "generate_internal_forecast",
    "prepare_monthly_series",
    "select_forecast_method",
    "calculate_material_gap",
    "calculate_material_requirements",
    "extract_production_quantities_from_orders",
    "map_ribbing_type_to_material",
]
