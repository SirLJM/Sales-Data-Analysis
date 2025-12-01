import sys
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import uuid
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader
from utils.import_utils import compute_file_hash, is_file_imported, insert_sales_batch

load_dotenv(find_dotenv(filename='.env'))

BATCH_SIZE = 1000

def _parse_sku_components(sku: str):
    model = sku[:5] if len(sku) >= 5 else None
    color = sku[5:7] if len(sku) >= 7 else None
    size = sku[7:9] if len(sku) >= 9 else None
    return model, color, size


def _prepare_sale_record(row, file_path, start_date, end_date, batch_id):
    sku = row['sku']
    sale_date = row['data']
    model, color, size = _parse_sku_components(sku)

    return {
        'order_id': row['order_id'],
        'sale_date': sale_date,
        'sku': sku,
        'quantity': row['ilosc'],
        'unit_price': row['cena'],
        'total_amount': row['razem'],
        'model': model,
        'color': color,
        'size': size,
        'year_month': sale_date.strftime('%Y-%m') if sale_date else None,
        'source_file': file_path.name,
        'file_start_date': start_date,
        'file_end_date': end_date,
        'import_batch_id': batch_id,
        'data_source': 'current'
    }


def _record_file_import(engine, file_path, file_hash, start_date, end_date, batch_id, records_imported, processing_time):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO file_imports (
                file_path, file_name, file_type, file_hash, file_size,
                file_start_date, file_end_date, import_batch_id,
                import_status, records_imported, records_failed,
                processing_time_ms, import_triggered_by
            ) VALUES (
                :file_path, :file_name, :file_type, :file_hash, :file_size,
                :file_start_date, :file_end_date, :import_batch_id,
                :import_status, :records_imported, :records_failed,
                :processing_time_ms, :import_triggered_by
            )
        """), {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_type': 'sales_current',
            'file_hash': file_hash,
            'file_size': file_path.stat().st_size,
            'file_start_date': start_date,
            'file_end_date': end_date,
            'import_batch_id': batch_id,
            'import_status': 'completed',
            'records_imported': records_imported,
            'records_failed': 0,
            'processing_time_ms': processing_time,
            'import_triggered_by': 'import_current_sales'
        })
        conn.commit()


def _process_dataframe_in_batches(df, engine, file_path, start_date, end_date, batch_id, batch_size=1000):
    records_imported = 0
    batch_data = []

    for _, row in df.iterrows():
        batch_data.append(_prepare_sale_record(row, file_path, start_date, end_date, batch_id))

        if len(batch_data) >= batch_size:
            records_imported += insert_sales_batch(engine, batch_data)
            batch_data = []

    if batch_data:
        records_imported += insert_sales_batch(engine, batch_data)

    return records_imported


def _import_single_file(engine, loader, file_path, start_date, end_date, file_hash):
    batch_id = str(uuid.uuid4())
    file_start_time = datetime.now()

    df = loader.load_sales_file(file_path)

    if df.empty:
        print(f"Skipping empty file: {file_path.name}")
        return 0

    records_imported = _process_dataframe_in_batches(df, engine, file_path, start_date, end_date, batch_id)
    processing_time = int((datetime.now() - file_start_time).total_seconds() * 1000)

    _record_file_import(engine, file_path, file_hash, start_date, end_date, batch_id, records_imported, processing_time)

    print(f"OK {file_path.name}: {records_imported} records ({processing_time}ms)")
    return records_imported


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

def build_sales_record(
        row,
        file_path,
        start_date,
        end_date,
        batch_id: str,
) -> dict:
    sku = row["sku"]
    sale_date = row["data"]

    return {
        "order_id": row["order_id"],
        "sale_date": sale_date,
        "sku": sku,
        "quantity": row["ilosc"],
        "unit_price": row["cena"],
        "total_amount": row["razem"],
        "model": sku[:5] if len(sku) >= 5 else None,
        "color": sku[5:7] if len(sku) >= 7 else None,
        "size": sku[7:9] if len(sku) >= 9 else None,
        "year_month": sale_date.strftime("%Y-%m") if sale_date else None,
        "source_file": file_path.name,
        "file_start_date": start_date,
        "file_end_date": end_date,
        "import_batch_id": batch_id,
        "data_source": "current",
    }


def log_file_import(
        engine,
        file_path,
        file_hash: str,
        start_date,
        end_date,
        batch_id: str,
        records_imported: int,
        processing_time_ms: int,
        table_type: str = "sales_current",
        import_trigger: str = "import_current_sales",
        import_status: str = "completed",
) -> None:
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                INSERT INTO file_imports (
                    file_path, file_name, file_type, file_hash, file_size,
                    file_start_date, file_end_date, import_batch_id,
                    import_status, records_imported, records_failed,
                    processing_time_ms, import_triggered_by
                ) VALUES (
                             :file_path, :file_name, :file_type, :file_hash, :file_size,
                             :file_start_date, :file_end_date, :import_batch_id,
                             :import_status, :records_imported, :records_failed,
                             :processing_time_ms, :import_triggered_by
                         )
                """
            ),
            {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": table_type,
                "file_hash": file_hash,
                "file_size": file_path.stat().st_size,
                "file_start_date": start_date,
                "file_end_date": end_date,
                "import_batch_id": batch_id,
                "import_status": import_status,
                "records_imported": records_imported,
                "records_failed": 0,
                "processing_time_ms": processing_time_ms,
                "import_triggered_by": import_trigger,
            },
        )
        conn.commit()

def import_current_sales(db_connection_string: str):
    print("Starting current year sales data import...")
    print("=" * 60)

    engine = create_engine(db_connection_string)
    loader = SalesDataLoader()

    if not loader.current_sales_dir.exists():
        print(f"Current sales directory not found: {loader.current_sales_dir}")
        return

    current_files = loader.collect_files_from_directory(loader.current_sales_dir)
    if not current_files:
        print("No current sales files found")
        return

    current_files.sort(key=lambda x: x[2], reverse=True)

    files_to_import = []
    for file_path, start_date, end_date in current_files:
        file_hash = compute_file_hash(file_path)
        if not is_file_imported(engine, file_hash, "sales_current"):
            files_to_import.append((file_path, start_date, end_date, file_hash))

    if not files_to_import:
        print("No new current sales files to import")
        return

    print(f"Found {len(files_to_import)} file(s) to import:")
    for file_path, start_date, end_date, _ in files_to_import:
        print(f"  - {file_path.name}: {start_date.date()} to {end_date.date()}")

    total_records = 0

    for file_path, start_date, end_date, file_hash in tqdm(
            files_to_import, desc="Importing files"
    ):
        batch_id = str(uuid.uuid4())
        file_start_time = datetime.now()

        try:
            sales_df = loader.load_sales_file(file_path)
            if sales_df.empty:
                print(f"Skipping empty file: {file_path.name}")
                continue

            records_imported = 0
            batch_data = []

            for _, row in sales_df.iterrows():
                batch_data.append(
                    build_sales_record(
                        row=row,
                        file_path=file_path,
                        start_date=start_date,
                        end_date=end_date,
                        batch_id=batch_id,
                    )
                )

                if len(batch_data) >= BATCH_SIZE:
                    records_imported += insert_sales_batch(engine, batch_data)
                    batch_data = []

            if batch_data:
                records_imported += insert_sales_batch(engine, batch_data)

            processing_time_ms = int(
                (datetime.now() - file_start_time).total_seconds() * 1000
            )

            log_file_import(
                engine=engine,
                file_path=file_path,
                file_hash=file_hash,
                start_date=start_date,
                end_date=end_date,
                batch_id=batch_id,
                records_imported=records_imported,
                processing_time_ms=processing_time_ms,
            )

            total_records += records_imported
            print(
                f"OK {file_path.name}: {records_imported} records ({processing_time_ms}ms)"
            )

        except Exception as exc:
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
