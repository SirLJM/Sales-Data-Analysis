from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pandas import DataFrame

from utils.logging_config import get_logger
from utils.parallel_loader import parallel_load
from .dtype_optimizer import (
    get_optimal_sales_dtypes,
    optimize_dtypes,
)
from .validator import DataValidator

USING_SHEET_S = "Using sheet: %s"

logger = get_logger("loader")

PATH_TO = "/path/to"

CSV = ".csv"

XLSX = ".xlsx"

ANY_XLSX = "*.xlsx"

ANY_CSV = "*.csv"


def load_size_aliases_from_excel(sizes_file_path: Path) -> dict[str, str]:
    df = pd.read_excel(sizes_file_path)
    df = df[["size", "metric"]].copy()
    df.columns = ["size_code", "size_alias"]
    df["size_code"] = df["size_code"].astype(str).str.zfill(2)
    df["size_alias"] = df["size_alias"].astype(str)
    return dict(zip(df["size_code"], df["size_alias"]))


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

    def _process_forecast_subdir(self, subdir: Path, seen_dates: dict[datetime, Path]) -> None:
        try:
            folder_date = datetime.strptime(subdir.name, "%Y-%m-%d")
        except ValueError:
            return

        forecast_files = list(subdir.glob("forecast_*.csv")) + list(subdir.glob("forecast_*.xlsx"))

        for file_path in forecast_files:
            if folder_date not in seen_dates or self._should_replace_forecast_file(
                    file_path, seen_dates[folder_date]
            ):
                seen_dates[folder_date] = file_path

    def _process_direct_forecast_files(self, seen_dates: dict[datetime, Path]) -> None:
        direct_files = list(self.forecast_dir.glob("forecast_*.csv")) + list(
            self.forecast_dir.glob("forecast_*.xlsx")
        )

        for file_path in direct_files:
            parsed_date = self._parse_forecast_filename(file_path.name)
            if parsed_date and (parsed_date not in seen_dates or self._should_replace_forecast_file(
                    file_path, seen_dates[parsed_date]
            )):
                seen_dates[parsed_date] = file_path

    def find_forecast_files(self) -> list[tuple[Path, datetime]]:
        seen_dates: dict[datetime, Path] = {}

        if not self.forecast_dir.exists():
            return []

        subdirs = [d for d in self.forecast_dir.iterdir() if d.is_dir()]

        for subdir in subdirs:
            self._process_forecast_subdir(subdir, seen_dates)

        if not seen_dates:
            self._process_direct_forecast_files(seen_dates)

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
    def _read_file(
            file_path: Path,
            find_sheet_method=None,
            usecols: list[str] | None = None,
            dtype: dict | None = None,
    ) -> DataFrame | dict[Any, DataFrame]:
        if file_path.suffix == CSV:
            return pd.read_csv(file_path, usecols=usecols, dtype=dtype)
        elif file_path.suffix == XLSX:
            sheet_name = find_sheet_method(file_path) if find_sheet_method else None
            result = pd.read_excel(
                file_path,
                sheet_name=sheet_name or "Sheet1",
                usecols=usecols,
                dtype=dtype,
            )
            return result
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
        sales_cols = ["order_id", "data", "sku", "ilosc", "cena", "razem"]
        dtype = get_optimal_sales_dtypes()
        dtype_without_date = {k: v for k, v in dtype.items() if k != "data"}

        df = self._read_file(
            file_path,
            self.validator.find_sales_sheet,
            usecols=sales_cols,
            dtype=dtype_without_date,
        )
        df = self._validate_and_clean_sales_data(df)
        df = self._add_sales_metadata(df, file_path)
        return optimize_dtypes(df)

    def _validate_and_filter_stock_data(self, df: pd.DataFrame) -> pd.DataFrame:
        is_valid, errors = self.validator.validate_stock_data(df)
        if not is_valid:
            raise ValueError(f"Invalid stock data: {errors}")

        df = df[df["aktywny"] == 1]
        return df[["sku", "nazwa", "cena_netto", "available_stock"]].copy()

    def load_stock_file(self, file_path: Path) -> pd.DataFrame:
        logger.info("Loading stock file: %s", file_path.name)

        sheet_name = (
            self.validator.find_stock_sheet(file_path) if file_path.suffix == XLSX else None
        )
        if sheet_name:
            logger.debug(USING_SHEET_S, sheet_name)
        elif file_path.suffix == XLSX:
            logger.debug("Using default sheet: Sheet1")

        df = self._read_file(file_path, self.validator.find_stock_sheet)
        df = self._validate_and_filter_stock_data(df)
        df = optimize_dtypes(df)

        logger.info("Loaded %d active SKUs", len(df))

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
        logger.info("Loading forecast file: %s", file_path.name)

        sheet_name = (
            self.validator.find_forecast_sheet(file_path) if file_path.suffix == XLSX else None
        )
        if sheet_name:
            logger.debug(USING_SHEET_S, sheet_name)
        elif file_path.suffix == XLSX:
            logger.debug("Using default sheet: Sheet1")

        df = self._read_file(file_path, self.validator.find_forecast_sheet)
        df = self._validate_and_prepare_forecast_data(df)
        df = optimize_dtypes(df)

        logger.info("Loaded %d forecast records for %d SKUs", len(df), df['sku'].nunique())

        return df

    def _load_single_sales_file(self, file_info: tuple[Path, datetime, datetime]) -> pd.DataFrame:
        file_path, _, _ = file_info
        df = self.load_sales_file(file_path)
        logger.debug("Loaded: %s (%d rows)", file_path.name, len(df))
        return df

    def consolidate_all_files(self) -> pd.DataFrame:
        files_info = self.find_data_files()

        if not files_info:
            raise ValueError(
                f"No data files found in {self.archival_sales_dir} or {self.current_sales_dir}"
            )

        logger.info("Found %d data file(s)", len(files_info))
        for file_path, start_date, end_date in files_info:
            logger.debug("  - %s: %s to %s", file_path.name, start_date.date(), end_date.date())

        logger.info("Loading files in parallel...")
        all_dataframes = parallel_load(
            files_info, self._load_single_sales_file, desc="Loading sales files"
        )

        consolidated_df = pd.concat(all_dataframes, ignore_index=True)
        consolidated_df = optimize_dtypes(consolidated_df, verbose=False)

        logger.info(
            "Consolidation complete: %d rows, %d orders, %d SKUs",
            len(consolidated_df),
            consolidated_df['order_id'].nunique(),
            consolidated_df['sku'].nunique()
        )

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
                    logger.debug("Using fallback: found in data/ folder")
                    return file_path

        return None

    def _read_model_metadata_file(self, file_path: Path) -> pd.DataFrame | None:
        if file_path.suffix == CSV:
            return pd.read_csv(file_path)
        elif file_path.suffix == XLSX:
            sheet_name = self.validator.find_model_metadata_sheet(file_path)
            if sheet_name:
                logger.debug(USING_SHEET_S, sheet_name)
                return pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
            else:
                logger.warning("Could not find valid sheet with metadata columns")
                return None
        return None

    def _validate_and_prepare_metadata(self, df: pd.DataFrame) -> pd.DataFrame | None:
        is_valid, errors = self.validator.validate_model_metadata(df)
        if not is_valid:
            logger.warning("Invalid model metadata: %s", errors)
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
            logger.warning("Model metadata file not found")
            return None

        logger.info("Loading model metadata: %s", file_path.name)

        try:
            df = self._read_model_metadata_file(file_path)
            if df is None:
                return None

            df = self._validate_and_prepare_metadata(df)
            if df is None:
                return None

            logger.info("Loaded %d models with metadata", len(df))
            return df

        except PermissionError:
            logger.error("File is locked/open. Please close the Excel file and restart the app.")
            return None
        except Exception as e:
            logger.warning("Could not load model metadata: %s", e)
            return None

    def load_color_aliases(self) -> dict[str, str]:
        file_path = self.find_model_metadata_file()

        if file_path is None:
            logger.warning("Color aliases file not found")
            return {}

        try:
            df = pd.read_excel(file_path, sheet_name='kolory', engine='openpyxl')
            df = df[["NUMER", "KOLOR"]].copy()
            df = df.dropna(subset=["NUMER", "KOLOR"])
            df["NUMER"] = df["NUMER"].astype(str).str.replace('*', '', regex=False).str[:2].str.zfill(2).str.upper()
            df["KOLOR"] = df["KOLOR"].astype(str)
            return dict(zip(df["NUMER"], df["KOLOR"]))

        except Exception as e:
            logger.warning("Could not load color aliases: %s", e)
            return {}

    @staticmethod
    def find_category_file() -> str:
        data_dir = Path(__file__).parent.parent / "data"

        exact_path = data_dir / "1. MODELE&KOLORY_NUMERACJA.xlsx"
        if exact_path.exists():
            return str(exact_path)

        for file in data_dir.glob("*.xlsx"):
            name_lower = file.name.lower()
            if "modele" in name_lower and "kolory" in name_lower:
                return str(file)

        raise FileNotFoundError(
            f"Category mapping file not found in {data_dir}. "
            "Expected '1. MODELE&KOLORY_NUMERACJA.xlsx' or similar."
        )

    def load_category_data(self) -> pd.DataFrame:
        import openpyxl

        file_path = self.find_category_file()

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet_name = self.validator.find_category_sheet(Path(file_path))
            wb.close()

            df = pd.read_excel(file_path, sheet_name=sheet_name)
            df = df[list(self.validator.CATEGORY_COLUMNS)]  # type: ignore[index]
            df = df.dropna(subset=["Model"])
            df["Model"] = df["Model"].astype(str).str.strip().str.upper()
            df = df.drop_duplicates(subset=["Model"], keep="first")

            self.validator.validate_category_data(df)
            return df

        except Exception as e:
            raise ValueError(f"Failed to load category data from {file_path}: {str(e)}")
