from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader

load_dotenv(find_dotenv(filename=".env"))


def import_color_aliases(connection_string: str) -> None:
    print("Starting color aliases import...")
    print("=" * 60)

    engine: Engine = create_engine(connection_string)

    loader = SalesDataLoader()
    color_mapping = loader.load_color_aliases()

    if not color_mapping:
        print("ERROR: No color aliases found")
        return

    df = pd.DataFrame(list(color_mapping.items()), columns=["color_code", "color_name"])
    df = df.dropna()

    print(f"Loaded {len(df)} color mappings from file")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM color_aliases"))
        existing_count = result.fetchone()[0]
        print(f"Current database has {existing_count} color aliases")

    batch_data = df.to_dict("records")

    with engine.connect() as conn:
        for record in batch_data:
            conn.execute(
                text("""
                     INSERT INTO color_aliases (color_code, color_name)
                     VALUES (:color_code, :color_name)
                     ON CONFLICT (color_code) DO UPDATE SET color_name = EXCLUDED.color_name, updated_at = CURRENT_TIMESTAMP
                     """),
                record,
            )
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM color_aliases"))
        new_count = result.fetchone()[0]
        print(f"  OK Database now has {new_count} color aliases")

    print("\nSample mappings:")
    sample_df = df.head(10)
    for _, row in sample_df.iterrows():
        print(f"  {row['color_code']} -> {row['color_name']}")

    print("=" * 60)
    print("Color aliases import complete")

    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        print("\nPlease create a .env file in the project root with:")
        print("DATABASE_URL=postgresql://user:password@localhost:5432/inventory_db")
        sys.exit(1)

    import_color_aliases(db_url)
