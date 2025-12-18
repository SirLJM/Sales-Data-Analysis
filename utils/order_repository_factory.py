from __future__ import annotations

import os

from dotenv import load_dotenv

from utils.logging_config import get_logger
from utils.order_repository import (
    DatabaseOrderRepository,
    FileOrderRepository,
    OrderRepository,
)

load_dotenv()

logger = get_logger("order_repository_factory")

_repository: OrderRepository | None = None


def create_order_repository() -> OrderRepository:
    global _repository

    if _repository is not None:
        return _repository

    db_url = os.getenv("DATABASE_URL")
    data_source_mode = os.getenv("DATA_SOURCE_MODE", "file")

    if db_url and data_source_mode == "database":
        logger.info("Using database order repository")
        _repository = DatabaseOrderRepository(db_url)
    else:
        logger.info("Using file order repository")
        _repository = FileOrderRepository()

    return _repository


def reset_repository() -> None:
    global _repository
    _repository = None
