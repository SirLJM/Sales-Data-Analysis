from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader
from utils.import_utils import (
    compute_file_hash,
    is_file_imported,
    log_file_import,
    process_sales_file_in_batches,
)
from utils.parallel_loader import parallel_load

load_dotenv(find_dotenv(filename=".env"))

BATCH_SIZE = 1000


def _collect_files_to_import(engine, loader):
    if not loader.current_sales_dir.exists():
        print(f"Current sales directory not found: {loader.current_sales_dir}")
        return []

    current_files = loader.collect_files_from_directory(loader.current_sales_dir)

    if not current_files:
        print("No current sales files found")
        return []

    current_files.sort(key=lambda x: x[2], reverse=True)

    files_to_import = []
    for file_path, start_date, end_date in current_files:
        file_hash = compute_file_hash(file_path)
        if not is_file_imported(engine, file_hash, "sales_current"):
            files_to_import.append((file_path, start_date, end_date, file_hash))

    return files_to_import


def _load_single_file(
        loader: SalesDataLoader, file_info: tuple
) -> tuple[tuple, pd.DataFrame] | None:
    file_path, _, _, _ = file_info
    try:
        df = loader.load_sales_file(file_path)
        if df.empty:
            print(f"  Skipping empty file: {file_path.name}")
            return None
        print(f"  Loaded: {file_path.name} ({len(df):,} rows)")
        return file_info, df
    except (ValueError, OSError, IOError) as e:
        print(f"  ERROR loading {file_path.name}: {e}")
        return None


def _insert_single_file(engine, file_info: tuple, df: pd.DataFrame) -> int:
    file_path, start_date, end_date, file_hash = file_info
    batch_id = str(uuid.uuid4())
    file_start_time = datetime.now()

    records_imported = process_sales_file_in_batches(
        df, engine, file_path, start_date, end_date, batch_id, "current", BATCH_SIZE
    )

    processing_time_ms = int((datetime.now() - file_start_time).total_seconds() * 1000)

    log_file_import(
        engine,
        file_path,
        file_hash,
        start_date,
        end_date,
        batch_id,
        records_imported,
        processing_time_ms,
        "sales_current",
        "import_current_sales",
    )

    print(f"  OK {file_path.name}: {records_imported} records ({processing_time_ms}ms)")
    return records_imported


def _print_import_summary(files_to_import):
    print(f"Found {len(files_to_import)} file(s) to import:")
    for file_path, start_date, end_date, _ in files_to_import:
        print(f"  - {file_path.name}: {start_date.date()} to {end_date.date()}")


def import_current_sales(connection_string: str):
    print("Starting current year sales data import...")
    print("=" * 60)

    engine = create_engine(connection_string)
    loader = SalesDataLoader()

    files_to_import = _collect_files_to_import(engine, loader)

    if not files_to_import:
        print("No new current sales files to import")
        return

    _print_import_summary(files_to_import)

    print(f"\nLoading {len(files_to_import)} file(s) in parallel...")
    loaded_data = parallel_load(
        files_to_import,
        lambda info: _load_single_file(loader, info),
        desc="Loading sales files",
    )

    if not loaded_data:
        print("No files loaded successfully")
        engine.dispose()
        return

    print(f"\nInserting {len(loaded_data)} file(s) to database...")
    total_records = 0
    for file_info, df in tqdm(loaded_data, desc="Inserting files"):
        try:
            total_records += _insert_single_file(engine, file_info, df)
        except (ValueError, OSError, IOError) as exc:
            file_path = file_info[0]
            print(f"ERROR inserting {file_path.name}: {exc}")

    print("=" * 60)
    print(f"Import complete: {total_records} total records imported")
    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_current_sales(db_url)
