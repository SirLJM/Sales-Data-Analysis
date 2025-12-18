from __future__ import annotations

from datetime import datetime

from utils.logging_config import get_logger
from utils.order_repository_factory import create_order_repository

logger = get_logger("order_manager")


def save_order(order_data: dict) -> bool:
    try:
        repository = create_order_repository()
        return repository.save(order_data)
    except Exception as e:
        logger.error("Error saving order: %s", e)
        return False


def get_active_orders() -> list:
    try:
        repository = create_order_repository()
        return repository.get_active()
    except Exception as e:
        logger.error("Error getting active orders: %s", e)
        return []


def archive_order(order_id: str) -> bool:
    try:
        repository = create_order_repository()
        return repository.archive(order_id)
    except Exception as e:
        logger.error("Error archiving order: %s", e)
        return False


def add_manual_order(order_id: str, model: str, order_date) -> bool:
    if not isinstance(order_date, datetime):
        order_date = datetime.combine(order_date, datetime.min.time())

    try:
        repository = create_order_repository()
        return repository.add_manual(order_id, model, order_date)
    except Exception as e:
        logger.error("Error adding manual order: %s", e)
        return False
