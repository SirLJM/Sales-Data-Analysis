from __future__ import annotations

import logging
import re
import tempfile
from datetime import datetime
from io import BytesIO

from camelot import read_pdf
from pypdf import PdfReader

from utils.logging_config import get_logger

logging.getLogger("pypdf").setLevel(logging.ERROR)

FOLDING = "składanie"

logger = get_logger("pdf_parser")

_facilities: list[str] = []
_categories: list[str] = []


def set_lookup_data(facilities: list[str], categories: list[str]) -> None:
    global _facilities, _categories
    _facilities = facilities
    _categories = categories


def parse_order_pdf(pdf_file: BytesIO | str) -> dict | None:
    try:
        if isinstance(pdf_file, BytesIO):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_file.getvalue())
                pdf_path = tmp.name
        else:
            pdf_path = pdf_file

        try:
            reader = PdfReader(pdf_path)
            page_text = reader.pages[0].extract_text()
            tables = read_pdf(pdf_path, pages="1", flavor="stream")

            if not tables:
                logger.warning("No tables found in PDF")
                return None

            return _extract_order_metadata(tables, page_text)
        finally:
            if isinstance(pdf_file, BytesIO):
                import os
                os.unlink(pdf_path)

    except Exception as e:
        logger.exception("Error parsing PDF: %s", e)
        return None


def _extract_operation(line_lower: str) -> str | None:
    if "szycie" in line_lower and FOLDING in line_lower:
        return "szycie i składanie"
    if "szycie" in line_lower:
        return "szycie"
    if FOLDING in line_lower:
        return FOLDING
    return None


def _extract_facility(line_lower: str) -> str | None:
    for facility in _facilities:
        facility_lower = facility.lower()
        facility_words = facility_lower.split()
        for word in facility_words:
            if len(word) > 3 and word in line_lower:
                return facility
    return None


def _extract_material(line: str) -> str | None:
    line_upper = line.upper()
    if "GSM" in line_upper:
        gsm_match = re.search(r"(\d+)\s*GSM", line_upper)
        material_keywords = ["DRES", "PĘTELKA", "DRAPANA", "SINGIEL"]
        material_parts = []
        for keyword in material_keywords:
            if keyword in line_upper:
                material_parts.append(keyword)
        if gsm_match:
            material_parts.append(f"{gsm_match.group(1)} GSM")
        if material_parts:
            return " ".join(material_parts)
    return None


def _get_product_keywords() -> list[str]:
    keywords = [c.upper() for c in _categories if c]
    default_keywords = ["BLUZA", "SUKIENKA", "SPODNIE", "KOSZULKA", "KAPTUR", "DRESS", "ŁATY"]
    for kw in default_keywords:
        if kw not in keywords:
            keywords.append(kw)
    return keywords


def _clean_product_name(name: str) -> str:
    return re.sub(r"\s*\d+\s*SZTUK.*", "", name.strip())


def _extract_product_name_from_text(page_text: str) -> str | None:
    keywords = _get_product_keywords()
    keywords_pattern = "|".join(re.escape(kw) for kw in keywords)
    product_patterns = [
        rf"((?:NOWA\s+)?(?:{keywords_pattern})(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ]+){{0,3}})",
        r"(\w+\s+kopertowa)",
    ]
    for pattern in product_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            return _clean_product_name(match.group(1))
    return None


def _cell_matches_keyword(cell_value: str, keywords: list[str]) -> bool:
    if len(cell_value) >= 50:
        return False
    return any(kw in cell_value.upper() for kw in keywords)


def _extract_product_name_from_table(tables) -> str | None:
    keywords = _get_product_keywords()
    for table in tables:
        df = table.df
        for row_idx in range(min(10, len(df))):
            for col_idx in range(len(df.columns)):
                cell_value = str(df.iloc[row_idx, col_idx]).strip()
                if _cell_matches_keyword(cell_value, keywords):
                    return cell_value
    return None


def _extract_model_from_table(tables) -> str | None:
    for table in tables:
        df = table.df
        for row_idx in range(min(10, len(df))):
            for col_idx in range(len(df.columns)):
                cell_value = str(df.iloc[row_idx, col_idx]).strip()
                model_match = re.search(r"([A-Z]{2}\d{3})", cell_value)
                if model_match:
                    return model_match.group(1)
    return None


def _extract_quantity_from_table(tables) -> int | None:
    for table in tables:
        df = table.df
        for row_idx in range(len(df)):
            cell_value = str(df.iloc[row_idx, -1]).strip()
            if cell_value.isdigit():
                qty = int(cell_value)
                if qty >= 100:
                    return qty
    return None


def _extract_order_metadata(tables, page_text: str) -> dict:
    metadata: dict = {
        "order_date": None,
        "model": None,
        "product_name": None,
        "material": None,
        "facility": None,
        "operation": None,
        "total_quantity": None,
    }

    date_match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', page_text)
    if date_match:
        metadata["order_date"] = _parse_date(date_match.group(1))

    for line in page_text.split('\n'):
        line_lower = line.lower()
        if not metadata["operation"]:
            metadata["operation"] = _extract_operation(line_lower)
        if not metadata["facility"]:
            metadata["facility"] = _extract_facility(line_lower)
        if not metadata["material"]:
            metadata["material"] = _extract_material(line)

    metadata["product_name"] = _extract_product_name_from_table(tables)
    if not metadata["product_name"]:
        metadata["product_name"] = _extract_product_name_from_text(page_text)

    qty_match = re.search(r"(\d+)\s*SZTUK", page_text)
    if qty_match:
        metadata["total_quantity"] = int(qty_match.group(1))
    else:
        metadata["total_quantity"] = _extract_quantity_from_table(tables)

    metadata["model"] = _extract_model_from_table(tables)
    if not metadata["model"]:
        model_match = re.search(r"([A-Z]{2}\d{3})", page_text)
        if model_match:
            metadata["model"] = model_match.group(1)

    return metadata


def _is_date_format(text: str) -> bool:
    date_pattern = r"\d{1,2}\.\d{1,2}\.\d{4}"
    return bool(re.match(date_pattern, text))


def _parse_date(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None
