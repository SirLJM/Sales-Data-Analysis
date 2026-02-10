from __future__ import annotations

import pandas as pd

from utils.logging_config import get_logger

logger = get_logger("material_planning")

LINING_MATERIAL_NAME = "SINGLE JERSEY Z ELASTANEM 180G"

RIBBING_TYPE_MAP: dict[str, str] = {
    "2x1": "ŚCIĄGACZ 2/1",
    "1x1": "ŚCIĄGACZ 1/1",
    "2x2": "ŚCIĄGACZ 2/2",
    "1x1 100": "ŚCIĄGACZ 1/1",
    "1x1 wiskoza": "ŚCIĄGACZ WISKOZOWY 2/1",
}


def map_ribbing_type_to_material(ribbing_type: str) -> str | None:
    if not ribbing_type:
        return None
    normalized = ribbing_type.strip().lower()
    return RIBBING_TYPE_MAP.get(normalized)


def extract_production_quantities_from_orders(
    active_orders: list[dict],
) -> pd.DataFrame:
    if not active_orders:
        return pd.DataFrame(columns=["model", "quantity"])

    rows = []
    for order in active_orders:
        model = order.get("model", "")
        quantity = order.get("total_quantity", 0)
        if model and quantity:
            rows.append({"model": str(model).strip().upper(), "quantity": int(quantity)})

    if not rows:
        return pd.DataFrame(columns=["model", "quantity"])

    df = pd.DataFrame(rows)
    return df.groupby("model", as_index=False).agg(quantity=("quantity", "sum"))


def _build_main_material_rows(
    bom_row: dict, quantity: int
) -> list[dict]:
    material_name = bom_row.get("main_material_name")
    if not material_name or str(material_name) == "None":
        return []

    consumption_mb = float(bom_row.get("main_consumption_mb", 0) or 0)
    consumption_kg = float(bom_row.get("main_consumption_kg", 0) or 0)

    if consumption_mb == 0 and consumption_kg == 0:
        return []

    return [{
        "material_name": str(material_name),
        "component_type": "main",
        "total_meters": consumption_mb * quantity,
        "total_kg": consumption_kg * quantity,
        "model": bom_row["model"],
        "quantity": quantity,
    }]


def _build_ribbing_rows(
    bom_row: dict, quantity: int
) -> list[dict]:
    ribbing_type = bom_row.get("ribbing_type")
    if not ribbing_type:
        return []

    material_name = map_ribbing_type_to_material(str(ribbing_type))
    if not material_name:
        return []

    consumption_mb = float(bom_row.get("ribbing_consumption_mb", 0) or 0)
    if consumption_mb == 0:
        return []

    return [{
        "material_name": material_name,
        "component_type": "ribbing",
        "total_meters": consumption_mb * quantity,
        "total_kg": 0.0,
        "model": bom_row["model"],
        "quantity": quantity,
    }]


def _build_lining_rows(
    bom_row: dict, quantity: int
) -> list[dict]:
    consumption_mb = float(bom_row.get("lining_consumption_mb", 0) or 0)
    if consumption_mb == 0:
        return []

    return [{
        "material_name": LINING_MATERIAL_NAME,
        "component_type": "lining",
        "total_meters": consumption_mb * quantity,
        "total_kg": 0.0,
        "model": bom_row["model"],
        "quantity": quantity,
    }]


def calculate_material_requirements(
    production_quantities: pd.DataFrame, bom_data: pd.DataFrame
) -> pd.DataFrame:
    if production_quantities.empty or bom_data.empty:
        return pd.DataFrame(columns=[
            "material_name", "component_type", "total_meters",
            "total_kg", "contributing_models", "model_count",
        ])

    merged = production_quantities.merge(bom_data, on="model", how="inner")

    if merged.empty:
        logger.warning("No matching models between production quantities and BOM data")
        return pd.DataFrame(columns=[
            "material_name", "component_type", "total_meters",
            "total_kg", "contributing_models", "model_count",
        ])

    all_rows: list[dict] = []
    for row in merged.to_dict("records"):
        qty = int(row["quantity"])
        all_rows.extend(_build_main_material_rows(row, qty))
        all_rows.extend(_build_ribbing_rows(row, qty))
        all_rows.extend(_build_lining_rows(row, qty))

    if not all_rows:
        return pd.DataFrame(columns=[
            "material_name", "component_type", "total_meters",
            "total_kg", "contributing_models", "model_count",
        ])

    detail_df = pd.DataFrame(all_rows)

    aggregated = detail_df.groupby(
        ["material_name", "component_type"], as_index=False
    ).agg(
        total_meters=("total_meters", "sum"),
        total_kg=("total_kg", "sum"),
        contributing_models=("model", lambda x: ", ".join(sorted(set(x)))),
        model_count=("model", "nunique"),
    )

    return aggregated.sort_values("total_meters", ascending=False).reset_index(drop=True)


def _merge_stock_and_calculate_gap(
    result: pd.DataFrame, material_stock: pd.DataFrame
) -> pd.DataFrame:
    stock_cols = ["material_name"]
    if "quantity_meters" in material_stock.columns:
        stock_cols.append("quantity_meters")
    if "quantity_kg" in material_stock.columns:
        stock_cols.append("quantity_kg")

    result = result.merge(
        material_stock[stock_cols].drop_duplicates(),
        on="material_name",
        how="left",
    )

    if "quantity_meters" in result.columns:
        result["quantity_meters"] = result["quantity_meters"].fillna(0)
        result["gap_meters"] = result["total_meters"] - result["quantity_meters"]
    else:
        result["quantity_meters"] = 0.0
        result["gap_meters"] = result["total_meters"]

    if "quantity_kg" in result.columns:
        result["quantity_kg"] = result["quantity_kg"].fillna(0)
        result["gap_kg"] = result["total_kg"] - result["quantity_kg"]
    else:
        result["quantity_kg"] = 0.0
        result["gap_kg"] = result["total_kg"]

    return result


def calculate_material_gap(
    requirements: pd.DataFrame,
    material_stock: pd.DataFrame | None,
    material_catalog: pd.DataFrame | None,
) -> pd.DataFrame:
    result = requirements.copy()

    if material_catalog is not None and not material_catalog.empty:
        result = result.merge(
            material_catalog[["material_name", "supplier"]].drop_duplicates(),
            on="material_name",
            how="left",
        )
    else:
        result["supplier"] = None

    if material_stock is not None and not material_stock.empty:
        result = _merge_stock_and_calculate_gap(result, material_stock)
    else:
        result["quantity_meters"] = 0.0
        result["quantity_kg"] = 0.0
        result["gap_meters"] = result["total_meters"]
        result["gap_kg"] = result["total_kg"]

    return result
