from __future__ import annotations

import hashlib
import json
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

from utils.logging_config import get_logger

from .data_source import DataSource

logger = get_logger("db_source")


class DatabaseSource(DataSource):

    def __init__(
            self, connection_string: str, pool_size: int = 10, pool_recycle: int = 3600
    ) -> None:
        self.connection_string = connection_string
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=pool_size,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
        )
        self._is_available = self._test_connection()

    def _test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Database connection failed: %s", e)
            return False

    def load_sales_data(
            self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> pd.DataFrame:

        query = """
                SELECT order_id,
                       sale_date    as data,
                       sku,
                       quantity     as ilosc,
                       unit_price   as cena,
                       total_amount as razem,
                       model,
                       color,
                       size,
                       source_file
                FROM raw_sales_transactions
                WHERE is_valid = TRUE \
                """

        params = {}

        if start_date is not None:
            query += " AND sale_date >= :start_date"
            params["start_date"] = start_date

        if end_date is not None:
            query += " AND sale_date <= :end_date"
            params["end_date"] = end_date

        query += " ORDER BY sale_date, sku"

        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn, params=params)

        if not df.empty and "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"])

        return df

    def load_stock_data(self, snapshot_date: datetime | None = None) -> pd.DataFrame:

        if snapshot_date is not None:
            query = """
                    SELECT sku,
                           product_name as nazwa,
                           net_price    as cena_netto,
                           gross_price  as cena_brutto,
                           total_stock  as stock,
                           available_stock,
                           1            as aktywny,
                           snapshot_date
                    FROM stock_snapshots
                    WHERE snapshot_date = :snapshot_date
                      AND is_active = TRUE
                    ORDER BY sku \
                    """
            params = {
                "snapshot_date": (
                    snapshot_date.date() if isinstance(snapshot_date, datetime) else snapshot_date
                )
            }
        else:
            query = """
                    SELECT sku,
                           product_name as nazwa,
                           net_price    as cena_netto,
                           gross_price  as cena_brutto,
                           total_stock  as stock,
                           available_stock,
                           1            as aktywny,
                           snapshot_date
                    FROM stock_snapshots
                    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM stock_snapshots)
                      AND is_active = TRUE
                    ORDER BY sku \
                    """
            params = {}

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn, params=params)

            return df
        except Exception as e:
            logger.error("Failed to load stock data: %s", e)
            return pd.DataFrame()

    def load_stock_history(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> pd.DataFrame:
        query = """
                SELECT sku,
                       product_name    as nazwa,
                       net_price       as cena_netto,
                       gross_price     as cena_brutto,
                       total_stock     as stock,
                       available_stock,
                       1               as aktywny,
                       snapshot_date
                FROM stock_snapshots
                WHERE is_active = TRUE
                """

        params = {}

        if start_date is not None:
            query += " AND snapshot_date >= :start_date"
            params["start_date"] = (
                start_date.date() if isinstance(start_date, datetime) else start_date
            )

        if end_date is not None:
            query += " AND snapshot_date <= :end_date"
            params["end_date"] = (
                end_date.date() if isinstance(end_date, datetime) else end_date
            )

        query += " ORDER BY snapshot_date, sku"

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn, params=params)

            if not df.empty and "snapshot_date" in df.columns:
                df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])

            return df
        except Exception as e:
            logger.error("Failed to load stock history: %s", e)
            return pd.DataFrame()

    def load_forecast_data(self, generated_date: datetime | None = None) -> pd.DataFrame:

        if generated_date is not None:
            query = """
                    SELECT forecast_date     as data,
                           sku,
                           model,
                           forecast_quantity as forecast,
                           generated_date
                    FROM forecast_data
                    WHERE generated_date = :generated_date
                    ORDER BY forecast_date, sku \
                    """
            params = {
                "generated_date": (
                    generated_date.date()
                    if isinstance(generated_date, datetime)
                    else generated_date
                )
            }
        else:
            query = """
                    SELECT forecast_date     as data,
                           sku,
                           model,
                           forecast_quantity as forecast,
                           generated_date
                    FROM forecast_data
                    WHERE generated_date = (SELECT MAX(generated_date) FROM forecast_data)
                    ORDER BY forecast_date, sku \
                    """
            params = {}

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn, params=params)

            if not df.empty and "data" in df.columns:
                df["data"] = pd.to_datetime(df["data"])

            return df
        except Exception as e:
            logger.error("Failed to load forecast data: %s", e)
            return pd.DataFrame()

    def get_sku_statistics(
            self, entity_type: str = "sku", force_recompute: bool = False
    ) -> pd.DataFrame:

        if force_recompute:
            return self._compute_sku_statistics(entity_type)

        query = """
                SELECT entity_id                as "SKU",
                       months_with_sales        as "MONTHS",
                       total_quantity           as "QUANTITY",
                       average_monthly_sales    as "AVERAGE SALES",
                       standard_deviation       as "SD",
                       coefficient_of_variation as "CV",
                       product_type             as "TYPE",
                       safety_stock             as "SS",
                       reorder_point            as "ROP",
                       first_sale_date,
                       last_2y_avg_monthly      as "LAST_2_YEARS_AVG",
                       is_seasonal,
                       seasonal_ss_in,
                       seasonal_ss_out,
                       seasonal_rop_in,
                       seasonal_rop_out,
                       computed_at,
                       configuration_hash
                FROM mv_valid_sku_stats
                WHERE entity_type = :entity_type
                ORDER BY total_quantity DESC \
                """

        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn, params={"entity_type": entity_type})

        if df.empty:
            return self._compute_sku_statistics(entity_type)

        from utils.settings_manager import load_settings

        settings = load_settings()
        current_hash = self._compute_settings_hash(settings)

        if not df.empty and "configuration_hash" in df.columns:
            cached_hash = df["configuration_hash"].iloc[0] if len(df) > 0 else None
            if cached_hash != current_hash:
                logger.info("Settings changed, recomputing statistics...")
                return self._compute_sku_statistics(entity_type)

        return df

    def get_order_priorities(
            self, top_n: int | None = None, force_recompute: bool = False
    ) -> pd.DataFrame:

        if force_recompute:
            return self._compute_order_priorities(top_n)

        query = """
                SELECT sku               as "SKU",
                       model             as "MODEL",
                       color             as "COLOR",
                       size              as "SIZE",
                       priority_score    as "PRIORITY_SCORE",
                       stockout_risk     as "STOCKOUT_RISK",
                       revenue_impact    as "REVENUE_IMPACT",
                       revenue_at_risk   as "REVENUE_AT_RISK",
                       current_stock     as "STOCK",
                       reorder_point     as "ROP",
                       deficit           as "DEFICIT",
                       forecast_leadtime as "FORECAST_LEADTIME",
                       coverage_gap      as "COVERAGE_GAP",
                       product_type      as "TYPE",
                       type_multiplier   as "TYPE_MULTIPLIER",
                       is_urgent         as "URGENT",
                       computed_at
                FROM mv_valid_order_priorities
                ORDER BY priority_score DESC \
                """

        if top_n is not None:
            query += f" LIMIT {top_n}"

        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)

        if df.empty:
            return self._compute_order_priorities(top_n)

        from utils.settings_manager import load_settings

        settings = load_settings()
        current_hash = self._compute_settings_hash(settings)

        if not df.empty and "configuration_hash" in df.columns:
            cached_hash = df["configuration_hash"].iloc[0] if len(df) > 0 else None
            if cached_hash != current_hash:
                logger.info("Settings changed, recomputing priorities...")
                return self._compute_order_priorities(top_n)

        return df

    def get_monthly_aggregations(
            self, entity_type: str = "sku", force_recompute: bool = False
    ) -> pd.DataFrame:

        query = """
                SELECT entity_type,
                       entity_id,
                       year_month,
                       total_quantity,
                       total_revenue,
                       transaction_count,
                       unique_orders,
                       avg_unit_price,
                       computed_at
                FROM mv_valid_monthly_aggs
                WHERE entity_type = :entity_type
                ORDER BY entity_id, year_month \
                """

        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn, params={"entity_type": entity_type})

        if df.empty and not force_recompute:
            logger.warning(
                "Materialized view mv_valid_monthly_aggs is empty for %s, falling back to file computation",
                entity_type)
            return self._compute_monthly_aggregations(entity_type)

        logger.debug("Using database monthly aggregations for %s: %d rows", entity_type, len(df))
        return df

    @staticmethod
    def _compute_settings_hash(settings: dict) -> str:
        relevant_keys = [
            "lead_time",
            "forecast_time",
            "cv_threshold_basic",
            "cv_threshold_seasonal",
            "z_score_basic",
            "z_score_regular",
            "z_score_seasonal_in",
            "z_score_seasonal_out",
            "z_score_new",
        ]
        settings_subset = {k: settings.get(k) for k in relevant_keys if k in settings}
        settings_json = json.dumps(settings_subset, sort_keys=True)
        return hashlib.md5(settings_json.encode()).hexdigest()

    @staticmethod
    def _compute_sku_statistics(entity_type: str) -> pd.DataFrame:
        from .file_source import FileSource

        file_source = FileSource()
        return file_source.get_sku_statistics(entity_type, force_recompute=True)

    @staticmethod
    def _compute_order_priorities(top_n: int | None = None) -> pd.DataFrame:
        from .file_source import FileSource

        file_source = FileSource()
        return file_source.get_order_priorities(top_n, force_recompute=True)

    @staticmethod
    def _compute_monthly_aggregations(entity_type: str) -> pd.DataFrame:
        from .file_source import FileSource

        file_source = FileSource()
        return file_source.get_monthly_aggregations(entity_type, force_recompute=True)

    def load_model_metadata(self) -> pd.DataFrame | None:
        query = """
                SELECT model,
                       primary_production,
                       secondary_production,
                       material_type,
                       material_weight
                FROM model_metadata
                ORDER BY model \
                """

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)

            if df.empty:
                logger.warning("No model metadata found in database")
                return None

            df.columns = [
                "Model",
                "SZWALNIA GŁÓWNA",
                "SZWALNIA DRUGA",
                "RODZAJ MATERIAŁU",
                "GRAMATURA",
            ]

            logger.debug("Loaded %d models with metadata from database", len(df))

            return df

        except Exception as e:
            logger.error("Failed to load model metadata from database: %s", e)
            return None

    def load_size_aliases(self) -> dict[str, str]:
        query = """
                SELECT size_code, size_alias
                FROM size_aliases
                ORDER BY size_code
                """

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)

            if df.empty:
                logger.warning("No size aliases found in database")
                return {}

            return dict(zip(df["size_code"], df["size_alias"]))

        except Exception as e:
            logger.error("Failed to load size aliases from database: %s", e)
            return {}

    def load_color_aliases(self) -> dict[str, str]:
        query = """
                SELECT color_code, color_name
                FROM color_aliases
                ORDER BY color_code
                """

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)

            if df.empty:
                logger.warning("No color aliases found in database")
                return {}

            return dict(zip(df["color_code"], df["color_name"]))

        except Exception as e:
            logger.error("Failed to load color aliases from database: %s", e)
            return {}

    def load_category_mappings(self) -> pd.DataFrame:
        query = """
            SELECT
                model,
                grupa,
                podgrupa,
                kategoria,
                nazwa
            FROM category_mappings
            ORDER BY model
        """

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)

            if df.empty:
                logger.warning("No category mappings found in database")
                return pd.DataFrame()

            df.columns = ["Model", "Grupa", "Podgrupa", "Kategoria", "Nazwa"]
            return df

        except Exception as e:
            raise ValueError(f"Failed to load category mappings from database: {str(e)}")

    def is_available(self) -> bool:
        return self._is_available

    @staticmethod
    def get_data_source_type(**kwargs) -> str:
        return "database"

    def close(self) -> None:
        if self.engine:
            self.engine.dispose()
