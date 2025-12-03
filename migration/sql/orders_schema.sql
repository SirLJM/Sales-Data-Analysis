-- Orders System Schema
-- Created: 2025-12-03
-- Purpose: Order creation workflow with pattern matching and production metadata

-- =============================================================================
-- ORDERS TABLES
-- =============================================================================

-- Table: orders
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,

    order_id VARCHAR(100) NOT NULL UNIQUE,
    model VARCHAR(5) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    szwalnia_glowna VARCHAR(100),
    szwalnia_druga VARCHAR(100),
    rodzaj_materialu VARCHAR(100),
    gramatura VARCHAR(50),

    total_quantity INTEGER NOT NULL DEFAULT 0,
    total_patterns INTEGER NOT NULL DEFAULT 0,
    total_excess INTEGER NOT NULL DEFAULT 0,
    total_colors INTEGER NOT NULL DEFAULT 0,

    order_data JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_model ON orders(model);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_data ON orders USING GIN(order_data);


-- Table: order_items
CREATE TABLE IF NOT EXISTS order_items (
    id BIGSERIAL PRIMARY KEY,

    order_id VARCHAR(100) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    model VARCHAR(5) NOT NULL,
    color VARCHAR(2) NOT NULL,

    total_patterns INTEGER NOT NULL DEFAULT 0,
    total_excess INTEGER NOT NULL DEFAULT 0,
    coverage_status VARCHAR(20),

    size_quantities JSONB DEFAULT '{}'::jsonb,
    produced_quantities JSONB DEFAULT '{}'::jsonb,
    excess_quantities JSONB DEFAULT '{}'::jsonb,
    pattern_allocation JSONB DEFAULT '{}'::jsonb,

    forecast_leadtime INTEGER DEFAULT 0,
    deficit INTEGER DEFAULT 0,
    coverage_gap INTEGER DEFAULT 0,
    safety_stock INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 0,

    sales_month_1 INTEGER DEFAULT 0,
    sales_month_2 INTEGER DEFAULT 0,
    sales_month_3 INTEGER DEFAULT 0,
    sales_month_4 INTEGER DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_order_items_order_color UNIQUE(order_id, color)
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_model ON order_items(model);
CREATE INDEX IF NOT EXISTS idx_order_items_color ON order_items(color);
CREATE INDEX IF NOT EXISTS idx_order_items_coverage ON order_items(coverage_status);


-- Table: order_history
CREATE TABLE IF NOT EXISTS order_history (
    id BIGSERIAL PRIMARY KEY,

    order_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    notes TEXT,

    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_history_order_id ON order_history(order_id);
CREATE INDEX IF NOT EXISTS idx_order_history_changed_at ON order_history(changed_at DESC);


-- Trigger: Update updated_at timestamp on orders table
CREATE OR REPLACE FUNCTION update_orders_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_orders_timestamp ON orders;
CREATE TRIGGER trigger_update_orders_timestamp
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_orders_timestamp();


-- Trigger: Log order status changes to order_history
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO order_history (order_id, action, old_status, new_status, notes)
        VALUES (NEW.order_id, 'status_change', OLD.status, NEW.status,
                'Status changed from ' || OLD.status || ' to ' || NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_log_order_status_change ON orders;
CREATE TRIGGER trigger_log_order_status_change
    AFTER UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION log_order_status_change();
