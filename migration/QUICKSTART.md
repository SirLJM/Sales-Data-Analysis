# Database Setup Quick Start

This guide will help you set up the PostgreSQL database for the inventory management system.

## Prerequisites

1. **PostgreSQL 15+** installed and running
2. **Python 3.13+** with dependencies: `pip install -r requirements.txt`
3. **Data files** ready in the `data/` directory:
   - Sales CSV/Excel files
   - Stock snapshots
   - Forecast files
   - `MODELE&KOLORY_NUMERACJA.xlsx` (model metadata)
   - `sizes.xlsx` (size aliases)

## Setup Steps

### 1. Create Database

```sql
CREATE DATABASE inventory_db;
CREATE USER inventory_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
```

### 2. Configure Environment

Create `.env` file in project root:

```env
DATABASE_URL=postgresql://inventory_user:your_password@localhost:5432/inventory_db
DATA_SOURCE_MODE=file
```

**Important**: Keep `DATA_SOURCE_MODE=file` until data is imported!

### 3. Run Setup Script

This creates all tables, triggers, materialized views, and order tables:

```bash
python src/migration/setup_database.py
```

### 4. Import All Data

This imports sales, stock, forecast, model metadata, and size aliases:

```bash
python src/migration/import_all.py
```

This will take 5-30 minutes depending on data size.

### 5. Populate Cache Tables

This computes and caches monthly aggregations for fast queries:

```bash
python src/migration/populate_cache.py
```

### 6. Switch to Database Mode

Update `.env`:

```env
DATA_SOURCE_MODE=database
```

### 7. Run Application

```bash
cd src
py -m streamlit run app.py
```

You should see: `[OK] Using database data source`

---

## Script Reference

### Essential Scripts

- **`setup_database.py`** - Creates all database schema (tables, triggers, views)
- **`import_all.py`** - One-command import of all data types
- **`populate_cache.py`** - Populates cache tables for performance
- **`refresh_views.py`** - Refreshes materialized views (maintenance)

### Individual Import Scripts

Use these for incremental updates or when you only need to import specific data:

- **`initial_populate.py`** - Import archival sales data (historical years)
- **`import_current_sales.py`** - Import current year sales data
- **`import_stock.py`** - Import stock snapshots
- **`import_forecast.py`** - Import forecast data
- **`import_model_metadata.py`** - Import model metadata
- **`import_size_aliases.py`** - Import size aliases (required for order creation!)

### Order Management

- **`create_orders_table.py`** - Creates order tables (included in `setup_database.py`)

---

## Troubleshooting

### "DATABASE_URL not set"
- Check `.env` file exists in project root
- Verify `DATABASE_URL` is correctly formatted

### "Connection refused"
- Ensure PostgreSQL is running: `pg_ctl status`
- Verify port 5432 is accessible
- Check credentials are correct

### "File not found" errors
- Ensure data files are in the correct location
- Check `data/` directory structure

### Materialized views are empty
- Run `populate_cache.py` to fill cache tables
- Run `refresh_views.py` to refresh materialized views

### Order creation shows file loading instead of database
- This means cache tables are empty
- Run: `python src/migration/populate_cache.py`
- Verify: You should see `[OK] Using database monthly aggregations`

---

## Daily Maintenance

### Update Current Data

```bash
python src/migration/import_current_sales.py
python src/migration/import_stock.py
python src/migration/import_forecast.py
python src/migration/refresh_views.py
```

### Refresh Cache (Weekly)

```bash
python src/migration/populate_cache.py
python src/migration/refresh_views.py
```

---

## Performance Tips

1. **Cache population** is essential - without it, queries fall back to file loading
2. **Materialized views** provide 10-100x speedup over file-based queries
3. Run `VACUUM ANALYZE` monthly on large tables
4. Monitor slow queries with `pg_stat_statements`

---

## Need Help?

- See `README.md` for detailed documentation
- Check `CLAUDE.md` for development guidelines
- Review SQL files in `sql/` directory for schema details
