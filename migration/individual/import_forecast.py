from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader
from utils.import_utils import build_forecast_record

load_dotenv(find_dotenv(filename=".env"))

BATCH_SIZE = 1000


def _is_forecast_already_imported(engine, generated_date):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM forecast_data
            WHERE generated_date = :generated_date
        """
            ),
            {"generated_date": generated_date},
        )
        return result.fetchone()[0] > 0


def _insert_forecast_batch(engine, batch_data):
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            INSERT INTO forecast_data (
                forecast_date, sku, forecast_quantity,
                model, generated_date,
                source_file, import_batch_id
            )
            VALUES (
                :forecast_date, :sku, :forecast_quantity,
                :model, :generated_date,
                :source_file, :import_batch_id
            )
            ON CONFLICT (sku, forecast_date, generated_date) DO NOTHING
        """
            ),
            batch_data,
        )
        conn.commit()


def _process_forecast_file(engine, loader, file_path, generation_date):
    batch_id = str(uuid.uuid4())

    if _is_forecast_already_imported(engine, generation_date):
        print(f"  Skipping - forecast from {generation_date.date()} already exists")
        return

    df = loader.load_forecast_file(file_path)

    if df.empty:
        print("  Skipping empty file")
        return

    batch_data = []
    for _, row in df.iterrows():
        batch_data.append(build_forecast_record(row, generation_date, file_path, batch_id))

        if len(batch_data) >= BATCH_SIZE:
            _insert_forecast_batch(engine, batch_data)
            batch_data = []

    if batch_data:
        _insert_forecast_batch(engine, batch_data)

    print(f"  OK Imported forecast records for {df['sku'].nunique()} SKUs")


def _print_forecast_files_summary(forecast_files):
    print(f"Found {len(forecast_files)} forecast file(s):")
    for file_path, generation_date in forecast_files:
        print(f"  - {file_path.name}: generated {generation_date.date()}")


def import_forecast_data(connection_string: str):
    print("Starting forecast data import...")
    print("=" * 60)

    engine = create_engine(connection_string)
    loader = SalesDataLoader()

    forecast_files = loader.find_forecast_files()

    if not forecast_files:
        print("No forecast files found")
        return

    _print_forecast_files_summary(forecast_files)

    for file_path, generation_date in forecast_files:
        print(f"\nProcessing: {file_path.name}")
        try:
            _process_forecast_file(engine, loader, file_path, generation_date)
        except (ValueError, OSError, IOError) as e:
            print(f"  ERROR: {e}")

    print("=" * 60)
    print("Forecast import complete")
    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_forecast_data(db_url)
