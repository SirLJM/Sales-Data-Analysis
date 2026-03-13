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


_MATERIAL_KEYWORDS: list[tuple[str, str]] = [
    ("single jersey", "single_jersey"),
    ("singiel", "single_jersey"),
    ("dresówka", "dresowka"),
    ("dres ", "dresowka"),
    ("pętelkowa", "petelka"),
    ("pętelka", "petelka"),
    ("drapana", "drapana"),
    ("diagonal", "diagonal"),
    ("diagonalna", "diagonal"),
    ("bawełna", "bawelna"),
    ("interlock", "interlock"),
    ("muślin", "muslin"),
    ("softshell", "softshell"),
    ("wiskoz", "wiskoza"),
    ("bambusow", "bambus"),
    ("bambus", "bambus"),
    ("lacosta", "lacosta"),
    ("pika", "lacosta"),
    ("ściągacz", "sciagacz"),
    ("prązkowana", "sciagacz"),
    ("ściągaczowa", "sciagacz"),
    ("len ", "len"),
    ("len\xa0", "len"),
    ("eko", "eko"),
    ("peach", "peach"),
    ("premium", "premium"),
]


def _extract_material_keywords(name: str) -> set[str]:
    text = name.lower().replace("\xa0", " ").strip() + " "
    keywords: set[str] = set()
    for pattern, keyword in _MATERIAL_KEYWORDS:
        if pattern in text:
            keywords.add(keyword)
    return keywords


def _keyword_score(name_a: str, name_b: str) -> float:
    kw_a = _extract_material_keywords(name_a)
    kw_b = _extract_material_keywords(name_b)
    if not kw_a or not kw_b:
        return 0.0
    overlap = len(kw_a & kw_b)
    total = max(len(kw_a), len(kw_b))
    return overlap / total if total > 0 else 0.0


def _filter_by_gsm(rows: list[MaterialRow], target_gsm: str) -> list[MaterialRow]:
    if not target_gsm:
        return []
    candidates = []
    for row in rows:
        row_gsm = _normalize_gsm(row.gsm) if row.gsm else ""
        if not row_gsm or row_gsm == "-":
            continue
        if row_gsm == target_gsm:
            candidates.append(row)
    return candidates


def _best_keyword_match(
    candidates: list[MaterialRow], martyny_nazwa: str
) -> MaterialRow | None:
    best_row: MaterialRow | None = None
    best_score = -1.0
    for row in candidates:
        score = _keyword_score(martyny_nazwa, row.material_name)
        if score > best_score:
            best_score = score
            best_row = row
    if best_score > 0:
        logger.debug(
            "Matched '%s' -> '%s' (score=%.2f)",
            martyny_nazwa,
            best_row.material_name if best_row else "?",
            best_score,
        )
        return best_row
    return None


def find_constraint_for_model(
    rows: list[MaterialRow],
    gramatura: str,
    martyny_nazwa: str,
) -> MaterialRow | None:
    if not gramatura and not martyny_nazwa:
        return None

    target_gsm = _normalize_gsm(gramatura) if gramatura else ""
    candidates = _filter_by_gsm(rows, target_gsm)

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    if not martyny_nazwa:
        return candidates[0]

    match = _best_keyword_match(candidates, martyny_nazwa)
    return match if match else candidates[0]


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
