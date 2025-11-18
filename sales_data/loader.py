import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from typing import List, Optional


class SalesDataLoader:

    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse_filename(filename: str) -> Optional[tuple]:

        pattern = r'(\d{8})[_-](\d{8})\.csv'
        match = re.match(pattern, filename)

        if match:
            start_str, end_str = match.groups()
            try:
                start_date = datetime.strptime(start_str, '%Y%m%d')
                end_date = datetime.strptime(end_str, '%Y%m%d')
                return start_date, end_date
            except ValueError:
                return None
        return None

    def find_data_files(self) -> List[tuple]:

        files_info = []

        for file_path in self.data_directory.glob("*.csv"):
            date_range = self._parse_filename(file_path.name)
            if date_range:
                files_info.append((file_path, date_range[0], date_range[1]))

        # Sort by start date
        files_info.sort(key=lambda x: x[1])

        return files_info

    def get_latest_current_year_file(self) -> Optional[Path]:

        current_year = datetime.now().year
        current_year_files = []

        for file_path in self.data_directory.glob("*.csv"):
            date_range = self._parse_filename(file_path.name)
            if date_range and date_range[0].year == current_year:
                current_year_files.append((file_path, date_range[1]))

        if not current_year_files:
            return None

        current_year_files.sort(key=lambda x: x[1], reverse=True)
        return current_year_files[0][0]

    def load_csv_file(self, file_path: Path) -> pd.DataFrame:
        """
        Expected columns:
        - order_id: Order identifier
        - data: Date in format 'YYYY-MM-DD HH:MM:SS'
        - sku: Product ID
        - ilosc: Quantity
        - cena: Price
        - razem: Total
        """

        df = pd.read_csv(file_path)

        expected_columns = ['order_id', 'data', 'sku', 'ilosc', 'cena', 'razem']
        if not all(col in df.columns for col in expected_columns):
            raise ValueError(
                f"CSV file {file_path.name} missing required columns. "
                f"Expected: {expected_columns}, Found: {df.columns.tolist()}"
            )

        df['data'] = pd.to_datetime(df['data'])

        # df['model'] = df['sku'].astype(str).str[:5]

        df = df.dropna(how='all')

        date_range = self._parse_filename(file_path.name)
        if date_range:
            df['file_start_date'] = date_range[0]
            df['file_end_date'] = date_range[1]
            df['source_file'] = file_path.name

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
            df = self.load_csv_file(file_path)
            print(f"  Loaded {len(df):,} rows")
            all_dataframes.append(df)

        consolidated_df = pd.concat(all_dataframes, ignore_index=True)

        # Sort by date
        # consolidated_df = consolidated_df.sort_values('data').reset_index(drop=True)

        print(f"\nConsolidation complete!")
        print(f"Total rows: {len(consolidated_df):,}")
        print(f"Unique orders: {consolidated_df['order_id'].nunique():,}")
        print(f"Unique products (SKUs): {consolidated_df['sku'].nunique():,}")

        return consolidated_df

    def get_aggregated_data(self) -> pd.DataFrame:
        return self.consolidate_all_files()
