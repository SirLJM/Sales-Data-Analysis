import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(find_dotenv(filename=".env"))


def create_orders_tables(connection_string: str) -> None:
    print("Starting orders table creation...")
    print("=" * 60)

    engine: Engine = create_engine(connection_string)

    schema_file = Path(__file__).parent / "sql" / "orders_schema.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return

    print(f"Found schema file: {schema_file.name}")

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        print("Executing schema SQL...")

        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()

        print("  OK Schema executed successfully")

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('orders', 'order_items', 'order_history')
                    ORDER BY table_name
                    """
                )
            )
            tables = result.fetchall()
            print(f"  OK Verified {len(tables)} tables created:")
            for table in tables:
                print(f"     - {table[0]}")

    except Exception as e:
        print(f"  ERROR: {e}")
        print("\nThis script is safe to run multiple times.")
        print("If tables already exist, this is expected behavior.")
    finally:
        engine.dispose()

    print("=" * 60)
    print("Orders table creation complete")


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        print("\nPlease create a .env file in the project root with:")
        print("DATABASE_URL=postgresql://user:password@localhost:5432/inventory_db")
        print("\nOr set DATA_SOURCE_MODE=file to use file-based data source")
        sys.exit(1)

    create_orders_tables(db_url)
