import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(find_dotenv(filename=".env"))

from migration.individual.import_current_sales import import_current_sales
from migration.individual.import_forecast import import_forecast_data
from migration.individual.import_model_metadata import import_model_metadata
from migration.individual.import_size_aliases import import_size_aliases
from migration.individual.import_color_aliases import import_color_aliases
from migration.individual.import_stock import import_stock_data
from initial_populate import populate_archival_sales


def refresh_materialized_views(connection_string: str):
    print("\n" + "=" * 60)
    print("Refreshing materialized views...")
    print("=" * 60)

    engine = create_engine(connection_string)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT matviewname
                    FROM pg_matviews
                    WHERE schemaname = 'public'
                    ORDER BY matviewname
                    """
                )
            )
            views = [row[0] for row in result]

            if not views:
                print("  No materialized views found (this is normal if not created yet)")
                engine.dispose()
                return

            for view in views:
                print(f"Refreshing {view}...")
                try:
                    conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                    conn.commit()
                    print("  OK")
                except Exception as e:
                    print(f"  Skipped ({str(e)[:50]}...)")

        print("Materialized views refresh complete")
    except Exception as e:
        print(f"Error refreshing views: {str(e)[:100]}")

    engine.dispose()


def print_import_summary(connection_string: str):
    print("\n" + "=" * 60)
    print("DATABASE IMPORT SUMMARY")
    print("=" * 60)

    engine = create_engine(connection_string)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT COUNT(*)                 as total_transactions,
                       MIN(sale_date)           as earliest_sale,
                       MAX(sale_date)           as latest_sale,
                       COUNT(DISTINCT sku)      as unique_skus,
                       COUNT(DISTINCT order_id) as unique_orders,
                       SUM(total_amount)        as total_revenue
                FROM raw_sales_transactions
                """
            )
        )
        row = result.fetchone()

        print("\nSales Transactions:")
        print(f"  Total transactions:  {row[0]:,}")
        print(f"  Date range:          {row[1].date()} to {row[2].date()}")
        print(f"  Unique SKUs:         {row[3]:,}")
        print(f"  Unique orders:       {row[4]:,}")
        print(
            f"  Total revenue:       ${row[5]:,.2f}" if row[5] else "  Total revenue:       $0.00"
        )

        result = conn.execute(
            text(
                """
                SELECT COUNT(*) as total_records, COUNT(DISTINCT snapshot_date) as unique_dates
                FROM stock_snapshots
                """
            )
        )
        row = result.fetchone()
        print("\nStock Snapshots:")
        print(f"  Total records:       {row[0]:,}")
        print(f"  Unique dates:        {row[1]}")

        result = conn.execute(
            text(
                """
                SELECT COUNT(*)                       as total_records,
                       COUNT(DISTINCT sku)            as unique_skus,
                       COUNT(DISTINCT generated_date) as unique_generations
                FROM forecast_data
                """
            )
        )
        row = result.fetchone()
        print("\nForecast Data:")
        print(f"  Total records:       {row[0]:,}")
        print(f"  Unique SKUs:         {row[1]:,}")
        print(f"  Forecast versions:   {row[2]}")

        result = conn.execute(
            text(
                """
                SELECT file_type, COUNT(*) as count, import_status
                FROM file_imports
                GROUP BY file_type, import_status
                ORDER BY file_type, import_status
                """
            )
        )
        print("\nFile Imports:")
        for row in result:
            print(f"  {row[0]:20s} {row[2]:10s} {row[1]:3d} files")

    engine.dispose()
    print("=" * 60)


def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        print("Please check your .env file")
        sys.exit(1)

    print("=" * 60)
    print("COMPLETE DATABASE IMPORT")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    start_time = datetime.now()

    print("\nStep 1: Importing archival sales data...")
    populate_archival_sales(db_url)

    print("\nStep 2: Importing current year sales data...")
    import_current_sales(db_url)

    print("\nStep 3: Importing stock data...")
    import_stock_data(db_url)

    print("\nStep 4: Importing forecast data...")
    import_forecast_data(db_url)

    print("\nStep 5: Importing model metadata...")
    import_model_metadata(db_url)

    print("\nStep 6: Importing size aliases...")
    import_size_aliases(db_url)

    print("\nStep 7: Importing color aliases...")
    import_color_aliases(db_url)

    print("\nStep 8: Refreshing materialized views...")
    refresh_materialized_views(db_url)

    elapsed = (datetime.now() - start_time).total_seconds()

    print_import_summary(db_url)

    print(f"\nComplete import finished in {elapsed:.1f} seconds")
    print("\nNext steps:")
    print("  1. Populate cache: python src/migration/populate_cache.py")
    print("  2. Update .env: Set DATA_SOURCE_MODE=database")
    print("  3. Run app: cd src && py -3.13 -m streamlit run app.py")
    print()


if __name__ == "__main__":
    main()
