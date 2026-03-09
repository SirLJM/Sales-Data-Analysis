from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from exceptions import MaterialConstraintError
from utils.logging_config import get_logger

logger = get_logger(__name__)

_CONSTRAINT_PATTERN = re.compile(r"min\s+(\d+)\s+(?:i\s+)?maks\s+(\d+)", re.IGNORECASE)

COL_GSM = 2
COL_NAME = 3
COL_BUTOR_KETY = 10
COL_SIERADZ = 11
COL_KONIN = 12


@dataclass
class MaterialConstraint:
    min_qty: int | None
    max_qty: int | None
    even_only: bool


@dataclass
class MaterialRow:
    gsm: str
    material_name: str
    butor_kety: MaterialConstraint | None
    sieradz: MaterialConstraint | None
    konin: MaterialConstraint | None


def parse_constraint_string(value: object) -> MaterialConstraint | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    text = str(value).strip().lower()

    if not text or text == "nan" or text == "n/d":
        return None

    if "parzyście" in text or "parzyscie" in text:
        return MaterialConstraint(min_qty=None, max_qty=None, even_only=True)

    match = _CONSTRAINT_PATTERN.search(text)
    if match:
        return MaterialConstraint(
            min_qty=int(match.group(1)),
            max_qty=int(match.group(2)),
            even_only=False,
        )

    logger.warning("Unrecognized constraint format: '%s'", text)
    return None


def _normalize_gsm(raw: str) -> str:
    text = str(raw).replace("\xa0", "").strip().upper()
    text = re.sub(r"[Gg]\s*$", "", text)
    text = text.strip()
    range_match = re.match(r"(\d+)", text)
    if range_match:
        return range_match.group(1)
    return text


def load_material_constraints(path: str | Path) -> list[MaterialRow]:
    path = Path(path)
    if not path.exists():
        raise MaterialConstraintError(f"Material constraints file not found: {path}")

    try:
        df = pd.read_excel(path, header=None)
    except Exception as e:
        raise MaterialConstraintError(f"Failed to read material constraints: {e}") from e

    rows: list[MaterialRow] = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        gsm_raw = row.iloc[COL_GSM]
        name_raw = row.iloc[COL_NAME]

        if pd.isna(gsm_raw) and pd.isna(name_raw):
            continue

        gsm = str(gsm_raw).strip() if not pd.isna(gsm_raw) else ""
        material_name = str(name_raw).strip() if not pd.isna(name_raw) else ""

        rows.append(MaterialRow(
            gsm=gsm,
            material_name=material_name,
            butor_kety=parse_constraint_string(row.iloc[COL_BUTOR_KETY]),
            sieradz=parse_constraint_string(row.iloc[COL_SIERADZ]),
            konin=parse_constraint_string(row.iloc[COL_KONIN]),
        ))

    logger.info("Loaded %d material constraint rows from %s", len(rows), path.name)
    return rows


def find_constraint_for_model(
    rows: list[MaterialRow],
    gramatura: str,
    rodzaj_materialu: str,
) -> MaterialRow | None:
    if not gramatura and not rodzaj_materialu:
        return None

    target_gsm = _normalize_gsm(gramatura) if gramatura else ""
    target_name = rodzaj_materialu.strip().lower() if rodzaj_materialu else ""

    for row in rows:
        if _matches_material_row(row, target_gsm, target_name):
            return row

    return None


def _matches_material_row(row: MaterialRow, target_gsm: str, target_name: str) -> bool:
    row_gsm = _normalize_gsm(row.gsm) if row.gsm else ""
    row_name = row.material_name.strip().lower() if row.material_name else ""

    gsm_matches = target_gsm and row_gsm and target_gsm == row_gsm
    gsm_conflicts = target_gsm and row_gsm and target_gsm != row_gsm
    name_matches = target_name and row_name and target_name == row_name
    name_conflicts = target_name and row_name and target_name != row_name

    if gsm_conflicts or name_conflicts:
        return False

    return bool(gsm_matches or name_matches)


def resolve_facility_constraint(
    row: MaterialRow,
    szwalnia_glowna: str,
) -> MaterialConstraint | None:
    if not szwalnia_glowna:
        return None

    facility = szwalnia_glowna.upper()

    if "BUTOR" in facility or "KĘTY" in facility or "KETY" in facility:
        return row.butor_kety
    if "SIERADZ" in facility:
        return row.sieradz
    if "KONIN" in facility:
        return row.konin

    logger.warning("Unknown facility '%s', cannot resolve constraint", szwalnia_glowna)
    return None
