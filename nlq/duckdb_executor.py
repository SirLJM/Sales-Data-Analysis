from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from nlq.intent import QueryIntent
from nlq.sql_generator import SQLGenerator, TABLE_SALES, TABLE_STOCK, TABLE_FORECAST

MSG_NO_DATA_MATCH = "No data matches the query criteria."
MSG_QUERY_NOT_UNDERSTOOD = "Could not understand the query. Please try rephrasing."
MSG_SALES_NOT_LOADED = "Sales data not loaded."
MSG_STOCK_NOT_LOADED = "Stock data not loaded."
MSG_FORECAST_NOT_LOADED = "Forecast data not loaded."
MSG_SQL_ERROR = "SQL execution error"


class DuckDBExecutor:
    def __init__(
        self,
        sales_df: pd.DataFrame | None = None,
        stock_df: pd.DataFrame | None = None,
        forecast_df: pd.DataFrame | None = None,
        sku_summary_df: pd.DataFrame | None = None,
    ):
        self.sales_df = sales_df
        self.stock_df = stock_df
        self.forecast_df = forecast_df
        self.sku_summary_df = sku_summary_df
        self.sql_generator = SQLGenerator(dialect="duckdb")
        self._conn: duckdb.DuckDBPyConnection | None = None

    def execute(self, intent: QueryIntent) -> tuple[pd.DataFrame | None, str, str | None]:
        if not intent.is_valid():
            return None, MSG_QUERY_NOT_UNDERSTOOD, None

        sql = self.sql_generator.generate(intent)
        if not sql:
            return None, MSG_QUERY_NOT_UNDERSTOOD, None

        entity_type = intent.entity_type
        error = self._validate_data_availability(entity_type)
        if error:
            return None, error, sql

        try:
            result_df = self._execute_sql(sql, entity_type)
            if result_df is None or result_df.empty:
                return None, MSG_NO_DATA_MATCH, sql
            return result_df, "", sql
        except duckdb.Error as e:
            return None, f"{MSG_SQL_ERROR}: {str(e)}", sql

    def _validate_data_availability(self, entity_type: str | None) -> str | None:
        if entity_type == "sales" and (self.sales_df is None or self.sales_df.empty):
            return MSG_SALES_NOT_LOADED
        if entity_type == "stock" and (self.stock_df is None or self.stock_df.empty):
            return MSG_STOCK_NOT_LOADED
        if entity_type == "forecast" and (self.forecast_df is None or self.forecast_df.empty):
            return MSG_FORECAST_NOT_LOADED
        return None

    def _execute_sql(self, sql: str, entity_type: str | None) -> pd.DataFrame | None:
        conn = self._get_connection()
        self._register_dataframes(conn, entity_type)
        result = conn.execute(sql).fetchdf()
        return result

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = duckdb.connect(":memory:")
        return self._conn

    def _register_dataframes(self, conn: duckdb.DuckDBPyConnection, entity_type: str | None) -> None:
        if entity_type == "sales" and self.sales_df is not None:
            df = self._prepare_sales_df(self.sales_df)
            conn.register(TABLE_SALES, df)
        elif entity_type == "stock" and self.stock_df is not None:
            df = self._prepare_stock_df(self.stock_df)
            conn.register(TABLE_STOCK, df)
        elif entity_type == "forecast" and self.forecast_df is not None:
            df = self._prepare_forecast_df(self.forecast_df)
            conn.register(TABLE_FORECAST, df)

    @staticmethod
    def _prepare_sales_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = DuckDBExecutor._sanitize_dataframe(df)
        if "model" not in df.columns and "sku" in df.columns:
            df["model"] = df["sku"].astype(str).str[:5]
        if not pd.api.types.is_datetime64_any_dtype(df.get("data")):
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df

    @staticmethod
    def _prepare_stock_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = DuckDBExecutor._sanitize_dataframe(df)
        if "model" not in df.columns and "sku" in df.columns:
            df["model"] = df["sku"].astype(str).str[:5]
        return df

    @staticmethod
    def _prepare_forecast_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = DuckDBExecutor._sanitize_dataframe(df)
        if "model" not in df.columns and "sku" in df.columns:
            df["model"] = df["sku"].astype(str).str[:5]
        date_col = "data" if "data" in df.columns else "forecast_date"
        if date_col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        return df

    @staticmethod
    def _sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].dtype == object:
                first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(first_valid, np.ndarray):
                    df[col] = df[col].apply(
                        lambda x: x.tolist() if isinstance(x, np.ndarray) else x
                    )
        return df

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
