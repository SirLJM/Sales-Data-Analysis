import hashlib
from pathlib import Path
from sqlalchemy import text


def compute_file_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def is_file_imported(engine, file_hash: str, file_type: str) -> bool:
    query = text("""
        SELECT COUNT(*) as count
        FROM file_imports
        WHERE file_hash = :file_hash AND file_type = :file_type
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {'file_hash': file_hash, 'file_type': file_type})
        count = result.fetchone()[0]
        return count > 0


def insert_sales_batch(engine, batch_data: list) -> int:
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO raw_sales_transactions (
                order_id, sale_date, sku, quantity, unit_price, total_amount,
                model, color, size, year_month,
                source_file, file_start_date, file_end_date,
                import_batch_id, data_source
            )
            VALUES (
                :order_id, :sale_date, :sku, :quantity, :unit_price, :total_amount,
                :model, :color, :size, :year_month,
                :source_file, :file_start_date, :file_end_date,
                :import_batch_id, :data_source
            )
            ON CONFLICT (order_id, sku, sale_date, source_file) DO NOTHING
        """), batch_data)
        conn.commit()
    return len(batch_data)