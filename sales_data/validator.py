import pandas as pd
from typing import List, Optional, Tuple
from pathlib import Path


class DataValidator:
    SALES_COLUMNS = {'order_id', 'data', 'sku', 'ilosc', 'cena', 'razem'}
    STOCK_COLUMNS = {'sku', 'nazwa', 'cena_netto', 'cena_brutto', 'stock', 'available_stock', 'aktywny'}

    @staticmethod
    def validate_sales_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:

        errors = []

        missing_columns = DataValidator.SALES_COLUMNS - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        if len(df) == 0:
            errors.append("DataFrame is empty")

        if 'ilosc' in df.columns and not pd.api.types.is_numeric_dtype(df['ilosc']):
            errors.append("Column 'ilosc' must be numeric")

        if 'cena' in df.columns and not pd.api.types.is_numeric_dtype(df['cena']):
            errors.append("Column 'cena' must be numeric")

        if 'razem' in df.columns and not pd.api.types.is_numeric_dtype(df['razem']):
            errors.append("Column 'razem' must be numeric")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def validate_stock_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:

        errors = []

        missing_columns = DataValidator.STOCK_COLUMNS - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        if len(df) == 0:
            errors.append("DataFrame is empty")

        if 'stock' in df.columns and not pd.api.types.is_numeric_dtype(df['stock']):
            errors.append("Column 'stock' must be numeric")

        if 'available_stock' in df.columns and not pd.api.types.is_numeric_dtype(df['available_stock']):
            errors.append("Column 'available_stock' must be numeric")

        if 'aktywny' in df.columns and not pd.api.types.is_numeric_dtype(df['aktywny']):
            errors.append("Column 'aktywny' must be numeric (0 or 1)")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def find_sheet_by_columns(file_path: Path, required_columns: set, data_type: str = "data") -> Optional[str]:
        try:
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)
                    if required_columns.issubset(set(df.columns)) and data_type in df.columns:
                        return sheet_name
                except (ValueError, KeyError, pd.errors.EmptyDataError):
                    continue
            return None
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except pd.errors.EmptyDataError:
            raise ValueError(f"File is empty: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied: {file_path}")
        except Exception as e:
            raise RuntimeError(f"An error occurred: {e}")

    @staticmethod
    def find_sales_sheet(file_path: Path) -> Optional[str]:
        return DataValidator.find_sheet_by_columns(file_path, DataValidator.SALES_COLUMNS, "data")

    @staticmethod
    def find_stock_sheet(file_path: Path) -> Optional[str]:
        return DataValidator.find_sheet_by_columns(file_path, DataValidator.STOCK_COLUMNS, "stock")

    @staticmethod
    def get_data_summary(df: pd.DataFrame, data_type: str = "sales") -> dict:

        summary = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist()
        }

        if data_type == "sales":
            if 'sku' in df.columns:
                summary['unique_skus'] = df['sku'].nunique()
            if 'order_id' in df.columns:
                summary['unique_orders'] = df['order_id'].nunique()
            if 'data' in df.columns and len(df) > 0:
                min_date = df['data'].min().str
                max_date = df['data'].max()
                summary['date_range'] = f"{min_date} to {max_date}"

        elif data_type == "stock":
            if 'sku' in df.columns:
                summary['unique_skus'] = df['sku'].nunique()
            if 'aktywny' in df.columns:
                summary['active_skus'] = (df['aktywny'] == 1).sum()
                summary['inactive_skus'] = (df['aktywny'] == 0).sum()

        return summary
