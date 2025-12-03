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


def import_model_metadata(connection_string: str) -> None:
    print("Starting model metadata import...")
    print("=" * 60)

    engine: Engine = create_engine(connection_string)
    loader = SalesDataLoader()

    metadata_file = loader.find_model_metadata_file()

    if metadata_file is None:
        print("No model metadata file found")
        return

    print(f"Found metadata file: {metadata_file.name}")

    try:
        df = loader.load_model_metadata()

        if df is None or df.empty:
            print("No valid metadata to import")
            return

        print(f"Loaded {len(df)} models from file")

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM model_metadata"))
            existing_count = result.fetchone()[0]
            print(f"Current database has {existing_count} models")

        batch_data = [
            {
                "model": str(row["Model"]),
                "primary_production": str(row["SZWALNIA GŁÓWNA"]) if pd.notna(row["SZWALNIA GŁÓWNA"]) else "",
                "secondary_production": str(row["SZWALNIA DRUGA"]) if pd.notna(row["SZWALNIA DRUGA"]) else "",
                "material_type": str(row["RODZAJ MATERIAŁU"]) if pd.notna(row["RODZAJ MATERIAŁU"]) else "",
                "material_weight": str(row["GRAMATURA"]) if pd.notna(row["GRAMATURA"]) else "",
            }
            for row in df.to_dict('records')
        ]

        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO model_metadata (model, primary_production, secondary_production,
                                                material_type, material_weight)
                    VALUES (:model, :primary_production, :secondary_production,
                            :material_type, :material_weight)
                    ON CONFLICT (model) DO UPDATE SET primary_production   = EXCLUDED.primary_production,
                                                      secondary_production = EXCLUDED.secondary_production,
                                                      material_type        = EXCLUDED.material_type,
                                                      material_weight      = EXCLUDED.material_weight,
                                                      updated_at           = CURRENT_TIMESTAMP
                    """
                ),
                batch_data,
            )
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM model_metadata"))
            new_count = result.fetchone()[0]
            print(f"  OK Database now has {new_count} models")

    except (ValueError, OSError, IOError) as e:
        print(f"  ERROR: {e}")
    finally:
        engine.dispose()

    print("=" * 60)
    print("Model metadata import complete")


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_model_metadata(db_url)
