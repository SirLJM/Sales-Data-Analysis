from __future__ import annotations

import json
from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger("sku_exclude_manager")

EXCLUDED_SKUS_FILE = Path(__file__).parent.parent / "data" / "excluded_skus.json"


def load_excluded_skus() -> list[str]:
    if not EXCLUDED_SKUS_FILE.exists():
        return []
    try:
        with open(EXCLUDED_SKUS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(s) for s in data]
        return []
    except (json.JSONDecodeError, OSError):
        logger.warning("Failed to load excluded SKUs from %s", EXCLUDED_SKUS_FILE)
        return []


def save_excluded_skus(skus: list[str]) -> bool:
    try:
        sorted_skus = sorted(set(skus))
        with open(EXCLUDED_SKUS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted_skus, f, indent=2)
        logger.info("Saved %d excluded SKUs", len(sorted_skus))
        return True
    except OSError:
        logger.exception("Failed to save excluded SKUs to %s", EXCLUDED_SKUS_FILE)
        return False
