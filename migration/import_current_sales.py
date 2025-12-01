import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader
from utils.import_utils import (
    compute_file_hash,
    is_file_imported,
    log_file_import,
    process_sales_file_in_batches
)

load_dotenv(find_dotenv(filename='.env'))

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
        if not is_file_imported(engine, file_hash, 'sales_current'):
            files_to_import.append((file_path, start_date, end_date, file_hash))

    return files_to_import


def _process_single_file(engine, loader, file_info):
    file_path, start_date, end_date, file_hash = file_info
    batch_id = str(uuid.uuid4())
    file_start_time = datetime.now()

    sales_df = loader.load_sales_file(file_path)
    if sales_df.empty:
        print(f"Skipping empty file: {file_path.name}")
        return 0

    records_imported = process_sales_file_in_batches(
        sales_df, engine, file_path, start_date, end_date, batch_id, 'current', BATCH_SIZE
    )

    processing_time_ms = int((datetime.now() - file_start_time).total_seconds() * 1000)

    log_file_import(
        engine, file_path, file_hash, start_date, end_date, batch_id,
        records_imported, processing_time_ms, 'sales_current', 'import_current_sales'
    )

    print(f"OK {file_path.name}: {records_imported} records ({processing_time_ms}ms)")
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

    total_records = 0

    for file_info in tqdm(files_to_import, desc="Importing files"):
        try:
            total_records += _process_single_file(engine, loader, file_info)
        except (ValueError, OSError, IOError) as exc:
            file_path = file_info[0]
            print(f"ERROR importing {file_path.name}: {exc}")

    print("=" * 60)
    print(f"Import complete: {total_records} total records imported")
    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_current_sales(db_url)
