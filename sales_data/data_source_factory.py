from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from utils.logging_config import get_logger

from .data_source import DataSource
from .file_source import FileSource

SETTINGS_FILE = "settings.json"
DEFAULT_CONFIG = {"mode": "file"}

logger = get_logger("data_source_factory")


def _get_settings_path() -> Path:
    return Path(__file__).parent.parent / SETTINGS_FILE


def _load_settings_file() -> dict:
    config_path = _get_settings_path()
    if not config_path.exists():
        return {}
    with open(config_path, "r") as f:
        return json.load(f)


def _save_settings_file(settings: dict) -> None:
    with open(_get_settings_path(), "w") as f:
        json.dump(settings, f, indent=2)


def _load_data_source_config() -> dict:
    settings = _load_settings_file()
    return settings.get("data_source", DEFAULT_CONFIG.copy())


def _get_effective_mode(config: dict) -> str:
    return os.environ.get("DATA_SOURCE_MODE") or config.get("mode") or "file"


class DataSourceFactory:

    @staticmethod
    def _get_connection_string(config: dict) -> str | None:
        return config.get("connection_string") or os.environ.get("DATABASE_URL")

    @staticmethod
    def _create_database_source(connection_string: str, config: dict) -> DataSource:
        from .db_source import DatabaseSource

        pool_size = config.get("pool_size", 10)
        pool_recycle = config.get("pool_recycle", 3600)

        db_source = DatabaseSource(connection_string, pool_size, pool_recycle)

        if db_source.is_available():
            logger.info("Using database data source")
            return db_source

        logger.warning("Database unavailable, falling back to file mode")
        return FileSource()

    @staticmethod
    def _handle_database_mode(config: dict) -> DataSource:
        connection_string = DataSourceFactory._get_connection_string(config)

        if not connection_string:
            logger.warning("No database connection string found, using file mode")
            return FileSource()

        try:
            return DataSourceFactory._create_database_source(connection_string, config)
        except Exception as e:
            logger.error("Database connection failed: %s", e)
            if config.get("fallback_to_file", True):
                logger.info("Falling back to file mode")
                return FileSource()
            raise

    @staticmethod
    def create_data_source() -> DataSource:
        load_dotenv()
        config = _load_data_source_config()
        mode = _get_effective_mode(config)

        if mode == "database":
            return DataSourceFactory._handle_database_mode(config)

        logger.info("Using file data source")
        return FileSource()

    @staticmethod
    def get_current_mode() -> str:
        load_dotenv()
        config = _load_data_source_config()
        return _get_effective_mode(config)

    @staticmethod
    def switch_mode(mode: str) -> None:
        if mode not in ["file", "database"]:
            raise ValueError("Mode must be 'file' or 'database'")

        settings = _load_settings_file()
        if "data_source" not in settings:
            settings["data_source"] = {}

        settings["data_source"]["mode"] = mode
        _save_settings_file(settings)

        logger.info("Data source mode switched to: %s", mode)
