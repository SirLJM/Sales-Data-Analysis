from __future__ import annotations

from typing import Final

_current_language: str = "en"


def set_language(lang: str) -> None:
    global _current_language
    if lang in TRANSLATIONS:
        _current_language = lang


def get_language() -> str:
    return _current_language


def t(key: str) -> str:
    translations = TRANSLATIONS.get(_current_language, TRANSLATIONS["en"])
    return translations.get(key, TRANSLATIONS["en"].get(key, key))


class Keys:
    PAGE_TITLE: Final[str] = "page_title"

    TAB_TASK_PLANNER: Final[str] = "tab_task_planner"
    TAB_SALES_ANALYSIS: Final[str] = "tab_sales_analysis"
    TAB_PATTERN_OPTIMIZER: Final[str] = "tab_pattern_optimizer"
    TAB_WEEKLY_ANALYSIS: Final[str] = "tab_weekly_analysis"
    TAB_MONTHLY_ANALYSIS: Final[str] = "tab_monthly_analysis"
    TAB_ORDER_RECOMMENDATIONS: Final[str] = "tab_order_recommendations"
    TAB_ORDER_CREATION: Final[str] = "tab_order_creation"
    TAB_ORDER_TRACKING: Final[str] = "tab_order_tracking"
    TAB_FORECAST_ACCURACY: Final[str] = "tab_forecast_accuracy"
    TAB_FORECAST_COMPARISON: Final[str] = "tab_forecast_comparison"
    TAB_ML_FORECAST: Final[str] = "tab_ml_forecast"
    TAB_NL_QUERY: Final[str] = "tab_nl_query"

    SIDEBAR_PARAMETERS: Final[str] = "sidebar_parameters"
    SIDEBAR_LEAD_TIME_FORECAST: Final[str] = "sidebar_lead_time_forecast"
    SIDEBAR_SERVICE_LEVELS: Final[str] = "sidebar_service_levels"
    SIDEBAR_PATTERN_OPTIMIZER: Final[str] = "sidebar_pattern_optimizer"
    SIDEBAR_CURRENT_PARAMS: Final[str] = "sidebar_current_params"
    SIDEBAR_VIEW_OPTIONS: Final[str] = "sidebar_view_options"
    SIDEBAR_LOAD_DATA: Final[str] = "sidebar_load_data"

    BTN_SAVE: Final[str] = "btn_save"
    BTN_RESET: Final[str] = "btn_reset"
    BTN_CANCEL: Final[str] = "btn_cancel"
    BTN_CLEAR: Final[str] = "btn_clear"
    BTN_DOWNLOAD_CSV: Final[str] = "btn_download_csv"
    BTN_GENERATE: Final[str] = "btn_generate"
    BTN_REFRESH: Final[str] = "btn_refresh"
    BTN_CREATE_ORDER: Final[str] = "btn_create_order"
    BTN_SAVE_TO_DB: Final[str] = "btn_save_to_db"
    BTN_RUN_OPTIMIZATION: Final[str] = "btn_run_optimization"
    BTN_NEW_SET: Final[str] = "btn_new_set"
    BTN_EDIT_SET: Final[str] = "btn_edit_set"
    BTN_DELETE_SET: Final[str] = "btn_delete_set"
    BTN_SAVE_ALL: Final[str] = "btn_save_all"
    BTN_RELOAD: Final[str] = "btn_reload"
    BTN_SAVE_PATTERN_SET: Final[str] = "btn_save_pattern_set"
    BTN_LOAD_SALES_HISTORY: Final[str] = "btn_load_sales_history"
    BTN_EXECUTE: Final[str] = "btn_execute"
    BTN_ADD_ORDER: Final[str] = "btn_add_order"
    BTN_ARCHIVE: Final[str] = "btn_archive"
    BTN_PARSE_PDF: Final[str] = "btn_parse_pdf"
    BTN_GENERATE_RECOMMENDATIONS: Final[str] = "btn_generate_recommendations"
    BTN_GENERATE_COMPARISON: Final[str] = "btn_generate_comparison"
    BTN_GENERATE_FORECASTS: Final[str] = "btn_generate_forecasts"

    LEAD_TIME_MONTHS: Final[str] = "lead_time_months"
    LEAD_TIME_HELP: Final[str] = "lead_time_help"
    SYNC_FORECAST: Final[str] = "sync_forecast"
    SYNC_FORECAST_HELP: Final[str] = "sync_forecast_help"
    FORECAST_TIME_MONTHS: Final[str] = "forecast_time_months"
    FORECAST_TIME_HELP: Final[str] = "forecast_time_help"

    TYPE_BASIC: Final[str] = "type_basic"
    TYPE_REGULAR: Final[str] = "type_regular"
    TYPE_SEASONAL: Final[str] = "type_seasonal"
    TYPE_NEW: Final[str] = "type_new"

    COL_TYPE: Final[str] = "col_type"
    COL_CV: Final[str] = "col_cv"
    COL_ZSCORE: Final[str] = "col_zscore"
    COL_ALGORITHM: Final[str] = "col_algorithm"

    ALG_GREEDY_OVERSHOOT: Final[str] = "alg_greedy_overshoot"
    ALG_CLASSIC_GREEDY: Final[str] = "alg_classic_greedy"
    ALG_HELP: Final[str] = "alg_help"

    GROUP_BY_MODEL: Final[str] = "group_by_model"
    LOAD_STOCK_DATA: Final[str] = "load_stock_data"
    LOAD_FORECAST_DATA: Final[str] = "load_forecast_data"

    MSG_SAVED: Final[str] = "msg_saved"
    MSG_SAVE_FAILED: Final[str] = "msg_save_failed"
    MSG_NO_STOCK_FILE: Final[str] = "msg_no_stock_file"
    MSG_NO_FORECAST_FILE: Final[str] = "msg_no_forecast_file"
    MSG_ERROR_PROCESSING_FORECAST: Final[str] = "msg_error_processing_forecast"
    MSG_NO_DATA_AVAILABLE: Final[str] = "msg_no_data_available"
    MSG_NOT_FOUND: Final[str] = "msg_not_found"
    MSG_LOAD_BOTH_DATASETS: Final[str] = "msg_load_both_datasets"
    MSG_NO_FORECAST_DATA: Final[str] = "msg_no_forecast_data"

    TITLE_TASK_PLANNER: Final[str] = "title_task_planner"
    TITLE_SALES_DATA_ANALYSIS: Final[str] = "title_sales_data_analysis"
    TITLE_STOCK_PROJECTION: Final[str] = "title_stock_projection"
    TITLE_YEARLY_SALES_TREND: Final[str] = "title_yearly_sales_trend"
    TITLE_STOCK_STATUS: Final[str] = "title_stock_status"
    TITLE_ORDER_QUANTITIES: Final[str] = "title_order_quantities"
    TITLE_SALES_HISTORY: Final[str] = "title_sales_history"
    TITLE_PATTERN_SETS: Final[str] = "title_pattern_sets"
    TITLE_OPTIMIZATION: Final[str] = "title_optimization"
    TITLE_ORDER_SUMMARY: Final[str] = "title_order_summary"
    TITLE_WEEKLY_ANALYSIS: Final[str] = "title_weekly_analysis"
    TITLE_MONTHLY_ANALYSIS: Final[str] = "title_monthly_analysis"
    TITLE_ORDER_RECOMMENDATIONS: Final[str] = "title_order_recommendations"
    TITLE_ORDER_CREATION: Final[str] = "title_order_creation"
    TITLE_ORDER_TRACKING: Final[str] = "title_order_tracking"
    TITLE_FORECAST_ACCURACY: Final[str] = "title_forecast_accuracy"
    TITLE_FORECAST_COMPARISON: Final[str] = "title_forecast_comparison"
    TITLE_ML_FORECAST: Final[str] = "title_ml_forecast"
    TITLE_NL_QUERY: Final[str] = "title_nl_query"
    TITLE_TOP_SALES_REPORT: Final[str] = "title_top_sales_report"
    TITLE_TOP_5_BY_TYPE: Final[str] = "title_top_5_by_type"
    TITLE_NEW_PRODUCTS_MONITORING: Final[str] = "title_new_products_monitoring"
    TITLE_ACTIVE_ORDERS: Final[str] = "title_active_orders"
    TITLE_MANUAL_ORDER: Final[str] = "title_manual_order"
    TITLE_IMPORT_PDF: Final[str] = "title_import_pdf"
    TITLE_RECOMMENDATION_PARAMS: Final[str] = "title_recommendation_params"

    SEARCH_MODEL: Final[str] = "search_model"
    SEARCH_SKU: Final[str] = "search_sku"
    SEARCH_MODEL_PLACEHOLDER: Final[str] = "search_model_placeholder"
    SEARCH_SKU_PLACEHOLDER: Final[str] = "search_sku_placeholder"
    SHOW_ONLY_BELOW_ROP: Final[str] = "show_only_below_rop"
    BESTSELLERS: Final[str] = "bestsellers"
    FILTER_BY_TYPE: Final[str] = "filter_by_type"
    OVERSTOCKED_FILTER: Final[str] = "overstocked_filter"
    SHOW_OVERSTOCKED: Final[str] = "show_overstocked"
    OVERSTOCKED_BY_PCT: Final[str] = "overstocked_by_pct"

    SHOWING_N_OF_M: Final[str] = "showing_n_of_m"
    MODELS: Final[str] = "models"
    SKUS: Final[str] = "skus"

    METRIC_TOTAL_SKUS: Final[str] = "metric_total_skus"
    METRIC_TOTAL_QUANTITY: Final[str] = "metric_total_quantity"
    METRIC_BELOW_ROP: Final[str] = "metric_below_rop"
    METRIC_TOTAL_DEFICIT: Final[str] = "metric_total_deficit"
    METRIC_PCT_BELOW_ROP: Final[str] = "metric_pct_below_rop"
    METRIC_OVERSTOCKED: Final[str] = "metric_overstocked"
    METRIC_NORMAL: Final[str] = "metric_normal"
    METRIC_TOTAL_STOCK: Final[str] = "metric_total_stock"
    METRIC_TOTAL_STOCK_VALUE: Final[str] = "metric_total_stock_value"
    METRIC_CURRENT_STOCK: Final[str] = "metric_current_stock"
    METRIC_ROP: Final[str] = "metric_rop"
    METRIC_SAFETY_STOCK: Final[str] = "metric_safety_stock"
    METRIC_AVG_MONTHLY_SALES: Final[str] = "metric_avg_monthly_sales"
    METRIC_FIRST_SALE_YEAR: Final[str] = "metric_first_sale_year"
    METRIC_YEARS_ACTIVE: Final[str] = "metric_years_active"
    METRIC_TOTAL_HISTORICAL_SALES: Final[str] = "metric_total_historical_sales"
    METRIC_FORECAST_FUTURE: Final[str] = "metric_forecast_future"
    METRIC_LAST_WEEK: Final[str] = "metric_last_week"
    METRIC_SAME_WEEK_LAST_YEAR: Final[str] = "metric_same_week_last_year"
    METRIC_NEW_PRODUCTS: Final[str] = "metric_new_products"
    METRIC_WEEKS_TRACKED: Final[str] = "metric_weeks_tracked"
    METRIC_TOTAL_SALES: Final[str] = "metric_total_sales"
    METRIC_CURRENT_PERIOD: Final[str] = "metric_current_period"
    METRIC_SAME_PERIOD_LAST_YEAR: Final[str] = "metric_same_period_last_year"
    METRIC_TOTAL_YOY_CHANGE: Final[str] = "metric_total_yoy_change"
    METRIC_RISING_CATEGORIES: Final[str] = "metric_rising_categories"
    METRIC_FALLING_CATEGORIES: Final[str] = "metric_falling_categories"
    METRIC_UNCATEGORIZED: Final[str] = "metric_uncategorized"
    METRIC_MAPE: Final[str] = "metric_mape"
    METRIC_BIAS: Final[str] = "metric_bias"
    METRIC_MISSED_OPPORTUNITY: Final[str] = "metric_missed_opportunity"
    METRIC_VOLUME_ACCURACY: Final[str] = "metric_volume_accuracy"
    METRIC_ROWS: Final[str] = "metric_rows"
    METRIC_COLUMNS: Final[str] = "metric_columns"

    DOWNLOAD_MODEL_SUMMARY: Final[str] = "download_model_summary"
    DOWNLOAD_SKU_SUMMARY: Final[str] = "download_sku_summary"
    DOWNLOAD_WEEKLY_ANALYSIS: Final[str] = "download_weekly_analysis"
    DOWNLOAD_PODGRUPA_SUMMARY: Final[str] = "download_podgrupa_summary"
    DOWNLOAD_CATEGORY_DETAILS: Final[str] = "download_category_details"
    DOWNLOAD_RESULTS: Final[str] = "download_results"

    ENTER_MODEL_TO_ANALYZE: Final[str] = "enter_model_to_analyze"
    ENTER_SKU_TO_ANALYZE: Final[str] = "enter_sku_to_analyze"
    PROJECTION_MONTHS: Final[str] = "projection_months"
    ITEMS_AVAILABLE: Final[str] = "items_available"

    CHART_PROJECTED_STOCK: Final[str] = "chart_projected_stock"
    CHART_ROP: Final[str] = "chart_rop"
    CHART_SAFETY_STOCK: Final[str] = "chart_safety_stock"
    CHART_ZERO_STOCK: Final[str] = "chart_zero_stock"
    CHART_ROP_REACHED: Final[str] = "chart_rop_reached"
    CHART_STOCKOUT: Final[str] = "chart_stockout"
    CHART_HISTORICAL_SALES: Final[str] = "chart_historical_sales"
    CHART_FORECAST: Final[str] = "chart_forecast"
    CHART_DATE: Final[str] = "chart_date"
    CHART_QUANTITY: Final[str] = "chart_quantity"
    CHART_YEAR: Final[str] = "chart_year"
    CHART_QUANTITY_SOLD: Final[str] = "chart_quantity_sold"

    STOCK_PROJECTION_FOR: Final[str] = "stock_projection_for"
    YEARLY_SALES_TREND_FOR: Final[str] = "yearly_sales_trend_for"
    STOCK_STATUS_DISTRIBUTION: Final[str] = "stock_status_distribution"

    WARN_ROP_IN_DAYS: Final[str] = "warn_rop_in_days"
    ERR_STOCKOUT_IN_DAYS: Final[str] = "err_stockout_in_days"

    GROUP_BY: Final[str] = "group_by"
    GROUP_MODEL: Final[str] = "group_model"
    GROUP_MODEL_COLOR: Final[str] = "group_model_color"

    SORT_BY: Final[str] = "sort_by"
    FILTER_BY_CODE: Final[str] = "filter_by_code"
    ALL_ITEMS_SUMMARY: Final[str] = "all_items_summary"
    YOY_TREND: Final[str] = "yoy_trend"

    YEARLY_CAPTION: Final[str] = "yearly_caption"
    WEEKLY_CAPTION: Final[str] = "weekly_caption"
    WEEKLY_TOP_SALES_CAPTION: Final[str] = "weekly_top_sales_caption"
    WEEKLY_NEW_PRODUCTS_CAPTION: Final[str] = "weekly_new_products_caption"
    MONTHLY_CAPTION: Final[str] = "monthly_caption"

    RISING_STAR: Final[str] = "rising_star"
    FALLING_STAR: Final[str] = "falling_star"
    NO_RISING_PRODUCTS: Final[str] = "no_rising_products"
    NO_FALLING_PRODUCTS: Final[str] = "no_falling_products"
    NO_PRODUCTS_FOUND: Final[str] = "no_products_found"
    NO_NEW_PRODUCTS: Final[str] = "no_new_products"
    ZERO_SALES_WARNING: Final[str] = "zero_sales_warning"
    VIEW_ZERO_SALES: Final[str] = "view_zero_sales"

    SALES_BY_AGE_GROUP: Final[str] = "sales_by_age_group"
    CLOTHING_CATEGORY: Final[str] = "clothing_category"
    CURRENT_SALES: Final[str] = "current_sales"
    PRIOR_YEAR_SALES: Final[str] = "prior_year_sales"
    DIFFERENCE: Final[str] = "difference"
    CHANGE_PCT: Final[str] = "change_pct"
    NO_DATA_AGE_GROUP: Final[str] = "no_data_age_group"
    CATEGORY_MAPPINGS_ERROR: Final[str] = "category_mappings_error"
    NO_SALES_DATA: Final[str] = "no_sales_data"
    CLICK_GENERATE: Final[str] = "click_generate"

    PRIORITY_WEIGHTS: Final[str] = "priority_weights"
    TYPE_MULTIPLIERS: Final[str] = "type_multipliers"
    STOCKOUT_RISK_PARAMS: Final[str] = "stockout_risk_params"
    FILTER_BY_FACILITY: Final[str] = "filter_by_facility"
    PARAM_STOCKOUT_RISK: Final[str] = "param_stockout_risk"
    PARAM_REVENUE_IMPACT: Final[str] = "param_revenue_impact"
    PARAM_DEMAND_FORECAST: Final[str] = "param_demand_forecast"
    PARAM_ZERO_STOCK_PENALTY: Final[str] = "param_zero_stock_penalty"
    PARAM_BELOW_ROP_PENALTY: Final[str] = "param_below_rop_penalty"
    PARAM_DEMAND_CAP: Final[str] = "param_demand_cap"
    PARAM_TOP_PRIORITY: Final[str] = "param_top_priority"
    INCLUDE_FACILITIES: Final[str] = "include_facilities"
    EXCLUDE_FACILITIES: Final[str] = "exclude_facilities"
    FORECAST_SOURCE: Final[str] = "forecast_source"
    EXTERNAL: Final[str] = "external"
    TOP_PRIORITY_ITEMS: Final[str] = "top_priority_items"
    SHOWING_TOP_N: Final[str] = "showing_top_n"
    LOAD_STOCK_FORECAST: Final[str] = "load_stock_forecast"
    FILTERED_ACTIVE_ORDERS: Final[str] = "filtered_active_orders"

    PATTERN_SET_NAME: Final[str] = "pattern_set_name"
    NUM_SIZE_CATEGORIES: Final[str] = "num_size_categories"
    DEFINE_SIZE_CATEGORIES: Final[str] = "define_size_categories"
    SIZE_N: Final[str] = "size_n"
    NUM_PATTERNS: Final[str] = "num_patterns"
    PATTERN_NAME: Final[str] = "pattern_name"
    QUANTITIES_PER_SIZE: Final[str] = "quantities_per_size"
    SELECT_ACTIVE_PATTERN_SET: Final[str] = "select_active_pattern_set"
    MIN_ORDER_PER_PATTERN: Final[str] = "min_order_per_pattern"
    USING_SIZES_FROM: Final[str] = "using_sizes_from"
    ENTER_SALES_PER_SIZE: Final[str] = "enter_sales_per_size"
    NO_PATTERN_SETS: Final[str] = "no_pattern_sets"
    PATTERN_SETS_SAVED: Final[str] = "pattern_sets_saved"
    ALL_REQUIREMENTS_MET: Final[str] = "all_requirements_met"
    MIN_ORDER_VIOLATIONS: Final[str] = "min_order_violations"
    SOME_NOT_COVERED: Final[str] = "some_not_covered"
    EXCLUDED_SIZES: Final[str] = "excluded_sizes"
    COMPLETE_ALL_FIELDS: Final[str] = "complete_all_fields"
    PATTERN: Final[str] = "pattern"
    COUNT: Final[str] = "count"
    COMPOSITION: Final[str] = "composition"
    STATUS: Final[str] = "status"
    PATTERN_ALLOCATION: Final[str] = "pattern_allocation"
    PRODUCTION_VS_REQUIRED: Final[str] = "production_vs_required"
    REQUIRED: Final[str] = "required"
    PRODUCED: Final[str] = "produced"
    EXCESS: Final[str] = "excess"
    TOTAL: Final[str] = "total"

    ENTER_MODEL_CODE: Final[str] = "enter_model_code"
    NO_ITEMS_SELECTED: Final[str] = "no_items_selected"
    MULTIPLE_MODELS_SELECTED: Final[str] = "multiple_models_selected"
    MODEL_NOT_FOUND: Final[str] = "model_not_found"
    NO_DATA_FOR_MODEL: Final[str] = "no_data_for_model"
    NO_FORECAST_DEFICIT: Final[str] = "no_forecast_deficit"
    PATTERN_SET_NOT_FOUND: Final[str] = "pattern_set_not_found"
    CREATE_PATTERN_SET_HINT: Final[str] = "create_pattern_set_hint"
    FOUND_PATTERN_SET: Final[str] = "found_pattern_set"
    CREATED_ORDER: Final[str] = "created_order"
    URGENT_COLORS: Final[str] = "urgent_colors"

    ORDER_ID: Final[str] = "order_id"
    ORDER_DATE: Final[str] = "order_date"
    MODEL: Final[str] = "model"
    PRODUCT: Final[str] = "product"
    QUANTITY: Final[str] = "quantity"
    FACILITY: Final[str] = "facility"
    OPERATION: Final[str] = "operation"
    MATERIAL: Final[str] = "material"
    DAYS_ELAPSED: Final[str] = "days_elapsed"
    UPLOAD_PDF: Final[str] = "upload_pdf"
    FILE_UPLOADED: Final[str] = "file_uploaded"
    PDF_PARSED: Final[str] = "pdf_parsed"
    ORDER_CREATED_PDF: Final[str] = "order_created_pdf"
    ORDER_ADDED: Final[str] = "order_added"
    NO_ACTIVE_ORDERS: Final[str] = "no_active_orders"
    ORDER_ARCHIVED: Final[str] = "order_archived"
    FAILED_PARSE_PDF: Final[str] = "failed_parse_pdf"
    FAILED_CREATE_ORDER: Final[str] = "failed_create_order"
    FAILED_ADD_ORDER: Final[str] = "failed_add_order"
    FAILED_ARCHIVE_ORDER: Final[str] = "failed_archive_order"
    TOTAL_ACTIVE_ORDERS: Final[str] = "total_active_orders"
    ORDERS_READY: Final[str] = "orders_ready"
    STATUS_READY: Final[str] = "status_ready"
    STATUS_PENDING: Final[str] = "status_pending"
    ARCHIVE_ORDER: Final[str] = "archive_order"

    ANALYSIS_START_DATE: Final[str] = "analysis_start_date"
    ANALYSIS_END_DATE: Final[str] = "analysis_end_date"
    FORECAST_LOOKBACK: Final[str] = "forecast_lookback"
    VIEW_LEVEL: Final[str] = "view_level"
    SKU_LEVEL: Final[str] = "sku_level"
    MODEL_LEVEL: Final[str] = "model_level"
    OVERALL_ACCURACY_METRICS: Final[str] = "overall_accuracy_metrics"
    MAPE_HELP: Final[str] = "mape_help"
    BIAS_HELP: Final[str] = "bias_help"
    MISSED_OPP_HELP: Final[str] = "missed_opp_help"
    VOLUME_ACC_HELP: Final[str] = "volume_acc_help"
    GOOD: Final[str] = "good"
    ACCEPTABLE: Final[str] = "acceptable"
    POOR: Final[str] = "poor"
    OVER_FORECASTING: Final[str] = "over_forecasting"
    UNDER_FORECASTING: Final[str] = "under_forecasting"
    PRODUCT_TYPE_BREAKDOWN: Final[str] = "product_type_breakdown"
    TREND_CHART: Final[str] = "trend_chart"

    COMPARE_FORECASTS: Final[str] = "compare_forecasts"
    GENERATE_NEW: Final[str] = "generate_new"
    HISTORICAL_FORECASTS: Final[str] = "historical_forecasts"
    FORECAST_HORIZON: Final[str] = "forecast_horizon"
    ANALYSIS_LEVEL: Final[str] = "analysis_level"
    ENTITY_FILTER: Final[str] = "entity_filter"
    FORECAST_METHOD: Final[str] = "forecast_method"
    GENERATE_AS_OF: Final[str] = "generate_as_of"
    COMPARE_AS_OF: Final[str] = "compare_as_of"
    ALL_ENTITIES: Final[str] = "all_entities"
    TOP_N_BY_VOLUME: Final[str] = "top_n_by_volume"
    BY_PRODUCT_TYPE: Final[str] = "by_product_type"
    AUTO_SELECT: Final[str] = "auto_select"
    NUMBER_TOP_ENTITIES: Final[str] = "number_top_entities"
    PRODUCT_TYPES: Final[str] = "product_types"
    FILTER_BY_MODEL: Final[str] = "filter_by_model"
    FORECAST_METHOD_HELP: Final[str] = "forecast_method_help"
    DATE_CAPTION: Final[str] = "date_caption"

    MANAGE_MODELS: Final[str] = "manage_models"
    TRAINING_PARAMS: Final[str] = "training_params"
    MODELS_TO_EVALUATE: Final[str] = "models_to_evaluate"
    ML_MODELS: Final[str] = "ml_models"
    STATISTICAL_MODELS: Final[str] = "statistical_models"
    ENTITY_LEVEL: Final[str] = "entity_level"
    TOP_N_ENTITIES: Final[str] = "top_n_entities"
    CV_METRIC: Final[str] = "cv_metric"
    CV_SPLITS: Final[str] = "cv_splits"
    CV_TEST_SIZE: Final[str] = "cv_test_size"
    INCLUDE_STATISTICAL: Final[str] = "include_statistical"
    TRAINING_COMPLETE: Final[str] = "training_complete"

    QUERY_DATA: Final[str] = "query_data"
    DB_MODE_INFO: Final[str] = "db_mode_info"
    FILE_MODE_INFO: Final[str] = "file_mode_info"
    ENTER_QUERY: Final[str] = "enter_query"
    RESULTS: Final[str] = "results"
    QUERY_PLACEHOLDER: Final[str] = "query_placeholder"
    QUERY_INTERPRETATION: Final[str] = "query_interpretation"
    EXAMPLE_QUERIES: Final[str] = "example_queries"
    CLICK_TO_COPY: Final[str] = "click_to_copy"
    LOW_CONFIDENCE: Final[str] = "low_confidence"
    COULD_NOT_UNDERSTAND: Final[str] = "could_not_understand"
    NO_RESULTS: Final[str] = "no_results"

    INPUT_MODEL_COLOR: Final[str] = "input_model_color"
    INPUT_MODEL: Final[str] = "input_model"
    ENTER_CODE_PLACEHOLDER: Final[str] = "enter_code_placeholder"
    NOT_FOUND_IN_SALES: Final[str] = "not_found_in_sales"
    NO_DATA_FOR_SUMMARY: Final[str] = "no_data_for_summary"
    TYPE_TO_FILTER: Final[str] = "type_to_filter"
    ITEMS_AVAILABLE_SHORT: Final[str] = "items_available_short"
    ERR_SALES_ANALYSIS: Final[str] = "err_sales_analysis"
    ERR_WEEKLY_ANALYSIS: Final[str] = "err_weekly_analysis"
    ERR_TOP_SALES_REPORT: Final[str] = "err_top_sales_report"
    ERR_TOP_5_BY_TYPE: Final[str] = "err_top_5_by_type"
    ERR_GENERATING_WEEKLY: Final[str] = "err_generating_weekly"
    WEEKLY_SALES_BY_MODEL: Final[str] = "weekly_sales_by_model"
    GENERATING_WEEKLY: Final[str] = "generating_weekly"
    ERR_MONTHLY_ANALYSIS: Final[str] = "err_monthly_analysis"
    BTN_GENERATE_MONTHLY_YOY: Final[str] = "btn_generate_monthly_yoy"
    CALCULATING_YOY: Final[str] = "calculating_yoy"
    ANALYSIS_SUCCESS: Final[str] = "analysis_success"
    ANALYSIS_FAILED: Final[str] = "analysis_failed"
    PRIOR_PERIOD: Final[str] = "prior_period"
    UNKNOWN: Final[str] = "unknown"
    NEW: Final[str] = "new"
    AGE_GROUP: Final[str] = "age_group"
    CATEGORY: Final[str] = "category"
    ERR_ORDER_RECOMMENDATIONS: Final[str] = "err_order_recommendations"
    ORDER_RECOMMENDATIONS_DESC: Final[str] = "order_recommendations_desc"
    RECOMMENDATION_PARAMS_HELP: Final[str] = "recommendation_params_help"
    CURRENT_WEIGHTS_SUM: Final[str] = "current_weights_sum"
    MODEL_METADATA_NOT_AVAILABLE: Final[str] = "model_metadata_not_available"
    NO_ML_FORECASTS: Final[str] = "no_ml_forecasts"
    CALCULATING_PRIORITIES: Final[str] = "calculating_priorities"
    ANALYZED_N_SKUS: Final[str] = "analyzed_n_skus"
    ERR_GENERATING_RECOMMENDATIONS: Final[str] = "err_generating_recommendations"
    ITEMS_SELECTED: Final[str] = "items_selected"
    NAVIGATE_ORDER_CREATION: Final[str] = "navigate_order_creation"
    SELECT_ITEMS_TO_ORDER: Final[str] = "select_items_to_order"
    FULL_MODEL_COLOR_SUMMARY: Final[str] = "full_model_color_summary"
    DOWNLOAD_PRIORITY_REPORT: Final[str] = "download_priority_report"
    NO_DATA: Final[str] = "no_data"
    HELP_WEIGHT_STOCKOUT: Final[str] = "help_weight_stockout"
    HELP_WEIGHT_REVENUE: Final[str] = "help_weight_revenue"
    HELP_WEIGHT_DEMAND: Final[str] = "help_weight_demand"
    HELP_MULT_NEW: Final[str] = "help_mult_new"
    HELP_MULT_SEASONAL: Final[str] = "help_mult_seasonal"
    HELP_MULT_REGULAR: Final[str] = "help_mult_regular"
    HELP_MULT_BASIC: Final[str] = "help_mult_basic"
    HELP_ZERO_PENALTY: Final[str] = "help_zero_penalty"
    HELP_BELOW_ROP_PENALTY: Final[str] = "help_below_rop_penalty"
    HELP_DEMAND_CAP: Final[str] = "help_demand_cap"
    HELP_INCLUDE_FACILITIES: Final[str] = "help_include_facilities"
    HELP_EXCLUDE_FACILITIES: Final[str] = "help_exclude_facilities"
    HELP_FORECAST_SOURCE: Final[str] = "help_forecast_source"
    HELP_SELECT_ITEMS: Final[str] = "help_select_items"
    NEW_PRODUCTS: Final[str] = "new_products"
    STOCKOUT_RISK: Final[str] = "stockout_risk"
    REVENUE_IMPACT: Final[str] = "revenue_impact"
    DEMAND_FORECAST: Final[str] = "demand_forecast"
    ZERO_STOCK_PENALTY: Final[str] = "zero_stock_penalty"
    BELOW_ROP_PENALTY: Final[str] = "below_rop_penalty"
    DEMAND_CAP: Final[str] = "demand_cap"
    TOP_PRIORITY_TO_ORDER: Final[str] = "top_priority_to_order"
    SHOWING_TOP_MODEL_COLOR: Final[str] = "showing_top_model_color"
    SELECT: Final[str] = "select"
    LOAD_STOCK_AND_FORECAST: Final[str] = "load_stock_and_forecast"

    TITLE_MANUAL_ORDER_CREATION: Final[str] = "title_manual_order_creation"
    TITLE_SIZE_DISTRIBUTION: Final[str] = "title_size_distribution"
    TITLE_SIZE_COLOR_TABLE: Final[str] = "title_size_color_table"
    TITLE_ZERO_STOCK_PRODUCTION: Final[str] = "title_zero_stock_production"
    COLOR_FILTER_ALL: Final[str] = "color_filter_all"
    COLOR_FILTER_MODEL: Final[str] = "color_filter_model"
    COLOR_FILTER_ACTIVE: Final[str] = "color_filter_active"
    TITLE_FACILITY_CAPACITY: Final[str] = "title_facility_capacity"
    TITLE_EDIT_CAPACITY: Final[str] = "title_edit_capacity"

    ENTER_MODEL_CODE_HELP: Final[str] = "enter_model_code_help"
    ENTER_MODEL_PLACEHOLDER: Final[str] = "enter_model_placeholder"
    LOADING_DATA_FOR_MODEL: Final[str] = "loading_data_for_model"
    ORDER_FOR_MODEL: Final[str] = "order_for_model"
    NO_RECOMMENDATIONS_DATA: Final[str] = "no_recommendations_data"
    SELECT_MODEL_TO_PROCESS: Final[str] = "select_model_to_process"
    SELECT_MODEL_LABEL: Final[str] = "select_model_label"

    LABEL_PRIMARY_FACILITY: Final[str] = "label_primary_facility"
    LABEL_SECONDARY_FACILITY: Final[str] = "label_secondary_facility"
    LABEL_MATERIAL_TYPE: Final[str] = "label_material_type"
    LABEL_MATERIAL_WEIGHT: Final[str] = "label_material_weight"
    LABEL_MODEL_CODE: Final[str] = "label_model_code"
    LABEL_PRODUCT_NAME: Final[str] = "label_product_name"
    LABEL_PARSING_PDF: Final[str] = "label_parsing_pdf"
    LABEL_CAPACITY: Final[str] = "label_capacity"
    LABEL_ORDERS: Final[str] = "label_orders"
    LABEL_TOTAL_QTY: Final[str] = "label_total_qty"
    LABEL_UTILIZATION: Final[str] = "label_utilization"

    PLACEHOLDER_MODEL_CODE: Final[str] = "placeholder_model_code"
    PLACEHOLDER_PRODUCT_NAME: Final[str] = "placeholder_product_name"
    PLACEHOLDER_FACILITY: Final[str] = "placeholder_facility"
    PLACEHOLDER_OPERATION: Final[str] = "placeholder_operation"
    PLACEHOLDER_MATERIAL: Final[str] = "placeholder_material"

    HELP_ORDER_DATE: Final[str] = "help_order_date"
    HELP_UPLOAD_PDF: Final[str] = "help_upload_pdf"
    HELP_ARCHIVE_CHECKBOX: Final[str] = "help_archive_checkbox"
    HELP_CAPACITY_EDITOR: Final[str] = "help_capacity_editor"

    BTN_CREATE_FROM_PDF: Final[str] = "btn_create_from_pdf"
    BTN_DOWNLOAD_ORDER_CSV: Final[str] = "btn_download_order_csv"
    BTN_COPY_TABLE: Final[str] = "btn_copy_table"
    BTN_SAVE_CAPACITY: Final[str] = "btn_save_capacity"
    BTN_ARCHIVE_N_ORDERS: Final[str] = "btn_archive_n_orders"

    MSG_ORDER_SAVED: Final[str] = "msg_order_saved"
    MSG_ORDER_SAVE_FAILED: Final[str] = "msg_order_save_failed"
    MSG_CAPACITY_SAVED: Final[str] = "msg_capacity_saved"
    MSG_NO_FACILITY_DATA: Final[str] = "msg_no_facility_data"
    MSG_NO_CAPACITY_DATA: Final[str] = "msg_no_capacity_data"
    MSG_COULD_NOT_LOAD_SALES: Final[str] = "msg_could_not_load_sales"
    MSG_ENTER_MODEL_CODE: Final[str] = "msg_enter_model_code"

    ERR_ORDER_CREATION: Final[str] = "err_order_creation"
    ERR_ORDER_TRACKING: Final[str] = "err_order_tracking"
    ERR_SAVING_ORDER: Final[str] = "err_saving_order"

    CAPTION_SIZE_DISTRIBUTION: Final[str] = "caption_size_distribution"
    CAPTION_TOTAL_QTY_FACILITIES: Final[str] = "caption_total_qty_facilities"

    NA: Final[str] = "na"
    PRODUCED_SIZE_QTY: Final[str] = "produced_size_qty"

    TITLE_SIZE_PATTERN_OPTIMIZER: Final[str] = "title_size_pattern_optimizer"
    LOADED_SALES_HISTORY: Final[str] = "loaded_sales_history"
    NO_SALES_DATA_FOR_MODEL: Final[str] = "no_sales_data_for_model"
    SIZES: Final[str] = "sizes"
    PATTERNS: Final[str] = "patterns"
    CREATE_EDIT_PATTERN_SET: Final[str] = "create_edit_pattern_set"
    USING_ALGORITHM: Final[str] = "using_algorithm"
    ERR_NO_PATTERN_SETS: Final[str] = "err_no_pattern_sets"
    ERR_SELECT_PATTERN_SET: Final[str] = "err_select_pattern_set"
    ERR_ENTER_QUANTITIES: Final[str] = "err_enter_quantities"
    ERR_PATTERN_SET_NOT_FOUND: Final[str] = "err_pattern_set_not_found"
    NO_PATTERNS_ALLOCATED: Final[str] = "no_patterns_allocated"
    SIZE: Final[str] = "size"
    SALES: Final[str] = "sales"
    EXCLUDED: Final[str] = "excluded"
    ERR_PATTERN_OPTIMIZER: Final[str] = "err_pattern_optimizer"

    BTN_GENERATE_ACCURACY_REPORT: Final[str] = "btn_generate_accuracy_report"
    BTN_CLEAR_RESULTS: Final[str] = "btn_clear_results"
    ANALYSIS_PARAMETERS: Final[str] = "analysis_parameters"
    HELP_ANALYSIS_START: Final[str] = "help_analysis_start"
    HELP_ANALYSIS_END: Final[str] = "help_analysis_end"
    HELP_FORECAST_LOOKBACK: Final[str] = "help_forecast_lookback"
    ERR_ANALYSIS_PERIOD_TOO_SHORT: Final[str] = "err_analysis_period_too_short"
    INFO_ANALYSIS_PERIOD: Final[str] = "info_analysis_period"
    LOADING_ACCURACY_METRICS: Final[str] = "loading_accuracy_metrics"
    ERR_NO_SALES_FOR_PERIOD: Final[str] = "err_no_sales_for_period"
    ERR_NO_FORECAST_FOUND: Final[str] = "err_no_forecast_found"
    WARN_NO_STOCK_HISTORY: Final[str] = "warn_no_stock_history"
    ERR_ACCURACY_CALCULATION: Final[str] = "err_accuracy_calculation"
    MSG_ACCURACY_SUCCESS: Final[str] = "msg_accuracy_success"
    INFO_USING_FORECAST: Final[str] = "info_using_forecast"
    STOCKOUT_DAYS: Final[str] = "stockout_days"
    FCST_VS_ACT: Final[str] = "fcst_vs_act"
    ACCURACY_BY_ITEM: Final[str] = "accuracy_by_item"
    SEARCH_ENTITY: Final[str] = "search_entity"
    SEARCH_ENTITY_PLACEHOLDER: Final[str] = "search_entity_placeholder"
    SHOWING_N_OF_M_ITEMS: Final[str] = "showing_n_of_m_items"
    DOWNLOAD_ACCURACY_REPORT: Final[str] = "download_accuracy_report"
    ACCURACY_BY_PRODUCT_TYPE: Final[str] = "accuracy_by_product_type"
    MAPE_BY_PRODUCT_TYPE: Final[str] = "mape_by_product_type"
    ACCURACY_TREND_OVER_TIME: Final[str] = "accuracy_trend_over_time"
    CHART_WEEK: Final[str] = "chart_week"
    CHART_MAPE_PCT: Final[str] = "chart_mape_pct"
    ITEM_DETAIL_VIEW: Final[str] = "item_detail_view"
    SELECT_ENTITY_DETAILS: Final[str] = "select_entity_details"
    DAYS_ANALYZED: Final[str] = "days_analyzed"
    DAYS_STOCKOUT: Final[str] = "days_stockout"
    FORECAST_TOTAL: Final[str] = "forecast_total"
    ACTUAL_TOTAL: Final[str] = "actual_total"
    WARN_MISSED_OPPORTUNITY: Final[str] = "warn_missed_opportunity"
    ERR_FORECAST_ACCURACY: Final[str] = "err_forecast_accuracy"
    CAPTION_FORECAST_ACCURACY: Final[str] = "caption_forecast_accuracy"
    MSG_NO_SALES_DATA_LOAD: Final[str] = "msg_no_sales_data_load"

    FC_ERROR_IN_TAB: Final[str] = "fc_error_in_tab"
    FC_PARAMETERS: Final[str] = "fc_parameters"
    FC_MODEL_FASTER: Final[str] = "fc_model_faster"
    FC_SKU_SLOWER: Final[str] = "fc_sku_slower"
    FC_MOVING_AVG: Final[str] = "fc_moving_avg"
    FC_EXP_SMOOTHING: Final[str] = "fc_exp_smoothing"
    FC_HOLT_WINTERS: Final[str] = "fc_holt_winters"
    FC_SARIMA: Final[str] = "fc_sarima"
    FC_AUTO_ARIMA: Final[str] = "fc_auto_arima"
    FC_GENERATE_AS_OF_HELP: Final[str] = "fc_generate_as_of_help"
    FC_COMPARE_AS_OF_HELP: Final[str] = "fc_compare_as_of_help"
    FC_LOADING_DATA: Final[str] = "fc_loading_data"
    FC_LOADING_MONTHLY_AGG: Final[str] = "fc_loading_monthly_agg"
    FC_NO_MONTHLY_AGG: Final[str] = "fc_no_monthly_agg"
    FC_NO_DATA_BEFORE_DATE: Final[str] = "fc_no_data_before_date"
    FC_LOADING_FORECASTS: Final[str] = "fc_loading_forecasts"
    FC_NO_EXTERNAL_FORECAST: Final[str] = "fc_no_external_forecast"
    FC_LOADING_SALES: Final[str] = "fc_loading_sales"
    FC_NO_SALES_FOR_COMPARISON: Final[str] = "fc_no_sales_for_comparison"
    FC_PREPARING_ENTITIES: Final[str] = "fc_preparing_entities"
    FC_NO_ENTITIES_FOUND: Final[str] = "fc_no_entities_found"
    FC_PROCESSING_ENTITIES: Final[str] = "fc_processing_entities"
    FC_GENERATING_FORECASTS: Final[str] = "fc_generating_forecasts"
    FC_FORECASTING_PROGRESS: Final[str] = "fc_forecasting_progress"
    FC_CALCULATING_METRICS: Final[str] = "fc_calculating_metrics"
    FC_DONE: Final[str] = "fc_done"
    FC_NO_INTERNAL_FORECASTS: Final[str] = "fc_no_internal_forecasts"
    FC_COMPARISON_COMPLETE: Final[str] = "fc_comparison_complete"
    FC_ENTITIES_FAILED: Final[str] = "fc_entities_failed"
    FC_ERROR: Final[str] = "fc_error"
    FC_FORECAST_INFO: Final[str] = "fc_forecast_info"
    FC_FORECAST_PERIOD: Final[str] = "fc_forecast_period"
    FC_OVERALL_SUMMARY: Final[str] = "fc_overall_summary"
    FC_INTERNAL_MAPE: Final[str] = "fc_internal_mape"
    FC_EXTERNAL_MAPE: Final[str] = "fc_external_mape"
    FC_MORE_ACCURATE: Final[str] = "fc_more_accurate"
    FC_INTERNAL_WINS: Final[str] = "fc_internal_wins"
    FC_EXTERNAL_WINS: Final[str] = "fc_external_wins"
    FC_TIE: Final[str] = "fc_tie"
    FC_AVG_IMPROVEMENT: Final[str] = "fc_avg_improvement"
    FC_METHODS_USED: Final[str] = "fc_methods_used"
    FC_WINNER_BY_TYPE: Final[str] = "fc_winner_by_type"
    FC_NO_TYPE_BREAKDOWN: Final[str] = "fc_no_type_breakdown"
    FC_ALL_FORECAST_ITEMS: Final[str] = "fc_all_forecast_items"
    FC_NO_FORECAST_DATA: Final[str] = "fc_no_forecast_data"
    FC_VIEW_ALL_ITEMS: Final[str] = "fc_view_all_items"
    FC_SEARCH_ENTITY: Final[str] = "fc_search_entity"
    FC_ORDER: Final[str] = "fc_order"
    FC_TOTAL_ROWS: Final[str] = "fc_total_rows"
    FC_DOWNLOAD_ALL_FORECASTS: Final[str] = "fc_download_all_forecasts"
    FC_DETAILED_COMPARISON: Final[str] = "fc_detailed_comparison"
    FC_NO_COMPARISON_DATA: Final[str] = "fc_no_comparison_data"
    FC_IMPROVEMENT: Final[str] = "fc_improvement"
    FC_DOWNLOAD_FULL_REPORT: Final[str] = "fc_download_full_report"
    FC_ENTITY_DETAIL_CHART: Final[str] = "fc_entity_detail_chart"
    FC_NO_DATA_FOR_CHART: Final[str] = "fc_no_data_for_chart"
    FC_SELECT_ENTITY: Final[str] = "fc_select_entity"
    FC_CHART_ACTUAL: Final[str] = "fc_chart_actual"
    FC_CHART_INTERNAL: Final[str] = "fc_chart_internal"
    FC_CHART_EXTERNAL: Final[str] = "fc_chart_external"
    FC_CHART_TITLE: Final[str] = "fc_chart_title"
    FC_CHART_MONTH: Final[str] = "fc_chart_month"
    FC_SAVE_FORECAST: Final[str] = "fc_save_forecast"
    FC_NO_FORECAST_TO_SAVE: Final[str] = "fc_no_forecast_to_save"
    FC_NOTES_OPTIONAL: Final[str] = "fc_notes_optional"
    FC_NOTES_PLACEHOLDER: Final[str] = "fc_notes_placeholder"
    FC_SAVE_TO_HISTORY: Final[str] = "fc_save_to_history"
    FC_FORECAST_SAVED: Final[str] = "fc_forecast_saved"
    FC_ERROR_SAVING: Final[str] = "fc_error_saving"
    FC_HISTORICAL_INTERNAL: Final[str] = "fc_historical_internal"
    FC_NO_HISTORICAL: Final[str] = "fc_no_historical"
    FC_SELECT_HISTORICAL: Final[str] = "fc_select_historical"
    FC_ENTITY_TYPE: Final[str] = "fc_entity_type"
    FC_HORIZON: Final[str] = "fc_horizon"
    FC_SUCCESS: Final[str] = "fc_success"
    FC_FAILED: Final[str] = "fc_failed"
    FC_METHODS: Final[str] = "fc_methods"
    FC_NOTES: Final[str] = "fc_notes"
    FC_ANALYSIS_SETTINGS: Final[str] = "fc_analysis_settings"
    FC_FORECAST_COVERS: Final[str] = "fc_forecast_covers"
    FC_ANALYZE_AS_OF: Final[str] = "fc_analyze_as_of"
    FC_ANALYZE_AS_OF_HELP: Final[str] = "fc_analyze_as_of_help"
    FC_SET_AS_OF_INFO: Final[str] = "fc_set_as_of_info"
    FC_LOAD_COMPARE: Final[str] = "fc_load_compare"
    FC_DELETE: Final[str] = "fc_delete"
    FC_FORECAST_DELETED: Final[str] = "fc_forecast_deleted"
    FC_DELETE_FAILED: Final[str] = "fc_delete_failed"
    FC_FAILED_LOAD: Final[str] = "fc_failed_load"
    FC_NO_SALES_FOR_PERIOD: Final[str] = "fc_no_sales_for_period"
    FC_HISTORICAL_LOADED: Final[str] = "fc_historical_loaded"
    FC_ASCENDING: Final[str] = "fc_ascending"
    FC_DESCENDING: Final[str] = "fc_descending"
    FC_COL_ENTITY: Final[str] = "fc_col_entity"
    FC_COL_PERIOD: Final[str] = "fc_col_period"
    FC_COL_INTERNAL_FORECAST: Final[str] = "fc_col_internal_forecast"
    FC_COL_EXTERNAL_FORECAST: Final[str] = "fc_col_external_forecast"
    FC_COL_ACTUAL_SALES: Final[str] = "fc_col_actual_sales"
    FC_COL_METHOD: Final[str] = "fc_col_method"
    FC_COL_MONTHS: Final[str] = "fc_col_months"
    FC_COL_ACTUAL_VOLUME: Final[str] = "fc_col_actual_volume"
    FC_COL_INT_MAPE: Final[str] = "fc_col_int_mape"
    FC_COL_EXT_MAPE: Final[str] = "fc_col_ext_mape"
    FC_COL_WINNER: Final[str] = "fc_col_winner"
    FC_COL_TYPE: Final[str] = "fc_col_type"
    FC_COL_TOTAL: Final[str] = "fc_col_total"
    FC_COL_INTERNAL_WINS: Final[str] = "fc_col_internal_wins"
    FC_COL_EXTERNAL_WINS: Final[str] = "fc_col_external_wins"
    FC_COL_TIES: Final[str] = "fc_col_ties"
    FC_COL_INTERNAL_WIN_PCT: Final[str] = "fc_col_internal_win_pct"
    FC_COL_AVG_INT_MAPE: Final[str] = "fc_col_avg_int_mape"
    FC_COL_AVG_EXT_MAPE: Final[str] = "fc_col_avg_ext_mape"
    FC_CLEAR_RESULTS: Final[str] = "fc_clear_results"

    ML_ERROR_IN_TAB: Final[str] = "ml_error_in_tab"
    ML_TRAIN_DESCRIPTION: Final[str] = "ml_train_description"
    ML_TAB_TRAIN: Final[str] = "ml_tab_train"
    ML_TAB_GENERATE: Final[str] = "ml_tab_generate"
    ML_TAB_MANAGE: Final[str] = "ml_tab_manage"
    ML_LOADING_DATA: Final[str] = "ml_loading_data"
    ML_LOADING_MONTHLY_AGG: Final[str] = "ml_loading_monthly_agg"
    ML_NO_MONTHLY_AGG: Final[str] = "ml_no_monthly_agg"
    ML_LOADING_SKU_STATS: Final[str] = "ml_loading_sku_stats"
    ML_PREPARING_ENTITIES: Final[str] = "ml_preparing_entities"
    ML_NO_ENTITIES_FOUND: Final[str] = "ml_no_entities_found"
    ML_TRAINING_FOR_ENTITIES: Final[str] = "ml_training_for_entities"
    ML_TRAINING_PROGRESS: Final[str] = "ml_training_progress"
    ML_TRAINING_MODELS: Final[str] = "ml_training_models"
    ML_SAVING_MODELS: Final[str] = "ml_saving_models"
    ML_TRAINING_ERROR: Final[str] = "ml_training_error"
    ML_TRAINING_RESULTS: Final[str] = "ml_training_results"
    ML_TOTAL_ENTITIES: Final[str] = "ml_total_entities"
    ML_AVG_CV_SCORE: Final[str] = "ml_avg_cv_score"
    ML_MODEL_DISTRIBUTION: Final[str] = "ml_model_distribution"
    ML_BEST_MODEL_SELECTION: Final[str] = "ml_best_model_selection"
    ML_FORECAST_PREVIEW: Final[str] = "ml_forecast_preview"
    ML_COL_ENTITY: Final[str] = "ml_col_entity"
    ML_COL_MODEL: Final[str] = "ml_col_model"
    ML_COL_CV_SCORE: Final[str] = "ml_col_cv_score"
    ML_COL_TOTAL_FORECAST: Final[str] = "ml_col_total_forecast"
    ML_DOWNLOAD_FORECASTS: Final[str] = "ml_download_forecasts"
    ML_GENERATE_FROM_SAVED: Final[str] = "ml_generate_from_saved"
    ML_NO_TRAINED_MODELS: Final[str] = "ml_no_trained_models"
    ML_MODELS_AVAILABLE: Final[str] = "ml_models_available"
    ML_ENTITY_FILTER: Final[str] = "ml_entity_filter"
    ML_GENERATING_FORECASTS: Final[str] = "ml_generating_forecasts"
    ML_NO_MODELS_MATCHING: Final[str] = "ml_no_models_matching"
    ML_COULD_NOT_LOAD_AGG: Final[str] = "ml_could_not_load_agg"
    ML_GENERATING_PROGRESS: Final[str] = "ml_generating_progress"
    ML_GENERATED_FORECASTS: Final[str] = "ml_generated_forecasts"
    ML_NO_FORECASTS_GENERATED: Final[str] = "ml_no_forecasts_generated"
    ML_MANAGE_TITLE: Final[str] = "ml_manage_title"
    ML_NO_MODELS_FOUND: Final[str] = "ml_no_models_found"
    ML_TOTAL_MODELS: Final[str] = "ml_total_models"
    ML_MOST_COMMON_MODEL: Final[str] = "ml_most_common_model"
    ML_SEARCH_ENTITY: Final[str] = "ml_search_entity"
    ML_FILTER_BY_TYPE: Final[str] = "ml_filter_by_type"
    ML_ALL: Final[str] = "ml_all"
    ML_SHOWING_MODELS: Final[str] = "ml_showing_models"
    ML_COL_TYPE: Final[str] = "ml_col_type"
    ML_COL_TRAINED: Final[str] = "ml_col_trained"
    ML_MODEL_DETAILS: Final[str] = "ml_model_details"
    ML_NO_MODELS_TO_DISPLAY: Final[str] = "ml_no_models_to_display"
    ML_SELECT_FOR_DETAILS: Final[str] = "ml_select_for_details"
    ML_MODEL_TYPE: Final[str] = "ml_model_type"
    ML_TRAINED_AT: Final[str] = "ml_trained_at"
    ML_CV_METRIC: Final[str] = "ml_cv_metric"
    ML_PRODUCT_TYPE: Final[str] = "ml_product_type"
    ML_FEATURE_IMPORTANCE: Final[str] = "ml_feature_importance"
    ML_TOP_FEATURES: Final[str] = "ml_top_features"
    ML_DELETE_MODEL_FOR: Final[str] = "ml_delete_model_for"
    ML_MODEL_DELETED: Final[str] = "ml_model_deleted"
    ML_DELETE_FAILED: Final[str] = "ml_delete_failed"
    ML_BULK_ACTIONS: Final[str] = "ml_bulk_actions"
    ML_DELETE_ALL_MODELS: Final[str] = "ml_delete_all_models"
    ML_DELETED_MODELS: Final[str] = "ml_deleted_models"
    ML_EXPORT_MODEL_REPORT: Final[str] = "ml_export_model_report"
    ML_DOWNLOAD_REPORT: Final[str] = "ml_download_report"
    ML_MODEL_DETAILED: Final[str] = "ml_model_detailed"
    ML_SKU_DETAILED: Final[str] = "ml_sku_detailed"
    ML_ENTITIES_FAILED: Final[str] = "ml_entities_failed"
    ML_SELECT_ENTITY_DETAILS: Final[str] = "ml_select_entity_details"
    ML_ENTITY: Final[str] = "ml_entity"
    ML_CV_SCORE: Final[str] = "ml_cv_score"

    NLQ_QUERY: Final[str] = "nlq_query"
    NLQ_PROCESSING: Final[str] = "nlq_processing"
    NLQ_CONFIDENCE: Final[str] = "nlq_confidence"
    NLQ_INTERPRETATION: Final[str] = "nlq_interpretation"
    NLQ_GENERATED_SQL: Final[str] = "nlq_generated_sql"
    NLQ_DOWNLOAD_RESULTS: Final[str] = "nlq_download_results"
    NLQ_TITLE: Final[str] = "nlq_title"
    NLQ_CAPTION: Final[str] = "nlq_caption"
    NLQ_DATABASE_MODE: Final[str] = "nlq_database_mode"
    NLQ_FILE_MODE: Final[str] = "nlq_file_mode"
    NLQ_ENTER_QUERY: Final[str] = "nlq_enter_query"
    NLQ_PLACEHOLDER: Final[str] = "nlq_placeholder"
    NLQ_EXECUTE: Final[str] = "nlq_execute"
    NLQ_CLEAR: Final[str] = "nlq_clear"
    NLQ_COULD_NOT_UNDERSTAND: Final[str] = "nlq_could_not_understand"
    NLQ_INTERPRETATION_SQL: Final[str] = "nlq_interpretation_sql"
    NLQ_LOW_CONFIDENCE: Final[str] = "nlq_low_confidence"
    NLQ_NO_RESULTS: Final[str] = "nlq_no_results"
    NLQ_RESULTS: Final[str] = "nlq_results"
    NLQ_ROWS: Final[str] = "nlq_rows"
    NLQ_COLUMNS: Final[str] = "nlq_columns"
    NLQ_EXAMPLE_QUERIES: Final[str] = "nlq_example_queries"
    NLQ_CLICK_EXAMPLE: Final[str] = "nlq_click_example"
    NLQ_ERROR_IN_TAB: Final[str] = "nlq_error_in_tab"

    DISPLAY_LAST_YEAR: Final[str] = "display_last_year"
    DISPLAY_CHANGE: Final[str] = "display_change"
    DISPLAY_TOTAL_PATTERNS: Final[str] = "display_total_patterns"
    DISPLAY_TOTAL_EXCESS: Final[str] = "display_total_excess"
    DISPLAY_COVERAGE: Final[str] = "display_coverage"
    DISPLAY_DOWNLOAD_CSV: Final[str] = "display_download_csv"
    DISPLAY_MODEL: Final[str] = "display_model"

    TASK_ADD_NEW: Final[str] = "task_add_new"
    TASK_TITLE: Final[str] = "task_title"
    TASK_TITLE_PLACEHOLDER: Final[str] = "task_title_placeholder"
    TASK_DESCRIPTION: Final[str] = "task_description"
    TASK_DESCRIPTION_PLACEHOLDER: Final[str] = "task_description_placeholder"
    TASK_DESCRIPTION_HELP: Final[str] = "task_description_help"
    TASK_DUE_DATE: Final[str] = "task_due_date"
    TASK_PRIORITY: Final[str] = "task_priority"
    TASK_PRIORITY_HIGH: Final[str] = "task_priority_high"
    TASK_PRIORITY_MEDIUM: Final[str] = "task_priority_medium"
    TASK_PRIORITY_LOW: Final[str] = "task_priority_low"
    TASK_STATUS_TODO: Final[str] = "task_status_todo"
    TASK_STATUS_IN_PROGRESS: Final[str] = "task_status_in_progress"
    TASK_STATUS_DONE: Final[str] = "task_status_done"
    TASK_ADD_BTN: Final[str] = "task_add_btn"
    TASK_DELETE_BTN: Final[str] = "task_delete_btn"
    TASK_EDIT_BTN: Final[str] = "task_edit_btn"
    TASK_SAVE_BTN: Final[str] = "task_save_btn"
    TASK_LIST: Final[str] = "task_list"
    TASK_KANBAN: Final[str] = "task_kanban"
    TASK_FILTER_STATUS: Final[str] = "task_filter_status"
    TASK_FILTER_PRIORITY: Final[str] = "task_filter_priority"
    TASK_FILTER_ALL: Final[str] = "task_filter_all"
    TASK_NO_TASKS: Final[str] = "task_no_tasks"
    TASK_CREATED: Final[str] = "task_created"
    TASK_DUE: Final[str] = "task_due"
    ERR_TASK_PLANNER: Final[str] = "err_task_planner"
    ERR_TASK_TITLE_REQUIRED: Final[str] = "err_task_title_required"

    PROGRESS_LOADING_DATA: Final[str] = "progress_loading_data"
    PROGRESS_LOADING_SALES: Final[str] = "progress_loading_sales"
    PROGRESS_LOADING_STOCK: Final[str] = "progress_loading_stock"
    PROGRESS_LOADING_FORECAST: Final[str] = "progress_loading_forecast"
    PROGRESS_LOADING_METADATA: Final[str] = "progress_loading_metadata"
    PROGRESS_DONE: Final[str] = "progress_done"


_EN_LOADING_DATA = "Loading data..."
_PL_LOADING_DATA = "Wczytywanie danych..."
_PL_QUANTITY = "Ilość"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        Keys.PAGE_TITLE: "Inventory & Pattern Optimizer",

        Keys.TAB_TASK_PLANNER: "📝 Task Planner",
        Keys.TAB_SALES_ANALYSIS: "📊 Sales & Inventory Analysis",
        Keys.TAB_PATTERN_OPTIMIZER: "✂️ Size Pattern Optimizer",
        Keys.TAB_WEEKLY_ANALYSIS: "📋 Weekly Analysis",
        Keys.TAB_MONTHLY_ANALYSIS: "📆 Monthly Analysis",
        Keys.TAB_ORDER_RECOMMENDATIONS: "🎯 Order Recommendations",
        Keys.TAB_ORDER_CREATION: "🛒 Order Creation",
        Keys.TAB_ORDER_TRACKING: "🚚 Order Tracking",
        Keys.TAB_FORECAST_ACCURACY: "📈 Forecast Accuracy",
        Keys.TAB_FORECAST_COMPARISON: "🔬 Forecast Comparison",
        Keys.TAB_ML_FORECAST: "🤖 ML Forecast",
        Keys.TAB_NL_QUERY: "🔍 NL Query",

        Keys.SIDEBAR_PARAMETERS: "Parameters",
        Keys.SIDEBAR_LEAD_TIME_FORECAST: "Lead Time & Forecast",
        Keys.SIDEBAR_SERVICE_LEVELS: "Service Levels",
        Keys.SIDEBAR_PATTERN_OPTIMIZER: "Pattern Optimizer",
        Keys.SIDEBAR_CURRENT_PARAMS: "Current Parameters:",
        Keys.SIDEBAR_VIEW_OPTIONS: "View Options",
        Keys.SIDEBAR_LOAD_DATA: "Load additional data",

        Keys.BTN_SAVE: "💾 Save",
        Keys.BTN_RESET: "🔄 Reset",
        Keys.BTN_CANCEL: "Cancel",
        Keys.BTN_CLEAR: "Clear",
        Keys.BTN_DOWNLOAD_CSV: "Download CSV",
        Keys.BTN_GENERATE: "Generate",
        Keys.BTN_REFRESH: "Refresh",
        Keys.BTN_CREATE_ORDER: "Create Order",
        Keys.BTN_SAVE_TO_DB: "💾 Save to Database",
        Keys.BTN_RUN_OPTIMIZATION: "Run Optimization",
        Keys.BTN_NEW_SET: "New Set",
        Keys.BTN_EDIT_SET: "Edit Set",
        Keys.BTN_DELETE_SET: "Delete Set",
        Keys.BTN_SAVE_ALL: "Save All",
        Keys.BTN_RELOAD: "Reload",
        Keys.BTN_SAVE_PATTERN_SET: "Save Pattern Set",
        Keys.BTN_LOAD_SALES_HISTORY: "Load Sales History",
        Keys.BTN_EXECUTE: "Execute",
        Keys.BTN_ADD_ORDER: "Add Order",
        Keys.BTN_ARCHIVE: "Archive",
        Keys.BTN_PARSE_PDF: "Parse PDF",
        Keys.BTN_GENERATE_RECOMMENDATIONS: "Generate Recommendations",
        Keys.BTN_GENERATE_COMPARISON: "Generate Comparison",
        Keys.BTN_GENERATE_FORECASTS: "Generate Forecasts",

        Keys.LEAD_TIME_MONTHS: "Lead time in months",
        Keys.LEAD_TIME_HELP: "Time between order placement and receipt (used in ROP and SS calculations)",
        Keys.SYNC_FORECAST: "Sync forecast time with lead time",
        Keys.SYNC_FORECAST_HELP: "When enabled, forecast time automatically matches lead time",
        Keys.FORECAST_TIME_MONTHS: "Forecast time in months",
        Keys.FORECAST_TIME_HELP: "Time period for forecast calculations (independent of lead time when sync is off)",

        Keys.TYPE_BASIC: "Basic",
        Keys.TYPE_REGULAR: "Regular",
        Keys.TYPE_SEASONAL: "Seasonal",
        Keys.TYPE_NEW: "New",

        Keys.COL_TYPE: "Type",
        Keys.COL_CV: "CV",
        Keys.COL_ZSCORE: "Z-Score",
        Keys.COL_ALGORITHM: "Algorithm",

        Keys.ALG_GREEDY_OVERSHOOT: "Greedy Overshoot",
        Keys.ALG_CLASSIC_GREEDY: "Classic Greedy",
        Keys.ALG_HELP: "Greedy Overshoot: Better coverage with slightly higher excess. Classic Greedy: Minimal excess but may undercover.",

        Keys.GROUP_BY_MODEL: "Group by Model (first 5 chars)",
        Keys.LOAD_STOCK_DATA: "Load stock data from data directory",
        Keys.LOAD_FORECAST_DATA: "Load forecast data from data directory",

        Keys.MSG_SAVED: "Saved!",
        Keys.MSG_SAVE_FAILED: "Save failed",
        Keys.MSG_NO_STOCK_FILE: "No stock file found. Stock-related columns will not be available.",
        Keys.MSG_NO_FORECAST_FILE: "No forecast file found. Forecast columns will not be available.",
        Keys.MSG_ERROR_PROCESSING_FORECAST: "Error processing forecast data: {error}",
        Keys.MSG_NO_DATA_AVAILABLE: "No data available",
        Keys.MSG_NOT_FOUND: "'{id}' not found",
        Keys.MSG_LOAD_BOTH_DATASETS: "No {entity_type} have both stock and forecast data available. Load both datasets to use this feature.",
        Keys.MSG_NO_FORECAST_DATA: "No forecast data available for this {entity} in the projection window.",

        Keys.TITLE_TASK_PLANNER: "📝 Task Planner",
        Keys.TITLE_SALES_DATA_ANALYSIS: "Sales Data Analysis",
        Keys.TITLE_STOCK_PROJECTION: "📈 Stock Projection Analysis",
        Keys.TITLE_YEARLY_SALES_TREND: "📊 Yearly Sales Trend",
        Keys.TITLE_STOCK_STATUS: "Stock Status",
        Keys.TITLE_ORDER_QUANTITIES: "Order Quantities",
        Keys.TITLE_SALES_HISTORY: "Sales History (last 4 months)",
        Keys.TITLE_PATTERN_SETS: "Pattern Sets",
        Keys.TITLE_OPTIMIZATION: "Optimization",
        Keys.TITLE_ORDER_SUMMARY: "Order Summary",
        Keys.TITLE_WEEKLY_ANALYSIS: "📅 Weekly Analysis",
        Keys.TITLE_MONTHLY_ANALYSIS: "📅 Monthly Year-over-Year Analysis by Category",
        Keys.TITLE_ORDER_RECOMMENDATIONS: "🎯 Order Recommendations",
        Keys.TITLE_ORDER_CREATION: "📋 Order Creation",
        Keys.TITLE_ORDER_TRACKING: "📦 Order Tracking",
        Keys.TITLE_FORECAST_ACCURACY: "Forecast Accuracy Monitoring",
        Keys.TITLE_FORECAST_COMPARISON: "Forecast Comparison",
        Keys.TITLE_ML_FORECAST: "ML Forecast",
        Keys.TITLE_NL_QUERY: "🔍 Natural Language Query",
        Keys.TITLE_TOP_SALES_REPORT: "⭐ Top Sales Report",
        Keys.TITLE_TOP_5_BY_TYPE: "🏆 Top 5 Products by Type",
        Keys.TITLE_NEW_PRODUCTS_MONITORING: "📊 New Products Launch Monitoring",
        Keys.TITLE_ACTIVE_ORDERS: "📋 Active Orders",
        Keys.TITLE_MANUAL_ORDER: "📝 Add Manual Order",
        Keys.TITLE_IMPORT_PDF: "📄 Import Order from PDF",
        Keys.TITLE_RECOMMENDATION_PARAMS: "⚙️ Recommendation Parameters",

        Keys.SEARCH_MODEL: "Search for Model:",
        Keys.SEARCH_SKU: "Search for SKU:",
        Keys.SEARCH_MODEL_PLACEHOLDER: "Enter Model or partial Model...",
        Keys.SEARCH_SKU_PLACEHOLDER: "Enter SKU or partial SKU...",
        Keys.SHOW_ONLY_BELOW_ROP: "Show only below ROP",
        Keys.BESTSELLERS: "Bestsellers (>300/mo)",
        Keys.FILTER_BY_TYPE: "Filter by Type:",
        Keys.OVERSTOCKED_FILTER: "**Overstocked Filter:**",
        Keys.SHOW_OVERSTOCKED: "Show overstocked items",
        Keys.OVERSTOCKED_BY_PCT: "Overstocked by %:",

        Keys.SHOWING_N_OF_M: "Showing {count} of {total} {items}",
        Keys.MODELS: "Model(s)",
        Keys.SKUS: "SKU(s)",

        Keys.METRIC_TOTAL_SKUS: "Total SKUs",
        Keys.METRIC_TOTAL_QUANTITY: "Total Quantity",
        Keys.METRIC_BELOW_ROP: "Below ROP",
        Keys.METRIC_TOTAL_DEFICIT: "Total Deficit (units)",
        Keys.METRIC_PCT_BELOW_ROP: "% Below ROP",
        Keys.METRIC_OVERSTOCKED: "Overstocked",
        Keys.METRIC_NORMAL: "Normal",
        Keys.METRIC_TOTAL_STOCK: "Total STOCK",
        Keys.METRIC_TOTAL_STOCK_VALUE: "Total Stock Value",
        Keys.METRIC_CURRENT_STOCK: "Current Stock",
        Keys.METRIC_ROP: "ROP",
        Keys.METRIC_SAFETY_STOCK: "Safety Stock",
        Keys.METRIC_AVG_MONTHLY_SALES: "Avg Monthly Sales",
        Keys.METRIC_FIRST_SALE_YEAR: "First Sale Year",
        Keys.METRIC_YEARS_ACTIVE: "Years Active",
        Keys.METRIC_TOTAL_HISTORICAL_SALES: "Total Historical Sales",
        Keys.METRIC_FORECAST_FUTURE: "Forecast (Future)",
        Keys.METRIC_LAST_WEEK: "Last Week",
        Keys.METRIC_SAME_WEEK_LAST_YEAR: "Same Week Last Year",
        Keys.METRIC_NEW_PRODUCTS: "New Products",
        Keys.METRIC_WEEKS_TRACKED: "Weeks Tracked",
        Keys.METRIC_TOTAL_SALES: "Total Sales",
        Keys.METRIC_CURRENT_PERIOD: "Current Period",
        Keys.METRIC_SAME_PERIOD_LAST_YEAR: "Same Period Last Year",
        Keys.METRIC_TOTAL_YOY_CHANGE: "Total YoY Change",
        Keys.METRIC_RISING_CATEGORIES: "Rising Categories",
        Keys.METRIC_FALLING_CATEGORIES: "Falling Categories",
        Keys.METRIC_UNCATEGORIZED: "Uncategorized",
        Keys.METRIC_MAPE: "MAPE",
        Keys.METRIC_BIAS: "BIAS",
        Keys.METRIC_MISSED_OPPORTUNITY: "Missed Opportunity",
        Keys.METRIC_VOLUME_ACCURACY: "Volume Accuracy",
        Keys.METRIC_ROWS: "Rows",
        Keys.METRIC_COLUMNS: "Columns",

        Keys.DOWNLOAD_MODEL_SUMMARY: "Download Model Summary CSV",
        Keys.DOWNLOAD_SKU_SUMMARY: "Download SKU Summary CSV",
        Keys.DOWNLOAD_WEEKLY_ANALYSIS: "📥 Download Weekly Analysis (CSV)",
        Keys.DOWNLOAD_PODGRUPA_SUMMARY: "📥 Download Podgrupa Summary (CSV)",
        Keys.DOWNLOAD_CATEGORY_DETAILS: "📥 Download Category Details (CSV)",
        Keys.DOWNLOAD_RESULTS: "📥 Download Results (CSV)",

        Keys.ENTER_MODEL_TO_ANALYZE: "Enter Model to analyze:",
        Keys.ENTER_SKU_TO_ANALYZE: "Enter SKU to analyze:",
        Keys.PROJECTION_MONTHS: "Projection months:",
        Keys.ITEMS_AVAILABLE: "📦 {count} {entity_type} available with complete data",

        Keys.CHART_PROJECTED_STOCK: "Projected Stock",
        Keys.CHART_ROP: "ROP ({value:.0f})",
        Keys.CHART_SAFETY_STOCK: "Safety Stock ({value:.0f})",
        Keys.CHART_ZERO_STOCK: "Zero Stock",
        Keys.CHART_ROP_REACHED: "ROP Reached",
        Keys.CHART_STOCKOUT: "Stockout!",
        Keys.CHART_HISTORICAL_SALES: "Historical Sales",
        Keys.CHART_FORECAST: "Forecast",
        Keys.CHART_DATE: "Date",
        Keys.CHART_QUANTITY: "Quantity",
        Keys.CHART_YEAR: "Year",
        Keys.CHART_QUANTITY_SOLD: "Quantity Sold",

        Keys.STOCK_PROJECTION_FOR: "Stock Projection for {entity} {id}",
        Keys.YEARLY_SALES_TREND_FOR: "Yearly Sales Trend: {entity} {id}",
        Keys.STOCK_STATUS_DISTRIBUTION: "Stock Status Distribution (Overstock threshold: {threshold}%)",

        Keys.WARN_ROP_IN_DAYS: "Stock will reach ROP in {days} days ({date})",
        Keys.ERR_STOCKOUT_IN_DAYS: "🚨 Stockout predicted in {days} days ({date})",

        Keys.GROUP_BY: "Group by:",
        Keys.GROUP_MODEL: "Model",
        Keys.GROUP_MODEL_COLOR: "Model + Color",

        Keys.SORT_BY: "Sort by:",
        Keys.FILTER_BY_CODE: "Filter by code:",
        Keys.ALL_ITEMS_SUMMARY: "📋 All Items Summary Table",
        Keys.YOY_TREND: "YoY Trend ({prev} → {curr}):",

        Keys.YEARLY_CAPTION: "Track product lifecycle: historical sales and forecast to identify candidates for discontinuation",
        Keys.WEEKLY_CAPTION: "Compare previous week's sales to same week last year (Monday-Sunday)",
        Keys.WEEKLY_TOP_SALES_CAPTION: "Best sellers from last week by product category",
        Keys.WEEKLY_NEW_PRODUCTS_CAPTION: "Track weekly sales for products launched in the last 2 months (Weeks aligned to calendar Wednesdays)",
        Keys.MONTHLY_CAPTION: "Compare monthly sales quantities from current year to previous year, organized by age group (Podgrupa) and clothing category (Kategoria). Automatically excludes the current incomplete month.",

        Keys.RISING_STAR: "🚀 RISING STAR",
        Keys.FALLING_STAR: "📉 FALLING STAR",
        Keys.NO_RISING_PRODUCTS: "No rising products found",
        Keys.NO_FALLING_PRODUCTS: "No falling products found",
        Keys.NO_PRODUCTS_FOUND: "No {type} products found",
        Keys.NO_NEW_PRODUCTS: "No new products found with first sale in the last {days} days",
        Keys.ZERO_SALES_WARNING: "⚠️ {count} product(s) with ZERO sales in tracked period",
        Keys.VIEW_ZERO_SALES: "View zero-sales products",

        Keys.SALES_BY_AGE_GROUP: "Sales by Age Group & Category",
        Keys.CLOTHING_CATEGORY: "Clothing Category",
        Keys.CURRENT_SALES: "Current Sales",
        Keys.PRIOR_YEAR_SALES: "Prior Year Sales",
        Keys.DIFFERENCE: "Difference",
        Keys.CHANGE_PCT: "Change %",
        Keys.NO_DATA_AGE_GROUP: "No data for this age group.",
        Keys.CATEGORY_MAPPINGS_ERROR: "Category mappings not available. Please ensure the Kategorie sheet exists in the data file or database table is populated.",
        Keys.NO_SALES_DATA: "No sales data loaded. Please ensure data is loaded in Tab 1.",
        Keys.CLICK_GENERATE: "Click 'Generate Monthly YoY Analysis' to start the analysis.",

        Keys.PRIORITY_WEIGHTS: "**Priority Weights** (contribution to final score)",
        Keys.TYPE_MULTIPLIERS: "**Type Multipliers** (priority boost by product type)",
        Keys.STOCKOUT_RISK_PARAMS: "**Stockout Risk & Other Parameters**",
        Keys.FILTER_BY_FACILITY: "**Filter by Production Facility**",
        Keys.PARAM_STOCKOUT_RISK: "Stockout Risk",
        Keys.PARAM_REVENUE_IMPACT: "Revenue Impact",
        Keys.PARAM_DEMAND_FORECAST: "Demand Forecast",
        Keys.PARAM_ZERO_STOCK_PENALTY: "Zero Stock Penalty",
        Keys.PARAM_BELOW_ROP_PENALTY: "Below ROP Max Penalty",
        Keys.PARAM_DEMAND_CAP: "Demand Cap",
        Keys.PARAM_TOP_PRIORITY: "Top priority items:",
        Keys.INCLUDE_FACILITIES: "Include Facilities:",
        Keys.EXCLUDE_FACILITIES: "Exclude Facilities:",
        Keys.FORECAST_SOURCE: "Forecast Source:",
        Keys.EXTERNAL: "External",
        Keys.TOP_PRIORITY_ITEMS: "Top Priority Items to Order",
        Keys.SHOWING_TOP_N: "Showing top {n} MODEL+COLOR combinations by priority",
        Keys.LOAD_STOCK_FORECAST: "Please load both stock and forecast data in Tab 1 to use this feature.",
        Keys.FILTERED_ACTIVE_ORDERS: "ℹ️ Filtered out {count} model(s) with active orders: {models}",

        Keys.PATTERN_SET_NAME: "Set Name",
        Keys.NUM_SIZE_CATEGORIES: "Number of size categories",
        Keys.DEFINE_SIZE_CATEGORIES: "Define size categories:",
        Keys.SIZE_N: "Size {n}",
        Keys.NUM_PATTERNS: "Number of patterns in this set",
        Keys.PATTERN_NAME: "Pattern Name",
        Keys.QUANTITIES_PER_SIZE: "Quantities per size",
        Keys.SELECT_ACTIVE_PATTERN_SET: "Select Active Pattern Set:",
        Keys.MIN_ORDER_PER_PATTERN: "Minimum order per pattern: {min} units",
        Keys.USING_SIZES_FROM: "Using sizes from: {name}",
        Keys.ENTER_SALES_PER_SIZE: "Enter total sales per size or load automatically. Sizes with < 3 sales will be excluded.",
        Keys.NO_PATTERN_SETS: "No pattern sets defined. Create a pattern set to get started!",
        Keys.PATTERN_SETS_SAVED: "Pattern sets saved!",
        Keys.ALL_REQUIREMENTS_MET: "All requirements covered and minimum orders met!",
        Keys.MIN_ORDER_VIOLATIONS: "Minimum order violations (need {min} per pattern): {violations}",
        Keys.SOME_NOT_COVERED: "Some requirements not covered",
        Keys.EXCLUDED_SIZES: "Excluded sizes (sales < 3 in last 4 months): {sizes}",
        Keys.COMPLETE_ALL_FIELDS: "Please complete all fields: set name, {num_sizes} size names, and {num_patterns} patterns!",
        Keys.PATTERN: "Pattern",
        Keys.COUNT: "Count",
        Keys.COMPOSITION: "Composition",
        Keys.STATUS: "Status",
        Keys.PATTERN_ALLOCATION: "Pattern Allocation",
        Keys.PRODUCTION_VS_REQUIRED: "Production vs Required",
        Keys.REQUIRED: "Required",
        Keys.PRODUCED: "Produced",
        Keys.EXCESS: "Excess",
        Keys.TOTAL: "TOTAL",

        Keys.ENTER_MODEL_CODE: "Enter Model Code",
        Keys.NO_ITEMS_SELECTED: "No items selected. Use the manual input above or go to Order Recommendations tab.",
        Keys.MULTIPLE_MODELS_SELECTED: "Selected items span {count} models. Please select one model to process.",
        Keys.MODEL_NOT_FOUND: "Model '{model}' not found in sales data.",
        Keys.NO_DATA_FOR_MODEL: "No data found for model '{model}'",
        Keys.NO_FORECAST_DEFICIT: "No items with positive forecast or deficit found for model '{model}'",
        Keys.PATTERN_SET_NOT_FOUND: "Pattern set '{model}' not found",
        Keys.CREATE_PATTERN_SET_HINT: "Please create a pattern set in the Pattern Optimizer tab with name matching the model code",
        Keys.FOUND_PATTERN_SET: "Found pattern set: {name}",
        Keys.CREATED_ORDER: "Created order for model {model} with {count} colors",
        Keys.URGENT_COLORS: "**Urgent colors:** {colors}",

        Keys.ORDER_ID: "Order ID",
        Keys.ORDER_DATE: "Order Date",
        Keys.MODEL: "Model",
        Keys.PRODUCT: "Product",
        Keys.QUANTITY: "Quantity",
        Keys.FACILITY: "Facility",
        Keys.OPERATION: "Operation",
        Keys.MATERIAL: "Material",
        Keys.DAYS_ELAPSED: "Days Elapsed",
        Keys.UPLOAD_PDF: "Upload order PDF file",
        Keys.FILE_UPLOADED: "File uploaded: {filename}",
        Keys.PDF_PARSED: "PDF parsed successfully",
        Keys.ORDER_CREATED_PDF: "Order {order_id} created from PDF",
        Keys.ORDER_ADDED: "Order {order_id} added to active orders",
        Keys.NO_ACTIVE_ORDERS: "No active orders. Create orders in Tab 5 or add manual orders above.",
        Keys.ORDER_ARCHIVED: "Archived order {order_id}",
        Keys.FAILED_PARSE_PDF: "Failed to parse PDF. Please check the file format.",
        Keys.FAILED_CREATE_ORDER: "Failed to create order",
        Keys.FAILED_ADD_ORDER: "Failed to add order",
        Keys.FAILED_ARCHIVE_ORDER: "Failed to archive order {order_id}",
        Keys.TOTAL_ACTIVE_ORDERS: "📦 Total active orders: {count}",
        Keys.ORDERS_READY: "🚚 Orders ready for delivery (should be in stock now) (>= {threshold} days): {count}",
        Keys.STATUS_READY: "🚚 Ready",
        Keys.STATUS_PENDING: "⏳ {days}d",
        Keys.ARCHIVE_ORDER: "Check to archive this order",

        Keys.ANALYSIS_START_DATE: "Analysis Start Date",
        Keys.ANALYSIS_END_DATE: "Analysis End Date",
        Keys.FORECAST_LOOKBACK: "Forecast Lookback (months)",
        Keys.VIEW_LEVEL: "View Level",
        Keys.SKU_LEVEL: "SKU Level",
        Keys.MODEL_LEVEL: "Model Level",
        Keys.OVERALL_ACCURACY_METRICS: "Overall Accuracy Metrics",
        Keys.MAPE_HELP: "Mean Absolute Percentage Error (lower is better)",
        Keys.BIAS_HELP: "Positive = over-forecasting, Negative = under-forecasting",
        Keys.MISSED_OPP_HELP: "Forecast quantity during stockout periods",
        Keys.VOLUME_ACC_HELP: "How close total forecast was to total actual",
        Keys.GOOD: "Good",
        Keys.ACCEPTABLE: "Acceptable",
        Keys.POOR: "Poor",
        Keys.OVER_FORECASTING: "Over-forecasting",
        Keys.UNDER_FORECASTING: "Under-forecasting",
        Keys.PRODUCT_TYPE_BREAKDOWN: "Product Type Breakdown",
        Keys.TREND_CHART: "Weekly MAPE Trend",

        Keys.COMPARE_FORECASTS: "Compare internal forecasts (generated using statsmodels) vs external forecasts",
        Keys.GENERATE_NEW: "Generate New",
        Keys.HISTORICAL_FORECASTS: "Historical Forecasts",
        Keys.FORECAST_HORIZON: "Forecast Horizon (months)",
        Keys.ANALYSIS_LEVEL: "Analysis Level",
        Keys.ENTITY_FILTER: "Entity Filter",
        Keys.FORECAST_METHOD: "Forecast Method",
        Keys.GENERATE_AS_OF: "Generate 'as of' date",
        Keys.COMPARE_AS_OF: "Compare 'as of' date",
        Keys.ALL_ENTITIES: "All entities",
        Keys.TOP_N_BY_VOLUME: "Top N by volume",
        Keys.BY_PRODUCT_TYPE: "By product type",
        Keys.AUTO_SELECT: "Auto (select by type)",
        Keys.NUMBER_TOP_ENTITIES: "Number of top entities",
        Keys.PRODUCT_TYPES: "Product Types",
        Keys.FILTER_BY_MODEL: "Filter by Model (optional)",
        Keys.FORECAST_METHOD_HELP: "Auto selects method based on product type. AutoARIMA automatically finds best ARIMA parameters.",
        Keys.DATE_CAPTION: "**Generation date**: Only sales up to this date are used to generate forecast. **Comparison date**: Actual sales from forecast period up to this date are loaded for accuracy comparison.",

        Keys.MANAGE_MODELS: "Manage Models",
        Keys.TRAINING_PARAMS: "Training Parameters",
        Keys.MODELS_TO_EVALUATE: "**Models to Evaluate**",
        Keys.ML_MODELS: "ML Models",
        Keys.STATISTICAL_MODELS: "Statistical Models",
        Keys.ENTITY_LEVEL: "Entity Level",
        Keys.TOP_N_ENTITIES: "Top N entities by volume",
        Keys.CV_METRIC: "CV Metric",
        Keys.CV_SPLITS: "CV Splits",
        Keys.CV_TEST_SIZE: "CV Test Size (months)",
        Keys.INCLUDE_STATISTICAL: "Include Statistical (Holt-Winters, SARIMA)",
        Keys.TRAINING_COMPLETE: "Training complete! {count} models trained, {saved} saved.",

        Keys.QUERY_DATA: "Query your data using natural language (English or Polish)",
        Keys.DB_MODE_INFO: "Database mode: queries executed via SQL on PostgreSQL",
        Keys.FILE_MODE_INFO: "File mode: queries executed via SQL on DuckDB",
        Keys.ENTER_QUERY: "Enter your query",
        Keys.RESULTS: "Results",
        Keys.QUERY_PLACEHOLDER: "e.g., sales of model CH086 last 2 years",
        Keys.QUERY_INTERPRETATION: "Query interpretation & SQL",
        Keys.EXAMPLE_QUERIES: "📚 Example queries",
        Keys.CLICK_TO_COPY: "Click on any example to copy it to your clipboard:",
        Keys.LOW_CONFIDENCE: "Low confidence - results may not match your intent",
        Keys.COULD_NOT_UNDERSTAND: "Could not understand the query. Please try rephrasing.",
        Keys.NO_RESULTS: "No results found",

        Keys.INPUT_MODEL_COLOR: "Model + Color (e.g. AB123RD):",
        Keys.INPUT_MODEL: "Model (e.g. AB123):",
        Keys.ENTER_CODE_PLACEHOLDER: "Enter code...",
        Keys.NOT_FOUND_IN_SALES: "'{id}' not found in sales data",
        Keys.NO_DATA_FOR_SUMMARY: "No data available for summary table",
        Keys.TYPE_TO_FILTER: "Type to filter...",
        Keys.ITEMS_AVAILABLE_SHORT: "📦 {count} items available",
        Keys.ERR_SALES_ANALYSIS: "Error in Sales Analysis: {error}",
        Keys.ERR_WEEKLY_ANALYSIS: "Error in Weekly Analysis: {error}",
        Keys.ERR_TOP_SALES_REPORT: "Error generating TOP SALES REPORT: {error}",
        Keys.ERR_TOP_5_BY_TYPE: "Error generating Top 5 by Type: {error}",
        Keys.ERR_GENERATING_WEEKLY: "Error generating weekly analysis: {error}",
        Keys.WEEKLY_SALES_BY_MODEL: "Weekly Sales by Model",
        Keys.GENERATING_WEEKLY: "Generating weekly analysis...",
        Keys.ERR_MONTHLY_ANALYSIS: "Error in Monthly Analysis: {error}",
        Keys.BTN_GENERATE_MONTHLY_YOY: "Generate Monthly YoY Analysis",
        Keys.CALCULATING_YOY: "Calculating year-over-year comparison...",
        Keys.ANALYSIS_SUCCESS: "Analysis generated successfully!",
        Keys.ANALYSIS_FAILED: "Analysis failed: {error}",
        Keys.PRIOR_PERIOD: "Prior Period",
        Keys.UNKNOWN: "Unknown",
        Keys.NEW: "New",
        Keys.AGE_GROUP: "Age Group",
        Keys.CATEGORY: "Category",
        Keys.ERR_ORDER_RECOMMENDATIONS: "Error in Order Recommendations: {error}",
        Keys.ORDER_RECOMMENDATIONS_DESC: "Automatically prioritize which models and colors to order based on stock levels, forecasts, and ROP thresholds.",
        Keys.RECOMMENDATION_PARAMS_HELP: "Adjust these parameters to tune the priority scoring algorithm",
        Keys.CURRENT_WEIGHTS_SUM: "Current weights sum: {sum:.2f} (ideally 1.0)",
        Keys.MODEL_METADATA_NOT_AVAILABLE: "Model metadata not available. Showing all items.",
        Keys.NO_ML_FORECASTS: "No ML forecasts available. Train models first in Tab 10.",
        Keys.CALCULATING_PRIORITIES: "Calculating order priorities...",
        Keys.ANALYZED_N_SKUS: "Analyzed {count} SKUs using {source} forecast - scroll down to view results",
        Keys.ERR_GENERATING_RECOMMENDATIONS: "Error generating recommendations: {error}",
        Keys.ITEMS_SELECTED: "{count} items selected",
        Keys.NAVIGATE_ORDER_CREATION: "Please navigate to the 'Order Creation' tab to complete the order",
        Keys.SELECT_ITEMS_TO_ORDER: "Select items above to create an order",
        Keys.FULL_MODEL_COLOR_SUMMARY: "Full Model+Color Priority Summary",
        Keys.DOWNLOAD_PRIORITY_REPORT: "📥 Download Full Priority Report (SKU level)",
        Keys.NO_DATA: "No data",
        Keys.HELP_WEIGHT_STOCKOUT: "Weight for stockout risk factor in priority calculation. Higher values prioritize items at risk of stockout.",
        Keys.HELP_WEIGHT_REVENUE: "Weight for revenue impact in priority calculation. Higher values prioritize high-revenue items.",
        Keys.HELP_WEIGHT_DEMAND: "Weight for demand forecast in priority calculation. Higher values prioritize items with high forecasted demand.",
        Keys.HELP_MULT_NEW: "Multiplier for new products (< 12 months). Values > 1.0 increase priority.",
        Keys.HELP_MULT_SEASONAL: "Multiplier for seasonal products (CV > 1.0).",
        Keys.HELP_MULT_REGULAR: "Multiplier for regular products (0.6 < CV < 1.0).",
        Keys.HELP_MULT_BASIC: "Multiplier for basic products (CV < 0.6).",
        Keys.HELP_ZERO_PENALTY: "Risk score for SKUs with zero stock AND forecasted demand.",
        Keys.HELP_BELOW_ROP_PENALTY: "Maximum risk score for items below Reorder Point (ROP).",
        Keys.HELP_DEMAND_CAP: "Maximum forecast value used in priority calculation.",
        Keys.HELP_INCLUDE_FACILITIES: "Select facilities to INCLUDE. Empty = include all.",
        Keys.HELP_EXCLUDE_FACILITIES: "Select facilities to EXCLUDE. Takes precedence over include.",
        Keys.HELP_FORECAST_SOURCE: "External uses loaded forecast file. ML uses trained ML models from Tab 10.",
        Keys.HELP_SELECT_ITEMS: "Select items to create order",
        Keys.NEW_PRODUCTS: "New Products",
        Keys.STOCKOUT_RISK: "Stockout Risk",
        Keys.REVENUE_IMPACT: "Revenue Impact",
        Keys.DEMAND_FORECAST: "Demand Forecast",
        Keys.ZERO_STOCK_PENALTY: "Zero Stock Penalty",
        Keys.BELOW_ROP_PENALTY: "Below ROP Max Penalty",
        Keys.DEMAND_CAP: "Demand Cap",
        Keys.TOP_PRIORITY_TO_ORDER: "Top Priority Items to Order",
        Keys.SHOWING_TOP_MODEL_COLOR: "Showing top {count} MODEL+COLOR combinations by priority",
        Keys.SELECT: "Select",
        Keys.LOAD_STOCK_AND_FORECAST: "Please load both stock and forecast data in Tab 1 to use this feature.",

        Keys.TITLE_MANUAL_ORDER_CREATION: "📝 Manual Order Creation",
        Keys.TITLE_SIZE_DISTRIBUTION: "Size Distribution",
        Keys.TITLE_SIZE_COLOR_TABLE: "Size x Color Production Table",
        Keys.TITLE_ZERO_STOCK_PRODUCTION: "Zero Stock Production (Color x Size)",
        Keys.COLOR_FILTER_ALL: "All colors",
        Keys.COLOR_FILTER_MODEL: "Model colors",
        Keys.COLOR_FILTER_ACTIVE: "Active only",
        Keys.TITLE_FACILITY_CAPACITY: "🏭 Facility Capacity",
        Keys.TITLE_EDIT_CAPACITY: "⚙️ Edit Monthly Capacity",

        Keys.ENTER_MODEL_CODE_HELP: "Enter any model code (5 characters) to create an order.",
        Keys.ENTER_MODEL_PLACEHOLDER: "e.g., CH031",
        Keys.LOADING_DATA_FOR_MODEL: "Loading data for model {model}...",
        Keys.ORDER_FOR_MODEL: "Order for Model: {model}",
        Keys.NO_RECOMMENDATIONS_DATA: "No recommendations data available for {model}-{color}",
        Keys.SELECT_MODEL_TO_PROCESS: "Selected items span {count} models. Please select one model to process.",
        Keys.SELECT_MODEL_LABEL: "Select model to create order:",

        Keys.LABEL_PRIMARY_FACILITY: "Primary Facility",
        Keys.LABEL_SECONDARY_FACILITY: "Secondary Facility",
        Keys.LABEL_MATERIAL_TYPE: "Material Type",
        Keys.LABEL_MATERIAL_WEIGHT: "Material Weight",
        Keys.LABEL_MODEL_CODE: "Model Code",
        Keys.LABEL_PRODUCT_NAME: "Product Name",
        Keys.LABEL_PARSING_PDF: "Parsing PDF...",
        Keys.LABEL_CAPACITY: "Capacity",
        Keys.LABEL_ORDERS: "Orders",
        Keys.LABEL_TOTAL_QTY: "Total Qty",
        Keys.LABEL_UTILIZATION: "Utilization",

        Keys.PLACEHOLDER_MODEL_CODE: "e.g., ABC12",
        Keys.PLACEHOLDER_PRODUCT_NAME: "e.g., Bluza",
        Keys.PLACEHOLDER_FACILITY: "e.g., Sieradz",
        Keys.PLACEHOLDER_OPERATION: "e.g., szycie i skladanie",
        Keys.PLACEHOLDER_MATERIAL: "e.g., DRES PETELKA 280 GSM",

        Keys.HELP_ORDER_DATE: "Date when the order was placed",
        Keys.HELP_UPLOAD_PDF: "Upload a PDF file containing order details",
        Keys.HELP_ARCHIVE_CHECKBOX: "Check to archive this order",
        Keys.HELP_CAPACITY_EDITOR: "Set monthly production capacity for each facility",

        Keys.BTN_CREATE_FROM_PDF: "Create Order from PDF",
        Keys.BTN_DOWNLOAD_ORDER_CSV: "📥 Download CSV",
        Keys.BTN_COPY_TABLE: "📋 Copy table to clipboard",
        Keys.BTN_SAVE_CAPACITY: "💾 Save Capacity",
        Keys.BTN_ARCHIVE_N_ORDERS: "Archive {count} Order(s)",

        Keys.MSG_ORDER_SAVED: "Order {order_id} saved successfully!",
        Keys.MSG_ORDER_SAVE_FAILED: "Failed to save order",
        Keys.MSG_CAPACITY_SAVED: "Capacity settings saved",
        Keys.MSG_NO_FACILITY_DATA: "No facility data available in active orders.",
        Keys.MSG_NO_CAPACITY_DATA: "No active orders to calculate facility capacity.",
        Keys.MSG_COULD_NOT_LOAD_SALES: "Could not load sales history: {error}",
        Keys.MSG_ENTER_MODEL_CODE: "Please enter a model code",

        Keys.ERR_ORDER_CREATION: "Error in Order Creation: {error}",
        Keys.ERR_ORDER_TRACKING: "Error in Order Tracking: {error}",
        Keys.ERR_SAVING_ORDER: "Error saving order: {error}",

        Keys.CAPTION_SIZE_DISTRIBUTION: "All colors combined + last 3 months sales history",
        Keys.CAPTION_TOTAL_QTY_FACILITIES: "📊 Total quantity across all facilities: {total:,}",

        Keys.NA: "N/A",
        Keys.PRODUCED_SIZE_QTY: "Produced (Size:Qty)",

        Keys.TITLE_SIZE_PATTERN_OPTIMIZER: "Size Pattern Optimizer",
        Keys.LOADED_SALES_HISTORY: "Loaded sales history for {model} (all colors)",
        Keys.NO_SALES_DATA_FOR_MODEL: "No sales data found for {model}",
        Keys.SIZES: "Sizes",
        Keys.PATTERNS: "Patterns",
        Keys.CREATE_EDIT_PATTERN_SET: "Create/Edit Pattern Set",
        Keys.USING_ALGORITHM: "Using algorithm: **{algorithm}** (change in sidebar)",
        Keys.ERR_NO_PATTERN_SETS: "Please add at least one pattern set before optimizing!",
        Keys.ERR_SELECT_PATTERN_SET: "Please select an active pattern set!",
        Keys.ERR_ENTER_QUANTITIES: "Please enter quantities to optimize!",
        Keys.ERR_PATTERN_SET_NOT_FOUND: "Active pattern set not found!",
        Keys.NO_PATTERNS_ALLOCATED: "No patterns allocated",
        Keys.SIZE: "Size",
        Keys.SALES: "sales",
        Keys.EXCLUDED: "excluded",
        Keys.ERR_PATTERN_OPTIMIZER: "Error in Pattern Optimizer: {error}",

        Keys.BTN_GENERATE_ACCURACY_REPORT: "Generate Accuracy Report",
        Keys.BTN_CLEAR_RESULTS: "Clear Results",
        Keys.ANALYSIS_PARAMETERS: "Analysis Parameters",
        Keys.HELP_ANALYSIS_START: "Start of period to analyze accuracy",
        Keys.HELP_ANALYSIS_END: "End of period to analyze accuracy",
        Keys.HELP_FORECAST_LOOKBACK: "How many months before analysis start to look for forecast",
        Keys.ERR_ANALYSIS_PERIOD_TOO_SHORT: "Analysis period ({days} days) must be at least {min_days} days (current lead time: {lead_time} months)",
        Keys.INFO_ANALYSIS_PERIOD: "Analyzing {days} days. Using forecast generated around {date}",
        Keys.LOADING_ACCURACY_METRICS: "Loading data and calculating accuracy metrics...",
        Keys.ERR_NO_SALES_FOR_PERIOD: "No sales data found for the selected period",
        Keys.ERR_NO_FORECAST_FOUND: "No forecast found for approximately {months} months before {date}",
        Keys.WARN_NO_STOCK_HISTORY: "No stock history found. Stockout analysis will be limited.",
        Keys.ERR_ACCURACY_CALCULATION: "Could not calculate accuracy metrics. Check data alignment.",
        Keys.MSG_ACCURACY_SUCCESS: "Accuracy report generated successfully!",
        Keys.INFO_USING_FORECAST: "Using forecast generated on: **{date}**",
        Keys.STOCKOUT_DAYS: "{days:,} stockout days",
        Keys.FCST_VS_ACT: "Fcst: {forecast:,} | Act: {actual:,}",
        Keys.ACCURACY_BY_ITEM: "Accuracy by Item",
        Keys.SEARCH_ENTITY: "Search {entity}",
        Keys.SEARCH_ENTITY_PLACEHOLDER: "Enter {entity} or partial match...",
        Keys.SHOWING_N_OF_M_ITEMS: "Showing {n} of {m} items",
        Keys.DOWNLOAD_ACCURACY_REPORT: "Download Accuracy Report (CSV)",
        Keys.ACCURACY_BY_PRODUCT_TYPE: "Accuracy by Product Type",
        Keys.MAPE_BY_PRODUCT_TYPE: "MAPE by Product Type",
        Keys.ACCURACY_TREND_OVER_TIME: "Accuracy Trend Over Time",
        Keys.CHART_WEEK: "Week",
        Keys.CHART_MAPE_PCT: "MAPE (%)",
        Keys.ITEM_DETAIL_VIEW: "Item Detail View",
        Keys.SELECT_ENTITY_DETAILS: "Select {entity} to view details",
        Keys.DAYS_ANALYZED: "Days Analyzed",
        Keys.DAYS_STOCKOUT: "Days Stockout",
        Keys.FORECAST_TOTAL: "Forecast Total",
        Keys.ACTUAL_TOTAL: "Actual Total",
        Keys.WARN_MISSED_OPPORTUNITY: "Missed opportunity: {units:,} units during {days} stockout days",
        Keys.ERR_FORECAST_ACCURACY: "Error in Forecast Accuracy: {error}",
        Keys.CAPTION_FORECAST_ACCURACY: "Compare historical forecasts against actual sales to evaluate forecast quality",
        Keys.MSG_NO_SALES_DATA_LOAD: "No sales data available. Please load sales data first.",

        Keys.FC_ERROR_IN_TAB: "Error in Forecast Comparison: {error}",
        Keys.FC_PARAMETERS: "Parameters",
        Keys.FC_MODEL_FASTER: "Model (faster)",
        Keys.FC_SKU_SLOWER: "SKU (slower)",
        Keys.FC_MOVING_AVG: "Moving Average",
        Keys.FC_EXP_SMOOTHING: "Exponential Smoothing",
        Keys.FC_HOLT_WINTERS: "Holt-Winters",
        Keys.FC_SARIMA: "SARIMA",
        Keys.FC_AUTO_ARIMA: "AutoARIMA (sktime)",
        Keys.FC_GENERATE_AS_OF_HELP: "Simulate forecast generation as if it was this date. Only sales data up to this date will be used.",
        Keys.FC_COMPARE_AS_OF_HELP: "Date up to which actual sales are loaded for comparison. Set to future date of generation date to see forecast accuracy.",
        Keys.FC_LOADING_DATA: _EN_LOADING_DATA,
        Keys.FC_LOADING_MONTHLY_AGG: "Loading monthly aggregations...",
        Keys.FC_NO_MONTHLY_AGG: "No monthly aggregation data available",
        Keys.FC_NO_DATA_BEFORE_DATE: "No data available before {date}",
        Keys.FC_LOADING_FORECASTS: "Loading forecasts...",
        Keys.FC_NO_EXTERNAL_FORECAST: "No external forecast data available. Will only generate internal forecasts.",
        Keys.FC_LOADING_SALES: "Loading sales data for comparison...",
        Keys.FC_NO_SALES_FOR_COMPARISON: "No sales data available for comparison period ({start} to {end}). Actual values will be zero.",
        Keys.FC_PREPARING_ENTITIES: "Preparing entities...",
        Keys.FC_NO_ENTITIES_FOUND: "No entities found matching the filter criteria",
        Keys.FC_PROCESSING_ENTITIES: "Processing {count} entities (data up to {date})...",
        Keys.FC_GENERATING_FORECASTS: "Generating internal forecasts...",
        Keys.FC_FORECASTING_PROGRESS: "Forecasting {current}/{total}: {entity}",
        Keys.FC_CALCULATING_METRICS: "Calculating comparison metrics...",
        Keys.FC_DONE: "Done!",
        Keys.FC_NO_INTERNAL_FORECASTS: "Failed to generate any internal forecasts",
        Keys.FC_COMPARISON_COMPLETE: "Comparison complete! Processed {success} entities successfully. Generated as of {gen_date}, compared against sales up to {comp_date}.",
        Keys.FC_ENTITIES_FAILED: "{count} entities failed to forecast",
        Keys.FC_ERROR: "Error: {error}",
        Keys.FC_FORECAST_INFO: "Forecast generated 'as of': {gen_date} | Forecast period: {start} | Comparison data up to: {end}",
        Keys.FC_FORECAST_PERIOD: "Forecast period: {start} to {end}",
        Keys.FC_OVERALL_SUMMARY: "Overall Comparison Summary",
        Keys.FC_INTERNAL_MAPE: "Internal MAPE",
        Keys.FC_EXTERNAL_MAPE: "External MAPE",
        Keys.FC_MORE_ACCURATE: "More Accurate",
        Keys.FC_INTERNAL_WINS: "Internal ({count})",
        Keys.FC_EXTERNAL_WINS: "External ({count})",
        Keys.FC_TIE: "Tie",
        Keys.FC_AVG_IMPROVEMENT: "Avg Improvement",
        Keys.FC_METHODS_USED: "Methods used: {methods}",
        Keys.FC_WINNER_BY_TYPE: "Winner Breakdown by Product Type",
        Keys.FC_NO_TYPE_BREAKDOWN: "No type breakdown available",
        Keys.FC_ALL_FORECAST_ITEMS: "All Forecast Items",
        Keys.FC_NO_FORECAST_DATA: "No forecast data available",
        Keys.FC_VIEW_ALL_ITEMS: "View All Forecast Items",
        Keys.FC_SEARCH_ENTITY: "Search by Entity ID",
        Keys.FC_ORDER: "Order",
        Keys.FC_TOTAL_ROWS: "Total rows: {count}",
        Keys.FC_DOWNLOAD_ALL_FORECASTS: "Download All Forecasts (CSV)",
        Keys.FC_DETAILED_COMPARISON: "Detailed Comparison",
        Keys.FC_NO_COMPARISON_DATA: "No comparison data available",
        Keys.FC_IMPROVEMENT: "Improvement",
        Keys.FC_DOWNLOAD_FULL_REPORT: "Download Full Report (CSV)",
        Keys.FC_ENTITY_DETAIL_CHART: "Entity Detail Chart",
        Keys.FC_NO_DATA_FOR_CHART: "No comparison data available for charting",
        Keys.FC_SELECT_ENTITY: "Select Entity",
        Keys.FC_CHART_ACTUAL: "Actual",
        Keys.FC_CHART_INTERNAL: "Internal Forecast",
        Keys.FC_CHART_EXTERNAL: "External Forecast",
        Keys.FC_CHART_TITLE: "Forecast Comparison: {entity}",
        Keys.FC_CHART_MONTH: "Month",
        Keys.FC_SAVE_FORECAST: "Save Forecast",
        Keys.FC_NO_FORECAST_TO_SAVE: "No forecast data to save",
        Keys.FC_NOTES_OPTIONAL: "Notes (optional)",
        Keys.FC_NOTES_PLACEHOLDER: "e.g., Monthly comparison run",
        Keys.FC_SAVE_TO_HISTORY: "Save Forecast to History",
        Keys.FC_FORECAST_SAVED: "Forecast saved! Batch ID: {batch_id}...",
        Keys.FC_ERROR_SAVING: "Error saving forecast: {error}",
        Keys.FC_HISTORICAL_INTERNAL: "Historical Internal Forecasts",
        Keys.FC_NO_HISTORICAL: "No historical forecasts found. Generate and save a forecast first.",
        Keys.FC_SELECT_HISTORICAL: "Select Historical Forecast",
        Keys.FC_ENTITY_TYPE: "Entity Type",
        Keys.FC_HORIZON: "{months} months",
        Keys.FC_SUCCESS: "Success",
        Keys.FC_FAILED: "Failed",
        Keys.FC_METHODS: "Methods: {methods}",
        Keys.FC_NOTES: "Notes: {notes}",
        Keys.FC_ANALYSIS_SETTINGS: "Analysis Settings",
        Keys.FC_FORECAST_COVERS: "Forecast covers periods: {start} to {end}",
        Keys.FC_ANALYZE_AS_OF: "Analyze 'as of' date",
        Keys.FC_ANALYZE_AS_OF_HELP: "Select a date in the past to compare forecast against actual sales that occurred after the forecast was generated",
        Keys.FC_SET_AS_OF_INFO: "Set 'as of' date to analyze historical accuracy. Sales data will be loaded from forecast period up to this date.",
        Keys.FC_LOAD_COMPARE: "Load and Compare",
        Keys.FC_DELETE: "Delete",
        Keys.FC_FORECAST_DELETED: "Forecast deleted",
        Keys.FC_DELETE_FAILED: "Failed to delete forecast",
        Keys.FC_FAILED_LOAD: "Failed to load forecast data",
        Keys.FC_NO_SALES_FOR_PERIOD: "No sales data available for the selected period. Actual values will be zero.",
        Keys.FC_HISTORICAL_LOADED: "Historical forecast loaded! Sales data from {start} to {end}",
        Keys.FC_ASCENDING: "Ascending",
        Keys.FC_DESCENDING: "Descending",
        Keys.FC_COL_ENTITY: "Entity",
        Keys.FC_COL_PERIOD: "Period",
        Keys.FC_COL_INTERNAL_FORECAST: "Internal Forecast",
        Keys.FC_COL_EXTERNAL_FORECAST: "External Forecast",
        Keys.FC_COL_ACTUAL_SALES: "Actual Sales",
        Keys.FC_COL_METHOD: "Method",
        Keys.FC_COL_MONTHS: "Months",
        Keys.FC_COL_ACTUAL_VOLUME: "Actual Volume",
        Keys.FC_COL_INT_MAPE: "Int MAPE",
        Keys.FC_COL_EXT_MAPE: "Ext MAPE",
        Keys.FC_COL_WINNER: "Winner",
        Keys.FC_COL_TYPE: "Type",
        Keys.FC_COL_TOTAL: "Total",
        Keys.FC_COL_INTERNAL_WINS: "Internal Wins",
        Keys.FC_COL_EXTERNAL_WINS: "External Wins",
        Keys.FC_COL_TIES: "Ties",
        Keys.FC_COL_INTERNAL_WIN_PCT: "Internal Win %",
        Keys.FC_COL_AVG_INT_MAPE: "Avg Int MAPE",
        Keys.FC_COL_AVG_EXT_MAPE: "Avg Ext MAPE",
        Keys.FC_CLEAR_RESULTS: "Clear Results",

        Keys.ML_ERROR_IN_TAB: "Error in ML Forecast: {error}",
        Keys.ML_TRAIN_DESCRIPTION: "Train ML models with automatic selection per entity",
        Keys.ML_TAB_TRAIN: "Train Models",
        Keys.ML_TAB_GENERATE: "Generate Forecasts",
        Keys.ML_TAB_MANAGE: "Manage Models",
        Keys.ML_LOADING_DATA: _EN_LOADING_DATA,
        Keys.ML_LOADING_MONTHLY_AGG: "Loading monthly aggregations...",
        Keys.ML_NO_MONTHLY_AGG: "No monthly aggregation data available",
        Keys.ML_LOADING_SKU_STATS: "Loading SKU statistics...",
        Keys.ML_PREPARING_ENTITIES: "Preparing entities...",
        Keys.ML_NO_ENTITIES_FOUND: "No entities found matching the criteria",
        Keys.ML_TRAINING_FOR_ENTITIES: "Training models for {count} entities...",
        Keys.ML_TRAINING_PROGRESS: "Training {current}/{total}: {entity}",
        Keys.ML_TRAINING_MODELS: "Training models...",
        Keys.ML_SAVING_MODELS: "Saving models...",
        Keys.ML_TRAINING_ERROR: "Training error: {error}",
        Keys.ML_TRAINING_RESULTS: "Training Results",
        Keys.ML_TOTAL_ENTITIES: "Total Entities",
        Keys.ML_AVG_CV_SCORE: "Avg CV Score",
        Keys.ML_MODEL_DISTRIBUTION: "Model Distribution",
        Keys.ML_BEST_MODEL_SELECTION: "Best Model Selection",
        Keys.ML_FORECAST_PREVIEW: "Forecast Preview",
        Keys.ML_COL_ENTITY: "Entity",
        Keys.ML_COL_MODEL: "Model",
        Keys.ML_COL_CV_SCORE: "CV Score",
        Keys.ML_COL_TOTAL_FORECAST: "Total Forecast",
        Keys.ML_DOWNLOAD_FORECASTS: "Download Forecasts (CSV)",
        Keys.ML_GENERATE_FROM_SAVED: "Generate Forecasts from Saved Models",
        Keys.ML_NO_TRAINED_MODELS: "No trained models found. Train models first in the 'Train Models' tab.",
        Keys.ML_MODELS_AVAILABLE: "{count} trained models available",
        Keys.ML_ENTITY_FILTER: "Entity Filter (optional)",
        Keys.ML_GENERATING_FORECASTS: "Generating forecasts...",
        Keys.ML_NO_MODELS_MATCHING: "No models found matching the filter",
        Keys.ML_COULD_NOT_LOAD_AGG: "Could not load monthly aggregations",
        Keys.ML_GENERATING_PROGRESS: "Generating {current}/{total}: {entity}",
        Keys.ML_GENERATED_FORECASTS: "Generated forecasts for {count} entities",
        Keys.ML_NO_FORECASTS_GENERATED: "No forecasts generated",
        Keys.ML_MANAGE_TITLE: "Manage Trained Models",
        Keys.ML_NO_MODELS_FOUND: "No trained models found.",
        Keys.ML_TOTAL_MODELS: "Total Models",
        Keys.ML_MOST_COMMON_MODEL: "Most Common Model",
        Keys.ML_SEARCH_ENTITY: "Search Entity",
        Keys.ML_FILTER_BY_TYPE: "Filter by Model Type",
        Keys.ML_ALL: "All",
        Keys.ML_SHOWING_MODELS: "Showing {count} models",
        Keys.ML_COL_TYPE: "Type",
        Keys.ML_COL_TRAINED: "Trained",
        Keys.ML_MODEL_DETAILS: "Model Details",
        Keys.ML_NO_MODELS_TO_DISPLAY: "No models to display",
        Keys.ML_SELECT_FOR_DETAILS: "Select Entity for Details",
        Keys.ML_MODEL_TYPE: "Model Type",
        Keys.ML_TRAINED_AT: "Trained At",
        Keys.ML_CV_METRIC: "CV Metric",
        Keys.ML_PRODUCT_TYPE: "Product Type",
        Keys.ML_FEATURE_IMPORTANCE: "Feature Importance",
        Keys.ML_TOP_FEATURES: "Top Features",
        Keys.ML_DELETE_MODEL_FOR: "Delete Model for {entity}",
        Keys.ML_MODEL_DELETED: "Deleted model for {entity}",
        Keys.ML_DELETE_FAILED: "Failed to delete model",
        Keys.ML_BULK_ACTIONS: "Bulk Actions",
        Keys.ML_DELETE_ALL_MODELS: "Delete All Models",
        Keys.ML_DELETED_MODELS: "Deleted {count} models",
        Keys.ML_EXPORT_MODEL_REPORT: "Export Model Report",
        Keys.ML_DOWNLOAD_REPORT: "Download Report",
        Keys.ML_MODEL_DETAILED: "Model (faster)",
        Keys.ML_SKU_DETAILED: "SKU (detailed)",
        Keys.ML_ENTITIES_FAILED: "{count} entities failed",
        Keys.ML_SELECT_ENTITY_DETAILS: "Select Entity for Details",
        Keys.ML_ENTITY: "Entity",
        Keys.ML_CV_SCORE: "CV Score",

        Keys.NLQ_QUERY: "Query",
        Keys.NLQ_PROCESSING: "Processing query...",
        Keys.NLQ_CONFIDENCE: "Confidence",
        Keys.NLQ_INTERPRETATION: "Interpretation",
        Keys.NLQ_GENERATED_SQL: "Generated SQL",
        Keys.NLQ_DOWNLOAD_RESULTS: "Download Results (CSV)",
        Keys.NLQ_TITLE: "Natural Language Query",
        Keys.NLQ_CAPTION: "Query your data using natural language (English or Polish)",
        Keys.NLQ_DATABASE_MODE: "Database mode: queries executed via SQL on PostgreSQL",
        Keys.NLQ_FILE_MODE: "File mode: queries executed via SQL on DuckDB",
        Keys.NLQ_ENTER_QUERY: "Enter your query",
        Keys.NLQ_PLACEHOLDER: "e.g., sales of model CH086 last 2 years",
        Keys.NLQ_EXECUTE: "Execute",
        Keys.NLQ_CLEAR: "Clear",
        Keys.NLQ_COULD_NOT_UNDERSTAND: "Could not understand the query. Please try rephrasing.",
        Keys.NLQ_INTERPRETATION_SQL: "Query interpretation & SQL",
        Keys.NLQ_LOW_CONFIDENCE: "Low confidence - results may not match your intent",
        Keys.NLQ_NO_RESULTS: "No results found",
        Keys.NLQ_RESULTS: "Results",
        Keys.NLQ_ROWS: "Rows",
        Keys.NLQ_COLUMNS: "Columns",
        Keys.NLQ_EXAMPLE_QUERIES: "Example queries",
        Keys.NLQ_CLICK_EXAMPLE: "Click on any example to copy it to your clipboard:",
        Keys.NLQ_ERROR_IN_TAB: "Error in Natural Language Query: {error}",

        Keys.DISPLAY_LAST_YEAR: "Last Year",
        Keys.DISPLAY_CHANGE: "Change",
        Keys.DISPLAY_TOTAL_PATTERNS: "Total Patterns",
        Keys.DISPLAY_TOTAL_EXCESS: "Total Excess",
        Keys.DISPLAY_COVERAGE: "Coverage",
        Keys.DISPLAY_DOWNLOAD_CSV: "Download CSV",
        Keys.DISPLAY_MODEL: "Model",

        Keys.TASK_ADD_NEW: "Add New Task",
        Keys.TASK_TITLE: "Title",
        Keys.TASK_TITLE_PLACEHOLDER: "Short task title...",
        Keys.TASK_DESCRIPTION: "Description",
        Keys.TASK_DESCRIPTION_PLACEHOLDER: "Detailed description (supports **bold**, *italic*, - lists)",
        Keys.TASK_DESCRIPTION_HELP: "Supports Markdown: **bold**, *italic*, - bullet lists, 1. numbered lists",
        Keys.TASK_DUE_DATE: "Due Date",
        Keys.TASK_PRIORITY: "Priority",
        Keys.TASK_PRIORITY_HIGH: "High",
        Keys.TASK_PRIORITY_MEDIUM: "Medium",
        Keys.TASK_PRIORITY_LOW: "Low",
        Keys.TASK_STATUS_TODO: "To Do",
        Keys.TASK_STATUS_IN_PROGRESS: "In Progress",
        Keys.TASK_STATUS_DONE: "Done",
        Keys.TASK_ADD_BTN: "Add Task",
        Keys.TASK_DELETE_BTN: "Delete",
        Keys.TASK_EDIT_BTN: "Edit",
        Keys.TASK_SAVE_BTN: "Save",
        Keys.TASK_LIST: "Task List",
        Keys.TASK_KANBAN: "Kanban Board",
        Keys.TASK_FILTER_STATUS: "Filter by Status",
        Keys.TASK_FILTER_PRIORITY: "Filter by Priority",
        Keys.TASK_FILTER_ALL: "All",
        Keys.TASK_NO_TASKS: "No tasks yet. Add your first task above!",
        Keys.TASK_CREATED: "Created",
        Keys.TASK_DUE: "Due",
        Keys.ERR_TASK_PLANNER: "Error in Task Planner: {error}",
        Keys.ERR_TASK_TITLE_REQUIRED: "Task title is required",

        Keys.PROGRESS_LOADING_DATA: _EN_LOADING_DATA,
        Keys.PROGRESS_LOADING_SALES: "Loading sales data...",
        Keys.PROGRESS_LOADING_STOCK: "Loading stock data...",
        Keys.PROGRESS_LOADING_FORECAST: "Loading forecast...",
        Keys.PROGRESS_LOADING_METADATA: "Loading metadata...",
        Keys.PROGRESS_DONE: "Done!",
    },

    "pl": {
        Keys.PAGE_TITLE: "Zarządzanie Zapasami i Optymalizator Wzorców",

        Keys.TAB_TASK_PLANNER: "📝 Planer Zadań",
        Keys.TAB_SALES_ANALYSIS: "📊 Analiza Sprzedaży i Zapasów",
        Keys.TAB_PATTERN_OPTIMIZER: "✂️ Optymalizator Rozmiarów",
        Keys.TAB_WEEKLY_ANALYSIS: "📋 Analiza Tygodniowa",
        Keys.TAB_MONTHLY_ANALYSIS: "📆 Analiza Miesięczna",
        Keys.TAB_ORDER_RECOMMENDATIONS: "🎯 Rekomendacje Zamówień",
        Keys.TAB_ORDER_CREATION: "🛒 Tworzenie Zamówienia",
        Keys.TAB_ORDER_TRACKING: "🚚 Śledzenie Zamówień",
        Keys.TAB_FORECAST_ACCURACY: "📈 Dokładność Prognozy",
        Keys.TAB_FORECAST_COMPARISON: "🔬 Porównanie Prognoz",
        Keys.TAB_ML_FORECAST: "🤖 Prognoza ML",
        Keys.TAB_NL_QUERY: "🔍 Zapytanie NL",

        Keys.SIDEBAR_PARAMETERS: "Parametry",
        Keys.SIDEBAR_LEAD_TIME_FORECAST: "Lead Time i Prognoza",
        Keys.SIDEBAR_SERVICE_LEVELS: "Poziomy Obsługi",
        Keys.SIDEBAR_PATTERN_OPTIMIZER: "Optymalizator Wzorców",
        Keys.SIDEBAR_CURRENT_PARAMS: "Aktualne Parametry:",
        Keys.SIDEBAR_VIEW_OPTIONS: "Opcje Widoku",
        Keys.SIDEBAR_LOAD_DATA: "Wczytaj dodatkowe dane",

        Keys.BTN_SAVE: "💾 Zapisz",
        Keys.BTN_RESET: "🔄 Resetuj",
        Keys.BTN_CANCEL: "Anuluj",
        Keys.BTN_CLEAR: "Wyczyść",
        Keys.BTN_DOWNLOAD_CSV: "Pobierz CSV",
        Keys.BTN_GENERATE: "Generuj",
        Keys.BTN_REFRESH: "Odśwież",
        Keys.BTN_CREATE_ORDER: "Utwórz Zamówienie",
        Keys.BTN_SAVE_TO_DB: "💾 Zapisz do Bazy",
        Keys.BTN_RUN_OPTIMIZATION: "Uruchom Optymalizację",
        Keys.BTN_NEW_SET: "Nowy Zestaw",
        Keys.BTN_EDIT_SET: "Edytuj Zestaw",
        Keys.BTN_DELETE_SET: "Usuń Zestaw",
        Keys.BTN_SAVE_ALL: "Zapisz Wszystko",
        Keys.BTN_RELOAD: "Wczytaj Ponownie",
        Keys.BTN_SAVE_PATTERN_SET: "Zapisz Zestaw Wzorców",
        Keys.BTN_LOAD_SALES_HISTORY: "Wczytaj Historię Sprzedaży",
        Keys.BTN_EXECUTE: "Wykonaj",
        Keys.BTN_ADD_ORDER: "Dodaj Zamówienie",
        Keys.BTN_ARCHIVE: "Archiwizuj",
        Keys.BTN_PARSE_PDF: "Parsuj PDF",
        Keys.BTN_GENERATE_RECOMMENDATIONS: "Generuj Rekomendacje",
        Keys.BTN_GENERATE_COMPARISON: "Generuj Porównanie",
        Keys.BTN_GENERATE_FORECASTS: "Generuj Prognozy",

        Keys.LEAD_TIME_MONTHS: "Lead time w miesiącach",
        Keys.LEAD_TIME_HELP: "Czas między złożeniem zamówienia a jego otrzymaniem (używany w obliczeniach ROP i SS)",
        Keys.SYNC_FORECAST: "Synchronizuj czas prognozy z lead time",
        Keys.SYNC_FORECAST_HELP: "Po włączeniu czas prognozy automatycznie odpowiada lead time",
        Keys.FORECAST_TIME_MONTHS: "Czas prognozy w miesiącach",
        Keys.FORECAST_TIME_HELP: "Okres dla obliczeń prognozy (niezależny od lead time gdy synchronizacja jest wyłączona)",

        Keys.TYPE_BASIC: "Podstawowy",
        Keys.TYPE_REGULAR: "Regularny",
        Keys.TYPE_SEASONAL: "Sezonowy",
        Keys.TYPE_NEW: "Nowy",

        Keys.COL_TYPE: "Typ",
        Keys.COL_CV: "CV",
        Keys.COL_ZSCORE: "Z-Score",
        Keys.COL_ALGORITHM: "Algorytm",

        Keys.ALG_GREEDY_OVERSHOOT: "Greedy Overshoot",
        Keys.ALG_CLASSIC_GREEDY: "Classic Greedy",
        Keys.ALG_HELP: "Greedy Overshoot: Lepsze pokrycie z nieco większym nadmiarem. Classic Greedy: Minimalny nadmiar, ale może nie pokryć wszystkiego.",

        Keys.GROUP_BY_MODEL: "Grupuj wg Modelu (pierwsze 5 znaków)",
        Keys.LOAD_STOCK_DATA: "Wczytaj dane o stanie z katalogu data",
        Keys.LOAD_FORECAST_DATA: "Wczytaj dane prognozy z katalogu data",

        Keys.MSG_SAVED: "Zapisano!",
        Keys.MSG_SAVE_FAILED: "Zapis nie powiódł się",
        Keys.MSG_NO_STOCK_FILE: "Nie znaleziono pliku ze stanem magazynu. Kolumny związane ze stanem nie będą dostępne.",
        Keys.MSG_NO_FORECAST_FILE: "Nie znaleziono pliku z prognozą. Kolumny prognozy nie będą dostępne.",
        Keys.MSG_ERROR_PROCESSING_FORECAST: "Błąd podczas przetwarzania danych prognozy: {error}",
        Keys.MSG_NO_DATA_AVAILABLE: "Brak dostępnych danych",
        Keys.MSG_NOT_FOUND: "'{id}' nie znaleziono",
        Keys.MSG_LOAD_BOTH_DATASETS: "Żaden {entity_type} nie ma zarówno danych o stanie, jak i prognozy. Wczytaj oba zestawy danych, aby użyć tej funkcji.",
        Keys.MSG_NO_FORECAST_DATA: "Brak danych prognozy dla tego {entity} w oknie projekcji.",

        Keys.TITLE_TASK_PLANNER: "📝 Planer Zadań",
        Keys.TITLE_SALES_DATA_ANALYSIS: "Analiza Danych Sprzedaży",
        Keys.TITLE_STOCK_PROJECTION: "📈 Analiza Projekcji Stanu",
        Keys.TITLE_YEARLY_SALES_TREND: "📊 Roczny Trend Sprzedaży",
        Keys.TITLE_STOCK_STATUS: "Stan Magazynu",
        Keys.TITLE_ORDER_QUANTITIES: "Ilości Zamówienia",
        Keys.TITLE_SALES_HISTORY: "Historia Sprzedaży (ostatnie 4 miesiące)",
        Keys.TITLE_PATTERN_SETS: "Zestawy Wzorców",
        Keys.TITLE_OPTIMIZATION: "Optymalizacja",
        Keys.TITLE_ORDER_SUMMARY: "Podsumowanie Zamówienia",
        Keys.TITLE_WEEKLY_ANALYSIS: "📅 Analiza Tygodniowa",
        Keys.TITLE_MONTHLY_ANALYSIS: "📅 Miesięczna Analiza Rok do Roku wg Kategorii",
        Keys.TITLE_ORDER_RECOMMENDATIONS: "🎯 Rekomendacje Zamówień",
        Keys.TITLE_ORDER_CREATION: "📋 Tworzenie Zamówienia",
        Keys.TITLE_ORDER_TRACKING: "📦 Śledzenie Zamówień",
        Keys.TITLE_FORECAST_ACCURACY: "Monitoring Dokładności Prognozy",
        Keys.TITLE_FORECAST_COMPARISON: "Porównanie Prognoz",
        Keys.TITLE_ML_FORECAST: "Prognoza ML",
        Keys.TITLE_NL_QUERY: "🔍 Zapytanie w Języku Naturalnym",
        Keys.TITLE_TOP_SALES_REPORT: "⭐ Raport Top Sprzedaży",
        Keys.TITLE_TOP_5_BY_TYPE: "🏆 Top 5 Produktów wg Typu",
        Keys.TITLE_NEW_PRODUCTS_MONITORING: "📊 Monitoring Wprowadzania Nowych Produktów",
        Keys.TITLE_ACTIVE_ORDERS: "📋 Aktywne Zamówienia",
        Keys.TITLE_MANUAL_ORDER: "📝 Dodaj Ręczne Zamówienie",
        Keys.TITLE_IMPORT_PDF: "📄 Importuj Zamówienie z PDF",
        Keys.TITLE_RECOMMENDATION_PARAMS: "⚙️ Parametry Rekomendacji",

        Keys.SEARCH_MODEL: "Szukaj Modelu:",
        Keys.SEARCH_SKU: "Szukaj SKU:",
        Keys.SEARCH_MODEL_PLACEHOLDER: "Wpisz Model lub część Modelu...",
        Keys.SEARCH_SKU_PLACEHOLDER: "Wpisz SKU lub część SKU...",
        Keys.SHOW_ONLY_BELOW_ROP: "Pokaż tylko poniżej ROP",
        Keys.BESTSELLERS: "Bestsellery (>300/mies.)",
        Keys.FILTER_BY_TYPE: "Filtruj wg Typu:",
        Keys.OVERSTOCKED_FILTER: "**Filtr Nadstanów:**",
        Keys.SHOW_OVERSTOCKED: "Pokaż nadstany",
        Keys.OVERSTOCKED_BY_PCT: "Nadstan o %:",

        Keys.SHOWING_N_OF_M: "Pokazuję {count} z {total} {items}",
        Keys.MODELS: "Model(i)",
        Keys.SKUS: "SKU",

        Keys.METRIC_TOTAL_SKUS: "Łączna liczba SKU",
        Keys.METRIC_TOTAL_QUANTITY: "Łączna Ilość",
        Keys.METRIC_BELOW_ROP: "Poniżej ROP",
        Keys.METRIC_TOTAL_DEFICIT: "Łączny Deficyt (szt.)",
        Keys.METRIC_PCT_BELOW_ROP: "% Poniżej ROP",
        Keys.METRIC_OVERSTOCKED: "Nadstan",
        Keys.METRIC_NORMAL: "Normalny",
        Keys.METRIC_TOTAL_STOCK: "Łączny STAN",
        Keys.METRIC_TOTAL_STOCK_VALUE: "Łączna Wartość Stanu",
        Keys.METRIC_CURRENT_STOCK: "Aktualny Stan",
        Keys.METRIC_ROP: "ROP",
        Keys.METRIC_SAFETY_STOCK: "Zapas Bezpieczeństwa",
        Keys.METRIC_AVG_MONTHLY_SALES: "Śr. Sprzedaż Miesięczna",
        Keys.METRIC_FIRST_SALE_YEAR: "Rok Pierwszej Sprzedaży",
        Keys.METRIC_YEARS_ACTIVE: "Lat Aktywności",
        Keys.METRIC_TOTAL_HISTORICAL_SALES: "Łączna Sprzedaż Historyczna",
        Keys.METRIC_FORECAST_FUTURE: "Prognoza (Przyszła)",
        Keys.METRIC_LAST_WEEK: "Ostatni Tydzień",
        Keys.METRIC_SAME_WEEK_LAST_YEAR: "Ten Sam Tydzień Rok Temu",
        Keys.METRIC_NEW_PRODUCTS: "Nowe Produkty",
        Keys.METRIC_WEEKS_TRACKED: "Śledzonych Tygodni",
        Keys.METRIC_TOTAL_SALES: "Łączna Sprzedaż",
        Keys.METRIC_CURRENT_PERIOD: "Bieżący Okres",
        Keys.METRIC_SAME_PERIOD_LAST_YEAR: "Ten Sam Okres Rok Temu",
        Keys.METRIC_TOTAL_YOY_CHANGE: "Łączna Zmiana R/R",
        Keys.METRIC_RISING_CATEGORIES: "Rosnące Kategorie",
        Keys.METRIC_FALLING_CATEGORIES: "Spadające Kategorie",
        Keys.METRIC_UNCATEGORIZED: "Nieskategoryzowane",
        Keys.METRIC_MAPE: "MAPE",
        Keys.METRIC_BIAS: "BIAS",
        Keys.METRIC_MISSED_OPPORTUNITY: "Utracona Szansa",
        Keys.METRIC_VOLUME_ACCURACY: "Dokładność Wolumenu",
        Keys.METRIC_ROWS: "Wierszy",
        Keys.METRIC_COLUMNS: "Kolumn",

        Keys.DOWNLOAD_MODEL_SUMMARY: "Pobierz Podsumowanie Modeli CSV",
        Keys.DOWNLOAD_SKU_SUMMARY: "Pobierz Podsumowanie SKU CSV",
        Keys.DOWNLOAD_WEEKLY_ANALYSIS: "📥 Pobierz Analizę Tygodniową (CSV)",
        Keys.DOWNLOAD_PODGRUPA_SUMMARY: "📥 Pobierz Podsumowanie Podgrup (CSV)",
        Keys.DOWNLOAD_CATEGORY_DETAILS: "📥 Pobierz Szczegóły Kategorii (CSV)",
        Keys.DOWNLOAD_RESULTS: "📥 Pobierz Wyniki (CSV)",

        Keys.ENTER_MODEL_TO_ANALYZE: "Wpisz Model do analizy:",
        Keys.ENTER_SKU_TO_ANALYZE: "Wpisz SKU do analizy:",
        Keys.PROJECTION_MONTHS: "Miesiące projekcji:",
        Keys.ITEMS_AVAILABLE: "📦 {count} {entity_type} dostępnych z kompletnymi danymi",

        Keys.CHART_PROJECTED_STOCK: "Prognozowany Stan",
        Keys.CHART_ROP: "ROP ({value:.0f})",
        Keys.CHART_SAFETY_STOCK: "Zapas Bezpieczeństwa ({value:.0f})",
        Keys.CHART_ZERO_STOCK: "Zerowy Stan",
        Keys.CHART_ROP_REACHED: "Osiągnięto ROP",
        Keys.CHART_STOCKOUT: "Brak Towaru!",
        Keys.CHART_HISTORICAL_SALES: "Historyczna Sprzedaż",
        Keys.CHART_FORECAST: "Prognoza",
        Keys.CHART_DATE: "Data",
        Keys.CHART_QUANTITY: _PL_QUANTITY,
        Keys.CHART_YEAR: "Rok",
        Keys.CHART_QUANTITY_SOLD: "Sprzedana Ilość",

        Keys.STOCK_PROJECTION_FOR: "Projekcja Stanu dla {entity} {id}",
        Keys.YEARLY_SALES_TREND_FOR: "Roczny Trend Sprzedaży: {entity} {id}",
        Keys.STOCK_STATUS_DISTRIBUTION: "Rozkład Stanu Magazynu (Próg nadstanu: {threshold}%)",

        Keys.WARN_ROP_IN_DAYS: "Stan osiągnie ROP za {days} dni ({date})",
        Keys.ERR_STOCKOUT_IN_DAYS: "🚨 Przewidywany brak towaru za {days} dni ({date})",

        Keys.GROUP_BY: "Grupuj wg:",
        Keys.GROUP_MODEL: "Model",
        Keys.GROUP_MODEL_COLOR: "Model + Kolor",

        Keys.SORT_BY: "Sortuj wg:",
        Keys.FILTER_BY_CODE: "Filtruj wg kodu:",
        Keys.ALL_ITEMS_SUMMARY: "📋 Tabela Podsumowania Wszystkich Pozycji",
        Keys.YOY_TREND: "Trend R/R ({prev} → {curr}):",

        Keys.YEARLY_CAPTION: "Śledź cykl życia produktu: historyczna sprzedaż i prognoza do identyfikacji kandydatów do wycofania",
        Keys.WEEKLY_CAPTION: "Porównaj sprzedaż z poprzedniego tygodnia z tym samym tygodniem rok temu (poniedziałek-niedziela)",
        Keys.WEEKLY_TOP_SALES_CAPTION: "Bestsellery z ostatniego tygodnia wg kategorii produktów",
        Keys.WEEKLY_NEW_PRODUCTS_CAPTION: "Śledź tygodniową sprzedaż produktów wprowadzonych w ostatnich 2 miesiącach (Tygodnie wyrównane do środy)",
        Keys.MONTHLY_CAPTION: "Porównaj miesięczne ilości sprzedaży z bieżącego roku do poprzedniego, zorganizowane wg grupy wiekowej (Podgrupa) i kategorii odzieży (Kategoria). Automatycznie wyklucza bieżący niepełny miesiąc.",

        Keys.RISING_STAR: "🚀 WSCHODZĄCA GWIAZDA",
        Keys.FALLING_STAR: "📉 SPADAJĄCA GWIAZDA",
        Keys.NO_RISING_PRODUCTS: "Nie znaleziono rosnących produktów",
        Keys.NO_FALLING_PRODUCTS: "Nie znaleziono spadających produktów",
        Keys.NO_PRODUCTS_FOUND: "Nie znaleziono produktów {type}",
        Keys.NO_NEW_PRODUCTS: "Nie znaleziono nowych produktów z pierwszą sprzedażą w ostatnich {days} dniach",
        Keys.ZERO_SALES_WARNING: "⚠️ {count} produkt(ów) z ZEROWĄ sprzedażą w śledzonym okresie",
        Keys.VIEW_ZERO_SALES: "Zobacz produkty bez sprzedaży",

        Keys.SALES_BY_AGE_GROUP: "Sprzedaż wg Grupy Wiekowej i Kategorii",
        Keys.CLOTHING_CATEGORY: "Kategoria Odzieży",
        Keys.CURRENT_SALES: "Bieżąca Sprzedaż",
        Keys.PRIOR_YEAR_SALES: "Sprzedaż Rok Temu",
        Keys.DIFFERENCE: "Różnica",
        Keys.CHANGE_PCT: "Zmiana %",
        Keys.NO_DATA_AGE_GROUP: "Brak danych dla tej grupy wiekowej.",
        Keys.CATEGORY_MAPPINGS_ERROR: "Mapowania kategorii niedostępne. Upewnij się, że arkusz Kategorie istnieje w pliku danych lub tabela w bazie jest wypełniona.",
        Keys.NO_SALES_DATA: "Brak wczytanych danych sprzedaży. Upewnij się, że dane są wczytane w Zakładce 1.",
        Keys.CLICK_GENERATE: "Kliknij 'Generuj Miesięczną Analizę R/R', aby rozpocząć analizę.",

        Keys.PRIORITY_WEIGHTS: "**Wagi Priorytetów** (wkład do końcowego wyniku)",
        Keys.TYPE_MULTIPLIERS: "**Mnożniki Typów** (zwiększenie priorytetu wg typu produktu)",
        Keys.STOCKOUT_RISK_PARAMS: "**Ryzyko Braku Towaru i Inne Parametry**",
        Keys.FILTER_BY_FACILITY: "**Filtruj wg Zakładu Produkcyjnego**",
        Keys.PARAM_STOCKOUT_RISK: "Ryzyko Braku Towaru",
        Keys.PARAM_REVENUE_IMPACT: "Wpływ na Przychód",
        Keys.PARAM_DEMAND_FORECAST: "Prognoza Popytu",
        Keys.PARAM_ZERO_STOCK_PENALTY: "Kara za Zerowy Stan",
        Keys.PARAM_BELOW_ROP_PENALTY: "Max Kara za Poniżej ROP",
        Keys.PARAM_DEMAND_CAP: "Limit Popytu",
        Keys.PARAM_TOP_PRIORITY: "Najważniejsze pozycje:",
        Keys.INCLUDE_FACILITIES: "Uwzględnij Zakłady:",
        Keys.EXCLUDE_FACILITIES: "Wyklucz Zakłady:",
        Keys.FORECAST_SOURCE: "Źródło Prognozy:",
        Keys.EXTERNAL: "Zewnętrzna",
        Keys.TOP_PRIORITY_ITEMS: "Najpilniejsze Pozycje do Zamówienia",
        Keys.SHOWING_TOP_N: "Pokazuję top {n} kombinacji MODEL+KOLOR wg priorytetu",
        Keys.LOAD_STOCK_FORECAST: "Proszę wczytać dane o stanie i prognozę w Zakładce 1, aby użyć tej funkcji.",
        Keys.FILTERED_ACTIVE_ORDERS: "ℹ️ Odfiltrowano {count} model(i) z aktywnymi zamówieniami: {models}",

        Keys.PATTERN_SET_NAME: "Nazwa Zestawu",
        Keys.NUM_SIZE_CATEGORIES: "Liczba kategorii rozmiarów",
        Keys.DEFINE_SIZE_CATEGORIES: "Zdefiniuj kategorie rozmiarów:",
        Keys.SIZE_N: "Rozmiar {n}",
        Keys.NUM_PATTERNS: "Liczba wzorców w tym zestawie",
        Keys.PATTERN_NAME: "Nazwa Wzorca",
        Keys.QUANTITIES_PER_SIZE: "Ilości na rozmiar",
        Keys.SELECT_ACTIVE_PATTERN_SET: "Wybierz Aktywny Zestaw Wzorców:",
        Keys.MIN_ORDER_PER_PATTERN: "Minimalne zamówienie na wzorzec: {min} szt.",
        Keys.USING_SIZES_FROM: "Używane rozmiary z: {name}",
        Keys.ENTER_SALES_PER_SIZE: "Wprowadź całkowitą sprzedaż na rozmiar lub wczytaj automatycznie. Rozmiary ze sprzedażą < 3 będą wykluczone.",
        Keys.NO_PATTERN_SETS: "Brak zdefiniowanych zestawów wzorców. Utwórz zestaw wzorców, aby rozpocząć!",
        Keys.PATTERN_SETS_SAVED: "Zestawy wzorców zapisane!",
        Keys.ALL_REQUIREMENTS_MET: "Wszystkie wymagania pokryte i minimalne zamówienia spełnione!",
        Keys.MIN_ORDER_VIOLATIONS: "Naruszenia minimalnego zamówienia (potrzeba {min} na wzorzec): {violations}",
        Keys.SOME_NOT_COVERED: "Niektóre wymagania nie są pokryte",
        Keys.EXCLUDED_SIZES: "Wykluczone rozmiary (sprzedaż < 3 w ostatnich 4 miesiącach): {sizes}",
        Keys.COMPLETE_ALL_FIELDS: "Proszę uzupełnić wszystkie pola: nazwa zestawu, {num_sizes} nazw rozmiarów i {num_patterns} wzorców!",
        Keys.PATTERN: "Wzorzec",
        Keys.COUNT: _PL_QUANTITY,
        Keys.COMPOSITION: "Skład",
        Keys.STATUS: "Status",
        Keys.PATTERN_ALLOCATION: "Alokacja Wzorców",
        Keys.PRODUCTION_VS_REQUIRED: "Produkcja vs Wymagane",
        Keys.REQUIRED: "Wymagane",
        Keys.PRODUCED: "Wyprodukowane",
        Keys.EXCESS: "Nadwyżka",
        Keys.TOTAL: "SUMA",

        Keys.ENTER_MODEL_CODE: "Wprowadź Kod Modelu",
        Keys.NO_ITEMS_SELECTED: "Nie wybrano pozycji. Użyj ręcznego wprowadzania powyżej lub przejdź do zakładki Rekomendacji Zamówień.",
        Keys.MULTIPLE_MODELS_SELECTED: "Wybrane pozycje obejmują {count} modeli. Proszę wybrać jeden model do przetworzenia.",
        Keys.MODEL_NOT_FOUND: "Model '{model}' nie został znaleziony w danych sprzedaży.",
        Keys.NO_DATA_FOR_MODEL: "Nie znaleziono danych dla modelu '{model}'",
        Keys.NO_FORECAST_DEFICIT: "Nie znaleziono pozycji z dodatnią prognozą lub deficytem dla modelu '{model}'",
        Keys.PATTERN_SET_NOT_FOUND: "Zestaw wzorców '{model}' nie został znaleziony",
        Keys.CREATE_PATTERN_SET_HINT: "Proszę utworzyć zestaw wzorców w zakładce Optymalizatora Wzorców z nazwą odpowiadającą kodowi modelu",
        Keys.FOUND_PATTERN_SET: "Znaleziono zestaw wzorców: {name}",
        Keys.CREATED_ORDER: "Utworzono zamówienie dla modelu {model} z {count} kolorami",
        Keys.URGENT_COLORS: "**Pilne kolory:** {colors}",

        Keys.ORDER_ID: "ID Zamówienia",
        Keys.ORDER_DATE: "Data Zamówienia",
        Keys.MODEL: "Model",
        Keys.PRODUCT: "Produkt",
        Keys.QUANTITY: _PL_QUANTITY,
        Keys.FACILITY: "Zakład",
        Keys.OPERATION: "Operacja",
        Keys.MATERIAL: "Materiał",
        Keys.DAYS_ELAPSED: "Dni Minęło",
        Keys.UPLOAD_PDF: "Wgraj plik PDF zamówienia",
        Keys.FILE_UPLOADED: "Plik wgrany: {filename}",
        Keys.PDF_PARSED: "PDF sparsowany pomyślnie",
        Keys.ORDER_CREATED_PDF: "Zamówienie {order_id} utworzone z PDF",
        Keys.ORDER_ADDED: "Zamówienie {order_id} dodane do aktywnych zamówień",
        Keys.NO_ACTIVE_ORDERS: "Brak aktywnych zamówień. Utwórz zamówienia w Zakładce 5 lub dodaj ręczne zamówienia powyżej.",
        Keys.ORDER_ARCHIVED: "Zarchiwizowano zamówienie {order_id}",
        Keys.FAILED_PARSE_PDF: "Nie udało się sparsować PDF. Sprawdź format pliku.",
        Keys.FAILED_CREATE_ORDER: "Nie udało się utworzyć zamówienia",
        Keys.FAILED_ADD_ORDER: "Nie udało się dodać zamówienia",
        Keys.FAILED_ARCHIVE_ORDER: "Nie udało się zarchiwizować zamówienia {order_id}",
        Keys.TOTAL_ACTIVE_ORDERS: "📦 Łącznie aktywnych zamówień: {count}",
        Keys.ORDERS_READY: "🚚 Zamówienia gotowe do dostawy (powinny być w magazynie) (>= {threshold} dni): {count}",
        Keys.STATUS_READY: "🚚 Gotowe",
        Keys.STATUS_PENDING: "⏳ {days}d",
        Keys.ARCHIVE_ORDER: "Zaznacz, aby zarchiwizować to zamówienie",

        Keys.ANALYSIS_START_DATE: "Data Początkowa Analizy",
        Keys.ANALYSIS_END_DATE: "Data Końcowa Analizy",
        Keys.FORECAST_LOOKBACK: "Wstecz dla Prognozy (miesiące)",
        Keys.VIEW_LEVEL: "Poziom Widoku",
        Keys.SKU_LEVEL: "Poziom SKU",
        Keys.MODEL_LEVEL: "Poziom Modelu",
        Keys.OVERALL_ACCURACY_METRICS: "Ogólne Metryki Dokładności",
        Keys.MAPE_HELP: "Średni Bezwzględny Błąd Procentowy (niższy = lepiej)",
        Keys.BIAS_HELP: "Dodatni = nadprognozowanie, Ujemny = niedoprognozowanie",
        Keys.MISSED_OPP_HELP: "Ilość prognozy w okresach braku towaru",
        Keys.VOLUME_ACC_HELP: "Jak blisko łączna prognoza była do łącznej rzeczywistej",
        Keys.GOOD: "Dobra",
        Keys.ACCEPTABLE: "Akceptowalna",
        Keys.POOR: "Słaba",
        Keys.OVER_FORECASTING: "Nadprognozowanie",
        Keys.UNDER_FORECASTING: "Niedoprognozowanie",
        Keys.PRODUCT_TYPE_BREAKDOWN: "Podział wg Typu Produktu",
        Keys.TREND_CHART: "Tygodniowy Trend MAPE",

        Keys.COMPARE_FORECASTS: "Porównaj prognozy wewnętrzne (generowane za pomocą statsmodels) z prognozami zewnętrznymi",
        Keys.GENERATE_NEW: "Generuj Nową",
        Keys.HISTORICAL_FORECASTS: "Historyczne Prognozy",
        Keys.FORECAST_HORIZON: "Horyzont Prognozy (miesiące)",
        Keys.ANALYSIS_LEVEL: "Poziom Analizy",
        Keys.ENTITY_FILTER: "Filtr Encji",
        Keys.FORECAST_METHOD: "Metoda Prognozy",
        Keys.GENERATE_AS_OF: "Generuj 'na dzień'",
        Keys.COMPARE_AS_OF: "Porównaj 'na dzień'",
        Keys.ALL_ENTITIES: "Wszystkie encje",
        Keys.TOP_N_BY_VOLUME: "Top N wg wolumenu",
        Keys.BY_PRODUCT_TYPE: "Wg typu produktu",
        Keys.AUTO_SELECT: "Auto (wybór wg typu)",
        Keys.NUMBER_TOP_ENTITIES: "Liczba top encji",
        Keys.PRODUCT_TYPES: "Typy Produktów",
        Keys.FILTER_BY_MODEL: "Filtruj wg Modelu (opcjonalnie)",
        Keys.FORECAST_METHOD_HELP: "Auto wybiera metodę na podstawie typu produktu. AutoARIMA automatycznie znajduje najlepsze parametry ARIMA.",
        Keys.DATE_CAPTION: "**Data generowania**: Tylko sprzedaż do tej daty jest używana do generowania prognozy. **Data porównania**: Rzeczywista sprzedaż z okresu prognozy do tej daty jest wczytywana do porównania dokładności.",

        Keys.MANAGE_MODELS: "Zarządzaj Modelami",
        Keys.TRAINING_PARAMS: "Parametry Treningu",
        Keys.MODELS_TO_EVALUATE: "**Modele do Ewaluacji**",
        Keys.ML_MODELS: "Modele ML",
        Keys.STATISTICAL_MODELS: "Modele Statystyczne",
        Keys.ENTITY_LEVEL: "Poziom Encji",
        Keys.TOP_N_ENTITIES: "Top N encji wg wolumenu",
        Keys.CV_METRIC: "Metryka CV",
        Keys.CV_SPLITS: "Podziały CV",
        Keys.CV_TEST_SIZE: "Rozmiar Testu CV (miesiące)",
        Keys.INCLUDE_STATISTICAL: "Uwzględnij Statystyczne (Holt-Winters, SARIMA)",
        Keys.TRAINING_COMPLETE: "Trening zakończony! {count} modeli wytrenowanych, {saved} zapisanych.",

        Keys.QUERY_DATA: "Zapytaj o dane używając języka naturalnego (angielski lub polski)",
        Keys.DB_MODE_INFO: "Tryb bazy danych: zapytania wykonywane przez SQL na PostgreSQL",
        Keys.FILE_MODE_INFO: "Tryb plikowy: zapytania wykonywane przez SQL na DuckDB",
        Keys.ENTER_QUERY: "Wprowadź zapytanie",
        Keys.RESULTS: "Wyniki",
        Keys.QUERY_PLACEHOLDER: "np. sprzedaż modelu CH086 ostatnie 2 lata",
        Keys.QUERY_INTERPRETATION: "Interpretacja zapytania i SQL",
        Keys.EXAMPLE_QUERIES: "📚 Przykładowe zapytania",
        Keys.CLICK_TO_COPY: "Kliknij na dowolny przykład, aby skopiować do schowka:",
        Keys.LOW_CONFIDENCE: "Niska pewność - wyniki mogą nie odpowiadać Twoim intencjom",
        Keys.COULD_NOT_UNDERSTAND: "Nie można zrozumieć zapytania. Proszę spróbować przeformułować.",
        Keys.NO_RESULTS: "Nie znaleziono wyników",

        Keys.INPUT_MODEL_COLOR: "Model + Kolor (np. AB123RD):",
        Keys.INPUT_MODEL: "Model (np. AB123):",
        Keys.ENTER_CODE_PLACEHOLDER: "Wpisz kod...",
        Keys.NOT_FOUND_IN_SALES: "'{id}' nie znaleziono w danych sprzedaży",
        Keys.NO_DATA_FOR_SUMMARY: "Brak danych dla tabeli podsumowania",
        Keys.TYPE_TO_FILTER: "Wpisz, aby filtrować...",
        Keys.ITEMS_AVAILABLE_SHORT: "📦 {count} pozycji dostępnych",
        Keys.ERR_SALES_ANALYSIS: "Błąd w Analizie Sprzedaży: {error}",
        Keys.ERR_WEEKLY_ANALYSIS: "Błąd w Analizie Tygodniowej: {error}",
        Keys.ERR_TOP_SALES_REPORT: "Błąd generowania RAPORTU TOP SPRZEDAŻY: {error}",
        Keys.ERR_TOP_5_BY_TYPE: "Błąd generowania Top 5 wg Typu: {error}",
        Keys.ERR_GENERATING_WEEKLY: "Błąd generowania analizy tygodniowej: {error}",
        Keys.WEEKLY_SALES_BY_MODEL: "Tygodniowa Sprzedaż wg Modelu",
        Keys.GENERATING_WEEKLY: "Generowanie analizy tygodniowej...",
        Keys.ERR_MONTHLY_ANALYSIS: "Błąd w Analizie Miesięcznej: {error}",
        Keys.BTN_GENERATE_MONTHLY_YOY: "Generuj Miesięczną Analizę R/R",
        Keys.CALCULATING_YOY: "Obliczanie porównania rok do roku...",
        Keys.ANALYSIS_SUCCESS: "Analiza wygenerowana pomyślnie!",
        Keys.ANALYSIS_FAILED: "Analiza nie powiodła się: {error}",
        Keys.PRIOR_PERIOD: "Poprzedni Okres",
        Keys.UNKNOWN: "Nieznany",
        Keys.NEW: "Nowy",
        Keys.AGE_GROUP: "Grupa Wiekowa",
        Keys.CATEGORY: "Kategoria",
        Keys.ERR_ORDER_RECOMMENDATIONS: "Błąd w Rekomendacjach Zamówień: {error}",
        Keys.ORDER_RECOMMENDATIONS_DESC: "Automatycznie priorytetyzuj modele i kolory do zamówienia na podstawie stanów magazynowych, prognoz i progów ROP.",
        Keys.RECOMMENDATION_PARAMS_HELP: "Dostosuj te parametry, aby zoptymalizować algorytm priorytetyzacji",
        Keys.CURRENT_WEIGHTS_SUM: "Suma wag: {sum:.2f} (idealnie 1.0)",
        Keys.MODEL_METADATA_NOT_AVAILABLE: "Metadane modeli niedostępne. Wyświetlanie wszystkich pozycji.",
        Keys.NO_ML_FORECASTS: "Brak prognoz ML. Najpierw wytrenuj modele w zakładce 10.",
        Keys.CALCULATING_PRIORITIES: "Obliczanie priorytetów zamówień...",
        Keys.ANALYZED_N_SKUS: "Przeanalizowano {count} SKU używając prognozy {source} - przewiń w dół, aby zobaczyć wyniki",
        Keys.ERR_GENERATING_RECOMMENDATIONS: "Błąd generowania rekomendacji: {error}",
        Keys.ITEMS_SELECTED: "{count} pozycji wybranych",
        Keys.NAVIGATE_ORDER_CREATION: "Przejdź do zakładki 'Tworzenie Zamówień', aby zakończyć zamówienie",
        Keys.SELECT_ITEMS_TO_ORDER: "Wybierz pozycje powyżej, aby utworzyć zamówienie",
        Keys.FULL_MODEL_COLOR_SUMMARY: "Pełne Podsumowanie Priorytetów Model+Kolor",
        Keys.DOWNLOAD_PRIORITY_REPORT: "📥 Pobierz Pełny Raport Priorytetów (poziom SKU)",
        Keys.NO_DATA: "Brak danych",
        Keys.HELP_WEIGHT_STOCKOUT: "Waga ryzyka braku towaru w obliczaniu priorytetu. Wyższe wartości priorytetyzują pozycje zagrożone brakiem.",
        Keys.HELP_WEIGHT_REVENUE: "Waga wpływu przychodów w obliczaniu priorytetu. Wyższe wartości priorytetyzują pozycje o wysokich przychodach.",
        Keys.HELP_WEIGHT_DEMAND: "Waga prognozy popytu w obliczaniu priorytetu. Wyższe wartości priorytetyzują pozycje o wysokim prognozowanym popycie.",
        Keys.HELP_MULT_NEW: "Mnożnik dla nowych produktów (< 12 miesięcy). Wartości > 1.0 zwiększają priorytet.",
        Keys.HELP_MULT_SEASONAL: "Mnożnik dla produktów sezonowych (CV > 1.0).",
        Keys.HELP_MULT_REGULAR: "Mnożnik dla produktów regularnych (0.6 < CV < 1.0).",
        Keys.HELP_MULT_BASIC: "Mnożnik dla produktów podstawowych (CV < 0.6).",
        Keys.HELP_ZERO_PENALTY: "Wynik ryzyka dla SKU z zerowym stanem ORAZ prognozowanym popytem.",
        Keys.HELP_BELOW_ROP_PENALTY: "Maksymalny wynik ryzyka dla pozycji poniżej punktu zamawiania (ROP).",
        Keys.HELP_DEMAND_CAP: "Maksymalna wartość prognozy używana w obliczaniu priorytetu.",
        Keys.HELP_INCLUDE_FACILITIES: "Wybierz zakłady do UWZGLĘDNIENIA. Puste = uwzględnij wszystkie.",
        Keys.HELP_EXCLUDE_FACILITIES: "Wybierz zakłady do WYKLUCZENIA. Ma pierwszeństwo przed uwzględnieniem.",
        Keys.HELP_FORECAST_SOURCE: "Zewnętrzna używa wczytanego pliku prognozy. ML używa wytrenowanych modeli ML z zakładki 10.",
        Keys.HELP_SELECT_ITEMS: "Wybierz pozycje do utworzenia zamówienia",
        Keys.NEW_PRODUCTS: "Nowe Produkty",
        Keys.STOCKOUT_RISK: "Ryzyko Braku Towaru",
        Keys.REVENUE_IMPACT: "Wpływ na Przychód",
        Keys.DEMAND_FORECAST: "Prognoza Popytu",
        Keys.ZERO_STOCK_PENALTY: "Kara za Zerowy Stan",
        Keys.BELOW_ROP_PENALTY: "Maks. Kara Poniżej ROP",
        Keys.DEMAND_CAP: "Limit Popytu",
        Keys.TOP_PRIORITY_TO_ORDER: "Pozycje o Najwyższym Priorytecie do Zamówienia",
        Keys.SHOWING_TOP_MODEL_COLOR: "Pokazuję {count} najważniejszych kombinacji MODEL+KOLOR wg priorytetu",
        Keys.SELECT: "Wybierz",
        Keys.LOAD_STOCK_AND_FORECAST: "Załaduj dane stanów i prognoz w zakładce 1, aby użyć tej funkcji.",

        Keys.TITLE_MANUAL_ORDER_CREATION: "📝 Ręczne Tworzenie Zamówienia",
        Keys.TITLE_SIZE_DISTRIBUTION: "Rozkład Rozmiarów",
        Keys.TITLE_SIZE_COLOR_TABLE: "Tabela Rozmiar x Kolor Produkcji",
        Keys.TITLE_ZERO_STOCK_PRODUCTION: "Produkcja przy Zerowym Stanie (Kolor x Rozmiar)",
        Keys.COLOR_FILTER_ALL: "Wszystkie kolory",
        Keys.COLOR_FILTER_MODEL: "Kolory modelu",
        Keys.COLOR_FILTER_ACTIVE: "Tylko aktywne",
        Keys.TITLE_FACILITY_CAPACITY: "🏭 Pojemność Zakładów",
        Keys.TITLE_EDIT_CAPACITY: "⚙️ Edycja Miesięcznej Pojemności",

        Keys.ENTER_MODEL_CODE_HELP: "Wprowadź dowolny kod modelu (5 znaków), aby utworzyć zamówienie.",
        Keys.ENTER_MODEL_PLACEHOLDER: "np. CH031",
        Keys.LOADING_DATA_FOR_MODEL: "Ładowanie danych dla modelu {model}...",
        Keys.ORDER_FOR_MODEL: "Zamówienie dla Modelu: {model}",
        Keys.NO_RECOMMENDATIONS_DATA: "Brak danych rekomendacji dla {model}-{color}",
        Keys.SELECT_MODEL_TO_PROCESS: "Wybrane pozycje obejmują {count} modeli. Proszę wybrać jeden model do przetworzenia.",
        Keys.SELECT_MODEL_LABEL: "Wybierz model do utworzenia zamówienia:",

        Keys.LABEL_PRIMARY_FACILITY: "Zakład Główny",
        Keys.LABEL_SECONDARY_FACILITY: "Zakład Pomocniczy",
        Keys.LABEL_MATERIAL_TYPE: "Rodzaj Materiału",
        Keys.LABEL_MATERIAL_WEIGHT: "Gramatura",
        Keys.LABEL_MODEL_CODE: "Kod Modelu",
        Keys.LABEL_PRODUCT_NAME: "Nazwa Produktu",
        Keys.LABEL_PARSING_PDF: "Parsowanie PDF...",
        Keys.LABEL_CAPACITY: "Pojemność",
        Keys.LABEL_ORDERS: "Zamówienia",
        Keys.LABEL_TOTAL_QTY: "Łączna Ilość",
        Keys.LABEL_UTILIZATION: "Wykorzystanie",

        Keys.PLACEHOLDER_MODEL_CODE: "np. ABC12",
        Keys.PLACEHOLDER_PRODUCT_NAME: "np. Bluza",
        Keys.PLACEHOLDER_FACILITY: "np. Sieradz",
        Keys.PLACEHOLDER_OPERATION: "np. szycie i składanie",
        Keys.PLACEHOLDER_MATERIAL: "np. DRES PĘTELKA 280 GSM",

        Keys.HELP_ORDER_DATE: "Data złożenia zamówienia",
        Keys.HELP_UPLOAD_PDF: "Wgraj plik PDF zawierający szczegóły zamówienia",
        Keys.HELP_ARCHIVE_CHECKBOX: "Zaznacz, aby zarchiwizować to zamówienie",
        Keys.HELP_CAPACITY_EDITOR: "Ustaw miesięczną zdolność produkcyjną dla każdego zakładu",

        Keys.BTN_CREATE_FROM_PDF: "Utwórz Zamówienie z PDF",
        Keys.BTN_DOWNLOAD_ORDER_CSV: "📥 Pobierz CSV",
        Keys.BTN_COPY_TABLE: "📋 Kopiuj tabelę do schowka",
        Keys.BTN_SAVE_CAPACITY: "💾 Zapisz Pojemność",
        Keys.BTN_ARCHIVE_N_ORDERS: "Archiwizuj {count} Zamówień",

        Keys.MSG_ORDER_SAVED: "Zamówienie {order_id} zapisane pomyślnie!",
        Keys.MSG_ORDER_SAVE_FAILED: "Nie udało się zapisać zamówienia",
        Keys.MSG_CAPACITY_SAVED: "Ustawienia pojemności zapisane",
        Keys.MSG_NO_FACILITY_DATA: "Brak danych o zakładach w aktywnych zamówieniach.",
        Keys.MSG_NO_CAPACITY_DATA: "Brak aktywnych zamówień do obliczenia pojemności zakładów.",
        Keys.MSG_COULD_NOT_LOAD_SALES: "Nie udało się wczytać historii sprzedaży: {error}",
        Keys.MSG_ENTER_MODEL_CODE: "Proszę wprowadzić kod modelu",

        Keys.ERR_ORDER_CREATION: "Błąd w Tworzeniu Zamówienia: {error}",
        Keys.ERR_ORDER_TRACKING: "Błąd w Śledzeniu Zamówień: {error}",
        Keys.ERR_SAVING_ORDER: "Błąd podczas zapisywania zamówienia: {error}",

        Keys.CAPTION_SIZE_DISTRIBUTION: "Wszystkie kolory łącznie + historia sprzedaży z ostatnich 3 miesięcy",
        Keys.CAPTION_TOTAL_QTY_FACILITIES: "📊 Łączna ilość we wszystkich zakładach: {total:,}",

        Keys.NA: "N/D",
        Keys.PRODUCED_SIZE_QTY: "Wyprodukowane (Rozmiar:Ilość)",

        Keys.TITLE_SIZE_PATTERN_OPTIMIZER: "Optymalizator Wzorców Rozmiarów",
        Keys.LOADED_SALES_HISTORY: "Wczytano historię sprzedaży dla {model} (wszystkie kolory)",
        Keys.NO_SALES_DATA_FOR_MODEL: "Nie znaleziono danych sprzedaży dla {model}",
        Keys.SIZES: "Rozmiary",
        Keys.PATTERNS: "Wzorce",
        Keys.CREATE_EDIT_PATTERN_SET: "Utwórz/Edytuj Zestaw Wzorców",
        Keys.USING_ALGORITHM: "Używany algorytm: **{algorithm}** (zmień w panelu bocznym)",
        Keys.ERR_NO_PATTERN_SETS: "Proszę dodać co najmniej jeden zestaw wzorców przed optymalizacją!",
        Keys.ERR_SELECT_PATTERN_SET: "Proszę wybrać aktywny zestaw wzorców!",
        Keys.ERR_ENTER_QUANTITIES: "Proszę wprowadzić ilości do optymalizacji!",
        Keys.ERR_PATTERN_SET_NOT_FOUND: "Nie znaleziono aktywnego zestawu wzorców!",
        Keys.NO_PATTERNS_ALLOCATED: "Nie przydzielono wzorców",
        Keys.SIZE: "Rozmiar",
        Keys.SALES: "sprzedaż",
        Keys.EXCLUDED: "wykluczony",
        Keys.ERR_PATTERN_OPTIMIZER: "Błąd w Optymalizatorze Wzorców: {error}",

        Keys.BTN_GENERATE_ACCURACY_REPORT: "Generuj Raport Dokładności",
        Keys.BTN_CLEAR_RESULTS: "Wyczyść Wyniki",
        Keys.ANALYSIS_PARAMETERS: "Parametry Analizy",
        Keys.HELP_ANALYSIS_START: "Początek okresu do analizy dokładności",
        Keys.HELP_ANALYSIS_END: "Koniec okresu do analizy dokładności",
        Keys.HELP_FORECAST_LOOKBACK: "Ile miesięcy przed rozpoczęciem analizy szukać prognozy",
        Keys.ERR_ANALYSIS_PERIOD_TOO_SHORT: "Okres analizy ({days} dni) musi wynosić co najmniej {min_days} dni (aktualny lead time: {lead_time} miesięcy)",
        Keys.INFO_ANALYSIS_PERIOD: "Analizuję {days} dni. Używam prognozy wygenerowanej około {date}",
        Keys.LOADING_ACCURACY_METRICS: "Ładowanie danych i obliczanie metryk dokładności...",
        Keys.ERR_NO_SALES_FOR_PERIOD: "Nie znaleziono danych sprzedaży dla wybranego okresu",
        Keys.ERR_NO_FORECAST_FOUND: "Nie znaleziono prognozy dla około {months} miesięcy przed {date}",
        Keys.WARN_NO_STOCK_HISTORY: "Nie znaleziono historii stanów. Analiza braków będzie ograniczona.",
        Keys.ERR_ACCURACY_CALCULATION: "Nie można obliczyć metryk dokładności. Sprawdź zgodność danych.",
        Keys.MSG_ACCURACY_SUCCESS: "Raport dokładności wygenerowany pomyślnie!",
        Keys.INFO_USING_FORECAST: "Używam prognozy wygenerowanej: **{date}**",
        Keys.STOCKOUT_DAYS: "{days:,} dni braku towaru",
        Keys.FCST_VS_ACT: "Prognoza: {forecast:,} | Rzeczywista: {actual:,}",
        Keys.ACCURACY_BY_ITEM: "Dokładność wg Pozycji",
        Keys.SEARCH_ENTITY: "Szukaj {entity}",
        Keys.SEARCH_ENTITY_PLACEHOLDER: "Wpisz {entity} lub część...",
        Keys.SHOWING_N_OF_M_ITEMS: "Pokazuję {n} z {m} pozycji",
        Keys.DOWNLOAD_ACCURACY_REPORT: "Pobierz Raport Dokładności (CSV)",
        Keys.ACCURACY_BY_PRODUCT_TYPE: "Dokładność wg Typu Produktu",
        Keys.MAPE_BY_PRODUCT_TYPE: "MAPE wg Typu Produktu",
        Keys.ACCURACY_TREND_OVER_TIME: "Trend Dokładności w Czasie",
        Keys.CHART_WEEK: "Tydzień",
        Keys.CHART_MAPE_PCT: "MAPE (%)",
        Keys.ITEM_DETAIL_VIEW: "Widok Szczegółów Pozycji",
        Keys.SELECT_ENTITY_DETAILS: "Wybierz {entity} aby zobaczyć szczegóły",
        Keys.DAYS_ANALYZED: "Analizowane Dni",
        Keys.DAYS_STOCKOUT: "Dni Braku Towaru",
        Keys.FORECAST_TOTAL: "Suma Prognozy",
        Keys.ACTUAL_TOTAL: "Suma Rzeczywista",
        Keys.WARN_MISSED_OPPORTUNITY: "Utracona szansa: {units:,} szt. podczas {days} dni braku towaru",
        Keys.ERR_FORECAST_ACCURACY: "Błąd w Dokładności Prognozy: {error}",
        Keys.CAPTION_FORECAST_ACCURACY: "Porównaj historyczne prognozy z rzeczywistą sprzedażą, aby ocenić jakość prognozy",
        Keys.MSG_NO_SALES_DATA_LOAD: "Brak dostępnych danych sprzedaży. Proszę najpierw wczytać dane sprzedaży.",

        Keys.FC_ERROR_IN_TAB: "Błąd w Porównaniu Prognoz: {error}",
        Keys.FC_PARAMETERS: "Parametry",
        Keys.FC_MODEL_FASTER: "Model (szybszy)",
        Keys.FC_SKU_SLOWER: "SKU (wolniejszy)",
        Keys.FC_MOVING_AVG: "Średnia Ruchoma",
        Keys.FC_EXP_SMOOTHING: "Wygładzanie Wykładnicze",
        Keys.FC_HOLT_WINTERS: "Holt-Winters",
        Keys.FC_SARIMA: "SARIMA",
        Keys.FC_AUTO_ARIMA: "AutoARIMA (sktime)",
        Keys.FC_GENERATE_AS_OF_HELP: "Symuluj generowanie prognozy jakby było to w tej dacie. Tylko dane sprzedaży do tej daty zostaną użyte.",
        Keys.FC_COMPARE_AS_OF_HELP: "Data, do której rzeczywista sprzedaż jest wczytywana do porównania. Ustaw na przyszłą datę względem daty generowania, aby zobaczyć dokładność prognozy.",
        Keys.FC_LOADING_DATA: _PL_LOADING_DATA,
        Keys.FC_LOADING_MONTHLY_AGG: "Wczytywanie agregacji miesięcznych...",
        Keys.FC_NO_MONTHLY_AGG: "Brak dostępnych danych agregacji miesięcznych",
        Keys.FC_NO_DATA_BEFORE_DATE: "Brak danych przed datą {date}",
        Keys.FC_LOADING_FORECASTS: "Wczytywanie prognoz...",
        Keys.FC_NO_EXTERNAL_FORECAST: "Brak zewnętrznych danych prognozy. Zostaną wygenerowane tylko prognozy wewnętrzne.",
        Keys.FC_LOADING_SALES: "Wczytywanie danych sprzedaży do porównania...",
        Keys.FC_NO_SALES_FOR_COMPARISON: "Brak danych sprzedaży dla okresu porównania ({start} do {end}). Wartości rzeczywiste będą zerowe.",
        Keys.FC_PREPARING_ENTITIES: "Przygotowywanie encji...",
        Keys.FC_NO_ENTITIES_FOUND: "Nie znaleziono encji pasujących do kryteriów filtra",
        Keys.FC_PROCESSING_ENTITIES: "Przetwarzanie {count} encji (dane do {date})...",
        Keys.FC_GENERATING_FORECASTS: "Generowanie prognoz wewnętrznych...",
        Keys.FC_FORECASTING_PROGRESS: "Prognozowanie {current}/{total}: {entity}",
        Keys.FC_CALCULATING_METRICS: "Obliczanie metryk porównania...",
        Keys.FC_DONE: "Gotowe!",
        Keys.FC_NO_INTERNAL_FORECASTS: "Nie udało się wygenerować żadnych prognoz wewnętrznych",
        Keys.FC_COMPARISON_COMPLETE: "Porównanie zakończone! Przetworzono {success} encji pomyślnie. Wygenerowano na dzień {gen_date}, porównano ze sprzedażą do {comp_date}.",
        Keys.FC_ENTITIES_FAILED: "{count} encji nie udało się prognozować",
        Keys.FC_ERROR: "Błąd: {error}",
        Keys.FC_FORECAST_INFO: "Prognoza wygenerowana 'na dzień': {gen_date} | Okres prognozy: {start} | Dane porównania do: {end}",
        Keys.FC_FORECAST_PERIOD: "Okres prognozy: {start} do {end}",
        Keys.FC_OVERALL_SUMMARY: "Ogólne Podsumowanie Porównania",
        Keys.FC_INTERNAL_MAPE: "Wewnętrzny MAPE",
        Keys.FC_EXTERNAL_MAPE: "Zewnętrzny MAPE",
        Keys.FC_MORE_ACCURATE: "Dokładniejszy",
        Keys.FC_INTERNAL_WINS: "Wewnętrzny ({count})",
        Keys.FC_EXTERNAL_WINS: "Zewnętrzny ({count})",
        Keys.FC_TIE: "Remis",
        Keys.FC_AVG_IMPROVEMENT: "Śr. Poprawa",
        Keys.FC_METHODS_USED: "Użyte metody: {methods}",
        Keys.FC_WINNER_BY_TYPE: "Rozkład Zwycięzców wg Typu Produktu",
        Keys.FC_NO_TYPE_BREAKDOWN: "Brak podziału wg typu",
        Keys.FC_ALL_FORECAST_ITEMS: "Wszystkie Pozycje Prognozy",
        Keys.FC_NO_FORECAST_DATA: "Brak danych prognozy",
        Keys.FC_VIEW_ALL_ITEMS: "Zobacz Wszystkie Pozycje Prognozy",
        Keys.FC_SEARCH_ENTITY: "Szukaj wg ID Encji",
        Keys.FC_ORDER: "Kolejność",
        Keys.FC_TOTAL_ROWS: "Łącznie wierszy: {count}",
        Keys.FC_DOWNLOAD_ALL_FORECASTS: "Pobierz Wszystkie Prognozy (CSV)",
        Keys.FC_DETAILED_COMPARISON: "Szczegółowe Porównanie",
        Keys.FC_NO_COMPARISON_DATA: "Brak danych porównania",
        Keys.FC_IMPROVEMENT: "Poprawa",
        Keys.FC_DOWNLOAD_FULL_REPORT: "Pobierz Pełny Raport (CSV)",
        Keys.FC_ENTITY_DETAIL_CHART: "Wykres Szczegółów Encji",
        Keys.FC_NO_DATA_FOR_CHART: "Brak danych porównania do wykresu",
        Keys.FC_SELECT_ENTITY: "Wybierz Encję",
        Keys.FC_CHART_ACTUAL: "Rzeczywisty",
        Keys.FC_CHART_INTERNAL: "Prognoza Wewnętrzna",
        Keys.FC_CHART_EXTERNAL: "Prognoza Zewnętrzna",
        Keys.FC_CHART_TITLE: "Porównanie Prognoz: {entity}",
        Keys.FC_CHART_MONTH: "Miesiąc",
        Keys.FC_SAVE_FORECAST: "Zapisz Prognozę",
        Keys.FC_NO_FORECAST_TO_SAVE: "Brak danych prognozy do zapisu",
        Keys.FC_NOTES_OPTIONAL: "Notatki (opcjonalnie)",
        Keys.FC_NOTES_PLACEHOLDER: "np. Miesięczne porównanie",
        Keys.FC_SAVE_TO_HISTORY: "Zapisz Prognozę do Historii",
        Keys.FC_FORECAST_SAVED: "Prognoza zapisana! ID partii: {batch_id}...",
        Keys.FC_ERROR_SAVING: "Błąd zapisu prognozy: {error}",
        Keys.FC_HISTORICAL_INTERNAL: "Historyczne Prognozy Wewnętrzne",
        Keys.FC_NO_HISTORICAL: "Nie znaleziono historycznych prognoz. Najpierw wygeneruj i zapisz prognozę.",
        Keys.FC_SELECT_HISTORICAL: "Wybierz Historyczną Prognozę",
        Keys.FC_ENTITY_TYPE: "Typ Encji",
        Keys.FC_HORIZON: "{months} miesięcy",
        Keys.FC_SUCCESS: "Sukces",
        Keys.FC_FAILED: "Nieudane",
        Keys.FC_METHODS: "Metody: {methods}",
        Keys.FC_NOTES: "Notatki: {notes}",
        Keys.FC_ANALYSIS_SETTINGS: "Ustawienia Analizy",
        Keys.FC_FORECAST_COVERS: "Prognoza obejmuje okresy: {start} do {end}",
        Keys.FC_ANALYZE_AS_OF: "Analizuj 'na dzień'",
        Keys.FC_ANALYZE_AS_OF_HELP: "Wybierz datę w przeszłości, aby porównać prognozę z rzeczywistą sprzedażą, która nastąpiła po wygenerowaniu prognozy",
        Keys.FC_SET_AS_OF_INFO: "Ustaw datę 'na dzień', aby przeanalizować historyczną dokładność. Dane sprzedaży zostaną wczytane od okresu prognozy do tej daty.",
        Keys.FC_LOAD_COMPARE: "Wczytaj i Porównaj",
        Keys.FC_DELETE: "Usuń",
        Keys.FC_FORECAST_DELETED: "Prognoza usunięta",
        Keys.FC_DELETE_FAILED: "Nie udało się usunąć prognozy",
        Keys.FC_FAILED_LOAD: "Nie udało się wczytać danych prognozy",
        Keys.FC_NO_SALES_FOR_PERIOD: "Brak danych sprzedaży dla wybranego okresu. Wartości rzeczywiste będą zerowe.",
        Keys.FC_HISTORICAL_LOADED: "Historyczna prognoza wczytana! Dane sprzedaży od {start} do {end}",
        Keys.FC_ASCENDING: "Rosnąco",
        Keys.FC_DESCENDING: "Malejąco",
        Keys.FC_COL_ENTITY: "Encja",
        Keys.FC_COL_PERIOD: "Okres",
        Keys.FC_COL_INTERNAL_FORECAST: "Prognoza Wewnętrzna",
        Keys.FC_COL_EXTERNAL_FORECAST: "Prognoza Zewnętrzna",
        Keys.FC_COL_ACTUAL_SALES: "Rzeczywista Sprzedaż",
        Keys.FC_COL_METHOD: "Metoda",
        Keys.FC_COL_MONTHS: "Miesiące",
        Keys.FC_COL_ACTUAL_VOLUME: "Rzeczywisty Wolumen",
        Keys.FC_COL_INT_MAPE: "Wewn MAPE",
        Keys.FC_COL_EXT_MAPE: "Zewn MAPE",
        Keys.FC_COL_WINNER: "Zwycięzca",
        Keys.FC_COL_TYPE: "Typ",
        Keys.FC_COL_TOTAL: "Suma",
        Keys.FC_COL_INTERNAL_WINS: "Wygrane Wewn.",
        Keys.FC_COL_EXTERNAL_WINS: "Wygrane Zewn.",
        Keys.FC_COL_TIES: "Remisy",
        Keys.FC_COL_INTERNAL_WIN_PCT: "% Wygranych Wewn.",
        Keys.FC_COL_AVG_INT_MAPE: "Śr. Wewn. MAPE",
        Keys.FC_COL_AVG_EXT_MAPE: "Śr. Zewn. MAPE",
        Keys.FC_CLEAR_RESULTS: "Wyczyść Wyniki",

        Keys.ML_ERROR_IN_TAB: "Błąd w Prognozie ML: {error}",
        Keys.ML_TRAIN_DESCRIPTION: "Trenuj modele ML z automatycznym doborem dla każdej encji",
        Keys.ML_TAB_TRAIN: "Trenuj Modele",
        Keys.ML_TAB_GENERATE: "Generuj Prognozy",
        Keys.ML_TAB_MANAGE: "Zarządzaj Modelami",
        Keys.ML_LOADING_DATA: _PL_LOADING_DATA,
        Keys.ML_LOADING_MONTHLY_AGG: "Wczytywanie agregacji miesięcznych...",
        Keys.ML_NO_MONTHLY_AGG: "Brak dostępnych danych agregacji miesięcznych",
        Keys.ML_LOADING_SKU_STATS: "Wczytywanie statystyk SKU...",
        Keys.ML_PREPARING_ENTITIES: "Przygotowywanie encji...",
        Keys.ML_NO_ENTITIES_FOUND: "Nie znaleziono encji pasujących do kryteriów",
        Keys.ML_TRAINING_FOR_ENTITIES: "Trenowanie modeli dla {count} encji...",
        Keys.ML_TRAINING_PROGRESS: "Trenowanie {current}/{total}: {entity}",
        Keys.ML_TRAINING_MODELS: "Trenowanie modeli...",
        Keys.ML_SAVING_MODELS: "Zapisywanie modeli...",
        Keys.ML_TRAINING_ERROR: "Błąd treningu: {error}",
        Keys.ML_TRAINING_RESULTS: "Wyniki Treningu",
        Keys.ML_TOTAL_ENTITIES: "Łącznie Encji",
        Keys.ML_AVG_CV_SCORE: "Śr. Wynik CV",
        Keys.ML_MODEL_DISTRIBUTION: "Rozkład Modeli",
        Keys.ML_BEST_MODEL_SELECTION: "Wybór Najlepszego Modelu",
        Keys.ML_FORECAST_PREVIEW: "Podgląd Prognozy",
        Keys.ML_COL_ENTITY: "Encja",
        Keys.ML_COL_MODEL: "Model",
        Keys.ML_COL_CV_SCORE: "Wynik CV",
        Keys.ML_COL_TOTAL_FORECAST: "Suma Prognozy",
        Keys.ML_DOWNLOAD_FORECASTS: "Pobierz Prognozy (CSV)",
        Keys.ML_GENERATE_FROM_SAVED: "Generuj Prognozy z Zapisanych Modeli",
        Keys.ML_NO_TRAINED_MODELS: "Nie znaleziono wytrenowanych modeli. Najpierw wytrenuj modele w zakładce 'Trenuj Modele'.",
        Keys.ML_MODELS_AVAILABLE: "{count} wytrenowanych modeli dostępnych",
        Keys.ML_ENTITY_FILTER: "Filtr Encji (opcjonalnie)",
        Keys.ML_GENERATING_FORECASTS: "Generowanie prognoz...",
        Keys.ML_NO_MODELS_MATCHING: "Nie znaleziono modeli pasujących do filtra",
        Keys.ML_COULD_NOT_LOAD_AGG: "Nie udało się wczytać agregacji miesięcznych",
        Keys.ML_GENERATING_PROGRESS: "Generowanie {current}/{total}: {entity}",
        Keys.ML_GENERATED_FORECASTS: "Wygenerowano prognozy dla {count} encji",
        Keys.ML_NO_FORECASTS_GENERATED: "Nie wygenerowano żadnych prognoz",
        Keys.ML_MANAGE_TITLE: "Zarządzaj Wytrenowanymi Modelami",
        Keys.ML_NO_MODELS_FOUND: "Nie znaleziono wytrenowanych modeli.",
        Keys.ML_TOTAL_MODELS: "Łącznie Modeli",
        Keys.ML_MOST_COMMON_MODEL: "Najpopularniejszy Model",
        Keys.ML_SEARCH_ENTITY: "Szukaj Encji",
        Keys.ML_FILTER_BY_TYPE: "Filtruj wg Typu Modelu",
        Keys.ML_ALL: "Wszystkie",
        Keys.ML_SHOWING_MODELS: "Wyświetlanie {count} modeli",
        Keys.ML_COL_TYPE: "Typ",
        Keys.ML_COL_TRAINED: "Wytrenowany",
        Keys.ML_MODEL_DETAILS: "Szczegóły Modelu",
        Keys.ML_NO_MODELS_TO_DISPLAY: "Brak modeli do wyświetlenia",
        Keys.ML_SELECT_FOR_DETAILS: "Wybierz Encję dla Szczegółów",
        Keys.ML_MODEL_TYPE: "Typ Modelu",
        Keys.ML_TRAINED_AT: "Wytrenowany",
        Keys.ML_CV_METRIC: "Metryka CV",
        Keys.ML_PRODUCT_TYPE: "Typ Produktu",
        Keys.ML_FEATURE_IMPORTANCE: "Ważność Cech",
        Keys.ML_TOP_FEATURES: "Najważniejsze Cechy",
        Keys.ML_DELETE_MODEL_FOR: "Usuń Model dla {entity}",
        Keys.ML_MODEL_DELETED: "Usunięto model dla {entity}",
        Keys.ML_DELETE_FAILED: "Nie udało się usunąć modelu",
        Keys.ML_BULK_ACTIONS: "Akcje Zbiorcze",
        Keys.ML_DELETE_ALL_MODELS: "Usuń Wszystkie Modele",
        Keys.ML_DELETED_MODELS: "Usunięto {count} modeli",
        Keys.ML_EXPORT_MODEL_REPORT: "Eksportuj Raport Modeli",
        Keys.ML_DOWNLOAD_REPORT: "Pobierz Raport",
        Keys.ML_MODEL_DETAILED: "Model (szybszy)",
        Keys.ML_SKU_DETAILED: "SKU (szczegółowy)",
        Keys.ML_ENTITIES_FAILED: "{count} encji nieudanych",
        Keys.ML_SELECT_ENTITY_DETAILS: "Wybierz Encję dla Szczegółów",
        Keys.ML_ENTITY: "Encja",
        Keys.ML_CV_SCORE: "Wynik CV",

        Keys.NLQ_QUERY: "Zapytanie",
        Keys.NLQ_PROCESSING: "Przetwarzanie zapytania...",
        Keys.NLQ_CONFIDENCE: "Pewność",
        Keys.NLQ_INTERPRETATION: "Interpretacja",
        Keys.NLQ_GENERATED_SQL: "Wygenerowany SQL",
        Keys.NLQ_DOWNLOAD_RESULTS: "Pobierz Wyniki (CSV)",
        Keys.NLQ_TITLE: "Zapytania w Języku Naturalnym",
        Keys.NLQ_CAPTION: "Zapytaj swoje dane używając języka naturalnego (angielski lub polski)",
        Keys.NLQ_DATABASE_MODE: "Tryb bazy danych: zapytania wykonywane przez SQL na PostgreSQL",
        Keys.NLQ_FILE_MODE: "Tryb plikowy: zapytania wykonywane przez SQL na DuckDB",
        Keys.NLQ_ENTER_QUERY: "Wprowadź zapytanie",
        Keys.NLQ_PLACEHOLDER: "np. sprzedaż modelu CH086 ostatnie 2 lata",
        Keys.NLQ_EXECUTE: "Wykonaj",
        Keys.NLQ_CLEAR: "Wyczyść",
        Keys.NLQ_COULD_NOT_UNDERSTAND: "Nie udało się zrozumieć zapytania. Spróbuj przeformułować.",
        Keys.NLQ_INTERPRETATION_SQL: "Interpretacja zapytania i SQL",
        Keys.NLQ_LOW_CONFIDENCE: "Niska pewność - wyniki mogą nie odpowiadać Twojej intencji",
        Keys.NLQ_NO_RESULTS: "Brak wyników",
        Keys.NLQ_RESULTS: "Wyniki",
        Keys.NLQ_ROWS: "Wierszy",
        Keys.NLQ_COLUMNS: "Kolumn",
        Keys.NLQ_EXAMPLE_QUERIES: "Przykładowe zapytania",
        Keys.NLQ_CLICK_EXAMPLE: "Kliknij na przykład, aby skopiować do schowka:",
        Keys.NLQ_ERROR_IN_TAB: "Błąd w Zapytaniach Języka Naturalnego: {error}",

        Keys.DISPLAY_LAST_YEAR: "Poprzedni Rok",
        Keys.DISPLAY_CHANGE: "Zmiana",
        Keys.DISPLAY_TOTAL_PATTERNS: "Łącznie Wzorców",
        Keys.DISPLAY_TOTAL_EXCESS: "Łącznie Nadwyżki",
        Keys.DISPLAY_COVERAGE: "Pokrycie",
        Keys.DISPLAY_DOWNLOAD_CSV: "Pobierz CSV",
        Keys.DISPLAY_MODEL: "Model",

        Keys.TASK_ADD_NEW: "Dodaj Nowe Zadanie",
        Keys.TASK_TITLE: "Tytuł",
        Keys.TASK_TITLE_PLACEHOLDER: "Krótki tytuł zadania...",
        Keys.TASK_DESCRIPTION: "Opis",
        Keys.TASK_DESCRIPTION_PLACEHOLDER: "Szczegółowy opis (obsługuje **pogrubienie**, *kursywę*, - listy)",
        Keys.TASK_DESCRIPTION_HELP: "Obsługuje Markdown: **pogrubienie**, *kursywa*, - listy punktowane, 1. listy numerowane",
        Keys.TASK_DUE_DATE: "Termin",
        Keys.TASK_PRIORITY: "Priorytet",
        Keys.TASK_PRIORITY_HIGH: "Wysoki",
        Keys.TASK_PRIORITY_MEDIUM: "Średni",
        Keys.TASK_PRIORITY_LOW: "Niski",
        Keys.TASK_STATUS_TODO: "Do Zrobienia",
        Keys.TASK_STATUS_IN_PROGRESS: "W Trakcie",
        Keys.TASK_STATUS_DONE: "Zrobione",
        Keys.TASK_ADD_BTN: "Dodaj Zadanie",
        Keys.TASK_DELETE_BTN: "Usuń",
        Keys.TASK_EDIT_BTN: "Edytuj",
        Keys.TASK_SAVE_BTN: "Zapisz",
        Keys.TASK_LIST: "Lista Zadań",
        Keys.TASK_KANBAN: "Tablica Kanban",
        Keys.TASK_FILTER_STATUS: "Filtruj wg Statusu",
        Keys.TASK_FILTER_PRIORITY: "Filtruj wg Priorytetu",
        Keys.TASK_FILTER_ALL: "Wszystkie",
        Keys.TASK_NO_TASKS: "Brak zadań. Dodaj pierwsze zadanie powyżej!",
        Keys.TASK_CREATED: "Utworzono",
        Keys.TASK_DUE: "Termin",
        Keys.ERR_TASK_PLANNER: "Błąd w Planerze Zadań: {error}",
        Keys.ERR_TASK_TITLE_REQUIRED: "Tytuł zadania jest wymagany",

        Keys.PROGRESS_LOADING_DATA: _PL_LOADING_DATA,
        Keys.PROGRESS_LOADING_SALES: "Ładowanie sprzedaży...",
        Keys.PROGRESS_LOADING_STOCK: "Ładowanie stanu magazynowego...",
        Keys.PROGRESS_LOADING_FORECAST: "Ładowanie prognozy...",
        Keys.PROGRESS_LOADING_METADATA: "Ładowanie metadanych...",
        Keys.PROGRESS_DONE: "Gotowe!",
    },
}


def get_tab_names() -> list[str]:
    return [
        t(Keys.TAB_TASK_PLANNER),
        t(Keys.TAB_SALES_ANALYSIS),
        t(Keys.TAB_PATTERN_OPTIMIZER),
        t(Keys.TAB_WEEKLY_ANALYSIS),
        t(Keys.TAB_MONTHLY_ANALYSIS),
        t(Keys.TAB_ORDER_RECOMMENDATIONS),
        t(Keys.TAB_ORDER_CREATION),
        t(Keys.TAB_ORDER_TRACKING),
        t(Keys.TAB_FORECAST_ACCURACY),
        t(Keys.TAB_FORECAST_COMPARISON),
        t(Keys.TAB_ML_FORECAST),
        t(Keys.TAB_NL_QUERY),
    ]
