from __future__ import annotations

import json
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from utils.logging_config import get_logger

METADATA_JSON = "metadata.json"

logger = get_logger("internal_forecast_repository")

DATA_FORECASTS_DIR = Path(__file__).parent.parent / "data" / "internal_forecasts"


class InternalForecastRepository(ABC):
    @abstractmethod
    def save_forecast_batch(
            self,
            forecasts_df: pd.DataFrame,
            entity_type: str,
            horizon_months: int,
            stats: dict,
            parameters: dict | None = None,
            notes: str | None = None,
    ) -> str:
        pass

    @abstractmethod
    def get_forecast_batches(self, entity_type: str | None = None, limit: int = 20) -> list[dict]:
        pass

    @abstractmethod
    def get_forecast_batch(self, batch_id: str) -> pd.DataFrame | None:
        pass

    @abstractmethod
    def delete_forecast_batch(self, batch_id: str) -> bool:
        pass


class FileInternalForecastRepository(InternalForecastRepository):
    def __init__(self, base_dir: Path = DATA_FORECASTS_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_forecast_batch(
            self,
            forecasts_df: pd.DataFrame,
            entity_type: str,
            horizon_months: int,
            stats: dict,
            parameters: dict | None = None,
            notes: str | None = None,
    ) -> str:
        batch_id = str(uuid.uuid4())
        generated_at = datetime.now()
        timestamp = generated_at.strftime("%Y%m%d_%H%M%S")

        batch_dir = self.base_dir / f"{timestamp}_{batch_id[:8]}"
        batch_dir.mkdir(parents=True, exist_ok=True)

        forecasts_df.to_csv(batch_dir / "forecasts.csv", index=False)

        metadata = {
            "batch_id": batch_id,
            "generated_at": generated_at.isoformat(),
            "entity_type": entity_type,
            "horizon_months": horizon_months,
            "total_entities": stats.get("total", 0),
            "success_count": stats.get("success", 0),
            "failed_count": stats.get("failed", 0),
            "methods_used": stats.get("methods", {}),
            "parameters": parameters or {},
            "notes": notes,
        }

        with open(batch_dir / METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info("Saved forecast batch %s to %s", batch_id, batch_dir)
        return batch_id

    def get_forecast_batches(self, entity_type: str | None = None, limit: int = 20) -> list[dict]:
        batches = []

        if not self.base_dir.exists():
            return batches

        for batch_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not batch_dir.is_dir():
                continue

            metadata_file = batch_dir / METADATA_JSON
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                if entity_type and metadata.get("entity_type") != entity_type:
                    continue

                metadata["dir_name"] = batch_dir.name
                batches.append(metadata)

                if len(batches) >= limit:
                    break
            except Exception as e:
                logger.warning("Error reading metadata from %s: %s", batch_dir, e)

        return batches

    def get_forecast_batch(self, batch_id: str) -> pd.DataFrame | None:
        for batch_dir in self.base_dir.iterdir():
            if not batch_dir.is_dir():
                continue

            metadata_file = batch_dir / METADATA_JSON
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                if metadata.get("batch_id") == batch_id:
                    forecasts_file = batch_dir / "forecasts.csv"
                    if forecasts_file.exists():
                        return pd.read_csv(forecasts_file)
            except Exception as e:
                logger.warning("Error reading batch %s: %s", batch_dir, e)

        return None

    def delete_forecast_batch(self, batch_id: str) -> bool:
        for batch_dir in self.base_dir.iterdir():
            if not batch_dir.is_dir():
                continue

            metadata_file = batch_dir / METADATA_JSON
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                if metadata.get("batch_id") == batch_id:
                    import shutil
                    shutil.rmtree(batch_dir)
                    logger.info("Deleted forecast batch %s", batch_id)
                    return True
            except Exception as e:
                logger.warning("Error deleting batch %s: %s", batch_dir, e)

        return False


def _safe_float(value: Any) -> float | None:
    if value is None or not bool(pd.notna(value)):
        return None
    return float(value)


class DatabaseInternalForecastRepository(InternalForecastRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._engine = None

    def get_engine(self):
        if self._engine is None:
            self._engine = create_engine(self.database_url, pool_pre_ping=True)
        return self._engine

    @staticmethod
    def _build_forecast_records(
            forecasts_df: pd.DataFrame,
            batch_id: str,
            generated_at: datetime,
            entity_type: str,
            horizon_months: int,
    ) -> list[dict]:
        records = []
        for _, row in forecasts_df.iterrows():
            records.append({
                "forecast_batch_id": batch_id,
                "generated_at": generated_at,
                "entity_id": str(row.get("entity_id", "")),
                "entity_type": str(row.get("entity_type", entity_type)),
                "forecast_method": str(row.get("method", "unknown")),
                "forecast_period": str(row.get("period", "")),
                "forecast_value": float(row.get("forecast", 0) or 0),
                "lower_ci": _safe_float(row.get("lower_ci")),
                "upper_ci": _safe_float(row.get("upper_ci")),
                "horizon_months": horizon_months,
                "product_type": row.get("product_type"),
                "cv": _safe_float(row.get("cv")),
            })
        return records

    def save_forecast_batch(
            self,
            forecasts_df: pd.DataFrame,
            entity_type: str,
            horizon_months: int,
            stats: dict,
            parameters: dict | None = None,
            notes: str | None = None,
    ) -> str:
        batch_id = str(uuid.uuid4())
        generated_at = datetime.now()
        engine = self.get_engine()

        try:
            with engine.begin() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    text("""
                         INSERT INTO internal_forecast_batches
                         (id, generated_at, entity_type, horizon_months,
                          total_entities, success_count, failed_count,
                          methods_used, parameters, notes)
                         VALUES (:id, :generated_at, :entity_type, :horizon_months,
                                 :total_entities, :success_count, :failed_count,
                                 :methods_used, :parameters, :notes)
                         """),
                    {
                        "id": batch_id,
                        "generated_at": generated_at,
                        "entity_type": entity_type,
                        "horizon_months": horizon_months,
                        "total_entities": stats.get("total", 0),
                        "success_count": stats.get("success", 0),
                        "failed_count": stats.get("failed", 0),
                        "methods_used": json.dumps(stats.get("methods", {})),
                        "parameters": json.dumps(parameters or {}),
                        "notes": notes,
                    },
                )

                if not forecasts_df.empty:
                    forecast_records = DatabaseInternalForecastRepository._build_forecast_records(
                        forecasts_df, batch_id, generated_at, entity_type, horizon_months
                    )

                    conn.execute(
                        text("""
                             INSERT INTO internal_forecasts
                             (forecast_batch_id, generated_at, entity_id, entity_type,
                              forecast_method, forecast_period, forecast_value,
                              lower_ci, upper_ci, horizon_months, product_type, cv)
                             VALUES (:forecast_batch_id, :generated_at, :entity_id, :entity_type,
                                     :forecast_method, :forecast_period, :forecast_value,
                                     :lower_ci, :upper_ci, :horizon_months, :product_type, :cv)
                             """),
                        forecast_records,
                    )

            logger.info("Saved forecast batch %s to database (%d forecasts)", batch_id, len(forecasts_df))
            return batch_id

        except Exception as e:
            logger.exception("Error saving forecast batch to database: %s", e)
            raise

    def get_forecast_batches(self, entity_type: str | None = None, limit: int = 20) -> list[dict]:
        engine = self.get_engine()

        query = """
                SELECT id as batch_id,
                       generated_at,
                       entity_type,
                       horizon_months,
                       total_entities,
                       success_count,
                       failed_count,
                       methods_used,
                       parameters,
                       notes
                FROM internal_forecast_batches \
                """

        params: dict[str, int | str] = {"limit": limit}
        if entity_type:
            query += " WHERE entity_type = :entity_type"
            params["entity_type"] = entity_type

        query += " ORDER BY generated_at DESC LIMIT :limit"

        try:
            with engine.connect() as conn:  # type: ignore[attr-defined]
                result = conn.execute(text(query), params)
                batches = []
                for row in result:
                    batches.append({
                        "batch_id": str(row.batch_id),
                        "generated_at": row.generated_at.isoformat() if row.generated_at else None,
                        "entity_type": row.entity_type,
                        "horizon_months": row.horizon_months,
                        "total_entities": row.total_entities,
                        "success_count": row.success_count,
                        "failed_count": row.failed_count,
                        "methods_used": row.methods_used if isinstance(row.methods_used, dict) else json.loads(
                            row.methods_used or "{}"),
                        "parameters": row.parameters if isinstance(row.parameters, dict) else json.loads(
                            row.parameters or "{}"),
                        "notes": row.notes,
                    })
                return batches
        except Exception as e:
            logger.exception("Error getting forecast batches: %s", e)
            return []

    def get_forecast_batch(self, batch_id: str) -> pd.DataFrame | None:
        engine = self.get_engine()

        try:
            with engine.connect() as conn:  # type: ignore[attr-defined]
                result = conn.execute(
                    text("""
                         SELECT entity_id,
                                entity_type,
                                forecast_method as method,
                                forecast_period as period,
                                forecast_value  as forecast,
                                lower_ci,
                                upper_ci,
                                product_type,
                                cv
                         FROM internal_forecasts
                         WHERE forecast_batch_id = :batch_id
                         ORDER BY entity_id, forecast_period
                         """),
                    {"batch_id": batch_id},
                )

                rows = result.fetchall()
                if not rows:
                    return None

                columns = pd.Index(list(result.keys()))
                return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.exception("Error getting forecast batch %s: %s", batch_id, e)
            return None

    def delete_forecast_batch(self, batch_id: str) -> bool:
        engine = self.get_engine()

        try:
            with engine.begin() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    text("DELETE FROM internal_forecasts WHERE forecast_batch_id = :batch_id"),
                    {"batch_id": batch_id},
                )
                result = conn.execute(
                    text("DELETE FROM internal_forecast_batches WHERE id = :batch_id"),
                    {"batch_id": batch_id},
                )
                if result.rowcount > 0:
                    logger.info("Deleted forecast batch %s", batch_id)
                    return True
                return False

        except Exception as e:
            logger.exception("Error deleting forecast batch %s: %s", batch_id, e)
            return False


def create_internal_forecast_repository() -> InternalForecastRepository:
    from dotenv import load_dotenv
    load_dotenv()

    mode = os.getenv("DATA_SOURCE_MODE", "file")
    database_url = os.getenv("DATABASE_URL")

    if mode == "database" and database_url:
        try:
            repo = DatabaseInternalForecastRepository(database_url)
            repo.get_engine()
            return repo
        except Exception as e:
            logger.warning("Database not available, falling back to file: %s", e)

    return FileInternalForecastRepository()
