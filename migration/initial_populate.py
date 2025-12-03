import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uuid
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from tqdm import tqdm

from sales_data.loader import SalesDataLoader

sys.path.insert(0, str(Path(__file__).parent))
from utils.import_utils import (
    compute_file_hash,
    is_file_imported,
    log_file_import,
    process_sales_file_in_batches,
)

load_dotenv(find_dotenv(filename=".env"))

BATCH_SIZE = 1000


def _log_failed_import(engine, file_path, file_hash, batch_id, error_message):
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                          INSERT INTO file_imports (file_path, file_name, file_type, file_hash, file_size,
                                                    import_batch_id, import_status, error_message,
                                                    import_triggered_by)
                          VALUES (:file_path, :file_name, :file_type, :file_hash, :file_size,
                                  :import_batch_id, :import_status, :error_message,
                                  :import_triggered_by)
                          """
            ),
            {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": "sales_archival",
                "file_hash": file_hash,
                "file_size": file_path.stat().st_size if file_path.exists() else None,
                "import_batch_id": batch_id,
                "import_status": "failed",
                "error_message": error_message,
                "import_triggered_by": "initial_populate",
            },
        )
        conn.commit()


def _process_archival_file(engine, loader, file_info):
    file_path, start_date, end_date, file_hash = file_info
    batch_id = str(uuid.uuid4())
    file_start_time = datetime.now()

    df = loader.load_sales_file(file_path)

    if df.empty:
        print(f"Skipping empty file: {file_path.name}")
        return 0

    records_imported = process_sales_file_in_batches(
        df, engine, file_path, start_date, end_date, batch_id, "archival", BATCH_SIZE
    )

    processing_time = int((datetime.now() - file_start_time).total_seconds() * 1000)

    log_file_import(
        engine,
        file_path,
        file_hash,
        start_date,
        end_date,
        batch_id,
        records_imported,
        processing_time,
        "sales_archival",
        "initial_populate",
    )

    print(f"OK {file_path.name}: {records_imported} records ({processing_time}ms)")
    return records_imported


def _collect_archival_files_to_import(engine, loader):
    if not loader.archival_sales_dir.exists():
        print(f"Archival sales directory not found: {loader.archival_sales_dir}")
        return []

    files_to_import = []
    for file_path, start_date, end_date in loader.collect_files_from_directory(
        loader.archival_sales_dir
    ):
        file_hash = compute_file_hash(file_path)
        if not is_file_imported(engine, file_hash, "sales_archival"):
            files_to_import.append((file_path, start_date, end_date, file_hash))

    return files_to_import


def _toggle_cache_triggers(engine, enable: bool):
    action = "enable" if enable else "disable"
    with engine.connect() as conn:
        conn.execute(text(f"SELECT {action}_cache_triggers()"))
        conn.commit()
    status = "re-enabled" if enable else "disabled for bulk import"
    print(f"✓ Cache invalidation triggers {status}")


def populate_archival_sales(connection_string: str):
    print("Starting archival sales data import...")
    print("=" * 60)

    engine = create_engine(connection_string)
    loader = SalesDataLoader()

    files_to_import = _collect_archival_files_to_import(engine, loader)

    if not files_to_import:
        print("No new archival files to import")
        return

    print(f"Found {len(files_to_import)} files to import")

    _toggle_cache_triggers(engine, enable=False)

    total_records = 0

    for file_info in tqdm(files_to_import, desc="Importing files"):
        try:
            total_records += _process_archival_file(engine, loader, file_info)
        except (ValueError, OSError, IOError) as e:
            file_path, _, _, file_hash = file_info
            batch_id = str(uuid.uuid4())
            print(f"ERROR importing {file_path.name}: {str(e)}")
            _log_failed_import(engine, file_path, file_hash, batch_id, str(e))

    _toggle_cache_triggers(engine, enable=True)

    print("=" * 60)
    print(f"✓ Import complete: {total_records} total records imported")

    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Set it in .env file or export it:")
        print("  export DATABASE_URL='postgresql://user:password@localhost:5432/inventory_db'")
        sys.exit(1)

    populate_archival_sales(db_url)
