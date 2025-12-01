import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .data_source import DataSource
from .file_source import FileSource

SOURCE_CONFIG_JSON = 'data_source_config.json'


class DataSourceFactory:

    @staticmethod
    def create_data_source() -> DataSource:

        load_dotenv()

        config_path = Path(__file__).parent.parent / SOURCE_CONFIG_JSON

        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {'mode': 'file'}

        mode = os.environ.get('DATA_SOURCE_MODE', config.get('mode', 'file'))

        if mode == 'database':
            connection_string = config.get('connection_string') or os.environ.get('DATABASE_URL')

            if connection_string:
                try:
                    from .db_source import DatabaseSource

                    pool_size = config.get('pool_size', 10)
                    pool_recycle = config.get('pool_recycle', 3600)

                    db_source: DatabaseSource = DatabaseSource(connection_string, pool_size, pool_recycle)

                    if db_source.is_available():
                        print("[OK] Using database data source")
                        return db_source
                    else:
                        print("[WARN] Database unavailable, falling back to file mode")
                        return FileSource()

                except Exception as e:
                    print(f"[ERROR] Database connection failed: {e}")
                    if config.get('fallback_to_file', True):
                        print("[INFO] Falling back to file mode")
                        return FileSource()
                    else:
                        raise
            else:
                print("[WARN] No database connection string found, using file mode")
                return FileSource()

        print("[INFO] Using file data source")
        return FileSource()

    @staticmethod
    def get_current_mode() -> str:
        load_dotenv()

        config_path = Path(__file__).parent.parent / SOURCE_CONFIG_JSON

        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {'mode': 'file'}

        return os.environ.get('DATA_SOURCE_MODE', config.get('mode', 'file'))

    @staticmethod
    def switch_mode(mode: str) -> None:
        if mode not in ['file', 'database']:
            raise ValueError("Mode must be 'file' or 'database'")

        config_path = Path(__file__).parent.parent / SOURCE_CONFIG_JSON

        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        config['mode'] = mode

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"[OK] Data source mode switched to: {mode}")
