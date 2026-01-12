from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader
from utils.import_utils import build_forecast_record
from utils.parallel_loader import parallel_load

load_dotenv(find_dotenv(filename=".env"))

BATCH_SIZE = 1000


def _check_existing_dates(engine: Engine, forecast_files: list[tuple[Path, datetime]]) -> set[datetime]:
    dates = [d for _, d in forecast_files]
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT DISTINCT generated_date
                FROM forecast_data
                WHERE generated_date = ANY (:dates)
            """),
            {"dates": dates},
        )
        return {row[0] for row in result.fetchall()}


def _insert_forecast_batch(engine: Engine, batch_data: list[dict]) -> None:
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO forecast_data (forecast_date, sku, forecast_quantity,
                                           model, generated_date,
                                           source_file, import_batch_id)
                VALUES (:forecast_date, :sku, :forecast_quantity,
                        :model, :generated_date,
                        :source_file, :import_batch_id)
                ON CONFLICT (sku, forecast_date, generated_date) DO NOTHING
            """),
            batch_data,
        )
        conn.commit()


def _load_forecast_file(
    loader: SalesDataLoader, file_info: tuple[Path, datetime]
) -> tuple[Path, datetime, pd.DataFrame] | None:
    file_path, generation_date = file_info
    try:
        df = loader.load_forecast_file(file_path)
        if df.empty:
            print(f"  Skipping empty file: {file_path.name}")
            return None
        print(f"  Loaded: {file_path.name} ({len(df):,} rows)")
        return file_path, generation_date, df
    except (ValueError, OSError, IOError) as e:
        print(f"  ERROR loading {file_path.name}: {e}")
        return None


def _insert_forecast_file(
    engine: Engine, file_path: Path, generation_date: datetime, df: pd.DataFrame
) -> None:
    batch_id = str(uuid.uuid4())
    batch_data = [
        build_forecast_record(row, generation_date, file_path, batch_id)
        for _, row in df.iterrows()
    ]

    for i in range(0, len(batch_data), BATCH_SIZE):
        _insert_forecast_batch(engine, batch_data[i:i + BATCH_SIZE])

    print(f"  OK Imported forecast records for {df['sku'].nunique()} SKUs from {file_path.name}")


def _print_forecast_files_summary(forecast_files: list[tuple[Path, datetime]]) -> None:
    print(f"Found {len(forecast_files)} forecast file(s):")
    for file_path, generation_date in forecast_files:
        print(f"  - {file_path.name}: generated {generation_date.date()}")


def import_forecast_data(connection_string: str) -> None:
    print("Starting forecast data import...")
    print("=" * 60)

    engine = create_engine(connection_string)
    loader = SalesDataLoader()

    forecast_files = loader.find_forecast_files()

    if not forecast_files:
        print("No forecast files found")
        return

    _print_forecast_files_summary(forecast_files)

    existing_dates = _check_existing_dates(engine, forecast_files)
    files_to_import = [
        (path, date) for path, date in forecast_files if date not in existing_dates
    ]

    if not files_to_import:
        print("\nAll forecasts already imported, nothing to do")
        engine.dispose()
        return

    skipped = len(forecast_files) - len(files_to_import)
    if skipped > 0:
        print(f"\nSkipping {skipped} already imported file(s)")

    print(f"\nLoading {len(files_to_import)} file(s) in parallel...")
    loaded_data = parallel_load(
        files_to_import,
        lambda info: _load_forecast_file(loader, info),
        desc="Loading forecast files",
    )

    if not loaded_data:
        print("No files loaded successfully")
        engine.dispose()
        return

    print(f"\nInserting {len(loaded_data)} file(s) to database...")
    for file_path, generation_date, df in loaded_data:
        try:
            _insert_forecast_file(engine, file_path, generation_date, df)
        except (ValueError, OSError, IOError) as e:
            print(f"  ERROR inserting {file_path.name}: {e}")

    print("=" * 60)
    print("Forecast import complete")
    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_forecast_data(db_url)
