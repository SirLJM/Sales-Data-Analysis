from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from nlq.intent import QueryIntent

MSG_NO_DATA_MATCH = "No data matches the query criteria."
MSG_QUERY_NOT_UNDERSTOOD = "Could not understand the query. Please try rephrasing."
MSG_SALES_NOT_LOADED = "Sales data not loaded."
MSG_STOCK_NOT_LOADED = "Stock data not loaded."
MSG_FORECAST_NOT_LOADED = "Forecast data not loaded."

COL_MODEL = "model"
COL_SKU = "sku"
COL_COLOR = "color"
COL_SIZE = "size"
COL_DATA = "data"
COL_ILOSC = "ilosc"
COL_RAZEM = "razem"
COL_AVAILABLE_STOCK = "available_stock"
COL_STOCK = "stock"
COL_FORECAST = "forecast"
COL_FORECAST_QUANTITY = "forecast_quantity"
COL_FORECAST_DATE = "forecast_date"
COL_ROP = "ROP"
COL_SS = "SS"
COL_TYPE = "type"
COL_FACILITY = "SZWALNIA GŁÓWNA"


class QueryExecutor:
    def __init__(
        self,
        sales_df: pd.DataFrame | None = None,
        stock_df: pd.DataFrame | None = None,
        forecast_df: pd.DataFrame | None = None,
        sku_summary_df: pd.DataFrame | None = None,
    ):
        self.sales_df = sales_df
        self.stock_df = stock_df
        self.forecast_df = forecast_df
        self.sku_summary_df = sku_summary_df

    def execute(self, intent: QueryIntent) -> tuple[pd.DataFrame | None, str]:
        if not intent.is_valid():
            return None, MSG_QUERY_NOT_UNDERSTOOD

        entity_type = intent.entity_type
        if entity_type == "sales":
            return self._execute_sales(intent)
        if entity_type == "stock":
            return self._execute_stock(intent)
        if entity_type == "forecast":
            return self._execute_forecast(intent)
        return None, f"Unknown entity type: {entity_type}"

    def _execute_sales(self, intent: QueryIntent) -> tuple[pd.DataFrame | None, str]:
        if self.sales_df is None or self.sales_df.empty:
            return None, MSG_SALES_NOT_LOADED

        df = self.sales_df.copy()
        df = _ensure_model_column(df)
        df = _apply_identifier_filters(df, intent.identifiers)
        df = _apply_time_filter(df, intent, date_col=COL_DATA)
        df = self._apply_sales_filters(df, intent.filters)

        if df.empty:
            return None, MSG_NO_DATA_MATCH

        df = self._apply_aggregation(df, intent, entity_type="sales")
        df = _apply_limit(df, intent)
        return df, ""

    def _execute_stock(self, intent: QueryIntent) -> tuple[pd.DataFrame | None, str]:
        if self.stock_df is None or self.stock_df.empty:
            return None, MSG_STOCK_NOT_LOADED

        df = self.stock_df.copy()
        df = _ensure_model_column(df)
        df = _apply_identifier_filters(df, intent.identifiers)
        df = self._apply_stock_filters(df, intent.filters)

        if df.empty:
            return None, MSG_NO_DATA_MATCH

        df = self._apply_aggregation(df, intent, entity_type="stock")
        df = _apply_limit(df, intent)
        return df, ""

    def _execute_forecast(self, intent: QueryIntent) -> tuple[pd.DataFrame | None, str]:
        if self.forecast_df is None or self.forecast_df.empty:
            return None, MSG_FORECAST_NOT_LOADED

        df = self.forecast_df.copy()
        df = _ensure_model_column(df)
        df = _apply_identifier_filters(df, intent.identifiers)

        date_col = COL_DATA if COL_DATA in df.columns else COL_FORECAST_DATE
        df = _apply_time_filter(df, intent, date_col=date_col)

        if df.empty:
            return None, MSG_NO_DATA_MATCH

        df = self._apply_aggregation(df, intent, entity_type="forecast")
        df = _apply_limit(df, intent)
        return df, ""

    def _apply_sales_filters(self, df: pd.DataFrame, filters: list) -> pd.DataFrame:
        for filt in filters:
            if not isinstance(filt, tuple) or len(filt) < 3:
                continue
            field, _, value = filt[0], filt[1], filt[2]
            if field == COL_TYPE and self.sku_summary_df is not None:
                skus_of_type = self._get_skus_by_type(value)
                if COL_SKU in df.columns:
                    df = pd.DataFrame(df[df[COL_SKU].isin(skus_of_type)])
        return df

    def _apply_stock_filters(self, df: pd.DataFrame, filters: list) -> pd.DataFrame:
        for filt in filters:
            if not isinstance(filt, tuple) or len(filt) < 3:
                continue
            field, op, value = filt[0], filt[1], filt[2]
            df = self._apply_single_stock_filter(df, field, op, value)
        return df

    def _apply_single_stock_filter(
        self, df: pd.DataFrame, field: str, op: str, value: object
    ) -> pd.DataFrame:
        if field == COL_STOCK and COL_AVAILABLE_STOCK in df.columns:
            numeric_value = float(value) if isinstance(value, (int, float, str)) else 0
            return _apply_numeric_filter(df, COL_AVAILABLE_STOCK, op, numeric_value)
        if field == "below_rop" and value and self.sku_summary_df is not None:
            return self._filter_below_rop(df)
        if field == "overstock" and value and self.sku_summary_df is not None:
            return self._filter_overstock(df)
        if field == COL_TYPE and self.sku_summary_df is not None:
            skus_of_type = self._get_skus_by_type(value)
            if COL_SKU in df.columns:
                return pd.DataFrame(df[df[COL_SKU].isin(skus_of_type)])
        if field == "facility":
            return _filter_by_facility(df, value)
        return df

    def _filter_below_rop(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.sku_summary_df is None or COL_ROP not in self.sku_summary_df.columns:
            return df
        summary = self.sku_summary_df[[COL_SKU, COL_ROP]].copy()
        if COL_SKU in df.columns:
            merged = df.merge(summary, on=COL_SKU, how="left")
            if COL_AVAILABLE_STOCK in merged.columns:
                return pd.DataFrame(merged[merged[COL_AVAILABLE_STOCK] < merged[COL_ROP]].drop(columns=[COL_ROP]))
        return df

    def _filter_overstock(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.sku_summary_df is None:
            return df
        summary = self.sku_summary_df.copy()
        if COL_SS not in summary.columns or COL_ROP not in summary.columns:
            return df
        summary["overstock_threshold"] = summary[COL_ROP] + summary[COL_SS]
        summary = summary[[COL_SKU, "overstock_threshold"]]
        if COL_SKU in df.columns:
            merged = df.merge(summary, on=COL_SKU, how="left")
            if COL_AVAILABLE_STOCK in merged.columns:
                return pd.DataFrame(merged[merged[COL_AVAILABLE_STOCK] > merged["overstock_threshold"]].drop(
                    columns=["overstock_threshold"]
                ))
        return df

    def _get_skus_by_type(self, product_type: object) -> list:
        if self.sku_summary_df is None or COL_TYPE not in self.sku_summary_df.columns:
            return []
        return self.sku_summary_df[
            self.sku_summary_df[COL_TYPE].str.lower() == str(product_type).lower()
        ][COL_SKU].tolist()

    @staticmethod
    def _apply_aggregation(
        df: pd.DataFrame, intent: QueryIntent, entity_type: str
    ) -> pd.DataFrame:
        if not intent.aggregation:
            return df
        agg = intent.aggregation
        metric = intent.metric or "quantity"
        if entity_type == "sales":
            return _aggregate_sales(df, agg, metric)
        if entity_type == "stock":
            return _aggregate_stock(df, agg)
        if entity_type == "forecast":
            return _aggregate_forecast(df, agg)
        return df


def _ensure_model_column(df: pd.DataFrame) -> pd.DataFrame:
    if COL_MODEL not in df.columns and COL_SKU in df.columns:
        df = df.copy()
        df[COL_MODEL] = df[COL_SKU].astype(str).str[:5]
    return df


def _apply_identifier_filters(df: pd.DataFrame, identifiers: dict) -> pd.DataFrame:
    if not identifiers:
        return df
    if COL_MODEL in identifiers and COL_MODEL in df.columns:
        df = pd.DataFrame(df[df[COL_MODEL].str.upper() == identifiers[COL_MODEL].upper()])
    if COL_SKU in identifiers and COL_SKU in df.columns:
        df = pd.DataFrame(df[df[COL_SKU].str.upper() == identifiers[COL_SKU].upper()])
    if COL_COLOR in identifiers:
        df = _filter_by_color(df, identifiers[COL_COLOR])
    return df


def _filter_by_color(df: pd.DataFrame, color: str) -> pd.DataFrame:
    if COL_COLOR in df.columns:
        return pd.DataFrame(df[df[COL_COLOR].str.upper() == color.upper()])
    if COL_SKU in df.columns:
        return pd.DataFrame(df[df[COL_SKU].str[5:7].str.upper() == color.upper()])
    return df


def _apply_time_filter(
    df: pd.DataFrame, intent: QueryIntent, date_col: str = COL_DATA
) -> pd.DataFrame:
    if date_col not in df.columns or not intent.time_range:
        return df
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    time_value = intent.time_range[0] if isinstance(intent.time_range[0], tuple) else intent.time_range
    if intent.time_unit:
        return _apply_relative_time_filter(df, date_col, time_value, intent.time_unit)
    if isinstance(time_value, tuple) and len(time_value) == 2:
        start_year, end_year = time_value
        year_col = df[date_col].dt.year
        mask = (year_col >= start_year) & (year_col <= end_year)
        return df.loc[mask]  # type: ignore[return-value]
    return df


def _apply_relative_time_filter(
    df: pd.DataFrame, date_col: str, time_value: tuple | int, time_unit: str
) -> pd.DataFrame:
    num: int = time_value[0] if isinstance(time_value, tuple) else time_value
    end_date = datetime.now()
    start_date = _calculate_start_date(num, time_unit)
    return pd.DataFrame(df[(df[date_col] >= start_date) & (df[date_col] <= end_date)])


def _calculate_start_date(num: int, unit: str) -> datetime:
    now = datetime.now()
    if unit == "years":
        return now - timedelta(days=num * 365)
    if unit == "months":
        return now - timedelta(days=num * 30)
    if unit == "weeks":
        return now - timedelta(weeks=num)
    if unit == "days":
        return now - timedelta(days=num)
    return now


def _apply_numeric_filter(
    df: pd.DataFrame, column: str, op: str, value: float | int
) -> pd.DataFrame:
    if column not in df.columns:
        return df
    col = df[column]
    ops = {">": col > value, "<": col < value, ">=": col >= value,
           "<=": col <= value, "=": col == value}
    if op in ops:
        return pd.DataFrame(df[ops[op]])
    return df


def _filter_by_facility(df: pd.DataFrame, facility: object) -> pd.DataFrame:
    if COL_FACILITY in df.columns:
        return pd.DataFrame(df[df[COL_FACILITY].str.contains(str(facility), case=False, na=False)])
    return df


def _aggregate_sales(df: pd.DataFrame, agg: str, metric: str) -> pd.DataFrame:
    if COL_DATA not in df.columns:
        return df
    df = df.copy()
    value_col = COL_ILOSC if metric == "quantity" else COL_RAZEM
    if value_col not in df.columns:
        value_col = COL_ILOSC if COL_ILOSC in df.columns else str(df.columns[-1])
    if agg == "month":
        return _aggregate_by_period(df, COL_DATA, str(value_col), "M", "period", "total")
    if agg == "year":
        return _aggregate_by_year(df, COL_DATA, str(value_col))
    if agg == COL_MODEL:
        return _aggregate_by_column(df, COL_MODEL, str(value_col), "total")
    if agg == COL_COLOR:
        return _aggregate_sales_by_color(df, str(value_col))
    if agg == COL_SIZE:
        return _aggregate_sales_by_size(df, str(value_col))
    return df


def _aggregate_by_period(
    df: pd.DataFrame, date_col: str, value_col: str, freq: str, period_name: str, total_name: str
) -> pd.DataFrame:
    df[period_name] = df[date_col].dt.to_period(freq)  # type: ignore[union-attr]
    grouped = pd.DataFrame(df.groupby(period_name)[value_col].sum().reset_index())
    grouped.columns = pd.Index([period_name, total_name])
    return grouped


def _aggregate_by_year(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    df["year"] = df[date_col].dt.year  # type: ignore[union-attr]
    grouped = pd.DataFrame(df.groupby("year")[value_col].sum().reset_index())
    grouped.columns = pd.Index(["year", "total"])
    return grouped


def _aggregate_by_column(
    df: pd.DataFrame, group_col: str, value_col: str, total_name: str
) -> pd.DataFrame:
    grouped = pd.DataFrame(df.groupby(group_col)[value_col].sum().reset_index())
    grouped.columns = pd.Index([group_col, total_name])
    return pd.DataFrame(grouped.sort_values(total_name, ascending=False))


def _aggregate_sales_by_color(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    if COL_COLOR not in df.columns and COL_SKU in df.columns:
        df[COL_COLOR] = df[COL_SKU].str[5:7]
    if COL_COLOR in df.columns:
        return _aggregate_by_column(df, COL_COLOR, value_col, "total")
    return df


def _aggregate_sales_by_size(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    if COL_SIZE not in df.columns and COL_SKU in df.columns:
        df[COL_SIZE] = df[COL_SKU].str[7:9]
    if COL_SIZE in df.columns:
        return _aggregate_by_column(df, COL_SIZE, value_col, "total")
    return df


def _aggregate_stock(df: pd.DataFrame, agg: str) -> pd.DataFrame:
    stock_col = COL_AVAILABLE_STOCK if COL_AVAILABLE_STOCK in df.columns else COL_STOCK
    if stock_col not in df.columns:
        return df
    if agg == COL_MODEL:
        grouped = pd.DataFrame(df.groupby(COL_MODEL)[stock_col].sum().reset_index())
        grouped.columns = pd.Index([COL_MODEL, "total_stock"])
        return pd.DataFrame(grouped.sort_values("total_stock", ascending=False))
    if agg == COL_COLOR:
        if COL_COLOR not in df.columns and COL_SKU in df.columns:
            df = df.copy()
            df[COL_COLOR] = df[COL_SKU].str[5:7]
        if COL_COLOR in df.columns:
            grouped = pd.DataFrame(df.groupby(COL_COLOR)[stock_col].sum().reset_index())
            grouped.columns = pd.Index([COL_COLOR, "total_stock"])
            return pd.DataFrame(grouped.sort_values("total_stock", ascending=False))
    return df


def _aggregate_forecast(df: pd.DataFrame, agg: str) -> pd.DataFrame:
    forecast_col = COL_FORECAST if COL_FORECAST in df.columns else COL_FORECAST_QUANTITY
    if forecast_col not in df.columns:
        return df
    date_col = COL_DATA if COL_DATA in df.columns else COL_FORECAST_DATE
    if agg == "month" and date_col in df.columns:
        df = df.copy()
        df["period"] = pd.to_datetime(df[date_col]).dt.to_period("M")  # type: ignore[union-attr]
        grouped = pd.DataFrame(df.groupby("period")[forecast_col].sum().reset_index())
        grouped.columns = pd.Index(["period", "total_forecast"])
        return grouped
    if agg == COL_MODEL:
        grouped = pd.DataFrame(df.groupby(COL_MODEL)[forecast_col].sum().reset_index())
        grouped.columns = pd.Index([COL_MODEL, "total_forecast"])
        return pd.DataFrame(grouped.sort_values("total_forecast", ascending=False))
    return df


def _apply_limit(df: pd.DataFrame, intent: QueryIntent) -> pd.DataFrame:
    if intent.limit and len(df) > intent.limit:
        return df.head(intent.limit)
    return df
