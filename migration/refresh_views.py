from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

VIEWS_TO_REFRESH = [
    "mv_valid_monthly_aggs",
    "mv_valid_sku_stats",
    "mv_valid_order_priorities",
]


def _view_exists(conn, view_name: str) -> bool:
    query = text("SELECT COUNT(*) FROM pg_matviews WHERE matviewname = :view_name")
    result = conn.execute(query, {"view_name": view_name})
    return result.fetchone()[0] > 0


def _get_row_count(conn, view_name: str) -> int:
    result = conn.execute(text(f"SELECT COUNT(*) FROM {view_name}"))
    return result.fetchone()[0]


def _refresh_single_view(conn, view_name: str) -> None:
    print(f"\n  Refreshing {view_name}...")

    if not _view_exists(conn, view_name):
        print("    [SKIP] View does not exist")
        return

    before_count = _get_row_count(conn, view_name)
    conn.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
    conn.commit()
    after_count = _get_row_count(conn, view_name)

    print(f"    [OK] Refreshed: {before_count} -> {after_count} rows")


def refresh_materialized_views() -> int:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return 1

    print("=" * 60)
    print("Refreshing Materialized Views")
    print("=" * 60)

    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            for view in VIEWS_TO_REFRESH:
                _refresh_single_view(conn, view)

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
