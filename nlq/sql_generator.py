from __future__ import annotations

from datetime import datetime, timedelta

from nlq.intent import QueryIntent

TABLE_SALES = "sales"
TABLE_STOCK = "stock"
TABLE_FORECAST = "forecast"

ENTITY_TO_TABLE = {
    "sales": TABLE_SALES,
    "stock": TABLE_STOCK,
    "forecast": TABLE_FORECAST,
}

COL_MAP_SALES = {
    "date": "data",
    "quantity": "ilosc",
    "value": "razem",
    "sku": "sku",
    "model": "model",
}

COL_MAP_STOCK = {
    "sku": "sku",
    "model": "model",
    "stock": "available_stock",
    "name": "nazwa",
}

COL_MAP_FORECAST = {
    "date": "data",
    "sku": "sku",
    "model": "model",
    "forecast": "forecast",
}


class SQLGenerator:
    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def generate(self, intent: QueryIntent) -> str | None:
        if not intent.is_valid():
            return None

        entity_type = intent.entity_type
        if entity_type == "sales":
            return self._generate_sales_sql(intent)
        if entity_type == "stock":
            return self._generate_stock_sql(intent)
        if entity_type == "forecast":
            return self._generate_forecast_sql(intent)
        return None

    def _generate_sales_sql(self, intent: QueryIntent) -> str:
        select_clause = self._build_select_clause(intent, "sales")
        from_clause = f"FROM {TABLE_SALES}"
        where_clauses = self._build_where_clauses(intent)
        group_clause = self._build_group_clause(intent)
        order_clause = self._build_order_clause(intent, "sales")
        limit_clause = self._build_limit_clause(intent)

        sql = f"SELECT {select_clause}\n{from_clause}"
        if where_clauses:
            sql += f"\nWHERE {where_clauses}"
        if group_clause:
            sql += f"\n{group_clause}"
        if order_clause:
            sql += f"\n{order_clause}"
        if limit_clause:
            sql += f"\n{limit_clause}"

        return sql

    def _generate_stock_sql(self, intent: QueryIntent) -> str:
        select_clause = self._build_select_clause(intent, "stock")
        from_clause = f"FROM {TABLE_STOCK}"
        where_clauses = self._build_where_clauses(intent)
        group_clause = self._build_group_clause(intent)
        order_clause = self._build_order_clause(intent, "stock")
        limit_clause = self._build_limit_clause(intent)

        sql = f"SELECT {select_clause}\n{from_clause}"
        if where_clauses:
            sql += f"\nWHERE {where_clauses}"
        if group_clause:
            sql += f"\n{group_clause}"
        if order_clause:
            sql += f"\n{order_clause}"
        if limit_clause:
            sql += f"\n{limit_clause}"

        return sql

    def _generate_forecast_sql(self, intent: QueryIntent) -> str:
        select_clause = self._build_select_clause(intent, "forecast")
        from_clause = f"FROM {TABLE_FORECAST}"
        where_clauses = self._build_where_clauses(intent)
        group_clause = self._build_group_clause(intent)
        order_clause = self._build_order_clause(intent, "forecast")
        limit_clause = self._build_limit_clause(intent)

        sql = f"SELECT {select_clause}\n{from_clause}"
        if where_clauses:
            sql += f"\nWHERE {where_clauses}"
        if group_clause:
            sql += f"\n{group_clause}"
        if order_clause:
            sql += f"\n{order_clause}"
        if limit_clause:
            sql += f"\n{limit_clause}"

        return sql

    def _build_select_clause(self, intent: QueryIntent, entity_type: str) -> str:
        agg = intent.aggregation
        metric = intent.metric or "quantity"

        if not agg:
            return "*"

        if entity_type == "sales":
            value_col = "ilosc" if metric == "quantity" else "razem"
            return self._select_for_aggregation(agg, value_col, "total")
        if entity_type == "stock":
            return self._select_for_aggregation(agg, "available_stock", "total_stock")
        if entity_type == "forecast":
            return self._select_for_aggregation(agg, "forecast", "total_forecast")

        return "*"

    def _select_for_aggregation(self, agg: str, value_col: str, alias: str) -> str:
        if agg == "month":
            if self.dialect == "duckdb":
                return f"DATE_TRUNC('month', data) AS period, SUM({value_col}) AS {alias}"
            return f"DATE_FORMAT(data, '%Y-%m') AS period, SUM({value_col}) AS {alias}"
        if agg == "year":
            if self.dialect == "duckdb":
                return f"EXTRACT(YEAR FROM data) AS year, SUM({value_col}) AS {alias}"
            return f"YEAR(data) AS year, SUM({value_col}) AS {alias}"
        if agg == "model":
            return f"model, SUM({value_col}) AS {alias}"
        if agg == "color":
            return f"SUBSTRING(sku, 6, 2) AS color, SUM({value_col}) AS {alias}"
        if agg == "size":
            return f"SUBSTRING(sku, 8, 2) AS size, SUM({value_col}) AS {alias}"
        return "*"

    def _build_where_clauses(self, intent: QueryIntent) -> str:
        conditions = []

        conditions.extend(self._build_identifier_conditions(intent.identifiers))
        conditions.extend(self._build_time_conditions(intent))
        conditions.extend(self._build_filter_conditions(intent.filters))

        return " AND ".join(conditions) if conditions else ""

    @staticmethod
    def _build_identifier_conditions(identifiers: dict) -> list[str]:
        conditions = []
        if "model" in identifiers:
            model = identifiers["model"].upper()
            conditions.append(f"UPPER(model) = '{model}'")
        if "sku" in identifiers:
            sku = identifiers["sku"].upper()
            conditions.append(f"UPPER(sku) = '{sku}'")
        if "color" in identifiers:
            color = identifiers["color"].upper()
            conditions.append(f"UPPER(SUBSTRING(sku, 6, 2)) = '{color}'")
        return conditions

    def _build_time_conditions(self, intent: QueryIntent) -> list[str]:
        if not intent.time_range:
            return []

        date_col = "data"
        time_value = intent.time_range[0] if isinstance(intent.time_range[0], tuple) else intent.time_range

        if intent.time_unit:
            num = time_value[0] if isinstance(time_value, tuple) else time_value
            start_date = self._calculate_start_date(num, intent.time_unit)
            return [f"{date_col} >= '{start_date.strftime('%Y-%m-%d')}'"]

        if isinstance(time_value, tuple) and len(time_value) == 2:
            start_year, end_year = time_value
            if self.dialect == "duckdb":
                return [f"EXTRACT(YEAR FROM {date_col}) BETWEEN {start_year} AND {end_year}"]
            return [f"YEAR({date_col}) BETWEEN {start_year} AND {end_year}"]

        return []

    @staticmethod
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

    def _build_filter_conditions(self, filters: list) -> list[str]:
        conditions = []
        for filt in filters:
            if not isinstance(filt, tuple) or len(filt) < 3:
                continue
            field, op, value = filt[0], filt[1], filt[2]
            condition = self._single_filter_to_condition(field, op, value)
            if condition:
                conditions.append(condition)
        return conditions

    def _single_filter_to_condition(self, field: str, op: str, value: object) -> str | None:
        if field == "stock":
            sql_op = self._convert_operator(op)
            return f"available_stock {sql_op} {value}"
        if field == "type":
            return f"LOWER(type) = '{str(value).lower()}'"
        if field == "below_rop" and value:
            return "available_stock < ROP"
        if field == "overstock" and value:
            return "available_stock > (ROP + SS)"
        return None

    @staticmethod
    def _convert_operator(op: str) -> str:
        return {"=": "=", ">": ">", "<": "<", ">=": ">=", "<=": "<="}.get(op, "=")

    def _build_group_clause(self, intent: QueryIntent) -> str:
        agg = intent.aggregation
        if not agg:
            return ""
        if agg == "month":
            if self.dialect == "duckdb":
                return "GROUP BY DATE_TRUNC('month', data)"
            return "GROUP BY DATE_FORMAT(data, '%Y-%m')"
        if agg == "year":
            if self.dialect == "duckdb":
                return "GROUP BY EXTRACT(YEAR FROM data)"
            return "GROUP BY YEAR(data)"
        if agg == "model":
            return "GROUP BY model"
        if agg == "color":
            return "GROUP BY SUBSTRING(sku, 6, 2)"
        if agg == "size":
            return "GROUP BY SUBSTRING(sku, 8, 2)"
        return ""

    @staticmethod
    def _build_order_clause(intent: QueryIntent, entity_type: str) -> str:
        agg = intent.aggregation
        if not agg:
            return ""
        if agg in ("month", "year"):
            col = "period" if agg == "month" else "year"
            return f"ORDER BY {col}"
        alias = {"sales": "total", "stock": "total_stock", "forecast": "total_forecast"}.get(entity_type, "total")
        return f"ORDER BY {alias} DESC"

    @staticmethod
    def _build_limit_clause(intent: QueryIntent) -> str:
        if intent.limit:
            return f"LIMIT {intent.limit}"
        return ""
