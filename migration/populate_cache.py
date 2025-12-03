import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(find_dotenv(filename=".env"))


def populate_monthly_aggregations_cache():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return 1

    print("=" * 60)
    print("Populating Monthly Aggregations Cache")
    print("=" * 60)

    engine = create_engine(db_url)

    try:
        for entity_type in ["sku", "model"]:
            print(f"\nProcessing {entity_type.upper()} aggregations...")

            if entity_type == "model":
                group_col = "model"
            else:
                group_col = "sku"

            query = f"""
                SELECT
                    '{entity_type}' as entity_type,
                    {group_col} as entity_id,
                    TO_CHAR(sale_date, 'YYYY-MM') as year_month,
                    SUM(quantity) as total_quantity,
                    SUM(total_amount) as total_revenue,
                    COUNT(*) as transaction_count,
                    COUNT(DISTINCT order_id) as unique_orders,
                    AVG(unit_price) as avg_unit_price
                FROM raw_sales_transactions
                WHERE is_valid = TRUE
                  AND {group_col} IS NOT NULL
                GROUP BY {group_col}, TO_CHAR(sale_date, 'YYYY-MM')
                ORDER BY {group_col}, year_month
            """

            print("  Computing aggregations from raw_sales_transactions...")

            with engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)

                if df.empty:
                    print(f"  [WARN] No data found for {entity_type}")
                    continue

                print(f"  Computed {len(df):,} aggregation records")

                print("  Clearing existing cache...")
                conn.execute(
                    text("DELETE FROM cache_monthly_aggregations WHERE entity_type = :entity_type"),
                    {"entity_type": entity_type}
                )
                conn.commit()

                print("  Inserting into cache_monthly_aggregations...")

                records = df.to_dict('records')
                conn.execute(
                    text("""
                         INSERT INTO cache_monthly_aggregations (entity_type, entity_id, year_month,
                                                                 total_quantity, total_revenue, transaction_count,
                                                                 unique_orders, avg_unit_price,
                                                                 cache_version, computed_at, is_valid)
                         VALUES (:entity_type, :entity_id, :year_month,
                                 :total_quantity, :total_revenue, :transaction_count,
                                 :unique_orders, :avg_unit_price,
                                 1, CURRENT_TIMESTAMP, TRUE)
                         """),
                    records
                )
                conn.commit()

                print(f"  [OK] Inserted {len(records):,} records")

        print("\nRefreshing materialized view...")
        with engine.connect() as conn:
            conn.execute(text("REFRESH MATERIALIZED VIEW mv_valid_monthly_aggs"))
            conn.commit()

            result = conn.execute(text("SELECT COUNT(*) FROM mv_valid_monthly_aggs"))
            count = result.fetchone()[0]
            print(f"  [OK] mv_valid_monthly_aggs: {count:,} rows")

        print("\n" + "=" * 60)
        print("Cache population complete!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    exit_code = populate_monthly_aggregations_cache()
    sys.exit(exit_code)
