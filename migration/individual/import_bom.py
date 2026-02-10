from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_data.loader import SalesDataLoader

load_dotenv(find_dotenv(filename=".env"))

UPSERT_BOM_SQL = """
    INSERT INTO bom_components (
        model, main_material_name, main_consumption_m2, main_consumption_mb,
        main_consumption_kg, main_yield_mb_kg, main_width,
        ribbing_type, ribbing_consumption_mb, lining_consumption_mb,
        is_outlet, is_withdrawn
    ) VALUES (
        :model, :main_material_name, :main_consumption_m2, :main_consumption_mb,
        :main_consumption_kg, :main_yield_mb_kg, :main_width,
        :ribbing_type, :ribbing_consumption_mb, :lining_consumption_mb,
        :is_outlet, :is_withdrawn
    )
    ON CONFLICT (model) DO UPDATE SET
        main_material_name     = EXCLUDED.main_material_name,
        main_consumption_m2    = EXCLUDED.main_consumption_m2,
        main_consumption_mb    = EXCLUDED.main_consumption_mb,
        main_consumption_kg    = EXCLUDED.main_consumption_kg,
        main_yield_mb_kg       = EXCLUDED.main_yield_mb_kg,
        main_width             = EXCLUDED.main_width,
        ribbing_type           = EXCLUDED.ribbing_type,
        ribbing_consumption_mb = EXCLUDED.ribbing_consumption_mb,
        lining_consumption_mb  = EXCLUDED.lining_consumption_mb,
        is_outlet              = EXCLUDED.is_outlet,
        is_withdrawn           = EXCLUDED.is_withdrawn,
        updated_at             = CURRENT_TIMESTAMP
"""

UPSERT_CATALOG_SQL = """
    INSERT INTO material_catalog (
        material_name, supplier, composition, material_type,
        layout_width, yield_m_per_kg
    ) VALUES (
        :material_name, :supplier, :composition, :material_type,
        :layout_width, :yield_m_per_kg
    )
    ON CONFLICT (material_name) DO UPDATE SET
        supplier       = EXCLUDED.supplier,
        composition    = EXCLUDED.composition,
        material_type  = EXCLUDED.material_type,
        layout_width   = EXCLUDED.layout_width,
        yield_m_per_kg = EXCLUDED.yield_m_per_kg,
        updated_at     = CURRENT_TIMESTAMP
"""


def _safe_str(value: Any) -> str | None:
    if pd.isna(value) or str(value) == "None":
        return None
    return str(value).strip()


def _safe_float(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _safe_bool(value: Any) -> bool:
    if pd.isna(value):
        return False
    return bool(value)


def _row_to_bom(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": str(row.get("model", "")).strip(),
        "main_material_name": _safe_str(row.get("main_material_name")),
        "main_consumption_m2": _safe_float(row.get("main_consumption_m2")),
        "main_consumption_mb": _safe_float(row.get("main_consumption_mb")),
        "main_consumption_kg": _safe_float(row.get("main_consumption_kg")),
        "main_yield_mb_kg": _safe_float(row.get("main_yield_mb_kg")),
        "main_width": _safe_float(row.get("main_width")),
        "ribbing_type": _safe_str(row.get("ribbing_type")),
        "ribbing_consumption_mb": _safe_float(row.get("ribbing_consumption_mb")),
        "lining_consumption_mb": _safe_float(row.get("lining_consumption_mb")),
        "is_outlet": _safe_bool(row.get("is_outlet")),
        "is_withdrawn": _safe_bool(row.get("is_withdrawn")),
    }


def _row_to_catalog(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "material_name": str(row.get("material_name", "")).strip(),
        "supplier": _safe_str(row.get("supplier")),
        "composition": _safe_str(row.get("composition")),
        "material_type": _safe_str(row.get("material_type")),
        "layout_width": _safe_float(row.get("layout_width")),
        "yield_m_per_kg": _safe_float(row.get("yield_m_per_kg")),
    }


def _get_count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        row = result.fetchone()
        return int(row[0]) if row else 0


def import_bom_data(connection_string: str) -> None:
    print("Starting BOM data import...")
    print("=" * 60)

    engine: Engine = create_engine(connection_string)
    loader = SalesDataLoader()

    bom_df = loader.load_bom_data()
    if bom_df is not None and not bom_df.empty:
        print(f"Loaded {len(bom_df)} BOM entries from file")

        batch_data = [
            _row_to_bom(row)
            for row in cast(list[dict[str, Any]], bom_df.to_dict("records"))
        ]

        with engine.connect() as conn:
            conn.execute(text(UPSERT_BOM_SQL), batch_data)
            conn.commit()

        print(f"  OK Database now has {_get_count(engine, 'bom_components')} BOM entries")
    else:
        print("No BOM data found to import")

    catalog_df = loader.load_material_catalog()
    if catalog_df is not None and not catalog_df.empty:
        print(f"Loaded {len(catalog_df)} material catalog entries from file")

        batch_data = [
            _row_to_catalog(row)
            for row in cast(list[dict[str, Any]], catalog_df.to_dict("records"))
        ]

        with engine.connect() as conn:
            conn.execute(text(UPSERT_CATALOG_SQL), batch_data)
            conn.commit()

        print(f"  OK Database now has {_get_count(engine, 'material_catalog')} catalog entries")
    else:
        print("No material catalog data found to import")

    engine.dispose()
    print("=" * 60)
    print("BOM data import complete")


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)

    import_bom_data(db_url)
