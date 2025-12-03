import json
import os
from typing import Dict

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


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
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return False

    engine = create_engine(db_url)

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
                    "status": order_data.get("status", "draft"),
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
            "draft",
            f"Order created with {order_data.get('total_colors', 0)} colors",
            engine
        )

        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        engine.dispose()


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
        orders_dir = "data/orders"
        os.makedirs(orders_dir, exist_ok=True)

        filename = f"{orders_dir}/{order_data['order_id']}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(order_data, f, indent=2, default=str)

        return True
    except Exception as e:
        print(f"File save error: {e}")
        return False
