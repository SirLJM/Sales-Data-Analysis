import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from .validator import DataValidator

PATH_TO = "/path/to"

CSV = ".csv"

XLSX = ".xlsx"

ANY_XLSX = "*.xlsx"

ANY_CSV = "*.csv"


class SalesDataLoader:
    def __init__(self, paths_file: str | None = None) -> None:
        self.validator = DataValidator()

        paths_file_path = self._get_paths_file_path(paths_file)
        default_data_dir = Path(__file__).parent.parent / "data"

        if paths_file_path.exists():
            self._load_paths_from_file(paths_file_path, default_data_dir)
        else:
            self._set_default_paths(default_data_dir)

    @staticmethod
    def _get_paths_file_path(paths_file: str | None) -> Path:
        if paths_file is None:
            return Path(__file__).parent / "paths_to_files.txt"
        return Path(paths_file)

    @staticmethod
    def _is_valid_path(line: str) -> bool:
        return bool(line) and not line.startswith(PATH_TO)

    @staticmethod
    def _parse_path(line: str, default_path: Path) -> Path:
        if SalesDataLoader._is_valid_path(line):
            return Path(line)
        return default_path

    @staticmethod
    def _parse_optional_path(line: str) -> Path | None:
        if SalesDataLoader._is_valid_path(line):
            return Path(line)
        return None

    def _load_paths_from_file(self, paths_file_path: Path, default_data_dir: Path) -> None:
        with open(paths_file_path, "r", encoding="utf-8") as f:
            lines = [line.strip().strip("'\"") for line in f.readlines()]

        self.archival_sales_dir = (
            self._parse_path(lines[0], default_data_dir) if len(lines) > 0 else default_data_dir
        )
        self.current_sales_dir = (
            self._parse_path(lines[1], default_data_dir) if len(lines) > 1 else default_data_dir
        )
        self.stock_dir = (
            self._parse_path(lines[2], default_data_dir) if len(lines) > 2 else default_data_dir
        )
        self.forecast_dir = (
            self._parse_path(lines[3], default_data_dir) if len(lines) > 3 else default_data_dir
        )
        self.model_metadata_path = self._parse_optional_path(lines[4]) if len(lines) > 4 else None

    def _set_default_paths(self, default_data_dir: Path) -> None:
        self.archival_sales_dir = default_data_dir
        self.current_sales_dir = default_data_dir
        self.stock_dir = default_data_dir
        self.forecast_dir = default_data_dir
        self.model_metadata_path = None

    @staticmethod
    def _parse_sales_filename(filename: str) -> tuple[datetime, datetime] | None:

        pattern = r"(\d{8})[_-](\d{8})\.(csv|xlsx)$"
        match = re.match(pattern, filename)

        if match:
            start_str, end_str, _ = match.groups()
            try:
                start_date = datetime.strptime(start_str, "%Y%m%d")
                end_date = datetime.strptime(end_str, "%Y%m%d")
                return start_date, end_date
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_stock_filename(filename: str) -> datetime | None:

        pattern = r"^(\d{8})\.(csv|xlsx)$"
        match = re.match(pattern, filename)

        if match:
            date_str, _ = match.groups()
            try:
                file_date = datetime.strptime(date_str, "%Y%m%d")
                return file_date
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_forecast_filename(filename: str) -> datetime | None:
        pattern = r"^forecast_\d{4}_\d{2}_\d{2}_generated_(\d{4})_(\d{2})_(\d{2})\.(csv|xlsx)$"
        match = re.match(pattern, filename)

        if match:
            year, month, day, _ = match.groups()
            try:
                file_date = datetime(int(year), int(month), int(day))
                return file_date
            except ValueError:
                return None
        return None

    def collect_files_from_directory(
        self, directory: Path
    ) -> list[tuple[Path, datetime, datetime]]:
        collected_files = []
        for file_path in list(directory.glob(ANY_CSV)) + list(directory.glob(ANY_XLSX)):
            date_range = self._parse_sales_filename(file_path.name)
            if date_range is not None:
                collected_files.append((file_path, date_range[0], date_range[1]))
        return collected_files

    def _add_archival_files(
        self, files_info: list[tuple[Path, datetime, datetime]], seen_dates: set
    ) -> None:
        if not self.archival_sales_dir.exists():
            return

        for file_path, start_date, end_date in self.collect_files_from_directory(
            self.archival_sales_dir
        ):
            date_key = (start_date, end_date)
            if date_key not in seen_dates:
                files_info.append((file_path, start_date, end_date))
                seen_dates.add(date_key)

    def _add_latest_current_file(
        self, files_info: list[tuple[Path, datetime, datetime]], seen_dates: set
    ) -> None:
        if not self.current_sales_dir.exists():
            return

        current_files = self.collect_files_from_directory(self.current_sales_dir)
        if not current_files:
            return

        current_files.sort(key=lambda x: x[2], reverse=True)
        latest_file = current_files[0]
        date_key = (latest_file[1], latest_file[2])
        if date_key not in seen_dates:
            files_info.append(latest_file)
            seen_dates.add(date_key)

    def find_data_files(self) -> list[tuple[Path, datetime, datetime]]:
        files_info: list[tuple[Path, datetime, datetime]] = []
        seen_dates: set[tuple[datetime, datetime]] = set()

        self._add_archival_files(files_info, seen_dates)
        self._add_latest_current_file(files_info, seen_dates)

        files_info.sort(key=lambda x: x[1])

        return files_info

    def find_stock_files(self) -> list[tuple[Path, datetime]]:
        files_info = []
        seen_dates = set()

        if self.stock_dir.exists():
            for file_path in list(self.stock_dir.glob(ANY_CSV)) + list(
                self.stock_dir.glob(ANY_XLSX)
            ):
                file_date = self._parse_stock_filename(file_path.name)
                if file_date is not None and file_date not in seen_dates:
                    files_info.append((file_path, file_date))
                    seen_dates.add(file_date)

        files_info.sort(key=lambda x: x[1])

        return files_info

    @staticmethod
    def _should_replace_forecast_file(new_file: Path, existing_file: Path) -> bool:
        return new_file.suffix == XLSX and existing_file.suffix == CSV

    def find_forecast_files(self) -> list[tuple[Path, datetime]]:
        files_info: list[tuple[Path, datetime]] = []
        seen_dates: dict[datetime, Path] = {}

        if self.forecast_dir.exists():
            subdirs = [d for d in self.forecast_dir.iterdir() if d.is_dir()]

            for subdir in subdirs:
                try:
                    folder_date = datetime.strptime(subdir.name, "%Y-%m-%d")
                except ValueError:
                    continue

                forecast_files = list(subdir.glob("forecast_*.csv")) + list(
                    subdir.glob("forecast_*.xlsx")
                )

                for file_path in forecast_files:
                    if folder_date not in seen_dates or self._should_replace_forecast_file(
                        file_path, seen_dates[folder_date]
                    ):
                        seen_dates[folder_date] = file_path

            files_info = [(path, date) for date, path in seen_dates.items()]

        files_info.sort(key=lambda x: x[1])

        return files_info

    def get_latest_stock_file(self) -> Path | None:

        stock_files = self.find_stock_files()

        if not stock_files:
            return None

        return stock_files[-1][0]

    def get_latest_current_year_file(self) -> Path | None:
        current_year = datetime.now().year
        current_year_files = []

        if self.current_sales_dir.exists():
            for file_path in list(self.current_sales_dir.glob(ANY_CSV)) + list(
                self.current_sales_dir.glob(ANY_XLSX)
            ):
                date_range = self._parse_sales_filename(file_path.name)
                if date_range and date_range[0].year == current_year:
                    current_year_files.append((file_path, date_range[1]))

        if not current_year_files:
            return None

        current_year_files.sort(key=lambda x: x[1], reverse=True)
        return current_year_files[0][0]

    def get_latest_forecast_file(self) -> tuple[Path, datetime] | None:
        forecast_files = self.find_forecast_files()

        if not forecast_files:
            return None

        return forecast_files[-1]

    @staticmethod
    def _read_file(file_path: Path, find_sheet_method=None) -> pd.DataFrame:
        if file_path.suffix == CSV:
            return pd.read_csv(file_path)
        elif file_path.suffix == XLSX:
            sheet_name = find_sheet_method(file_path) if find_sheet_method else None
            result = pd.read_excel(file_path, sheet_name=sheet_name or "Sheet1")
            return result  # type: ignore[return-value]
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _validate_and_clean_sales_data(self, df: pd.DataFrame) -> pd.DataFrame:
        is_valid, errors = self.validator.validate_sales_data(df)
        if not is_valid:
            raise ValueError(f"Invalid sales data: {errors}")

        df["data"] = pd.to_datetime(df["data"])
        return df.dropna(how="all")

    def _add_sales_metadata(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        date_range = self._parse_sales_filename(file_path.name)
        if date_range:
            df["file_start_date"] = date_range[0]
            df["file_end_date"] = date_range[1]
            df["source_file"] = file_path.name
        return df

    def load_sales_file(self, file_path: Path) -> pd.DataFrame:
        df = self._read_file(file_path, self.validator.find_sales_sheet)
        df = self._validate_and_clean_sales_data(df)
        return self._add_sales_metadata(df, file_path)

    def _validate_and_filter_stock_data(self, df: pd.DataFrame) -> pd.DataFrame:
        is_valid, errors = self.validator.validate_stock_data(df)
        if not is_valid:
            raise ValueError(f"Invalid stock data: {errors}")

        df = df[df["aktywny"] == 1]
        return df[["sku", "nazwa", "cena_netto", "available_stock"]].copy()

    def load_stock_file(self, file_path: Path) -> pd.DataFrame:
        print(f"\nLoading stock file: {file_path.name}")

        sheet_name = (
            self.validator.find_stock_sheet(file_path) if file_path.suffix == XLSX else None
        )
        if sheet_name:
            print(f"  Using sheet: {sheet_name}")
        elif file_path.suffix == XLSX:
            print("Using default sheet: Sheet1")

        df = self._read_file(file_path, self.validator.find_stock_sheet)
        df = self._validate_and_filter_stock_data(df)

        print(f"  Loaded {len(df):,} active SKUs")

        return df

    def _validate_and_prepare_forecast_data(self, df: pd.DataFrame) -> pd.DataFrame:
        is_valid, errors = self.validator.validate_forecast_data(df)
        if not is_valid:
            raise ValueError(f"Invalid forecast data: {errors}")

        required_cols = ["data", "sku", "forecast"]
        if "model" in df.columns:
            required_cols.append("model")

        df = df[required_cols].copy()

        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"])

        return df

    def load_forecast_file(self, file_path: Path) -> pd.DataFrame:
        print(f"\nLoading forecast file: {file_path.name}")

        sheet_name = (
            self.validator.find_forecast_sheet(file_path) if file_path.suffix == XLSX else None
        )
        if sheet_name:
            print(f"  Using sheet: {sheet_name}")
        elif file_path.suffix == XLSX:
            print("Using default sheet: Sheet1")

        df = self._read_file(file_path, self.validator.find_forecast_sheet)
        df = self._validate_and_prepare_forecast_data(df)

        print(f"  Loaded {len(df):,} forecast records for {df['sku'].nunique():,} SKUs")

        return df

    def consolidate_all_files(self) -> pd.DataFrame:
        files_info = self.find_data_files()

        if not files_info:
            raise ValueError(
                f"No data files found in {self.archival_sales_dir} or {self.current_sales_dir}"
            )

        print(f"Found {len(files_info)} data file(s):")
        for file_path, start_date, end_date in files_info:
            print(f"  - {file_path.name}: {start_date.date()} to {end_date.date()}")

        all_dataframes = []

        for file_path, start_date, end_date in files_info:
            print(f"\nLoading: {file_path.name}...")
            df = self.load_sales_file(file_path)
            print(f"  Loaded {len(df):,} rows")
            all_dataframes.append(df)

        consolidated_df = pd.concat(all_dataframes, ignore_index=True)

        print("\nConsolidation complete!")
        print(f"Total rows: {len(consolidated_df):,}")
        print(f"Unique orders: {consolidated_df['order_id'].nunique():,}")
        print(f"Unique products (SKUs): {consolidated_df['sku'].nunique():,}")

        return consolidated_df

    def get_aggregated_data(self) -> pd.DataFrame:
        return self.consolidate_all_files()

    def find_model_metadata_file(self) -> Path | None:
        if self.model_metadata_path is not None and self.model_metadata_path.exists():
            return self.model_metadata_path

        data_dir = Path(__file__).parent.parent / "data"
        if data_dir.exists():
            for file_path in data_dir.glob(ANY_XLSX):
                if "MODELE" in file_path.name.upper() and "KOLORY" in file_path.name.upper():
                    print("(Using fallback: found in data/ folder)")
                    return file_path

        return None

    def _read_model_metadata_file(self, file_path: Path) -> pd.DataFrame | None:
        if file_path.suffix == CSV:
            return pd.read_csv(file_path)
        elif file_path.suffix == XLSX:
            sheet_name = self.validator.find_model_metadata_sheet(file_path)
            if sheet_name:
                print(f"  Using sheet: {sheet_name}")
                return pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
            else:
                print("  Could not find valid sheet with metadata columns")
                return None
        return None

    def _validate_and_prepare_metadata(self, df: pd.DataFrame) -> pd.DataFrame | None:
        is_valid, errors = self.validator.validate_model_metadata(df)
        if not is_valid:
            print(f"  Warning: Invalid model metadata: {errors}")
            return None

        required_cols = [
            "Model",
            "SZWALNIA GŁÓWNA",
            "SZWALNIA DRUGA",
            "RODZAJ MATERIAŁU",
            "GRAMATURA",
        ]
        df = df[required_cols].copy()
        df = df.dropna(subset=["Model"])

        return df

    def load_model_metadata(self) -> pd.DataFrame | None:
        file_path = self.find_model_metadata_file()

        if file_path is None:
            print("\nModel metadata file not found")
            return None

        print(f"\nLoading model metadata: {file_path.name}")

        try:
            df = self._read_model_metadata_file(file_path)
            if df is None:
                return None

            df = self._validate_and_prepare_metadata(df)
            if df is None:
                return None

            print(f"  Loaded {len(df):,} models with metadata")
            return df

        except PermissionError:
            print("Warning: File is locked/open. Please close the Excel file and restart the app.")
            return None
        except Exception as e:
            print(f"  Warning: Could not load model metadata: {e}")
            return None
