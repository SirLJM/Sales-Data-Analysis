from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd


class DataSource(ABC):

    @abstractmethod
    def load_sales_data(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def load_stock_data(self, snapshot_date: datetime | None = None) -> pd.DataFrame:
        pass

    @abstractmethod
    def load_stock_history(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def load_forecast_data(self, generated_date: datetime | None = None) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_sku_statistics(
        self, entity_type: str = "sku", force_recompute: bool = False
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_order_priorities(
        self, top_n: int | None = None, force_recompute: bool = False
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_monthly_aggregations(
        self, entity_type: str = "sku", force_recompute: bool = False
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def load_model_metadata(self) -> pd.DataFrame | None:
        pass

    @abstractmethod
    def load_size_aliases(self) -> dict[str, str]:
        pass

    @abstractmethod
    def load_color_aliases(self) -> dict[str, str]:
        pass

    @abstractmethod
    def load_category_mappings(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def get_data_source_type(self) -> str:
        pass

    @abstractmethod
    def load_outlet_models(self) -> set[str]:
        pass
