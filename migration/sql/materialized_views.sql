-- Materialized Views for Fast Data Access
-- Created: 2025-11-26

-- =============================================================================
-- MATERIALIZED VIEWS
-- =============================================================================

-- View: Latest stock snapshot per SKU
CREATE MATERIALIZED VIEW mv_latest_stock AS
SELECT DISTINCT ON (sku)
    sku,
    model,
    product_name,
    net_price,
    gross_price,
    total_stock,
    available_stock,
    snapshot_date,
    import_timestamp
FROM stock_snapshots
WHERE is_active = TRUE
ORDER BY sku, snapshot_date DESC, import_timestamp DESC;

CREATE UNIQUE INDEX idx_mv_latest_stock_sku ON mv_latest_stock(sku);
CREATE INDEX idx_mv_latest_stock_model ON mv_latest_stock(model);


-- View: Latest forecast per SKU and forecast_date
CREATE MATERIALIZED VIEW mv_latest_forecast AS
SELECT DISTINCT ON (sku, forecast_date)
    sku,
    model,
    forecast_date,
    forecast_quantity,
    generated_date,
    import_timestamp
FROM forecast_data
ORDER BY sku, forecast_date, generated_date DESC, import_timestamp DESC;

CREATE UNIQUE INDEX idx_mv_latest_forecast_sku_date ON mv_latest_forecast(sku, forecast_date);
CREATE INDEX idx_mv_latest_forecast_sku ON mv_latest_forecast(sku);
CREATE INDEX idx_mv_latest_forecast_date ON mv_latest_forecast(forecast_date);


-- View: Valid monthly aggregations cache
CREATE MATERIALIZED VIEW mv_valid_monthly_aggs AS
SELECT
    entity_type,
    entity_id,
    year_month,
    total_quantity,
    total_revenue,
    transaction_count,
    unique_orders,
    avg_unit_price,
    computed_at
FROM cache_monthly_aggregations
WHERE is_valid = TRUE
  AND cache_version = (
      SELECT MAX(cache_version)
      FROM cache_monthly_aggregations cma2
      WHERE cma2.entity_type = cache_monthly_aggregations.entity_type
        AND cma2.entity_id = cache_monthly_aggregations.entity_id
        AND cma2.year_month = cache_monthly_aggregations.year_month
        AND cma2.is_valid = TRUE
  );

CREATE INDEX idx_mv_monthly_aggs_entity ON mv_valid_monthly_aggs(entity_type, entity_id);
CREATE INDEX idx_mv_monthly_aggs_year_month ON mv_valid_monthly_aggs(year_month);


-- View: Valid SKU statistics cache
CREATE MATERIALIZED VIEW mv_valid_sku_stats AS
SELECT
    entity_type,
    entity_id,
    months_with_sales,
    total_quantity,
    average_monthly_sales,
    standard_deviation,
    coefficient_of_variation,
    first_sale_date,
    product_type,
    safety_stock,
    reorder_point,
    z_score_used,
    lead_time_months,
    is_seasonal,
    seasonal_ss_in,
    seasonal_ss_out,
    seasonal_rop_in,
    seasonal_rop_out,
    last_2y_avg_monthly,
    computed_at,
    based_on_data_until,
    configuration_hash
FROM cache_sku_statistics
WHERE is_valid = TRUE
  AND cache_version = (
      SELECT MAX(cache_version)
      FROM cache_sku_statistics css2
      WHERE css2.entity_type = cache_sku_statistics.entity_type
        AND css2.entity_id = cache_sku_statistics.entity_id
        AND css2.is_valid = TRUE
  );

CREATE INDEX idx_mv_sku_stats_entity ON mv_valid_sku_stats(entity_type, entity_id);
CREATE INDEX idx_mv_sku_stats_type ON mv_valid_sku_stats(product_type);


-- View: Valid order priorities cache
CREATE MATERIALIZED VIEW mv_valid_order_priorities AS
SELECT
    sku,
    model,
    color,
    size,
    priority_score,
    stockout_risk,
    revenue_impact,
    revenue_at_risk,
    current_stock,
    reorder_point,
    deficit,
    forecast_leadtime,
    coverage_gap,
    product_type,
    type_multiplier,
    is_urgent,
    computed_at,
    forecast_generated_date,
    stock_snapshot_date,
    configuration_hash
FROM cache_order_priorities
WHERE is_valid = TRUE
  AND cache_version = (
      SELECT MAX(cache_version)
      FROM cache_order_priorities cop2
      WHERE cop2.sku = cache_order_priorities.sku
        AND cop2.is_valid = TRUE
  );

CREATE INDEX idx_mv_priorities_model_color ON mv_valid_order_priorities(model, color);
CREATE INDEX idx_mv_priorities_score ON mv_valid_order_priorities(priority_score DESC);
CREATE INDEX idx_mv_priorities_urgent ON mv_valid_order_priorities(is_urgent) WHERE is_urgent = TRUE;


-- =============================================================================
-- REFRESH FUNCTIONS
-- =============================================================================

-- Function: Refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_stock;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_forecast;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_monthly_aggs;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_sku_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_order_priorities;
    RAISE NOTICE 'All materialized views refreshed';
END;
$$ LANGUAGE plpgsql;


-- Function: Refresh stock-related views only
CREATE OR REPLACE FUNCTION refresh_stock_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_stock;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_order_priorities;
    RAISE NOTICE 'Stock-related views refreshed';
END;
$$ LANGUAGE plpgsql;


-- Function: Refresh forecast-related views only
CREATE OR REPLACE FUNCTION refresh_forecast_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_forecast;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_order_priorities;
    RAISE NOTICE 'Forecast-related views refreshed';
END;
$$ LANGUAGE plpgsql;


-- Function: Refresh cache views only
CREATE OR REPLACE FUNCTION refresh_cache_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_monthly_aggs;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_sku_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_valid_order_priorities;
    RAISE NOTICE 'Cache views refreshed';
END;
$$ LANGUAGE plpgsql;
