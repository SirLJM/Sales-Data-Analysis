# Database Migration Guide

This guide will help you set up and migrate your inventory management system to PostgreSQL.

## Prerequisites

1. PostgreSQL 15+ installed
2. Python dependencies installed: `pip install -r requirements.txt`
3. Access to your Excel data files (sales, stock, forecast)

## Step 1: Install PostgreSQL

### Windows

Download and install from: https://www.postgresql.org/download/windows/

During installation:

- Remember your postgres user password
- Default port: 5432
- Install pgAdmin 4 (GUI tool)

### Verify Installation

```bash
psql --version
```

## Step 2: Create Database

Open pgAdmin or use the command line:

```sql
CREATE DATABASE inventory_db;
CREATE USER inventory_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
```

## Step 3: Run Schema Scripts

Execute the SQL scripts in order:

```bash
cd migration

# Create tables
psql -U inventory_user -d inventory_db -f schema.sql

# Create triggers
psql -U inventory_user -d inventory_db -f triggers.sql

# Create materialized views
psql -U inventory_user -d inventory_db -f materialized_views.sql
```

Or using pgAdmin:

1. Connect to `inventory_db`
2. Open Query Tool
3. Copy-paste each SQL file and execute

## Step 4: Configure Connection

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
DATABASE_URL=postgresql://inventory_user:your_secure_password@localhost:5432/inventory_db
DATA_SOURCE_MODE=file
```

**Important**: Keep `DATA_SOURCE_MODE=file` initially for testing.

## Step 5: Test Connection

```python
from sqlalchemy import create_engine, text

connection_string = "postgresql://inventory_user:your_password@localhost:5432/inventory_db"
engine = create_engine(connection_string)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print(result.fetchone())
```

## Step 6: Initial Data Import

Use the Python migration scripts to populate the database.

### Import Sales Data (Archival)

```python
from migration.initial_populate import populate_archival_sales

# This will take 5-30 minutes depending on data size
populate_archival_sales("postgresql://inventory_user:password@localhost:5432/inventory_db")
```

### Import Current Sales

```python
from sales_data.db_updater import DatabaseUpdater

updater = DatabaseUpdater("postgresql://inventory_user:password@localhost:5432/inventory_db")
records, message = updater.update_current_sales()
print(message)
```

### Import Stock Data

```python
records, message = updater.update_stock_snapshot()
print(message)
```

### Import Forecast Data

```python
records, message = updater.update_forecast()
print(message)
```

## Step 7: Verify Data

Check record counts:

```sql
SELECT COUNT(*) FROM raw_sales_transactions;
SELECT COUNT(*) FROM stock_snapshots;
SELECT COUNT(*) FROM forecast_data;
SELECT COUNT(*) FROM file_imports WHERE import_status = 'completed';
```

Check partitions:

```sql
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'raw_sales_transactions%'
ORDER BY tablename;
```

## Step 8: Switch to Database Mode

Once data is verified:

1. Edit `src/data_source_config.json`:

```json
{
  "mode": "database",
  "connection_string": null,
  "fallback_to_file": true
}
```

2. Or update `.env`:

```env
DATA_SOURCE_MODE=database
```

3. Restart the Streamlit app:

```bash
cd src
py -m streamlit run app.py
```

You should see: `✓ Using database data source`

## Step 9: Daily Updates

### Manual Update (via Streamlit UI)

- Open Tab 1 sidebar
- Click "🔄 Update Database" button

### Automated Update (Windows Task Scheduler)

Create `migration/daily_update.py`:

```python
from sales_data.db_updater import DatabaseUpdater
import os

connection_string = os.environ.get('DATABASE_URL')
updater = DatabaseUpdater(connection_string)

print("Updating sales...")
records, msg = updater.update_current_sales()
print(msg)

print("Updating stock...")
records, msg = updater.update_stock_snapshot()
print(msg)

updater.close()
```

Schedule to run daily at 7 AM.

## Troubleshooting

### Connection Refused

- Check PostgreSQL service is running: `pg_ctl status`
- Verify port 5432 is open
- Check `pg_hba.conf` allows local connections

### Slow Queries

- Check indexes: `SELECT * FROM pg_indexes WHERE tablename LIKE '%sales%'`
- Run `VACUUM ANALYZE` on large tables
- Check query plans: `EXPLAIN ANALYZE SELECT ...`

### Cache Not Updating

- Manually invalidate: `SELECT invalidate_all_caches()`
- Refresh materialized views: `SELECT refresh_all_materialized_views()`

### Rollback to File Mode

1. Edit `src/data_source_config.json`: `"mode": "file"`
2. Restart app
3. Files remain a source of truth

## Performance Monitoring

```sql
-- Slow queries log
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- Cache hit rates
SELECT
    schemaname,
    tablename,
    round(100.0 * sum(idx_scan) / nullif(sum(idx_scan + seq_scan), 0), 2) AS index_usage_pct
FROM pg_stat_user_tables
GROUP BY schemaname, tablename
ORDER BY index_usage_pct DESC;
```

## Maintenance

### Weekly

- `VACUUM ANALYZE` on large tables
- Check file import logs: `SELECT * FROM file_imports WHERE import_status = 'failed'`

### Monthly

- Add new year partitions if approaching the year boundary
- Review and archive old cache versions

### Yearly

```sql
-- Create next year partition
CREATE TABLE raw_sales_transactions_2027 PARTITION OF raw_sales_transactions
    FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
```

## Next Steps

Once database migration is complete:

1. Monitor performance improvements (should see 10-100x speedup)
2. Set up automated daily updates
3. Consider implementing cache pre-warming
4. Explore additional features (historical analysis, APIs, dashboards)
