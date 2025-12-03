import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()


def refresh_materialized_views():
    """Refresh all materialized views to populate cached data."""

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return 1

    print("=" * 60)
    print("Refreshing Materialized Views")
    print("=" * 60)

    engine = create_engine(db_url)

    views_to_refresh = [
        "mv_valid_monthly_aggs",
        "mv_valid_sku_stats",
        "mv_valid_order_priorities",
    ]

    try:
        with engine.connect() as conn:
            for view in views_to_refresh:
                print(f"\n  Refreshing {view}...")

                check_query = text("""
                                   SELECT COUNT(*)
                                   FROM pg_matviews
                                   WHERE matviewname = :view_name
                                   """)
                result = conn.execute(check_query, {"view_name": view})
                exists = result.fetchone()[0] > 0

                if not exists:
                    print("    [SKIP] View does not exist")
                    continue

                # Count rows before refresh
                count_query = text(f"SELECT COUNT(*) FROM {view}")
                result = conn.execute(count_query)
                before_count = result.fetchone()[0]

                # Refresh the view
                refresh_query = text(f"REFRESH MATERIALIZED VIEW {view}")
                conn.execute(refresh_query)
                conn.commit()

                # Count rows after refresh
                result = conn.execute(count_query)
                after_count = result.fetchone()[0]

                print(f"    [OK] Refreshed: {before_count} -> {after_count} rows")

        print("\n" + "=" * 60)
        print("All views refreshed successfully!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n  [ERROR] Failed to refresh views: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    exit_code = refresh_materialized_views()
    sys.exit(exit_code)
