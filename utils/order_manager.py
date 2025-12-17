import json
import os
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

DATA_ORDERS = "data/orders"

load_dotenv()

_engine = None


def _get_engine():
    global _engine
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None
    if _engine is None:
        _engine = create_engine(db_url, pool_pre_ping=True)
    return _engine


def save_order(order_data: Dict) -> bool:
    try:
        db_url = os.getenv("DATABASE_URL")
        data_source_mode = os.getenv("DATA_SOURCE_MODE", "file")

        if db_url and data_source_mode == "database":
            return save_order_to_database(order_data)
        else:
            return save_order_to_file(order_data)
    except Exception as e:
        print(f"Error saving order: {e}")
        return False


def save_order_to_database(order_data: Dict) -> bool:
    engine = _get_engine()
    if not engine:
        return False

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
                }
            )
            conn.commit()

        order_table_data = order_data.get("order_data", {}).get("order_table", [])
        if order_table_data:
            save_order_items_to_database(order_data["order_id"], order_table_data, engine)

        log_order_history(
            order_data["order_id"],
            "created",
            None,
            "active",
            f"Order created with {order_data.get('total_colors', 0)} colors",
            engine
        )

        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False


def save_order_items_to_database(order_id: str, order_table: list, engine) -> None:
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
                    }
                )
                conn.commit()
    except Exception as e:
        print(f"Error saving order items: {e}")


def log_order_history(order_id: str, action: str, old_status: str | None, new_status: str, notes: str, engine) -> None:
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
                }
            )
            conn.commit()
    except Exception as e:
        print(f"Error logging order history: {e}")


def save_order_to_file(order_data: Dict) -> bool:
    try:
        orders_dir = DATA_ORDERS
        os.makedirs(orders_dir, exist_ok=True)

        if 'status' not in order_data:
            order_data['status'] = 'active'
        if 'created_at' not in order_data:
            order_data['created_at'] = str(datetime.now())

        filename = f"{orders_dir}/{order_data['order_id']}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(order_data, f, indent=2, default=str)

        return True
    except Exception as e:
        print(f"File save error: {e}")
        return False


def get_active_orders() -> list:
    try:
        db_url = os.getenv("DATABASE_URL")
        data_source_mode = os.getenv("DATA_SOURCE_MODE", "file")

        if db_url and data_source_mode == "database":
            return get_active_orders_from_database()
        else:
            return get_active_orders_from_files()
    except Exception as e:
        print(f"Error getting active orders: {e}")
        return []


def get_active_orders_from_database() -> list:
    engine = _get_engine()
    if not engine:
        return []

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
                    "status": row.status
                })
            return orders
    except Exception as e:
        print(f"Database error getting active orders: {e}")
        return []


def get_active_orders_from_files() -> list:
    try:
        orders_dir = DATA_ORDERS
        if not os.path.exists(orders_dir):
            return []

        active_orders = []
        for filename in os.listdir(orders_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(orders_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    order_data = json.load(f)
                    if order_data.get('status') == 'active':
                        active_orders.append({
                            "order_id": order_data.get('order_id'),
                            "model": order_data.get('model'),
                            "order_date": order_data.get('created_at', order_data.get('order_date')),
                            "status": order_data.get('status')
                        })

        active_orders.sort(key=lambda x: x.get('order_date', ''), reverse=True)
        return active_orders
    except Exception as e:
        print(f"Error reading active orders from files: {e}")
        return []


def archive_order(order_id: str) -> bool:
    try:
        db_url = os.getenv("DATABASE_URL")
        data_source_mode = os.getenv("DATA_SOURCE_MODE", "file")

        if db_url and data_source_mode == "database":
            return archive_order_in_database(order_id)
        else:
            return archive_order_in_file(order_id)
    except Exception as e:
        print(f"Error archiving order: {e}")
        return False


def archive_order_in_database(order_id: str) -> bool:
    engine = _get_engine()
    if not engine:
        return False

    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                     UPDATE orders
                     SET status     = 'archived',
                         updated_at = NOW()
                     WHERE order_id = :order_id
                     """),
                {"order_id": order_id}
            )
            conn.commit()

        log_order_history(order_id, "archived", "active", "archived", "Order archived", engine)
        return True
    except Exception as e:
        print(f"Database error archiving order: {e}")
        return False


def archive_order_in_file(order_id: str) -> bool:
    try:
        orders_dir = "data/orders"
        filename = f"{orders_dir}/{order_id}.json"

        if not os.path.exists(filename):
            return False

        with open(filename, 'r', encoding='utf-8') as f:
            order_data = json.load(f)

        order_data['status'] = 'archived'
        order_data['archived_at'] = str(datetime.now())

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(order_data, f, indent=2, default=str)

        return True
    except Exception as e:
        print(f"Error archiving order in file: {e}")
        return False


def add_manual_order(order_id: str, model: str, order_date) -> bool:
    from datetime import datetime

    if not isinstance(order_date, datetime):
        from datetime import datetime as dt
        order_date = dt.combine(order_date, dt.min.time())

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
        "order_data": {}
    }

    try:
        db_url = os.getenv("DATABASE_URL")
        data_source_mode = os.getenv("DATA_SOURCE_MODE", "file")

        if db_url and data_source_mode == "database":
            return add_manual_order_to_database(order_data)
        else:
            return save_order_to_file(order_data)
    except Exception as e:
        print(f"Error adding manual order: {e}")
        return False


def add_manual_order_to_database(order_data: Dict) -> bool:
    engine = _get_engine()
    if not engine:
        return False

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
                    "order_id": order_data["order_id"],
                    "model": order_data["model"],
                    "status": "active",
                    "total_quantity": 0,
                    "total_patterns": 0,
                    "total_excess": 0,
                    "total_colors": 0,
                    "order_data": json.dumps({"manual_entry": True}),
                    "created_at": order_data["created_at"]
                }
            )
            conn.commit()

        log_order_history(
            order_data["order_id"],
            "created",
            None,
            "active",
            "Manual order entry",
            engine
        )
        return True
    except Exception as e:
        print(f"Database error adding manual order: {e}")
        return False
