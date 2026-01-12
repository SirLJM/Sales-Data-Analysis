from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader
from utils.import_utils import build_stock_record
from utils.parallel_loader import parallel_load

load_dotenv(find_dotenv(filename=".env"))

BATCH_SIZE = 1000


def _load_stock_file(
        loader: SalesDataLoader, file_info: tuple[Path, datetime]
) -> tuple[Path, datetime, list[dict]] | None:
    file_path, snapshot_date = file_info
    try:
        df = loader.load_stock_file(file_path)
        if df.empty:
            return None
        print(f"  Loaded: {file_path.name} ({len(df):,} rows)")
        batch_id = str(uuid.uuid4())
        records = [build_stock_record(row, snapshot_date, file_path, batch_id) for _, row in df.iterrows()]
        return file_path, snapshot_date, records
    except (ValueError, OSError, IOError) as e:
        print(f"  ERROR loading {file_path.name}: {e}")
        return None


def _check_existing_dates(engine: Engine, stock_files: list) -> set[datetime]:
    dates = [d for _, d in stock_files]
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT DISTINCT snapshot_date
                FROM stock_snapshots
                WHERE snapshot_date = ANY (:dates)
                """
            ),
            {"dates": dates},
        )
        return {row[0] for row in result.fetchall()}


def import_stock_data(connection_string: str):
    print("Starting stock data import...")
    print("=" * 60)

    engine = create_engine(connection_string)
    loader = SalesDataLoader()

    stock_files = loader.find_stock_files()

    if not stock_files:
        print("No stock files found")
        return

    print(f"Found {len(stock_files)} stock file(s):")
    for file_path, snapshot_date in stock_files:
        print(f"  - {file_path.name}: {snapshot_date.date()}")

    existing_dates = _check_existing_dates(engine, stock_files)
    files_to_import = [
        (path, date) for path, date in stock_files if date not in existing_dates
    ]

    if not files_to_import:
        print("\nAll files already imported, nothing to do")
        engine.dispose()
        return

    skipped = len(stock_files) - len(files_to_import)
    if skipped > 0:
        print(f"\nSkipping {skipped} already imported file(s)")

    print(f"\nLoading {len(files_to_import)} file(s) in parallel...")
    loaded_data = parallel_load(
        files_to_import,
        lambda info: _load_stock_file(loader, info),
        desc="Loading stock files",
    )

    print(f"\nInserting {len(loaded_data)} file(s) to database...")
    for file_path, snapshot_date, records in loaded_data:
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO stock_snapshots (snapshot_date, sku, product_name, net_price,
                                                 available_stock, model, source_file, import_batch_id)
                    VALUES (:snapshot_date, :sku, :product_name, :net_price,
                            :available_stock, :model, :source_file, :import_batch_id)
                    """
                ),
                records,
            )
            conn.commit()

        print(f"  OK Imported {len(records)} stock records from {file_path.name}")

    print("=" * 60)
    print("Stock import complete")
    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_stock_data(db_url)
