-- Automatic Cache Invalidation Triggers
-- Created: 2025-11-26

-- =============================================================================
-- TRIGGER FUNCTIONS
-- =============================================================================

-- Function: Invalidate caches when new sales data is inserted
CREATE OR REPLACE FUNCTION invalidate_sales_caches()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cache_monthly_aggregations
    SET is_valid = FALSE
    WHERE (entity_type = 'sku' AND entity_id = NEW.sku)
       OR (entity_type = 'model' AND entity_id = NEW.model);

    UPDATE cache_sku_statistics
    SET is_valid = FALSE
    WHERE (entity_type = 'sku' AND entity_id = NEW.sku)
       OR (entity_type = 'model' AND entity_id = NEW.model);

    UPDATE cache_seasonal_indices
    SET is_valid = FALSE
    WHERE (entity_type = 'sku' AND entity_id = NEW.sku)
       OR (entity_type = 'model' AND entity_id = NEW.model);

    UPDATE cache_order_priorities
    SET is_valid = FALSE
    WHERE sku = NEW.sku OR model = NEW.model;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Function: Invalidate order priority cache when stock changes
CREATE OR REPLACE FUNCTION invalidate_stock_caches()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cache_order_priorities
    SET is_valid = FALSE
    WHERE sku = NEW.sku OR model = NEW.model;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Function: Invalidate order priority cache when forecast changes
CREATE OR REPLACE FUNCTION invalidate_forecast_caches()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cache_order_priorities
    SET is_valid = FALSE
    WHERE sku = NEW.sku OR (NEW.model IS NOT NULL AND model = NEW.model);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Function: Update timestamp on record modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- TRIGGER ASSIGNMENTS
-- =============================================================================

-- Invalidate caches when sales data changes
CREATE TRIGGER trg_invalidate_sales_caches
AFTER INSERT ON raw_sales_transactions
FOR EACH ROW
EXECUTE FUNCTION invalidate_sales_caches();


-- Invalidate caches when stock data changes
CREATE TRIGGER trg_invalidate_stock_caches
AFTER INSERT OR UPDATE ON stock_snapshots
FOR EACH ROW
EXECUTE FUNCTION invalidate_stock_caches();


-- Invalidate caches when forecast data changes
CREATE TRIGGER trg_invalidate_forecast_caches
AFTER INSERT OR UPDATE ON forecast_data
FOR EACH ROW
EXECUTE FUNCTION invalidate_forecast_caches();


-- Update timestamp on sales transactions
CREATE TRIGGER trg_update_sales_timestamp
BEFORE UPDATE ON raw_sales_transactions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- Update timestamp on model metadata
CREATE TRIGGER trg_update_model_timestamp
BEFORE UPDATE ON model_metadata
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- Update timestamp on application settings
CREATE TRIGGER trg_update_settings_timestamp
BEFORE UPDATE ON application_settings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- HELPER FUNCTIONS FOR BULK IMPORTS
-- =============================================================================

-- Function: Disable cache invalidation triggers (for bulk imports)
CREATE OR REPLACE FUNCTION disable_cache_triggers()
RETURNS void AS $$
BEGIN
    ALTER TABLE raw_sales_transactions DISABLE TRIGGER trg_invalidate_sales_caches;
    ALTER TABLE stock_snapshots DISABLE TRIGGER trg_invalidate_stock_caches;
    ALTER TABLE forecast_data DISABLE TRIGGER trg_invalidate_forecast_caches;
    RAISE NOTICE 'Cache invalidation triggers disabled';
END;
$$ LANGUAGE plpgsql;


-- Function: Enable cache invalidation triggers (after bulk imports)
CREATE OR REPLACE FUNCTION enable_cache_triggers()
RETURNS void AS $$
BEGIN
    ALTER TABLE raw_sales_transactions ENABLE TRIGGER trg_invalidate_sales_caches;
    ALTER TABLE stock_snapshots ENABLE TRIGGER trg_invalidate_stock_caches;
    ALTER TABLE forecast_data ENABLE TRIGGER trg_invalidate_forecast_caches;
    RAISE NOTICE 'Cache invalidation triggers enabled';
END;
$$ LANGUAGE plpgsql;


-- Function: Manually invalidate all caches (for settings changes)
CREATE OR REPLACE FUNCTION invalidate_all_caches()
RETURNS void AS $$
BEGIN
    UPDATE cache_monthly_aggregations SET is_valid = FALSE WHERE is_valid = TRUE;
    UPDATE cache_sku_statistics SET is_valid = FALSE WHERE is_valid = TRUE;
    UPDATE cache_seasonal_indices SET is_valid = FALSE WHERE is_valid = TRUE;
    UPDATE cache_order_priorities SET is_valid = FALSE WHERE is_valid = TRUE;
    RAISE NOTICE 'All caches invalidated';
END;
$$ LANGUAGE plpgsql;
