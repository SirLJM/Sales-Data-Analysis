from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).parent.parent.parent))

from sales_data.loader import SalesDataLoader
from sales_data.validator import DataValidator

load_dotenv()


def import_category_mappings():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")

    engine = create_engine(database_url)
    loader = SalesDataLoader()

    print("=" * 60)
    print("Category Mappings Import")
    print("=" * 60)

    print("\n1. Loading category data from Excel...")
    try:
        category_df = loader.load_category_data()
        print(f"   ✓ Loaded {len(category_df)} category mappings")
    except Exception as e:
        print(f"   ✗ Failed to load: {str(e)}")
        return

    print("\n2. Validating data structure...")
    try:
        DataValidator.validate_category_data(category_df)
        print("   ✓ Validation passed")
    except Exception as e:
        print(f"   ✗ Validation failed: {str(e)}")
        return

    print("\n3. Preparing data for database...")
    db_df = category_df.rename(columns={
        "Model": "model",
        "Grupa": "grupa",
        "Podgrupa": "podgrupa",
        "Kategoria": "kategoria",
        "Nazwa": "nazwa"
    })

    records = cast(list[dict[str, Any]], db_df.to_dict('records'))
    print(f"   ✓ Prepared {len(records)} records")

    print("\n4. Inserting into database...")
    insert_query = """
                   INSERT INTO category_mappings (model, grupa, podgrupa, kategoria, nazwa)
                   VALUES (:model, :grupa, :podgrupa, :kategoria, :nazwa)
                   ON CONFLICT (model)
                       DO UPDATE SET grupa      = EXCLUDED.grupa,
                                     podgrupa   = EXCLUDED.podgrupa,
                                     kategoria  = EXCLUDED.kategoria,
                                     nazwa      = EXCLUDED.nazwa,
                                     updated_at = CURRENT_TIMESTAMP \
                   """

    try:
        with engine.begin() as conn:  # type: ignore[attr-defined]
            conn.execute(text(insert_query), records)
            print(f"   ✓ Inserted/updated {len(records)} records")
    except Exception as e:
        print(f"   ✗ Database insert failed: {str(e)}")
        return

    print("\n5. Verifying import...")
    with engine.begin() as conn:  # type: ignore[attr-defined]
        count_result = conn.execute(text("SELECT COUNT(*) FROM category_mappings"))
        total_count = count_result.scalar()

        podgrupa_result = conn.execute(
            text("SELECT podgrupa, COUNT(*) as cnt FROM category_mappings GROUP BY podgrupa ORDER BY cnt DESC")
        )
        podgrupa_counts = podgrupa_result.fetchall()

        print(f"   ✓ Total records in database: {total_count}")
        print("\n   Distribution by Podgrupa:")
        for podgrupa, count in podgrupa_counts:
            print(f"      - {podgrupa}: {count}")

    print("\n" + "=" * 60)
    print("Import completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    import_category_mappings()
