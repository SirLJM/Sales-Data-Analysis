-- PostgreSQL Database Schema for Inventory Management System
-- Created: 2025-11-26

-- =============================================================================
-- CORE DATA TABLES
-- =============================================================================

-- Table: raw_sales_transactions (Partitioned by year)
CREATE TABLE raw_sales_transactions (
    id BIGSERIAL,

    order_id VARCHAR(100) NOT NULL,
    sale_date TIMESTAMP NOT NULL,
    sku VARCHAR(20) NOT NULL,
    quantity NUMERIC(10,2) NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL,

    model VARCHAR(5),
    color VARCHAR(2),
    size VARCHAR(2),
    year_month VARCHAR(7),

    source_file VARCHAR(500) NOT NULL,
    file_start_date DATE NOT NULL,
    file_end_date DATE NOT NULL,
    import_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    import_batch_id UUID NOT NULL,
    data_source VARCHAR(50) NOT NULL,

    extra_fields JSONB DEFAULT '{}'::jsonb,

    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id, sale_date)
) PARTITION BY RANGE (sale_date);

CREATE TABLE raw_sales_transactions_2023 PARTITION OF raw_sales_transactions
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE raw_sales_transactions_2024 PARTITION OF raw_sales_transactions
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE raw_sales_transactions_2025 PARTITION OF raw_sales_transactions
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE raw_sales_transactions_2026 PARTITION OF raw_sales_transactions
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE INDEX idx_sales_sku ON raw_sales_transactions(sku);
CREATE INDEX idx_sales_model ON raw_sales_transactions(model);
CREATE INDEX idx_sales_date ON raw_sales_transactions(sale_date);
CREATE INDEX idx_sales_year_month ON raw_sales_transactions(year_month);
CREATE INDEX idx_sales_model_date ON raw_sales_transactions(model, sale_date);
CREATE INDEX idx_sales_sku_date ON raw_sales_transactions(sku, sale_date);
CREATE INDEX idx_sales_extra_fields ON raw_sales_transactions USING GIN(extra_fields);
CREATE UNIQUE INDEX idx_sales_unique_transaction
    ON raw_sales_transactions(order_id, sku, sale_date, source_file);


-- Table: stock_snapshots
CREATE TABLE stock_snapshots (
    id BIGSERIAL PRIMARY KEY,

    sku VARCHAR(20) NOT NULL,
    product_name VARCHAR(500),
    net_price NUMERIC(12,2),
    gross_price NUMERIC(12,2),
    total_stock NUMERIC(10,2),
    available_stock NUMERIC(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    model VARCHAR(5),

    snapshot_date DATE NOT NULL,
    source_file VARCHAR(500) NOT NULL,
    import_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    import_batch_id UUID NOT NULL,

    extra_fields JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_stock_sku_date UNIQUE(sku, snapshot_date)
);

CREATE INDEX idx_stock_sku ON stock_snapshots(sku);
CREATE INDEX idx_stock_model ON stock_snapshots(model);
CREATE INDEX idx_stock_date ON stock_snapshots(snapshot_date);
CREATE INDEX idx_stock_active ON stock_snapshots(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_stock_latest ON stock_snapshots(snapshot_date DESC, sku) WHERE is_active = TRUE;


-- Table: forecast_data
CREATE TABLE forecast_data (
    id BIGSERIAL PRIMARY KEY,

    forecast_date DATE NOT NULL,
    sku VARCHAR(20) NOT NULL,
    model VARCHAR(5),
    forecast_quantity NUMERIC(10,2) NOT NULL,

    generated_date DATE NOT NULL,
    source_file VARCHAR(500) NOT NULL,
    import_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    import_batch_id UUID NOT NULL,

    extra_fields JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_forecast_sku_date_gen UNIQUE(sku, forecast_date, generated_date)
);

CREATE INDEX idx_forecast_sku ON forecast_data(sku);
CREATE INDEX idx_forecast_date ON forecast_data(forecast_date);
CREATE INDEX idx_forecast_generated ON forecast_data(generated_date DESC);
CREATE INDEX idx_forecast_sku_date ON forecast_data(sku, forecast_date);


-- Table: model_metadata
CREATE TABLE model_metadata (
    id SERIAL PRIMARY KEY,

    model VARCHAR(20) NOT NULL UNIQUE,
    primary_production VARCHAR(100),
    secondary_production VARCHAR(100),
    material_type VARCHAR(100),
    material_weight VARCHAR(50),

    extra_fields JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_metadata_model ON model_metadata(model);


-- =============================================================================
-- IMPORT TRACKING TABLE
-- =============================================================================

CREATE TABLE file_imports (
    id SERIAL PRIMARY KEY,

    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    file_size BIGINT,

    file_start_date DATE,
    file_end_date DATE,

    import_batch_id UUID NOT NULL UNIQUE,
    import_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    import_status VARCHAR(50) NOT NULL,
    records_imported INTEGER,
    records_failed INTEGER,
    error_message TEXT,

    processing_time_ms INTEGER,
    import_triggered_by VARCHAR(100),

    CONSTRAINT uq_file_hash UNIQUE(file_hash, file_type)
);

CREATE INDEX idx_file_imports_type ON file_imports(file_type);
CREATE INDEX idx_file_imports_status ON file_imports(import_status);
CREATE INDEX idx_file_imports_timestamp ON file_imports(import_timestamp DESC);


-- =============================================================================
-- CACHE TABLES
-- =============================================================================

-- Table: cache_monthly_aggregations
CREATE TABLE cache_monthly_aggregations (
    id SERIAL PRIMARY KEY,

    entity_type VARCHAR(10) NOT NULL,
    entity_id VARCHAR(20) NOT NULL,
    year_month VARCHAR(7) NOT NULL,

    total_quantity NUMERIC(12,2) NOT NULL,
    total_revenue NUMERIC(15,2) NOT NULL,
    transaction_count INTEGER NOT NULL,
    unique_orders INTEGER NOT NULL,
    avg_unit_price NUMERIC(12,2),

    cache_version INTEGER NOT NULL DEFAULT 1,
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_data_hash VARCHAR(64),
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_cache_monthly UNIQUE(entity_type, entity_id, year_month, cache_version)
);

CREATE INDEX idx_cache_monthly_entity ON cache_monthly_aggregations(entity_type, entity_id);
CREATE INDEX idx_cache_monthly_valid ON cache_monthly_aggregations(is_valid) WHERE is_valid = TRUE;
CREATE INDEX idx_cache_monthly_year_month ON cache_monthly_aggregations(year_month);


-- Table: cache_sku_statistics
CREATE TABLE cache_sku_statistics (
    id SERIAL PRIMARY KEY,

    entity_type VARCHAR(10) NOT NULL,
    entity_id VARCHAR(20) NOT NULL,

    months_with_sales INTEGER NOT NULL,
    total_quantity NUMERIC(12,2) NOT NULL,
    average_monthly_sales NUMERIC(12,2) NOT NULL,
    standard_deviation NUMERIC(12,2) NOT NULL,
    coefficient_of_variation NUMERIC(8,4) NOT NULL,

    first_sale_date DATE,
    product_type VARCHAR(20),

    safety_stock NUMERIC(10,2),
    reorder_point NUMERIC(10,2),
    z_score_used NUMERIC(5,2),
    lead_time_months NUMERIC(4,2),

    is_seasonal BOOLEAN DEFAULT FALSE,
    seasonal_ss_in NUMERIC(10,2),
    seasonal_ss_out NUMERIC(10,2),
    seasonal_rop_in NUMERIC(10,2),
    seasonal_rop_out NUMERIC(10,2),

    last_2y_avg_monthly NUMERIC(12,2),

    cache_version INTEGER NOT NULL DEFAULT 1,
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    based_on_data_until DATE NOT NULL,
    configuration_hash VARCHAR(64),
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_cache_stats UNIQUE(entity_type, entity_id, cache_version)
);

CREATE INDEX idx_cache_stats_entity ON cache_sku_statistics(entity_type, entity_id);
CREATE INDEX idx_cache_stats_type ON cache_sku_statistics(product_type);
CREATE INDEX idx_cache_stats_valid ON cache_sku_statistics(is_valid) WHERE is_valid = TRUE;


-- Table: cache_seasonal_indices
CREATE TABLE cache_seasonal_indices (
    id SERIAL PRIMARY KEY,

    entity_type VARCHAR(10) NOT NULL,
    entity_id VARCHAR(20) NOT NULL,
    month_number INTEGER NOT NULL CHECK (month_number BETWEEN 1 AND 12),

    seasonal_index NUMERIC(8,4) NOT NULL,
    avg_monthly_sales NUMERIC(12,2) NOT NULL,
    is_in_season BOOLEAN NOT NULL,

    cache_version INTEGER NOT NULL DEFAULT 1,
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    based_on_data_until DATE NOT NULL,
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_cache_seasonal UNIQUE(entity_type, entity_id, month_number, cache_version)
);

CREATE INDEX idx_cache_seasonal_entity ON cache_seasonal_indices(entity_type, entity_id);
CREATE INDEX idx_cache_seasonal_valid ON cache_seasonal_indices(is_valid) WHERE is_valid = TRUE;


-- Table: cache_order_priorities
CREATE TABLE cache_order_priorities (
    id SERIAL PRIMARY KEY,

    sku VARCHAR(20) NOT NULL,
    model VARCHAR(5) NOT NULL,
    color VARCHAR(2) NOT NULL,
    size VARCHAR(2),

    priority_score NUMERIC(10,4) NOT NULL,
    stockout_risk NUMERIC(8,2) NOT NULL,
    revenue_impact NUMERIC(8,2) NOT NULL,
    revenue_at_risk NUMERIC(15,2),

    current_stock NUMERIC(10,2) NOT NULL,
    reorder_point NUMERIC(10,2) NOT NULL,
    deficit NUMERIC(10,2) NOT NULL,
    forecast_leadtime NUMERIC(10,2) NOT NULL,
    coverage_gap NUMERIC(10,2) NOT NULL,

    product_type VARCHAR(20) NOT NULL,
    type_multiplier NUMERIC(4,2) NOT NULL,
    is_urgent BOOLEAN NOT NULL,

    cache_version INTEGER NOT NULL DEFAULT 1,
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    forecast_generated_date DATE NOT NULL,
    stock_snapshot_date DATE NOT NULL,
    configuration_hash VARCHAR(64) NOT NULL,
    is_valid BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_cache_priorities_model_color ON cache_order_priorities(model, color);
CREATE INDEX idx_cache_priorities_score ON cache_order_priorities(priority_score DESC);
CREATE INDEX idx_cache_priorities_urgent ON cache_order_priorities(is_urgent) WHERE is_urgent = TRUE;
CREATE INDEX idx_cache_priorities_valid ON cache_order_priorities(is_valid) WHERE is_valid = TRUE;


-- =============================================================================
-- APPLICATION SETTINGS TABLE
-- =============================================================================

CREATE TABLE application_settings (
    id SERIAL PRIMARY KEY,

    settings_key VARCHAR(100) NOT NULL UNIQUE,
    settings_value JSONB NOT NULL,
    settings_hash VARCHAR(64) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_app_settings_key ON application_settings(settings_key);
