from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import create_engine, text

from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger("order_repository")

DATA_ORDERS = str(Path(__file__).parent.parent / "data" / "orders")


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

    def save(self, order_data: dict) -> bool:
        try:
            os.makedirs(self.orders_dir, exist_ok=True)
            logger.info("Saving order to: %s", self.orders_dir)
            logger.info("Order data keys: %s", list(order_data.keys()))

            if "status" not in order_data:
                order_data["status"] = "active"
            if "created_at" not in order_data:
                order_data["created_at"] = str(datetime.now())

            filename = f"{self.orders_dir}/{order_data['order_id']}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(order_data, f, indent=2, default=str)

            logger.info("Order saved successfully: %s", filename)
            return True
        except Exception as e:
            logger.exception("File save error: %s", e)
            return False

    def get_active(self) -> list[dict]:
        try:
            if not os.path.exists(self.orders_dir):
                return []

            active_orders = []
            for filename in os.listdir(self.orders_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.orders_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        order_data = json.load(f)
                        if order_data.get("status") == "active":
                            active_orders.append({
                                "order_id": order_data.get("order_id"),
                                "order_date": order_data.get("order_date"),
                                "model": order_data.get("model"),
                                "product_name": order_data.get("product_name"),
                                "total_quantity": order_data.get("total_quantity", 0),
                                "facility": order_data.get("facility"),
                                "operation": order_data.get("operation"),
                                "material": order_data.get("material"),
                                "status": order_data.get("status"),
                            })

            active_orders.sort(key=lambda x: x.get("order_date", ""), reverse=True)
            return active_orders
        except Exception as e:
            logger.error("Error reading active orders from files: %s", e)
            return []

    def archive(self, order_id: str) -> bool:
        try:
            filename = f"{self.orders_dir}/{order_id}.json"

            if not os.path.exists(filename):
                return False

            with open(filename, "r", encoding="utf-8") as f:
                order_data = json.load(f)

            order_data["status"] = "archived"
            order_data["archived_at"] = str(datetime.now())

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(order_data, f, indent=2, default=str)

            return True
        except Exception as e:
            logger.error("Error archiving order in file: %s", e)
            return False

    def add_manual(self, order_id: str, order_data: dict) -> bool:
        order_date = order_data.get("order_date") or datetime.now()
        full_order_data = {
            "order_id": order_id,
            "order_date": str(order_date),
            "model": order_data.get("model") or "",
            "product_name": order_data.get("product_name") or "",
            "total_quantity": order_data.get("total_quantity") or 0,
            "facility": order_data.get("facility") or "",
            "operation": order_data.get("operation") or "",
            "material": order_data.get("material") or "",
            "status": "active",
        }
        return self.save(full_order_data)


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
        order_date = order_data.get("order_date") or datetime.now()
        if isinstance(order_date, str):
            order_date = datetime.fromisoformat(order_date.replace("Z", "+00:00"))

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO orders (order_id, order_date, model, product_name,
                                            total_quantity, facility, operation, material, status)
                        VALUES (:order_id, :order_date, :model, :product_name,
                                :total_quantity, :facility, :operation, :material, :status)
                    """),
                    {
                        "order_id": order_data["order_id"],
                        "order_date": order_date,
                        "model": order_data.get("model") or "",
                        "product_name": order_data.get("product_name") or "",
                        "total_quantity": order_data.get("total_quantity") or 0,
                        "facility": order_data.get("facility") or "",
                        "operation": order_data.get("operation") or "",
                        "material": order_data.get("material") or "",
                        "status": order_data.get("status", "active"),
                    },
                )
                conn.commit()
            logger.info("Order saved to database: %s", order_data["order_id"])
            return True
        except Exception as e:
            logger.error("Database error saving order: %s", e)
            return False

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
                orders = []
                for row in result:
                    orders.append({
                        "order_id": row.order_id,
                        "order_date": row.order_date,
                        "model": row.model,
                        "product_name": row.product_name,
                        "total_quantity": row.total_quantity or 0,
                        "facility": row.facility,
                        "operation": row.operation,
                        "material": row.material,
                        "status": row.status,
                    })
                return orders
        except Exception as e:
            logger.error("Database error getting active orders: %s", e)
            return []

    def archive(self, order_id: str) -> bool:
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        UPDATE orders
                        SET status = 'archived'
                        WHERE order_id = :order_id
                    """),
                    {"order_id": order_id},
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error("Database error archiving order: %s", e)
            return False

    def add_manual(self, order_id: str, order_data: dict) -> bool:
        order_data["order_id"] = order_id
        return self.save(order_data)
