from __future__ import annotations

from datetime import datetime

import pandas as pd

from sales_data.analysis import (
    aggregate_by_model,
    aggregate_by_sku,
    aggregate_forecast_yearly,
    aggregate_order_by_model_color,
    aggregate_yearly_sales,
    calculate_forecast_date_range,
    calculate_forecast_metrics,
    calculate_last_two_years_avg_sales,
    calculate_model_stock_projection,
    calculate_monthly_yoy_by_category,
    calculate_order_priority,
    calculate_safety_stock_and_rop,
    calculate_size_priorities,
    calculate_size_sales_history,
    calculate_stock_projection,
    calculate_top_products_by_type,
    calculate_top_sales_report,
    classify_sku_type,
    determine_seasonal_months,
    find_urgent_colors,
    generate_order_recommendations,
    generate_weekly_new_products_analysis,
    get_last_n_months_sales_by_color,
    get_size_quantities_for_model_color,
    get_size_sales_by_month_for_model,
    optimize_pattern_with_aliases,
    parse_sku_components,
)

LEAD_TIME = 1.36


class SalesAnalyzer:
    def __init__(self, data: pd.DataFrame, copy: bool = True) -> None:
        self.data = data.copy() if copy else data
        if not pd.api.types.is_datetime64_any_dtype(self.data["data"]):
            self.data["data"] = pd.to_datetime(self.data["data"])

        if "model" not in self.data.columns:
            self.data["model"] = self.data["sku"].astype(str).str[:5]

    def aggregate_by_sku(self) -> pd.DataFrame:
        return aggregate_by_sku(self.data)

    def aggregate_by_model(self) -> pd.DataFrame:
        return aggregate_by_model(self.data)

    def calculate_last_two_years_avg_sales(self, by_model: bool = False) -> pd.DataFrame:
        return calculate_last_two_years_avg_sales(self.data, by_model)

    @staticmethod
    def classify_sku_type(
            sku_summary: pd.DataFrame, cv_basic: float, cv_seasonal: float
    ) -> pd.DataFrame:
        return classify_sku_type(sku_summary, cv_basic, cv_seasonal)

    def determine_seasonal_months(self) -> pd.DataFrame:
        return determine_seasonal_months(self.data)

    @staticmethod
    def calculate_safety_stock_and_rop(
            sku_summary: pd.DataFrame,
            seasonal_data: pd.DataFrame,
            z_basic: float,
            z_regular: float,
            z_seasonal_in: float,
            z_seasonal_out: float,
            z_new: float,
            lead_time_months: float = 1.36,
    ) -> pd.DataFrame:
        return calculate_safety_stock_and_rop(
            sku_summary, seasonal_data, z_basic, z_regular,
            z_seasonal_in, z_seasonal_out, z_new, lead_time_months
        )

    @staticmethod
    def calculate_forecast_date_range(forecast_time_months: float) -> tuple[pd.Timestamp, pd.Timestamp]:
        return calculate_forecast_date_range(forecast_time_months)

    @staticmethod
    def calculate_forecast_metrics(
            forecast_df: pd.DataFrame, forecast_time_months: float = None
    ) -> pd.DataFrame:
        return calculate_forecast_metrics(forecast_df, forecast_time_months)

    @staticmethod
    def calculate_stock_projection(
            sku: str,
            current_stock: float,
            rop: float,
            safety_stock: float,
            forecast_df: pd.DataFrame,
            start_date: datetime,
            projection_months: int = 12,
    ) -> pd.DataFrame:
        return calculate_stock_projection(
            sku, current_stock, rop, safety_stock, forecast_df, start_date, projection_months
        )

    @staticmethod
    def calculate_model_stock_projection(
            model: str,
            current_stock: float,
            rop: float,
            safety_stock: float,
            forecast_df: pd.DataFrame,
            start_date: datetime,
            projection_months: int = 12,
    ) -> pd.DataFrame:
        return calculate_model_stock_projection(
            model, current_stock, rop, safety_stock, forecast_df, start_date, projection_months
        )

    @staticmethod
    def parse_sku_components(sku: str) -> dict:
        return parse_sku_components(sku)

    @staticmethod
    def calculate_order_priority(
            summary_df: pd.DataFrame,
            forecast_df: pd.DataFrame,
            forecast_time_months: float = 5,
            settings: dict | None = None,
    ) -> pd.DataFrame:
        return calculate_order_priority(summary_df, forecast_df, forecast_time_months, settings)

    @staticmethod
    def aggregate_order_by_model_color(priority_df: pd.DataFrame) -> pd.DataFrame:
        return aggregate_order_by_model_color(priority_df)

    @staticmethod
    def get_size_quantities_for_model_color(
            priority_df: pd.DataFrame, model: str, color: str
    ) -> dict:
        return get_size_quantities_for_model_color(priority_df, model, color)

    @staticmethod
    def generate_order_recommendations(
            summary_df: pd.DataFrame,
            forecast_df: pd.DataFrame,
            forecast_time_months: float = 5,
            top_n: int = 10,
            settings: dict | None = None,
    ) -> dict:
        return generate_order_recommendations(
            summary_df, forecast_df, forecast_time_months, top_n, settings
        )

    @staticmethod
    def generate_weekly_new_products_analysis(
            sales_df: pd.DataFrame,
            stock_df: pd.DataFrame | None = None,
            lookback_days: int = 60,
            reference_date: datetime | None = None,
    ) -> pd.DataFrame:
        return generate_weekly_new_products_analysis(
            sales_df, stock_df, lookback_days, reference_date
        )

    @staticmethod
    def calculate_top_sales_report(
            sales_df: pd.DataFrame, reference_date: datetime | None = None
    ) -> dict:
        return calculate_top_sales_report(sales_df, reference_date)

    @staticmethod
    def calculate_top_products_by_type(
            sales_df: pd.DataFrame,
            cv_basic: float = 0.6,
            cv_seasonal: float = 1.0,
            reference_date: datetime | None = None,
    ) -> dict:
        return calculate_top_products_by_type(sales_df, cv_basic, cv_seasonal, reference_date)

    @staticmethod
    def find_urgent_colors(model_color_summary: pd.DataFrame, model: str) -> list[str]:
        return find_urgent_colors(model_color_summary, model)

    @staticmethod
    def get_last_n_months_sales_by_color(
            monthly_agg: pd.DataFrame,
            model: str,
            colors: list[str],
            months: int = 4
    ) -> pd.DataFrame:
        return get_last_n_months_sales_by_color(monthly_agg, model, colors, months)

    @staticmethod
    def calculate_size_priorities(
            sales_df: pd.DataFrame,
            model: str | None = None,
            size_aliases: dict[str, str] | None = None
    ) -> dict[str, float]:
        return calculate_size_priorities(sales_df, model, size_aliases)

    @staticmethod
    def calculate_size_sales_history(
            monthly_agg: pd.DataFrame,
            model: str,
            color: str,
            size_aliases: dict[str, str] | None = None,
            months: int = 4,
    ) -> dict[str, int]:
        return calculate_size_sales_history(monthly_agg, model, color, size_aliases, months)

    @staticmethod
    def get_size_sales_by_month_for_model(
            monthly_agg: pd.DataFrame,
            model: str,
            size_aliases: dict[str, str] | None = None,
            months: int = 3,
    ) -> dict[str, dict[str, int]]:
        return get_size_sales_by_month_for_model(monthly_agg, model, size_aliases, months)

    @staticmethod
    def optimize_pattern_with_aliases(
            priority_skus: pd.DataFrame,
            model: str,
            color: str,
            pattern_set,
            size_aliases: dict[str, str],
            min_per_pattern: int,
            algorithm_mode: str = "greedy_overshoot",
            size_sales_history: dict[str, int] | None = None,
    ) -> dict:
        return optimize_pattern_with_aliases(
            priority_skus, model, color, pattern_set, size_aliases, min_per_pattern, algorithm_mode, size_sales_history
        )

    @staticmethod
    def calculate_monthly_yoy_by_category(
            sales_df: pd.DataFrame,
            category_df: pd.DataFrame,
            reference_date: datetime = None
    ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        return calculate_monthly_yoy_by_category(sales_df, category_df, reference_date)

    def aggregate_yearly_sales(self, include_color: bool = False) -> pd.DataFrame:
        return aggregate_yearly_sales(self.data, _by_model=True, include_color=include_color)

    @staticmethod
    def aggregate_forecast_yearly(forecast_df: pd.DataFrame, include_color: bool = False) -> pd.DataFrame:
        return aggregate_forecast_yearly(forecast_df, include_color)
