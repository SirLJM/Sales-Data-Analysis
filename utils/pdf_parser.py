from __future__ import annotations

import logging
import re
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
    logger.debug("Loaded %d facilities: %s", len(facilities), facilities[:5])
    logger.debug("Loaded %d categories: %s", len(categories), categories[:5])


def parse_order_pdf(pdf_file: BytesIO | str) -> dict | None:
    try:
        if isinstance(pdf_file, BytesIO):
            temp_path = "temp_order.pdf"
            with open(temp_path, "wb") as f:
                f.write(pdf_file.getvalue())
            pdf_path = temp_path
        else:
            pdf_path = pdf_file

        reader = PdfReader(pdf_path)
        page_text = reader.pages[0].extract_text()

        tables = read_pdf(pdf_path, pages="1", flavor="stream")

        if not tables or len(tables) < 2:
            logger.warning("Expected table not found in PDF")
            return None

        order_data = _extract_order_metadata(tables, page_text)

        return order_data

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
    if ("DRES" in line or "GSM" in line) and ("PĘTELKA" in line or "GSM" in line):
        return line.strip()
    return None


def _extract_product_name(line: str) -> str | None:
    if "SZTUK" not in line:
        return None
    product_match = re.search(r'(.+?)\s+\d+\s*SZTUK', line)
    if product_match:
        return product_match.group(1).strip()
    return line.split("SZTUK")[0].strip() if "SZTUK" in line else None


def _extract_model_from_table(tables) -> str | None:
    main_table = tables[1].df if len(tables) > 1 else tables[0].df
    for col_idx in range(len(main_table.columns)):
        cell_value = str(main_table.iloc[1, col_idx]).strip()
        if re.match(r"^[A-Z]{2}\d{3}$", cell_value):
            return cell_value
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
        if not metadata["product_name"]:
            metadata["product_name"] = _extract_product_name(line)

    qty_match = re.search(r"(\d+)\s*SZTUK", page_text)
    if qty_match:
        metadata["total_quantity"] = int(qty_match.group(1))

    metadata["model"] = _extract_model_from_table(tables)

    return metadata


def _is_date_format(text: str) -> bool:
    date_pattern = r"\d{1,2}\.\d{1,2}\.\d{4}"
    return bool(re.match(date_pattern, text))


def _parse_date(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None
