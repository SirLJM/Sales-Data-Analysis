CREATE TABLE IF NOT EXISTS material_catalog (
    id              SERIAL PRIMARY KEY,
    material_name   TEXT NOT NULL UNIQUE,
    supplier        TEXT,
    composition     TEXT,
    material_type   TEXT,
    layout_width    NUMERIC(8,2) DEFAULT 0,
    yield_m_per_kg  NUMERIC(8,2) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bom_components (
    id                      SERIAL PRIMARY KEY,
    model                   VARCHAR(5) NOT NULL UNIQUE,
    main_material_name      TEXT,
    main_consumption_m2     NUMERIC(10,4) DEFAULT 0,
    main_consumption_mb     NUMERIC(10,4) DEFAULT 0,
    main_consumption_kg     NUMERIC(10,4) DEFAULT 0,
    main_yield_mb_kg        NUMERIC(10,4) DEFAULT 0,
    main_width              NUMERIC(8,2) DEFAULT 0,
    ribbing_type            TEXT,
    ribbing_consumption_mb  NUMERIC(10,4) DEFAULT 0,
    lining_consumption_mb   NUMERIC(10,4) DEFAULT 0,
    is_outlet               BOOLEAN DEFAULT FALSE,
    is_withdrawn            BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS material_stock (
    id              SERIAL PRIMARY KEY,
    material_name   TEXT NOT NULL,
    quantity_kg     NUMERIC(12,2) DEFAULT 0,
    quantity_meters NUMERIC(12,2) DEFAULT 0,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (material_name)
);

CREATE INDEX IF NOT EXISTS idx_bom_components_model ON bom_components(model);
CREATE INDEX IF NOT EXISTS idx_material_catalog_name ON material_catalog(material_name);
CREATE INDEX IF NOT EXISTS idx_material_stock_name ON material_stock(material_name);
