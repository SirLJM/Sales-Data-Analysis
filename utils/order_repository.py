from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import create_engine, text

from utils.logging_config import get_logger

logger = get_logger("order_repository")

DATA_ORDERS = "data/orders"


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
    def add_manual(self, order_id: str, model: str, order_date: datetime) -> bool:
        pass


class FileOrderRepository(OrderRepository):
    def __init__(self, orders_dir: str = DATA_ORDERS):
        self.orders_dir = orders_dir

    def save(self, order_data: dict) -> bool:
        try:
            os.makedirs(self.orders_dir, exist_ok=True)

            if "status" not in order_data:
                order_data["status"] = "active"
            if "created_at" not in order_data:
                order_data["created_at"] = str(datetime.now())

            filename = f"{self.orders_dir}/{order_data['order_id']}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(order_data, f, indent=2, default=str)

            return True
        except Exception as e:
            logger.error("File save error: %s", e)
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
                                "model": order_data.get("model"),
                                "order_date": order_data.get("created_at", order_data.get("order_date")),
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

    def add_manual(self, order_id: str, model: str, order_date: datetime) -> bool:
        order_data = {
            "order_id": order_id,
            "model": model,
            "status": "active",
            "created_at": str(order_date),
            "order_date": str(order_date),
            "manual_entry": True,
            "total_quantity": 0,
            "total_patterns": 0,
            "total_excess": 0,
            "total_colors": 0,
            "order_data": {},
        }
        return self.save(order_data)


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

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO orders (order_id, model, status, szwalnia_glowna, szwalnia_druga,
                                            rodzaj_materialu, gramatura, total_quantity, total_patterns,
                                            total_excess, total_colors, order_data)
                        VALUES (:order_id, :model, :status, :szwalnia_glowna, :szwalnia_druga,
                                :rodzaj_materialu, :gramatura, :total_quantity, :total_patterns,
                                :total_excess, :total_colors, :order_data::jsonb)
                    """),
                    {
                        "order_id": order_data["order_id"],
                        "model": order_data["model"],
                        "status": order_data.get("status", "active"),
                        "szwalnia_glowna": order_data.get("szwalnia_glowna"),
                        "szwalnia_druga": order_data.get("szwalnia_druga"),
                        "rodzaj_materialu": order_data.get("rodzaj_materialu"),
                        "gramatura": order_data.get("gramatura"),
                        "total_quantity": order_data.get("total_quantity", 0),
                        "total_patterns": order_data.get("total_patterns", 0),
                        "total_excess": order_data.get("total_excess", 0),
                        "total_colors": order_data.get("total_colors", 0),
                        "order_data": json.dumps(order_data.get("order_data", {})),
                    },
                )
                conn.commit()

            order_table_data = order_data.get("order_data", {}).get("order_table", [])
            if order_table_data:
                self._save_order_items(order_data["order_id"], order_table_data)

            self._log_history(
                order_data["order_id"],
                "created",
                None,
                "active",
                f"Order created with {order_data.get('total_colors', 0)} colors",
            )

            return True
        except Exception as e:
            logger.error("Database error saving order: %s", e)
            return False

    def _save_order_items(self, order_id: str, order_table: list) -> None:
        engine = self._get_engine()

        try:
            for item in order_table:
                with engine.connect() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO order_items (order_id, model, color, total_patterns, total_excess,
                                                     coverage_status, produced_quantities, forecast_leadtime,
                                                     deficit, coverage_gap)
                            VALUES (:order_id, :model, :color, :total_patterns, :total_excess,
                                    :coverage_status, :produced_quantities::jsonb, :forecast_leadtime,
                                    :deficit, :coverage_gap)
                            ON CONFLICT (order_id, color) DO NOTHING
                        """),
                        {
                            "order_id": order_id,
                            "model": item.get("Model"),
                            "color": item.get("Color"),
                            "total_patterns": item.get("Total Patterns", 0),
                            "total_excess": item.get("Total Excess", 0),
                            "coverage_status": item.get("Coverage", ""),
                            "produced_quantities": json.dumps({}),
                            "forecast_leadtime": item.get("Forecast", 0),
                            "deficit": item.get("Deficit", 0),
                            "coverage_gap": item.get("Coverage Gap", 0),
                        },
                    )
                    conn.commit()
        except Exception as e:
            logger.error("Error saving order items: %s", e)

    def _log_history(
        self, order_id: str, action: str, old_status: str | None, new_status: str, notes: str
    ) -> None:
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO order_history (order_id, action, old_status, new_status, notes)
                        VALUES (:order_id, :action, :old_status, :new_status, :notes)
                    """),
                    {
                        "order_id": order_id,
                        "action": action,
                        "old_status": old_status,
                        "new_status": new_status,
                        "notes": notes,
                    },
                )
                conn.commit()
        except Exception as e:
            logger.error("Error logging order history: %s", e)

    def get_active(self) -> list[dict]:
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT order_id, model, created_at as order_date, status
                        FROM orders
                        WHERE status = 'active'
                        ORDER BY created_at DESC
                    """)
                )
                orders = []
                for row in result:
                    orders.append({
                        "order_id": row.order_id,
                        "model": row.model,
                        "order_date": row.order_date,
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
                        SET status = 'archived',
                            updated_at = NOW()
                        WHERE order_id = :order_id
                    """),
                    {"order_id": order_id},
                )
                conn.commit()

            self._log_history(order_id, "archived", "active", "archived", "Order archived")
            return True
        except Exception as e:
            logger.error("Database error archiving order: %s", e)
            return False

    def add_manual(self, order_id: str, model: str, order_date: datetime) -> bool:
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO orders (order_id, model, status, total_quantity, total_patterns,
                                            total_excess, total_colors, order_data, created_at)
                        VALUES (:order_id, :model, :status, :total_quantity, :total_patterns,
                                :total_excess, :total_colors, CAST(:order_data AS jsonb), :created_at)
                    """),
                    {
                        "order_id": order_id,
                        "model": model,
                        "status": "active",
                        "total_quantity": 0,
                        "total_patterns": 0,
                        "total_excess": 0,
                        "total_colors": 0,
                        "order_data": json.dumps({"manual_entry": True}),
                        "created_at": str(order_date),
                    },
                )
                conn.commit()

            self._log_history(order_id, "created", None, "active", "Manual order entry")
            return True
        except Exception as e:
            logger.error("Database error adding manual order: %s", e)
            return False
