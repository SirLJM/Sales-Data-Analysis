import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader

load_dotenv(find_dotenv(filename='.env'))

BATCH_SIZE = 1000


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

    for file_path, snapshot_date in stock_files:
        print(f"\nProcessing: {file_path.name}")
        batch_id = str(uuid.uuid4())

        with engine.connect() as conn:
            result = conn.execute(text("""
                                       SELECT COUNT(*)
                                       FROM stock_snapshots
                                       WHERE snapshot_date = :snapshot_date
                                       """), {'snapshot_date': snapshot_date})

            if result.fetchone()[0] > 0:
                print(f"  Skipping - data for {snapshot_date.date()} already exists")
                continue

        try:
            df = loader.load_stock_file(file_path)

            if df.empty:
                print("  Skipping empty file")
                continue

            batch_data = [
                {
                    'snapshot_date': snapshot_date,
                    'sku': row.sku,
                    'product_name': getattr(row, 'nazwa', ''),
                    'net_price': getattr(row, 'cena_netto', 0),
                    'available_stock': getattr(row, 'available_stock', 0),
                    'model': row.sku[:5] if len(row.sku) >= 5 else None,
                    'source_file': file_path.name,
                    'import_batch_id': batch_id
                }
                for row in df.itertuples(index=False)
            ]

            with engine.connect() as conn:
                conn.execute(text("""
                                  INSERT INTO stock_snapshots (snapshot_date, sku, product_name, net_price,
                                                               available_stock,
                                                               model, source_file, import_batch_id)
                                  VALUES (:snapshot_date, :sku, :product_name, :net_price, :available_stock,
                                          :model, :source_file, :import_batch_id)
                                  """), batch_data)
                conn.commit()

            print(f"  OK Imported {len(batch_data)} stock records")

        except (ValueError, OSError, IOError) as e:
            print(f"  ERROR: {e}")

    print("=" * 60)
    print("Stock import complete")
    engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_stock_data(db_url)
