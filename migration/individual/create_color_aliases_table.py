from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(find_dotenv(filename=".env"))


def create_color_aliases_table(connection_string: str) -> None:
    print("Creating color_aliases table...")
    print("=" * 60)

    engine = create_engine(connection_string)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'color_aliases')")
            )
            row = result.fetchone()
            table_exists = row[0] if row else False

            if table_exists:
                print("Table 'color_aliases' already exists")
                return

            print("Creating color_aliases table...")

            conn.execute(text("""
                CREATE TABLE color_aliases (
                    id SERIAL PRIMARY KEY,

                    color_code VARCHAR(2) NOT NULL UNIQUE,
                    color_name VARCHAR(100) NOT NULL,

                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """))

            conn.execute(text("CREATE INDEX idx_color_aliases_code ON color_aliases(color_code);"))
            conn.execute(text("CREATE INDEX idx_color_aliases_name ON color_aliases(color_name);"))

            conn.commit()

            print("  OK Table 'color_aliases' created successfully")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

    print("=" * 60)


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        print("\nPlease create a .env file in the project root with:")
        print("DATABASE_URL=postgresql://user:password@localhost:5432/inventory_db")
        sys.exit(1)

    create_color_aliases_table(db_url)
