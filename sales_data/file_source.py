from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logging_config import get_logger

from .analyzer import SalesAnalyzer
from .data_source import DataSource
from .loader import SalesDataLoader, load_size_aliases_from_excel

logger = get_logger("file_source")


class FileSource(DataSource):

    def __init__(self, paths_file: str | None = None) -> None:
        self.loader = SalesDataLoader(paths_file)
        self._sales_data: pd.DataFrame | None = None
        self._analyzer: SalesAnalyzer | None = None

    def load_sales_data(
            self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> pd.DataFrame:

        if self._sales_data is None:
            self._sales_data = self.loader.consolidate_all_files()

        df = self._sales_data.copy()

        if start_date is not None:
            df = df[df["data"] >= start_date]
        if end_date is not None:
            df = df[df["data"] <= end_date]

        return df

    def load_stock_data(self, snapshot_date: datetime | None = None) -> pd.DataFrame:
        stock_file = self.loader.get_latest_stock_file()
        if stock_file is None:
            return pd.DataFrame()

        return self.loader.load_stock_file(stock_file)

    def load_stock_history(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> pd.DataFrame:
        stock_files = self.loader.find_stock_files()
        if not stock_files:
            return pd.DataFrame()

        filtered_files = [
            (path, date) for path, date in stock_files
            if (start_date is None or date >= start_date)
            and (end_date is None or date <= end_date)
        ]

        if not filtered_files:
            return pd.DataFrame()

        all_stock_dfs = []
        for file_path, snapshot_date in filtered_files:
            try:
                df = self.loader.load_stock_file(file_path)
                df["snapshot_date"] = snapshot_date
                all_stock_dfs.append(df)
            except Exception as e:
                logger.warning("Failed to load stock file %s: %s", file_path, e)

        if not all_stock_dfs:
            return pd.DataFrame()

        return pd.concat(all_stock_dfs, ignore_index=True)

    def load_forecast_data(self, generated_date: datetime | None = None) -> pd.DataFrame:
        if generated_date is not None:
            return self._load_forecast_by_generated_date(generated_date)

        forecast_result = self.loader.get_latest_forecast_file()
        if forecast_result is None:
            return pd.DataFrame()

        forecast_file, _ = forecast_result
        return self.loader.load_forecast_file(forecast_file)

    def _load_forecast_by_generated_date(
        self, target_date: datetime, tolerance_days: int = 7
    ) -> pd.DataFrame:
        forecast_files = self.loader.find_forecast_files()
        if not forecast_files:
            return pd.DataFrame()

        matching_files = [
            (path, date) for path, date in forecast_files
            if abs((date - target_date).days) <= tolerance_days
        ]

        if not matching_files:
            logger.warning(
                "No forecast found within %d days of %s", tolerance_days, target_date
            )
            return pd.DataFrame()

        closest_file = min(matching_files, key=lambda x: abs((x[1] - target_date).days))
        logger.info("Loading forecast from %s (target: %s)", closest_file[1], target_date)

        df = self.loader.load_forecast_file(closest_file[0])
        df["generated_date"] = closest_file[1]
        return df

    def get_sku_statistics(
            self, entity_type: str = "sku", force_recompute: bool = False
    ) -> pd.DataFrame:

        if self._analyzer is None or force_recompute:
            sales_data = self.load_sales_data()
            self._analyzer = SalesAnalyzer(sales_data)

        if entity_type == "model":
            return self._analyzer.aggregate_by_model()
        else:
            return self._analyzer.aggregate_by_sku()

    def get_order_priorities(
            self, top_n: int | None = None, force_recompute: bool = False
    ) -> pd.DataFrame:

        summary = self.get_sku_statistics(entity_type="sku", force_recompute=force_recompute)
        forecast_df = self.load_forecast_data()

        if forecast_df.empty:
            return pd.DataFrame()

        from utils.settings_manager import load_settings

        settings = load_settings()

        forecast_time = settings.get("forecast_time", 5)

        assert self._analyzer is not None
        priority_df = self._analyzer.calculate_order_priority(
            summary, forecast_df, forecast_time, settings
        )

        if top_n is not None:
            priority_df = priority_df.head(top_n)

        return priority_df

    def get_monthly_aggregations(
            self, entity_type: str = "sku", force_recompute: bool = False
    ) -> pd.DataFrame:

        if self._analyzer is None or force_recompute:
            sales_data = self.load_sales_data()
            self._analyzer = SalesAnalyzer(sales_data)

        monthly_data = self._analyzer.data.copy()
        monthly_data["year_month"] = monthly_data["data"].dt.to_period("M")

        if entity_type == "model":
            group_col = "model"
        else:
            group_col = "sku"

        monthly_agg = (
            monthly_data.groupby([group_col, "year_month"], as_index=False)
            .agg({"ilosc": "sum", "razem": "sum", "order_id": "nunique"})
            .rename(
                columns={
                    group_col: "entity_id",
                    "ilosc": "total_quantity",
                    "razem": "total_revenue",
                    "order_id": "unique_orders",
                }
            )
        )

        monthly_agg["entity_type"] = entity_type
        monthly_agg["year_month"] = monthly_agg["year_month"].astype(str)

        return monthly_agg

    def load_model_metadata(self) -> pd.DataFrame | None:
        return self.loader.load_model_metadata()

    def load_size_aliases(self) -> dict[str, str]:
        try:
            sizes_file = Path(__file__).parent.parent / "data" / "sizes.xlsx"
            if sizes_file.exists():
                return load_size_aliases_from_excel(sizes_file)
            logger.warning("Size aliases file not found: %s", sizes_file)
            return {}
        except Exception as e:
            logger.error("Failed to load size aliases from file: %s", e)
            return {}

    def load_color_aliases(self) -> dict[str, str]:
        return self.loader.load_color_aliases()

    def load_category_mappings(self) -> pd.DataFrame:
        return self.loader.load_category_data()

    def is_available(self) -> bool:
        return True

    def get_data_source_type(self) -> str:
        return "file"
