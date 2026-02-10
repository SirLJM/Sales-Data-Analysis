from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def _get_sql_dir() -> Path:
    return Path(__file__).parent / "sql"


def _run_sql_file(engine, filename: str, description: str, continue_on_error: bool = True) -> bool:
    sql_file = _get_sql_dir() / filename

    if not sql_file.exists():
        print(f"   File not found: {sql_file}")
        return False

    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    try:
        with engine.connect() as conn:
            conn.execute(text(sql_content))
            conn.commit()
        print(f"   {description} created successfully")
        return True
    except Exception as e:
        print(f"   {description} creation failed: {e}")
        if continue_on_error:
            print("   Continuing...")
        return continue_on_error


def main():
    load_dotenv(Path(__file__).parent.parent / ".env")
    connection_string = os.environ.get("DATABASE_URL")

    if not connection_string:
        print("=" * 60)
        print("ERROR: DATABASE_URL not found in .env file")
        print("=" * 60)
        print("\nPlease create a .env file in the project root with:")
        print("DATABASE_URL=postgresql://inventory_user:password@localhost:5432/inventory_db")
        print("\nSee INSTALL_POSTGRESQL.md for detailed setup instructions")
        return 1

    print("=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60)

    print("\n1. Testing database connection...")
    engine = create_engine(connection_string)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            row = result.fetchone()
            version = str(row[0]) if row else "Unknown"
            print("   Connected successfully!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
    except Exception as e:
        print(f"   Connection failed: {e}")
        print("\nPlease verify:")
        print("  1. PostgreSQL is installed and running")
        print("  2. Database 'inventory_db' exists")
        print("  3. User 'inventory_user' exists with correct password")
        print("  4. .env file has correct DATABASE_URL")
        return 1

    sql_files = [
        ("schema.sql", "Schema", True),
        ("triggers.sql", "Triggers", True),
        ("orders_schema.sql", "Order tables", True),
        ("bom_schema.sql", "BOM tables", True),
        ("materialized_views.sql", "Materialized views", True),
    ]

    for idx, (filename, description, continue_on_error) in enumerate(sql_files, start=2):
        print(f"\n{idx}. Running {filename}...")
        if not _run_sql_file(engine, filename, description, continue_on_error):
            return 1

    print("\n6. Verifying database structure...")
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                    """
                )
            )
            tables = [row[0] for row in result]

            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"      - {table}")

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

            if views:
                print(f"\n   Found {len(views)} materialized views:")
                for view in views:
                    print(f"      - {view}")

            result = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM pg_trigger
                    WHERE tgname LIKE 'trg_%'
                    """
                )
            )
            trigger_row = result.fetchone()
            trigger_count = trigger_row[0] if trigger_row else 0
            print(f"\n   Found {trigger_count} triggers")

    except Exception as e:
        print(f"   Verification failed: {e}")
        return 1

    print("\n" + "=" * 60)
    print("Database setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Import data: python src/migration/import_all.py")
    print("  2. Populate cache: python src/migration/populate_cache.py")
    print("  3. Switch to database mode in .env: DATA_SOURCE_MODE=database")
    print("  4. Run app: cd src && py -m streamlit run app.py")

    engine.dispose()
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
