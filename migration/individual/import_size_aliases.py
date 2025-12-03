import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import load_size_aliases_from_excel

load_dotenv(find_dotenv(filename=".env"))


def import_size_aliases(connection_string: str) -> None:
    print("Starting size aliases import...")
    print("=" * 60)

    engine: Engine = create_engine(connection_string)

    sizes_file = Path(__file__).parent.parent / "data" / "sizes.xlsx"

    if not sizes_file.exists():
        print(f"ERROR: Size aliases file not found: {sizes_file}")
        return

    print(f"Found sizes file: {sizes_file.name}")

    try:
        size_mapping = load_size_aliases_from_excel(sizes_file)
        df = pd.DataFrame(list(size_mapping.items()), columns=["size_code", "size_alias"])
        df = df.dropna()

        print(f"Loaded {len(df)} size mappings from file")

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM size_aliases"))
            existing_count = result.fetchone()[0]
            print(f"Current database has {existing_count} size aliases")

        batch_data = df.to_dict("records")

        with engine.connect() as conn:
            for record in batch_data:
                conn.execute(
                    text("""
                         INSERT INTO size_aliases (size_code, size_alias)
                         VALUES (:size_code, :size_alias)
                         ON CONFLICT (size_code) DO UPDATE SET size_alias = EXCLUDED.size_alias
                         """),
                    record,
                )
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM size_aliases"))
            new_count = result.fetchone()[0]
            print(f"  OK Database now has {new_count} size aliases")

        print("\nSample mappings:")
        sample_df = df.head(10)
        for _, row in sample_df.iterrows():
            print(f"  {row['size_code']} -> {row['size_alias']}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

    print("=" * 60)
    print("Size aliases import complete")


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        print("\nPlease create a .env file in the project root with:")
        print("DATABASE_URL=postgresql://user:password@localhost:5432/inventory_db")
        sys.exit(1)

    import_size_aliases(db_url)
