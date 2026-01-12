from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from exceptions import OrderError
from utils.logging_config import get_logger

logger = get_logger("order_repository")

DATA_ORDERS = str(Path(__file__).parent.parent / "data" / "orders")

ORDER_FIELDS = ["order_id", "order_date", "model", "product_name", "total_quantity", "facility", "operation", "material", "status"]


def _extract_order_fields(order_data: dict) -> dict:
    return {
        "order_id": order_data.get("order_id"),
        "order_date": order_data.get("order_date"),
        "model": order_data.get("model") or "",
        "product_name": order_data.get("product_name") or "",
        "total_quantity": order_data.get("total_quantity") or 0,
        "facility": order_data.get("facility") or "",
        "operation": order_data.get("operation") or "",
        "material": order_data.get("material") or "",
        "status": order_data.get("status", "active"),
    }


def _parse_order_date(order_date) -> datetime:
    if isinstance(order_date, datetime):
        return order_date
    if isinstance(order_date, str):
        return datetime.fromisoformat(order_date.replace("Z", "+00:00"))
    return datetime.now()


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order_data: dict) -> bool:
        pass

    @abstractmethod
    def get_active(self) -> list[dict]:
        pass

    @abstractmethod
    def archive(self, order_id: str) -> bool:
        pass

    @abstractmethod
    def add_manual(self, order_id: str, order_data: dict) -> bool:
        pass


class FileOrderRepository(OrderRepository):
    def __init__(self, orders_dir: str = DATA_ORDERS):
        self.orders_dir = orders_dir

    def _get_order_path(self, order_id: str) -> str:
        return f"{self.orders_dir}/{order_id}.json"

    def _read_order_file(self, filename: str) -> dict | None:
        if not os.path.exists(filename):
            return None
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_order_file(self, filename: str, order_data: dict) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(order_data, f, indent=2, default=str)

    def save(self, order_data: dict) -> bool:
        try:
            os.makedirs(self.orders_dir, exist_ok=True)
            logger.info("Saving order to: %s", self.orders_dir)

            order_data.setdefault("status", "active")
            order_data.setdefault("created_at", str(datetime.now()))

            filename = self._get_order_path(order_data["order_id"])
            self._write_order_file(filename, order_data)

            logger.info("Order saved successfully: %s", filename)
            return True
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.exception("File save error: %s", e)
            raise OrderError(f"Failed to save order: {e}") from e

    def get_active(self) -> list[dict]:
        try:
            if not os.path.exists(self.orders_dir):
                return []

            active_orders = []
            for filename in os.listdir(self.orders_dir):
                if not filename.endswith(".json"):
                    continue
                filepath = os.path.join(self.orders_dir, filename)
                order_data = self._read_order_file(filepath)
                if order_data and order_data.get("status") == "active":
                    active_orders.append(_extract_order_fields(order_data))

            active_orders.sort(key=lambda x: x.get("order_date", ""), reverse=True)
            return active_orders
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error("Error reading active orders from files: %s", e)
            raise OrderError(f"Failed to read orders: {e}") from e

    def archive(self, order_id: str) -> bool:
        try:
            filename = self._get_order_path(order_id)
            order_data = self._read_order_file(filename)

            if order_data is None:
                return False

            order_data["status"] = "archived"
            order_data["archived_at"] = str(datetime.now())
            self._write_order_file(filename, order_data)

            return True
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error("Error archiving order in file: %s", e)
            raise OrderError(f"Failed to archive order: {e}") from e

    def add_manual(self, order_id: str, order_data: dict) -> bool:
        order_data["order_id"] = order_id
        order_data["order_date"] = str(order_data.get("order_date") or datetime.now())
        order_data["status"] = "active"
        return self.save(_extract_order_fields(order_data))


class DatabaseOrderRepository(OrderRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            self._engine = create_engine(self.database_url, pool_pre_ping=True)
        return self._engine

    def save(self, order_data: dict) -> bool:
        engine = self._get_engine()
        fields = _extract_order_fields(order_data)
        fields["order_date"] = _parse_order_date(fields["order_date"])

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO orders (order_id, order_date, model, product_name,
                                            total_quantity, facility, operation, material, status)
                        VALUES (:order_id, :order_date, :model, :product_name,
                                :total_quantity, :facility, :operation, :material, :status)
                    """),
                    fields,
                )
                conn.commit()
            logger.info("Order saved to database: %s", order_data["order_id"])
            return True
        except SQLAlchemyError as e:
            logger.error("Database error saving order: %s", e)
            raise OrderError(f"Database error saving order: {e}") from e

    def get_active(self) -> list[dict]:
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT order_id, order_date, model, product_name,
                               total_quantity, facility, operation, material, status
                        FROM orders
                        WHERE status = 'active'
                        ORDER BY order_date DESC
                    """)
                )
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error("Database error getting active orders: %s", e)
            raise OrderError(f"Database error getting orders: {e}") from e

    def archive(self, order_id: str) -> bool:
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE orders SET status = 'archived' WHERE order_id = :order_id"),
                    {"order_id": order_id},
                )
                conn.commit()
            return True
        except SQLAlchemyError as e:
            logger.error("Database error archiving order: %s", e)
            raise OrderError(f"Database error archiving order: {e}") from e

    def add_manual(self, order_id: str, order_data: dict) -> bool:
        order_data["order_id"] = order_id
        return self.save(order_data)
