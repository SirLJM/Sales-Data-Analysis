from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from utils.logging_config import get_logger

from .data_source import DataSource
from .file_source import FileSource

SETTINGS_FILE = "settings.json"

logger = get_logger("data_source_factory")


class DataSourceFactory:

    @staticmethod
    def _load_config():
        config_path = Path(__file__).parent.parent / SETTINGS_FILE
        if config_path.exists():
            with open(config_path, "r") as f:
                settings = json.load(f)
                return settings.get("data_source", {"mode": "file"})
        return {"mode": "file"}

    @staticmethod
    def _get_connection_string(config):
        return config.get("connection_string") or os.environ.get("DATABASE_URL")

    @staticmethod
    def _create_database_source(connection_string, config) -> DataSource:
        from .db_source import DatabaseSource

        pool_size = config.get("pool_size", 10)
        pool_recycle = config.get("pool_recycle", 3600)

        db_source = DatabaseSource(connection_string, pool_size, pool_recycle)

        if db_source.is_available():
            logger.info("Using database data source")
            return db_source
        else:
            logger.warning("Database unavailable, falling back to file mode")
            return FileSource()

    @staticmethod
    def _handle_database_mode(config) -> DataSource:
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
            else:
                raise

    @staticmethod
    def create_data_source() -> DataSource:
        load_dotenv()

        config = DataSourceFactory._load_config()
        mode = os.environ.get("DATA_SOURCE_MODE", config.get("mode", "file"))

        if mode == "database":
            return DataSourceFactory._handle_database_mode(config)

        logger.info("Using file data source")
        return FileSource()

    @staticmethod
    def get_current_mode() -> str:
        load_dotenv()

        config_path = Path(__file__).parent.parent / SETTINGS_FILE

        if config_path.exists():
            with open(config_path, "r") as f:
                settings = json.load(f)
                config = settings.get("data_source", {"mode": "file"})
        else:
            config = {"mode": "file"}

        return os.environ.get("DATA_SOURCE_MODE", config.get("mode", "file"))

    @staticmethod
    def switch_mode(mode: str) -> None:
        if mode not in ["file", "database"]:
            raise ValueError("Mode must be 'file' or 'database'")

        config_path = Path(__file__).parent.parent / SETTINGS_FILE

        if config_path.exists():
            with open(config_path, "r") as f:
                settings = json.load(f)
        else:
            settings = {"data_source": {}}

        if "data_source" not in settings:
            settings["data_source"] = {}

        settings["data_source"]["mode"] = mode

        with open(config_path, "w") as f:
            json.dump(settings, f, indent=2)

        logger.info("Data source mode switched to: %s", mode)
