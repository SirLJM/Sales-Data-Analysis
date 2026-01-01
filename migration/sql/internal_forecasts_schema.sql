-- =============================================================================
-- INTERNAL FORECASTS TABLE
-- Stores internally generated forecasts for historical comparison
-- =============================================================================

CREATE TABLE IF NOT EXISTS internal_forecasts
(
    id                BIGSERIAL PRIMARY KEY,

    forecast_batch_id UUID         NOT NULL,
    generated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    entity_id         VARCHAR(20)  NOT NULL,
    entity_type       VARCHAR(10)  NOT NULL,
    forecast_method   VARCHAR(50)  NOT NULL,

    forecast_period   VARCHAR(7)   NOT NULL,
    forecast_value    NUMERIC(12, 2) NOT NULL,
    lower_ci          NUMERIC(12, 2),
    upper_ci          NUMERIC(12, 2),

    horizon_months    INTEGER      NOT NULL,
    product_type      VARCHAR(20),
    cv                NUMERIC(8, 4),

    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_internal_forecasts_batch ON internal_forecasts (forecast_batch_id);
CREATE INDEX idx_internal_forecasts_entity ON internal_forecasts (entity_id, entity_type);
CREATE INDEX idx_internal_forecasts_generated ON internal_forecasts (generated_at);
CREATE INDEX idx_internal_forecasts_period ON internal_forecasts (forecast_period);


-- =============================================================================
-- INTERNAL FORECAST BATCHES TABLE
-- Metadata about each forecast generation run
-- =============================================================================

CREATE TABLE IF NOT EXISTS internal_forecast_batches
(
    id                UUID PRIMARY KEY,

    generated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    entity_type       VARCHAR(10)  NOT NULL,
    horizon_months    INTEGER      NOT NULL,

    total_entities    INTEGER      NOT NULL DEFAULT 0,
    success_count     INTEGER      NOT NULL DEFAULT 0,
    failed_count      INTEGER      NOT NULL DEFAULT 0,

    methods_used      JSONB        DEFAULT '{}'::jsonb,
    parameters        JSONB        DEFAULT '{}'::jsonb,

    notes             TEXT,

    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_internal_forecast_batches_generated ON internal_forecast_batches (generated_at);
CREATE INDEX idx_internal_forecast_batches_entity_type ON internal_forecast_batches (entity_type);
