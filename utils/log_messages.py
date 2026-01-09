from __future__ import annotations


class LogMsg:
    LOADED_RECORDS = "Loaded %d records"
    LOADED_ITEMS = "Loaded %d items"
    LOADED_SKUS = "Loaded %d SKUs"
    LOADED_MODELS = "Loaded %d models"
    LOADED_FILES = "Loaded %d files"
    FOUND_FILES = "Found %d files"
    PROCESSING_COMPLETE = "Processing complete: %d rows"
    VALIDATION_FAILED = "Validation failed: %s"
    FILE_NOT_FOUND = "File not found: %s"
    DIRECTORY_NOT_FOUND = "Directory not found: %s"

    OPTIMIZING_PATTERNS = "Optimizing patterns: %d sizes, %d patterns"
    OPTIMIZATION_RESULT = "Optimization result: %d patterns, %d excess"
    NO_SOLUTION_FOUND = "No solution found, using fallback"

    CALCULATING_STATS = "Calculating statistics for %d items"
    AGGREGATING_DATA = "Aggregating %d rows"
    MERGING_DATA = "Merging datasets: %d + %d rows"

    GENERATING_RECOMMENDATIONS = "Generating recommendations for %d items"
    RECOMMENDATIONS_COMPLETE = "Recommendations complete: %d priority items"

    LOADING_FROM_DB = "Loading from database: %s"
    LOADING_FROM_FILE = "Loading from file: %s"
    QUERY_RETURNED = "Query returned %d rows"

    CACHE_HIT = "Cache hit for %s"
    CACHE_MISS = "Cache miss for %s"

    FORECAST_LOADED = "Forecast loaded: %d records, %d SKUs"
    STOCK_LOADED = "Stock loaded: %d active items"
    SALES_LOADED = "Sales loaded: %d transactions"
    METADATA_LOADED = "Metadata loaded: %d models"

    PROJECTION_CALCULATED = "Projection calculated for %s"
    ACCURACY_CALCULATED = "Accuracy calculated: MAPE=%.1f%%"

    ORDER_CREATED = "Order created: %s"
    ORDER_SAVED = "Order saved: %s"

    INVALID_INPUT = "Invalid input: %s"
    PROCESSING_SKIPPED = "Processing skipped: %s"

    USING_SHEET = "Using sheet: %s"
    CONSOLIDATION_COMPLETE = "Consolidation complete: %d rows, %d orders, %d SKUs"


class LogLevel:
    INFO_THRESHOLD_ROWS = 1000
    INFO_THRESHOLD_FILES = 5
