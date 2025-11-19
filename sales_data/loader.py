import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from typing import List, Optional
from .validator import DataValidator


class SalesDataLoader:
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.validator = DataValidator()

    @staticmethod
    def _parse_filename(filename: str) -> Optional[tuple]:

        pattern = r'(\d{8})[_-](\d{8})\.(csv|xlsx)$'
        match = re.match(pattern, filename)

        if match:
            start_str, end_str, _ = match.groups()
            try:
                start_date = datetime.strptime(start_str, '%Y%m%d')
                end_date = datetime.strptime(end_str, '%Y%m%d')
                return start_date, end_date
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_stock_filename(filename: str) -> Optional[datetime]:

        pattern = r'^(\d{8})\.(csv|xlsx)$'
        match = re.match(pattern, filename)

        if match:
            date_str, _ = match.groups()
            try:
                file_date = datetime.strptime(date_str, '%Y%m%d')
                return file_date
            except ValueError:
                return None
        return None

    def find_data_files(self) -> List[tuple]:

        files_info = []
        seen_dates = set()

        for file_path in list(self.data_directory.glob("*.csv")) + list(self.data_directory.glob("*.xlsx")):
            date_range = self._parse_filename(file_path.name)
            if date_range is not None:
                date_key = (date_range[0], date_range[1])
                if date_key not in seen_dates:
                    files_info.append((file_path, date_range[0], date_range[1]))
                    seen_dates.add(date_key)

        # Sort by start date
        files_info.sort(key=lambda x: x[1])

        return files_info

    def find_stock_files(self) -> List[tuple]:

        files_info = []
        seen_dates = set()

        for file_path in list(self.data_directory.glob("*.csv")) + list(self.data_directory.glob("*.xlsx")):
            file_date = self._parse_stock_filename(file_path.name)
            if file_date is not None:
                if file_date not in seen_dates:
                    files_info.append((file_path, file_date))
                    seen_dates.add(file_date)

        # Sort by date
        files_info.sort(key=lambda x: x[1])

        return files_info

    def get_latest_stock_file(self) -> Optional[Path]:

        stock_files = self.find_stock_files()

        if not stock_files:
            return None

        return stock_files[-1][0]

    def get_latest_current_year_file(self) -> Optional[Path]:
        current_year = datetime.now().year
        current_year_files = []

        for file_path in list(self.data_directory.glob("*.csv")) + list(self.data_directory.glob("*.xlsx")):
            date_range = self._parse_filename(file_path.name)
            if date_range and date_range[0].year == current_year:
                current_year_files.append((file_path, date_range[1]))

        if not current_year_files:
            return None

        current_year_files.sort(key=lambda x: x[1], reverse=True)
        return current_year_files[0][0]

    def load_sales_file(self, file_path: Path) -> pd.DataFrame:

        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix == '.xlsx':
            sheet_name = self.validator.find_sales_sheet(file_path)
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path, sheet_name='Sheet1')
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        is_valid, errors = self.validator.validate_sales_data(df)
        if not is_valid:
            raise ValueError(f"Invalid sales data: {errors}")

        df['data'] = pd.to_datetime(df['data'])

        df = df.dropna(how='all')

        date_range = self._parse_filename(file_path.name)
        if date_range:
            df['file_start_date'] = date_range[0]
            df['file_end_date'] = date_range[1]
            df['source_file'] = file_path.name

        return df

    def load_stock_file(self, file_path: Path) -> pd.DataFrame:
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix == '.xlsx':
            sheet_name = self.validator.find_stock_sheet(file_path)
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path, sheet_name='Sheet1')
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        is_valid, errors = self.validator.validate_stock_data(df)
        if not is_valid:
            raise ValueError(f"Invalid stock data: {errors}")

        df = df[df['aktywny'] == 1]

        df = df[['sku', 'available_stock']].copy()

        return df

    def consolidate_all_files(self) -> pd.DataFrame:
        files_info = self.find_data_files()

        if not files_info:
            raise ValueError(f"No data files found in {self.data_directory}")

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

        print(f"\nConsolidation complete!")
        print(f"Total rows: {len(consolidated_df):,}")
        print(f"Unique orders: {consolidated_df['order_id'].nunique():,}")
        print(f"Unique products (SKUs): {consolidated_df['sku'].nunique():,}")

        return consolidated_df

    def get_aggregated_data(self) -> pd.DataFrame:
        return self.consolidate_all_files()
