from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from nlq.intent import QueryIntent
from nlq.sql_generator import SQLGenerator

MSG_NO_DATA_MATCH = "No data matches the query criteria."
MSG_QUERY_NOT_UNDERSTOOD = "Could not understand the query. Please try rephrasing."
MSG_DB_NOT_CONNECTED = "Database not connected."
MSG_SQL_ERROR = "SQL execution error"

TABLE_MAP = {
    "sales": "raw_sales_transactions",
    "stock": "stock_snapshots",
    "forecast": "forecast_data",
}

COL_MAP = {
    "sales": {
        "data": "sale_date",
        "ilosc": "quantity",
        "razem": "total_amount",
    },
    "stock": {
        "available_stock": "available_stock",
        "nazwa": "product_name",
    },
    "forecast": {
        "data": "forecast_date",
        "forecast": "forecast_quantity",
    },
}


class PostgresExecutor:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine
        self.sql_generator = SQLGenerator(dialect="postgresql")

    def execute(self, intent: QueryIntent) -> tuple[pd.DataFrame | None, str, str | None]:
        if not intent.is_valid():
            return None, MSG_QUERY_NOT_UNDERSTOOD, None

        if self.engine is None:
            return None, MSG_DB_NOT_CONNECTED, None

        sql = self.sql_generator.generate(intent)
        if not sql:
            return None, MSG_QUERY_NOT_UNDERSTOOD, None

        entity_type = intent.entity_type or "sales"
        adapted_sql = self._adapt_sql_for_postgres(sql, entity_type)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(adapted_sql))
                df = pd.DataFrame(result.fetchall(), columns=pd.Index(list(result.keys())))
                if df.empty:
                    return None, MSG_NO_DATA_MATCH, adapted_sql
                return df, "", adapted_sql
        except Exception as e:
            return None, f"{MSG_SQL_ERROR}: {str(e)}", adapted_sql

    @staticmethod
    def _adapt_sql_for_postgres(sql: str, entity_type: str) -> str:
        table_name = TABLE_MAP.get(entity_type, entity_type)
        adapted = sql.replace(f"FROM {entity_type}", f"FROM {table_name}")

        col_map = COL_MAP.get(entity_type, {})
        for duckdb_col, pg_col in col_map.items():
            adapted = adapted.replace(f" {duckdb_col}", f" {pg_col}")
            adapted = adapted.replace(f"({duckdb_col}", f"({pg_col}")
            adapted = adapted.replace(f",{duckdb_col}", f",{pg_col}")

        if entity_type == "sales":
            adapted = adapted.replace("DATE_TRUNC('month', data)", "DATE_TRUNC('month', sale_date)")
            adapted = adapted.replace("EXTRACT(YEAR FROM data)", "EXTRACT(YEAR FROM sale_date)")
            adapted = adapted.replace("data >=", "sale_date >=")
            adapted = adapted.replace("SUM(ilosc)", "SUM(quantity)")
            adapted = adapted.replace("SUM(razem)", "SUM(total_amount)")
        elif entity_type == "forecast":
            adapted = adapted.replace("DATE_TRUNC('month', data)", "DATE_TRUNC('month', forecast_date)")
            adapted = adapted.replace("data >=", "forecast_date >=")
            adapted = adapted.replace("SUM(forecast)", "SUM(forecast_quantity)")

        return adapted
