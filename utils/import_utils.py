from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def compute_file_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def is_file_imported(engine: Engine, file_hash: str, file_type: str) -> bool:
    query = text(
        """
        SELECT COUNT(*) as count
        FROM file_imports
        WHERE file_hash = :file_hash AND file_type = :file_type
    """
    )

    with engine.connect() as conn:
        result = conn.execute(query, {"file_hash": file_hash, "file_type": file_type})
        row = result.fetchone()
        if row is None:
            return False
        return bool(row[0] > 0)


def insert_sales_batch(engine: Engine, batch_data: list[dict]) -> int:
    with engine.connect() as conn:
        conn.execute(
            text(
                """
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
        """
            ),
            batch_data,
        )
        conn.commit()
    return len(batch_data)


def parse_sku_components(sku: str) -> tuple[str | None, str | None, str | None]:
    model = sku[:5] if len(sku) >= 5 else None
    color = sku[5:7] if len(sku) >= 7 else None
    size = sku[7:9] if len(sku) >= 9 else None
    return model, color, size


def build_sales_record(
    row: Any,
    file_path: Path,
    start_date: datetime,
    end_date: datetime,
    batch_id: str,
    data_source: str = "current",
) -> dict:
    sku = row["sku"]
    sale_date = row["data"]
    model, color, size = parse_sku_components(sku)

    return {
        "order_id": row["order_id"],
        "sale_date": sale_date,
        "sku": sku,
        "quantity": row["ilosc"],
        "unit_price": row["cena"],
        "total_amount": row["razem"],
        "model": model,
        "color": color,
        "size": size,
        "year_month": sale_date.strftime("%Y-%m") if sale_date else None,
        "source_file": file_path.name,
        "file_start_date": start_date,
        "file_end_date": end_date,
        "import_batch_id": batch_id,
        "data_source": data_source,
    }


def build_forecast_record(
    row: Any, generation_date: datetime, file_path: Path, batch_id: str
) -> dict:
    sku = row["sku"]
    forecast_date = row["data"]
    model, _, _ = parse_sku_components(sku)

    return {
        "forecast_date": forecast_date,
        "sku": sku,
        "forecast_quantity": row["forecast"],
        "model": model,
        "generated_date": generation_date,
        "source_file": file_path.name,
        "import_batch_id": batch_id,
    }


def build_stock_record(row: Any, snapshot_date: datetime, file_path: Path, batch_id: str) -> dict:
    sku = row["sku"]
    model, _, _ = parse_sku_components(sku)

    return {
        "snapshot_date": snapshot_date,
        "sku": sku,
        "product_name": row["nazwa"] if "nazwa" in row.index else "",
        "net_price": row["cena_netto"] if "cena_netto" in row.index else 0,
        "available_stock": row["available_stock"] if "available_stock" in row.index else 0,
        "model": model,
        "source_file": file_path.name,
        "import_batch_id": batch_id,
    }


def log_file_import(
    engine: Engine,
    file_path: Path,
    file_hash: str,
    start_date: datetime | None,
    end_date: datetime | None,
    batch_id: str,
    records_imported: int,
    processing_time_ms: int,
    file_type: str = "sales_current",
    import_trigger: str = "manual",
    import_status: str = "completed",
) -> None:
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                INSERT INTO file_imports (file_path, file_name, file_type, file_hash, file_size,
                                          file_start_date, file_end_date, import_batch_id,
                                          import_status, records_imported, records_failed,
                                          processing_time_ms, import_triggered_by)
                VALUES (:file_path, :file_name, :file_type, :file_hash, :file_size,
                        :file_start_date, :file_end_date, :import_batch_id,
                        :import_status, :records_imported, :records_failed,
                        :processing_time_ms, :import_triggered_by)
            """
            ),
            {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": file_type,
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


def process_sales_file_in_batches(
    df: pd.DataFrame,
    engine: Engine,
    file_path: Path,
    start_date: datetime,
    end_date: datetime,
    batch_id: str,
    data_source: str = "current",
    batch_size: int = 1000,
) -> int:
    records_imported = 0
    batch_data = []

    for _, row in df.iterrows():
        batch_data.append(
            build_sales_record(row, file_path, start_date, end_date, batch_id, data_source)
        )

        if len(batch_data) >= batch_size:
            records_imported += insert_sales_batch(engine, batch_data)
            batch_data = []

    if batch_data:
        records_imported += insert_sales_batch(engine, batch_data)

    return records_imported
