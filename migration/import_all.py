from __future__ import annotations

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
from utils.import_utils import log_info, log_error, log_header


def _fetch_single_row(conn, query: str) -> tuple:
    return conn.execute(text(query)).fetchone()


def refresh_materialized_views(connection_string: str) -> None:
    log_header("Refreshing materialized views...")

    engine = create_engine(connection_string)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT matviewname FROM pg_matviews
                WHERE schemaname = 'public' ORDER BY matviewname
            """))
            views = [row[0] for row in result]

            if not views:
                log_info("  No materialized views found (this is normal if not created yet)")
                engine.dispose()
                return

            for view in views:
                log_info(f"Refreshing {view}...")
                try:
                    conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                    conn.commit()
                    log_info("  OK")
                except Exception as e:
                    log_info(f"  Skipped ({str(e)[:50]}...)")

        log_info("Materialized views refresh complete")
    except Exception as e:
        log_error(f"Error refreshing views: {str(e)[:100]}")

    engine.dispose()


def _print_sales_summary(conn) -> None:
    row = _fetch_single_row(conn, """
        SELECT COUNT(*) as total, MIN(sale_date), MAX(sale_date),
               COUNT(DISTINCT sku), COUNT(DISTINCT order_id), SUM(total_amount)
        FROM raw_sales_transactions
    """)
    log_info("\nSales Transactions:")
    log_info(f"  Total transactions:  {row[0]:,}")
    log_info(f"  Date range:          {row[1].date()} to {row[2].date()}")
    log_info(f"  Unique SKUs:         {row[3]:,}")
    log_info(f"  Unique orders:       {row[4]:,}")
    revenue = f"${row[5]:,.2f}" if row[5] else "$0.00"
    log_info(f"  Total revenue:       {revenue}")


def _print_stock_summary(conn) -> None:
    row = _fetch_single_row(conn, """
        SELECT COUNT(*), COUNT(DISTINCT snapshot_date) FROM stock_snapshots
    """)
    log_info("\nStock Snapshots:")
    log_info(f"  Total records:       {row[0]:,}")
    log_info(f"  Unique dates:        {row[1]}")


def _print_forecast_summary(conn) -> None:
    row = _fetch_single_row(conn, """
        SELECT COUNT(*), COUNT(DISTINCT sku), COUNT(DISTINCT generated_date)
        FROM forecast_data
    """)
    log_info("\nForecast Data:")
    log_info(f"  Total records:       {row[0]:,}")
    log_info(f"  Unique SKUs:         {row[1]:,}")
    log_info(f"  Forecast versions:   {row[2]}")


def _print_file_imports_summary(conn) -> None:
    result = conn.execute(text("""
        SELECT file_type, COUNT(*), import_status
        FROM file_imports
        GROUP BY file_type, import_status
        ORDER BY file_type, import_status
    """))
    log_info("\nFile Imports:")
    for row in result:
        log_info(f"  {row[0]:20s} {row[2]:10s} {row[1]:3d} files")


def print_import_summary(connection_string: str) -> None:
    log_header("DATABASE IMPORT SUMMARY")

    engine = create_engine(connection_string)

    with engine.connect() as conn:
        _print_sales_summary(conn)
        _print_stock_summary(conn)
        _print_forecast_summary(conn)
        _print_file_imports_summary(conn)

    engine.dispose()
    log_info("=" * 60)


def main() -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        log_error("Error: DATABASE_URL not set")
        log_error("Please check your .env file")
        sys.exit(1)

    log_header("COMPLETE DATABASE IMPORT")
    log_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = datetime.now()

    import_steps = [
        ("Importing archival sales data", populate_archival_sales),
        ("Importing current year sales data", import_current_sales),
        ("Importing stock data", import_stock_data),
        ("Importing forecast data", import_forecast_data),
        ("Importing model metadata", import_model_metadata),
        ("Importing size aliases", import_size_aliases),
        ("Importing color aliases", import_color_aliases),
        ("Refreshing materialized views", refresh_materialized_views),
    ]

    for i, (description, func) in enumerate(import_steps, 1):
        log_info(f"\nStep {i}: {description}...")
        func(db_url)

    elapsed = (datetime.now() - start_time).total_seconds()

    print_import_summary(db_url)

    log_info(f"\nComplete import finished in {elapsed:.1f} seconds")
    log_info("\nNext steps:")
    log_info("  1. Populate cache: python src/migration/populate_cache.py")
    log_info("  2. Update .env: Set DATA_SOURCE_MODE=database")
    log_info("  3. Run app: cd src && py -3.13 -m streamlit run app.py")
    log_info("")


if __name__ == "__main__":
    main()
