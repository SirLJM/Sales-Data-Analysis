from __future__ import annotations

DUCKDB_SCHEMA = """\
Tables (DuckDB in-memory, file mode):

sales(sku VARCHAR, model VARCHAR, data TIMESTAMP, ilosc NUMERIC, razem NUMERIC)
  -- data=sale date, ilosc=quantity sold, razem=total amount/revenue

stock(sku VARCHAR, model VARCHAR, nazwa VARCHAR, available_stock NUMERIC)
  -- nazwa=product name

forecast(sku VARCHAR, model VARCHAR, data TIMESTAMP, forecast NUMERIC)
  -- data=forecast date, forecast=forecasted quantity
"""

POSTGRES_SCHEMA = """\
Tables (PostgreSQL):

raw_sales_transactions(id, order_id, sale_date TIMESTAMP, sku VARCHAR(20), quantity NUMERIC, unit_price NUMERIC, total_amount NUMERIC, model VARCHAR(5), color VARCHAR(2), size VARCHAR(2), year_month VARCHAR(7), source_file, is_valid BOOLEAN)
  Partitioned by sale_date. Indexes on sku, model, sale_date, year_month.

stock_snapshots(id, sku VARCHAR(20), product_name VARCHAR, net_price NUMERIC, gross_price NUMERIC, total_stock NUMERIC, available_stock NUMERIC, is_active BOOLEAN, model VARCHAR(5), snapshot_date DATE)

forecast_data(id, forecast_date DATE, sku VARCHAR(20), model VARCHAR(5), forecast_quantity NUMERIC, generated_date DATE)

model_metadata(model VARCHAR(20) UNIQUE, primary_production VARCHAR, secondary_production VARCHAR, material_type VARCHAR, material_weight VARCHAR)

category_mappings(model VARCHAR(5) PK, grupa VARCHAR, podgrupa VARCHAR, kategoria VARCHAR, nazwa TEXT)
  -- grupa: top-level (Dzieci/Dorośli/Niemowlę), podgrupa: age group, kategoria: clothing type

orders(order_id VARCHAR UNIQUE, order_date DATE, model VARCHAR, product_name VARCHAR, total_quantity INT, facility VARCHAR, status VARCHAR DEFAULT 'active')

cache_sku_statistics(entity_type VARCHAR, entity_id VARCHAR, months_with_sales INT, total_quantity NUMERIC, average_monthly_sales NUMERIC, standard_deviation NUMERIC, coefficient_of_variation NUMERIC, product_type VARCHAR, safety_stock NUMERIC, reorder_point NUMERIC, is_seasonal BOOLEAN)

cache_monthly_aggregations(entity_type VARCHAR, entity_id VARCHAR, year_month VARCHAR, total_quantity NUMERIC, total_revenue NUMERIC, transaction_count INT)

cache_order_priorities(sku VARCHAR, model VARCHAR, priority_score NUMERIC, stockout_risk NUMERIC, current_stock NUMERIC, reorder_point NUMERIC, deficit NUMERIC, product_type VARCHAR, is_urgent BOOLEAN)

size_aliases(size_code VARCHAR(2), size_alias VARCHAR)
color_aliases(color_code VARCHAR(2), color_name VARCHAR)

Materialized views (prefer these for common lookups):
  mv_latest_stock(sku, model, product_name, net_price, gross_price, total_stock, available_stock, snapshot_date)
  mv_latest_forecast(sku, model, forecast_date, forecast_quantity, generated_date)
  mv_valid_sku_stats — same cols as cache_sku_statistics, only valid+latest
  mv_valid_monthly_aggs — same cols as cache_monthly_aggregations, only valid+latest
  mv_valid_order_priorities — same cols as cache_order_priorities, only valid+latest
"""

QUERY_GUIDELINES = """\
Rules:
- Generate only SELECT or WITH (CTE) statements. Never INSERT/UPDATE/DELETE/DROP.
- SKU is 9 characters: model=sku[1:5] (first 5 chars), color=sku[6:7], size=sku[8:9].
- In PostgreSQL use SUBSTRING(sku, 1, 5) for model extraction. In DuckDB use sku[:5].
- Product types: 'new', 'basic', 'seasonal', 'regular' (in cache_sku_statistics.product_type or mv_valid_sku_stats.product_type).
- For "below ROP" queries, join stock with cache_sku_statistics on sku and compare available_stock < reorder_point.
- Use materialized views (mv_*) in PostgreSQL mode when possible — they are pre-filtered for latest/valid data.
- In file mode (DuckDB): date column is 'data', quantity is 'ilosc', revenue is 'razem'.
- In database mode (PostgreSQL): date column is 'sale_date', quantity is 'quantity', revenue is 'total_amount'.
- Always include a LIMIT clause unless the user explicitly wants all rows. Default to LIMIT 100.
- The user may write in Polish or English. Interpret both.
"""

DUCKDB_EXAMPLES = """\
Examples (DuckDB file mode):

Q: "sales of model CH086 last 2 years"
SQL: SELECT * FROM sales WHERE UPPER(model) = 'CH086' AND data >= CURRENT_DATE - INTERVAL '2 years' LIMIT 100

Q: "top 10 models by sales"
SQL: SELECT model, SUM(ilosc) AS total_qty FROM sales GROUP BY model ORDER BY total_qty DESC LIMIT 10

Q: "monthly sales for model JU386"
SQL: SELECT DATE_TRUNC('month', data) AS month, SUM(ilosc) AS qty, SUM(razem) AS revenue FROM sales WHERE UPPER(model) = 'JU386' GROUP BY month ORDER BY month

Q: "current stock for model DO322"
SQL: SELECT * FROM stock WHERE UPPER(model) = 'DO322' LIMIT 100

Q: "forecast for next 3 months"
SQL: SELECT * FROM forecast WHERE data >= CURRENT_DATE AND data < CURRENT_DATE + INTERVAL '3 months' ORDER BY data LIMIT 100
"""

POSTGRES_EXAMPLES = """\
Examples (PostgreSQL database mode):

Q: "sales of model CH086 last 2 years"
SQL: SELECT sku, sale_date, quantity, total_amount FROM raw_sales_transactions WHERE model = 'CH086' AND sale_date >= CURRENT_DATE - INTERVAL '2 years' ORDER BY sale_date LIMIT 100

Q: "top 10 models by total revenue"
SQL: SELECT model, SUM(quantity) AS total_qty, SUM(total_amount) AS total_revenue FROM raw_sales_transactions GROUP BY model ORDER BY total_revenue DESC LIMIT 10

Q: "stock below reorder point"
SQL: SELECT s.sku, s.model, s.available_stock, st.reorder_point, st.product_type FROM mv_latest_stock s JOIN mv_valid_sku_stats st ON s.sku = st.entity_id WHERE s.available_stock < st.reorder_point ORDER BY (st.reorder_point - s.available_stock) DESC LIMIT 100

Q: "monthly sales trend for model JU386"
SQL: SELECT year_month, SUM(quantity) AS qty, SUM(total_amount) AS revenue FROM raw_sales_transactions WHERE model = 'JU386' GROUP BY year_month ORDER BY year_month

Q: "seasonal products with low stock"
SQL: SELECT s.sku, s.model, s.available_stock, st.product_type, st.reorder_point FROM mv_latest_stock s JOIN mv_valid_sku_stats st ON s.sku = st.entity_id WHERE st.product_type = 'seasonal' AND s.available_stock < st.reorder_point ORDER BY s.available_stock LIMIT 100

Q: "category breakdown of sales"
SQL: SELECT c.kategoria, c.podgrupa, SUM(r.quantity) AS total_qty FROM raw_sales_transactions r JOIN category_mappings c ON r.model = c.model GROUP BY c.kategoria, c.podgrupa ORDER BY total_qty DESC LIMIT 50
"""


def get_schema_context(is_database_mode: bool) -> str:
    if is_database_mode:
        return f"{POSTGRES_SCHEMA}\n{QUERY_GUIDELINES}\n{POSTGRES_EXAMPLES}"
    return f"{DUCKDB_SCHEMA}\n{QUERY_GUIDELINES}\n{DUCKDB_EXAMPLES}"
