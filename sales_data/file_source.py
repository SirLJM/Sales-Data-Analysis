from datetime import datetime

import pandas as pd

from .analyzer import SalesAnalyzer
from .data_source import DataSource
from .loader import SalesDataLoader


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

    def load_forecast_data(self, generated_date: datetime | None = None) -> pd.DataFrame:
        forecast_result = self.loader.get_latest_forecast_file()
        if forecast_result is None:
            return pd.DataFrame()

        forecast_file, _ = forecast_result
        return self.loader.load_forecast_file(forecast_file)

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

        forecast_date = (
            forecast_df["data"].max() if "data" in forecast_df.columns else datetime.now()
        )
        lead_time = settings.get("forecast_time", 1.36)

        assert self._analyzer is not None
        priority_df = self._analyzer.calculate_order_priority(
            summary, forecast_df, forecast_date, lead_time, settings
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

    def is_available(self) -> bool:
        return True

    def get_data_source_type(self) -> str:
        return "file"
