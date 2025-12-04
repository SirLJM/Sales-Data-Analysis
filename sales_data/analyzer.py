from datetime import datetime, timedelta

import numpy as np
import pandas as pd

lead_time = 1.36

AVERAGE_SALES = "AVERAGE SALES"


class SalesAnalyzer:
    def __init__(self, data: pd.DataFrame) -> None:
        self.data = data.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.data["data"]):
            self.data["data"] = pd.to_datetime(self.data["data"])

        self.data["model"] = self.data["sku"].astype(str).str[:5]

    @staticmethod
    def _get_week_start_monday(date: datetime) -> datetime:
        days_since_mon = date.weekday()
        week_start = date - timedelta(days=days_since_mon)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _get_last_week_range(reference_date: datetime) -> tuple[datetime, datetime]:
        if reference_date.weekday() >= 2:
            last_week_start = SalesAnalyzer._get_week_start_monday(reference_date)
        else:
            last_week_start = SalesAnalyzer._get_week_start_monday(
                reference_date - timedelta(days=7)
            )

        last_week_end = last_week_start + timedelta(days=6)
        last_week_end = last_week_end.replace(hour=23, minute=59, second=59, microsecond=999999)

        return last_week_start, last_week_end

    def aggregate_by_sku(self) -> pd.DataFrame:
        self.data["year_month"] = self.data["data"].dt.to_period("M")

        first_sale = self.data.groupby("sku")["data"].min().reset_index()
        first_sale.columns = ["SKU", "first_sale"]

        monthly_sales = self.data.groupby(["sku", "year_month"], as_index=False)["ilosc"].sum()

        sku_summary = monthly_sales.groupby("sku", as_index=False).agg(
            {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}  # type: ignore[arg-type]
        )

        sku_summary.columns = ["SKU", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD"]

        sku_summary["CV"] = sku_summary["SD"] / sku_summary[AVERAGE_SALES]
        sku_summary["CV"] = sku_summary["CV"].fillna(0)

        sku_summary = pd.merge(sku_summary, first_sale, on="SKU", how="left")

        return sku_summary.sort_values("SKU", ascending=False)

    def aggregate_by_model(self) -> pd.DataFrame:
        self.data["year_month"] = self.data["data"].dt.to_period("M")

        first_sale = self.data.groupby("model")["data"].min().reset_index()
        first_sale.columns = ["MODEL", "first_sale"]

        monthly_sales = self.data.groupby(["model", "year_month"], as_index=False)["ilosc"].sum()

        model_summary = monthly_sales.groupby("model", as_index=False).agg(
            {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}  # type: ignore[arg-type]
        )

        model_summary.columns = ["MODEL", "MONTHS", "QUANTITY", AVERAGE_SALES, "SD"]

        model_summary["CV"] = model_summary["SD"] / model_summary[AVERAGE_SALES]
        model_summary["CV"] = model_summary["CV"].fillna(0)

        model_summary = pd.merge(model_summary, first_sale, on="MODEL", how="left")

        return model_summary.sort_values("MODEL", ascending=False)

    def calculate_last_two_years_avg_sales(self, by_model: bool = False) -> pd.DataFrame:
        df = self.data.copy()

        two_years_ago = datetime.today() - timedelta(days=730)
        df_last_2_years = df[df["data"] >= two_years_ago].copy()

        df_last_2_years["year_month"] = df_last_2_years["data"].dt.to_period("M")

        if by_model:
            monthly_sales = df_last_2_years.groupby(["model", "year_month"], as_index=False)[
                "ilosc"
            ].sum()
            # noinspection PyUnresolvedReferences
            avg_sales = monthly_sales.groupby("model", as_index=False)["ilosc"].mean()
            avg_sales.columns = ["MODEL", "LAST_2_YEARS_AVG"]
        else:
            monthly_sales = df_last_2_years.groupby(["sku", "year_month"], as_index=False)[
                "ilosc"
            ].sum()
            # noinspection PyUnresolvedReferences
            avg_sales = monthly_sales.groupby("sku", as_index=False)["ilosc"].mean()
            avg_sales.columns = ["SKU", "LAST_2_YEARS_AVG"]

        avg_sales["LAST_2_YEARS_AVG"] = avg_sales["LAST_2_YEARS_AVG"].round(2)

        return avg_sales

    @staticmethod
    def classify_sku_type(
            sku_summary: pd.DataFrame, cv_basic: float, cv_seasonal: float
    ) -> pd.DataFrame:
        df = sku_summary.copy()

        one_year_ago = datetime.today() - timedelta(days=365)

        df["TYPE"] = "regular"
        df.loc[df["first_sale"] > one_year_ago, "TYPE"] = "new"
        df.loc[(df["TYPE"] != "new") & (df["CV"] < cv_basic), "TYPE"] = "basic"
        df.loc[(df["TYPE"] != "new") & (df["CV"] > cv_seasonal), "TYPE"] = "seasonal"

        return df

    def determine_seasonal_months(self) -> pd.DataFrame:
        df = self.data.copy()

        two_years_ago = datetime.today() - timedelta(days=730)
        df = df[df["data"] >= two_years_ago]

        df["month"] = df["data"].dt.month
        df["year"] = df["data"].dt.year

        monthly_sales = df.groupby(["sku", "year", "month"], as_index=False)["ilosc"].sum()

        # noinspection PyUnresolvedReferences
        avg_monthly_sales = monthly_sales.groupby(["sku", "month"], as_index=False)["ilosc"].mean()
        avg_monthly_sales = avg_monthly_sales.rename(columns={"sku": "SKU", "ilosc": "avg_sales"})

        overall_avg = avg_monthly_sales.groupby("SKU", as_index=False)["avg_sales"].mean()
        overall_avg = overall_avg.rename(columns={"avg_sales": "overall_avg"})

        seasonal_data = avg_monthly_sales.merge(overall_avg, on="SKU")
        seasonal_data["seasonal_index"] = seasonal_data["avg_sales"] / seasonal_data["overall_avg"]
        seasonal_data["is_in_season"] = seasonal_data["seasonal_index"] > 1.2

        return seasonal_data[["SKU", "month", "avg_sales", "seasonal_index", "is_in_season"]]

    @staticmethod
    def calculate_safety_stock_and_rop(
            sku_summary: pd.DataFrame,
            seasonal_data: pd.DataFrame,
            z_basic: float,
            z_regular: float,
            z_seasonal_in: float,
            z_seasonal_out: float,
            z_new: float,
    ) -> pd.DataFrame:
        df = sku_summary.copy()

        id_column = "MODEL" if "MODEL" in df.columns else "SKU"

        z_score_map = {
            "basic": z_basic,
            "regular": z_regular,
            "seasonal": z_seasonal_in,  # default for seasonal, later overwritten
            "new": z_new,
        }
        df["z_score"] = df["TYPE"].map(z_score_map)

        current_month = datetime.today().month

        sqrt_lead_time = np.sqrt(lead_time)

        df["SS"] = df["z_score"] * df["SD"] * sqrt_lead_time
        df["ROP"] = df[AVERAGE_SALES] * lead_time + df["SS"]

        seasonal_mask = df["TYPE"] == "seasonal"
        if isinstance(seasonal_mask, pd.Series) and seasonal_mask.any():
            seasonal_items = df[seasonal_mask][id_column].tolist()
            seasonal_current = seasonal_data[
                (seasonal_data["SKU"].isin(seasonal_items))
                & (seasonal_data["month"] == current_month)
                ][["SKU", "is_in_season"]]

            df = df.merge(seasonal_current, left_on=id_column, right_on="SKU", how="left")
            if id_column == "MODEL":
                df = df.drop(columns=["SKU"], errors="ignore")

            df["SS_IN"] = np.where(seasonal_mask, z_seasonal_in * df["SD"] * sqrt_lead_time, np.nan)
            df["ROP_IN"] = np.where(
                seasonal_mask, df[AVERAGE_SALES] * lead_time + df["SS_IN"], np.nan
            )

            df["SS_OUT"] = np.where(
                seasonal_mask, z_seasonal_out * df["SD"] * sqrt_lead_time, np.nan
            )
            df["ROP_OUT"] = np.where(
                seasonal_mask, df[AVERAGE_SALES] * lead_time + df["SS_OUT"], np.nan
            )

            in_season_mask = df["is_in_season"]
            out_season_mask = df["is_in_season"] is False

            df.loc[seasonal_mask & in_season_mask, "SS"] = df["SS_IN"]
            df.loc[seasonal_mask & in_season_mask, "ROP"] = df["ROP_IN"]
            df.loc[seasonal_mask & out_season_mask, "SS"] = df["SS_OUT"]
            df.loc[seasonal_mask & out_season_mask, "ROP"] = df["ROP_OUT"]

            df = df.drop(columns=["is_in_season"], errors="ignore")

        df = df.drop(columns=["z_score"], errors="ignore")

        df["SS"] = df["SS"].round(2)
        df["ROP"] = df["ROP"].round(2)
        if "SS_IN" in df.columns:
            df["SS_IN"] = df["SS_IN"].round(2)
            df["SS_OUT"] = df["SS_OUT"].round(2)
            df["ROP_IN"] = df["ROP_IN"].round(2)
            df["ROP_OUT"] = df["ROP_OUT"].round(2)

        base_cols = ["MONTHS", "QUANTITY", AVERAGE_SALES, "SD", "CV", "TYPE", "SS", "ROP"]
        return df[[id_column] + base_cols]

    @staticmethod
    def calculate_forecast_metrics(
            forecast_df: pd.DataFrame, file_date: datetime, lead_time_months: float = None
    ) -> pd.DataFrame:

        if forecast_df.empty:
            columns = ["sku", "FORECAST_8W", "FORECAST_16W"]
            if lead_time_months is not None:
                columns.append("FORECAST_LEADTIME")
            return pd.DataFrame(columns=columns)

        forecast_df["data"] = pd.to_datetime(forecast_df["data"])

        if file_date is None:
            file_date = forecast_df["data"].min()

        weeks_8_end = file_date + pd.Timedelta(weeks=8)
        weeks_16_end = file_date + pd.Timedelta(weeks=16)

        forecast_8w = forecast_df[
            (forecast_df["data"] >= file_date) & (forecast_df["data"] < weeks_8_end)
            ]

        forecast_16w = forecast_df[
            (forecast_df["data"] >= file_date) & (forecast_df["data"] < weeks_16_end)
            ]

        forecast_8w_grouped = forecast_8w.groupby("sku", as_index=False)["forecast"]
        # noinspection PyUnresolvedReferences
        forecast_8w_sum = forecast_8w_grouped.sum().rename(columns={"forecast": "FORECAST_8W"})

        forecast_16w_grouped = forecast_16w.groupby("sku", as_index=False)["forecast"]
        # noinspection PyUnresolvedReferences
        forecast_16w_sum = forecast_16w_grouped.sum().rename(columns={"forecast": "FORECAST_16W"})

        result = forecast_8w_sum.merge(forecast_16w_sum, on="sku", how="outer")

        result["FORECAST_8W"] = result["FORECAST_8W"].fillna(0).round(2)
        result["FORECAST_16W"] = result["FORECAST_16W"].fillna(0).round(2)

        if lead_time_months is not None:
            lead_time_days = lead_time_months * 30.44
            leadtime_end = file_date + pd.Timedelta(days=lead_time_days)

            forecast_leadtime = forecast_df[
                (forecast_df["data"] >= file_date) & (forecast_df["data"] < leadtime_end)
                ]

            forecast_leadtime_grouped = forecast_leadtime.groupby("sku", as_index=False)["forecast"]
            # noinspection PyUnresolvedReferences
            forecast_leadtime_sum = forecast_leadtime_grouped.sum().rename(columns={"forecast": "FORECAST_LEADTIME"})

            result = result.merge(forecast_leadtime_sum, on="sku", how="outer")
            result["FORECAST_LEADTIME"] = result["FORECAST_LEADTIME"].fillna(0).round(2)

        return result

    @staticmethod
    def _build_projection_from_forecast(
            forecast_data: pd.DataFrame,
            current_stock: float,
            rop: float,
            safety_stock: float,
            start_date: datetime,
    ) -> pd.DataFrame:
        projection = [
            {
                "date": start_date,
                "projected_stock": current_stock,
                "rop_reached": current_stock <= rop,
                "zero_reached": current_stock <= 0,
            }
        ]

        running_stock = current_stock

        for _, row in forecast_data.iterrows():
            running_stock -= row["forecast"]

            projection.append(
                {
                    "date": row["data"],
                    "projected_stock": running_stock,
                    "rop_reached": running_stock <= rop,
                    "zero_reached": running_stock <= 0,
                }
            )

        projection_df = pd.DataFrame(projection)
        projection_df["date"] = pd.to_datetime(projection_df["date"])
        projection_df["rop"] = rop
        projection_df["safety_stock"] = safety_stock

        return projection_df

    @staticmethod
    def _filter_and_prepare_forecast(
            forecast_df: pd.DataFrame,
            start_date: datetime,
            projection_months: int
    ) -> pd.DataFrame:
        df = forecast_df.copy()
        df["data"] = pd.to_datetime(df["data"])
        end_date = start_date + pd.DateOffset(months=projection_months)

        mask = (df["data"] >= start_date) & (df["data"] <= end_date)
        filtered = df.loc[mask, :].copy()

        sorted_result = filtered.sort_values(by="data")
        return sorted_result

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
        if forecast_df.empty:
            return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

        sku_forecast = forecast_df[forecast_df["sku"] == sku].copy()

        if sku_forecast.empty:
            return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

        sku_forecast = SalesAnalyzer._filter_and_prepare_forecast(
            sku_forecast, start_date, projection_months
        )

        return SalesAnalyzer._build_projection_from_forecast(
            sku_forecast, current_stock, rop, safety_stock, start_date
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
        if forecast_df.empty:
            return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

        forecast_df = forecast_df.copy()
        forecast_df["model"] = forecast_df["sku"].astype(str).str[:5]

        model_forecast = forecast_df[forecast_df["model"] == model].copy()

        if model_forecast.empty:
            return pd.DataFrame(columns=["date", "projected_stock", "rop_reached", "zero_reached"])

        model_forecast = SalesAnalyzer._filter_and_prepare_forecast(
            model_forecast, start_date, projection_months
        )

        model_forecast_aggregated = model_forecast.groupby("data", as_index=False).agg({"forecast": "sum"})

        return SalesAnalyzer._build_projection_from_forecast(
            model_forecast_aggregated, current_stock, rop, safety_stock, start_date
        )

    @staticmethod
    def parse_sku_components(sku: str) -> dict:
        sku_str = str(sku)
        return {
            "model": sku_str[:5] if len(sku_str) >= 5 else sku_str,
            "color": sku_str[5:7] if len(sku_str) >= 7 else "",
            "size": sku_str[7:9] if len(sku_str) >= 9 else "",
        }

    @staticmethod
    def calculate_order_priority(
            summary_df: pd.DataFrame,
            forecast_df: pd.DataFrame,
            forecast_date: datetime,
            lead_time_months: float = 1.36,
            settings: dict | None = None,
    ) -> pd.DataFrame:
        if settings is None:
            from utils.settings_manager import load_settings
            settings = load_settings()

        config = SalesAnalyzer._extract_priority_config(settings)
        df = summary_df.copy()

        SalesAnalyzer._validate_required_columns(df)
        df = SalesAnalyzer._add_forecast_leadtime(df, forecast_df, forecast_date, lead_time_months)
        df = SalesAnalyzer._add_sku_components(df)
        df = SalesAnalyzer._calculate_stockout_risk(df, config)
        df = SalesAnalyzer._calculate_revenue_impact(df)
        df = SalesAnalyzer._apply_type_multipliers(df, config["type_multipliers"])
        df = SalesAnalyzer._calculate_priority_score(df, config)
        df["URGENT"] = (df["STOCK"] <= 0) | ((df["STOCK"] < df["ROP"]) & (df["FORECAST_LEADTIME"] > df["STOCK"]))

        return df.sort_values("PRIORITY_SCORE", ascending=False)

    @staticmethod
    def _extract_priority_config(settings: dict) -> dict:
        rec_settings = settings.get("order_recommendations", {})
        stockout_cfg = rec_settings.get("stockout_risk", {})
        weights = rec_settings.get("priority_weights", {})

        return {
            "zero_stock_penalty": stockout_cfg.get("zero_stock_penalty", 100),
            "below_rop_max": stockout_cfg.get("below_rop_max_penalty", 80),
            "weight_stockout": weights.get("stockout_risk", 0.5),
            "weight_revenue": weights.get("revenue_impact", 0.3),
            "weight_demand": weights.get("demand_forecast", 0.2),
            "type_multipliers": rec_settings.get("type_multipliers", {}),
            "demand_cap": rec_settings.get("demand_cap", 100),
        }

    @staticmethod
    def _validate_required_columns(df: pd.DataFrame) -> None:
        required_cols = ["SKU", "STOCK", "ROP", "TYPE"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

    @staticmethod
    def _add_forecast_leadtime(
            df: pd.DataFrame, forecast_df: pd.DataFrame, forecast_date: datetime, lead_time_months: float
    ) -> pd.DataFrame:
        if forecast_df.empty:
            df["FORECAST_LEADTIME"] = 0
            return df

        lead_time_days = int(lead_time_months * 30.44)
        lead_time_end = forecast_date + pd.Timedelta(days=lead_time_days)
        forecast_window = forecast_df[
            (forecast_df["data"] >= forecast_date) & (forecast_df["data"] < lead_time_end)
            ]

        if forecast_window.empty:
            df["FORECAST_LEADTIME"] = 0
            return df

        forecast_sum = forecast_window.groupby("sku")["forecast"].sum().reset_index()
        forecast_sum.columns = ["SKU", "FORECAST_LEADTIME"]
        df = df.merge(forecast_sum, on="SKU", how="left")
        df["FORECAST_LEADTIME"] = df["FORECAST_LEADTIME"].fillna(0)
        return df

    @staticmethod
    def _add_sku_components(df: pd.DataFrame) -> pd.DataFrame:
        sku_components = df["SKU"].apply(SalesAnalyzer.parse_sku_components)
        df["MODEL"] = sku_components.apply(lambda x: x["model"])
        df["COLOR"] = sku_components.apply(lambda x: x["color"])
        df["SIZE"] = sku_components.apply(lambda x: x["size"])
        return df

    @staticmethod
    def _calculate_stockout_risk(df: pd.DataFrame, config: dict) -> pd.DataFrame:
        df["STOCKOUT_RISK"] = 0.0
        zero_stock_mask = (df["STOCK"] <= 0) & (df["FORECAST_LEADTIME"] > 0)
        df.loc[zero_stock_mask, "STOCKOUT_RISK"] = config["zero_stock_penalty"]

        below_rop_mask = (df["STOCK"] > 0) & (df["STOCK"] < df["ROP"])
        df.loc[below_rop_mask, "STOCKOUT_RISK"] = (
                (df["ROP"] - df["STOCK"]) / df["ROP"] * config["below_rop_max"]
        )
        return df

    @staticmethod
    def _calculate_revenue_impact(df: pd.DataFrame) -> pd.DataFrame:
        if "PRICE" in df.columns:
            df["REVENUE_AT_RISK"] = df["FORECAST_LEADTIME"] * df["PRICE"]
            max_revenue = df["REVENUE_AT_RISK"].max()
            df["REVENUE_IMPACT"] = (df["REVENUE_AT_RISK"] / max_revenue * 100) if max_revenue > 0 else 0
        else:
            max_forecast = df["FORECAST_LEADTIME"].max()
            df["REVENUE_IMPACT"] = (df["FORECAST_LEADTIME"] / max_forecast * 100) if max_forecast > 0 else 0
        return df

    @staticmethod
    def _apply_type_multipliers(df: pd.DataFrame, type_multipliers: dict) -> pd.DataFrame:
        default_type_mult = {"new": 1.2, "seasonal": 1.3, "regular": 1.0, "basic": 0.9}
        type_mult = {k: type_multipliers.get(k, v) for k, v in default_type_mult.items()}
        df["TYPE_MULTIPLIER"] = df["TYPE"].map(type_mult).fillna(1.0)
        return df

    @staticmethod
    def _calculate_priority_score(df: pd.DataFrame, config: dict) -> pd.DataFrame:
        df["DEFICIT"] = (df["ROP"] - df["STOCK"]).clip(lower=0)
        df["PRIORITY_SCORE"] = (
                                       (df["STOCKOUT_RISK"] * config["weight_stockout"])
                                       + (df["REVENUE_IMPACT"] * config["weight_revenue"])
                                       + (df["FORECAST_LEADTIME"].clip(upper=config["demand_cap"]) * config[
                                   "weight_demand"])
                               ) * df["TYPE_MULTIPLIER"]
        return df

    @staticmethod
    def aggregate_order_by_model_color(priority_df: pd.DataFrame) -> pd.DataFrame:
        agg_dict = {
            "PRIORITY_SCORE": "mean",
            "DEFICIT": "sum",
            "FORECAST_LEADTIME": "sum",
            "STOCK": "sum",
            "ROP": "sum",
            "SS": "sum",
            "URGENT": "any",
        }

        if "REVENUE_AT_RISK" in priority_df.columns:
            agg_dict["REVENUE_AT_RISK"] = "sum"

        grouped = (
            priority_df.groupby(["MODEL", "COLOR"], as_index=False)
            .agg(agg_dict)
            .sort_values("PRIORITY_SCORE", ascending=False)
        )

        grouped["COVERAGE_GAP"] = grouped["FORECAST_LEADTIME"] - grouped["STOCK"]
        grouped["COVERAGE_GAP"] = grouped["COVERAGE_GAP"].clip(lower=0)

        return grouped

    @staticmethod
    def get_size_quantities_for_model_color(
            priority_df: pd.DataFrame, model: str, color: str
    ) -> dict:
        filtered = priority_df[(priority_df["MODEL"] == model) & (priority_df["COLOR"] == color)]

        size_quantities = {}

        for _, row in filtered.iterrows():
            size = row["SIZE"]
            # Handle NaN values from DataFrame
            deficit = row.get("DEFICIT", 0)
            forecast = row.get("FORECAST_LEADTIME", 0)
            deficit = 0 if pd.isna(deficit) else deficit
            forecast = 0 if pd.isna(forecast) else forecast
            qty_needed = max(deficit, forecast)
            if size:
                size_quantities[size] = int(qty_needed)

        return size_quantities

    @staticmethod
    def generate_order_recommendations(
            summary_df: pd.DataFrame,
            forecast_df: pd.DataFrame,
            forecast_date: datetime,
            forecast_time_months: float = 1.36,
            top_n: int = 10,
            settings: dict | None = None,
    ) -> dict:
        priority_df = SalesAnalyzer.calculate_order_priority(
            summary_df, forecast_df, forecast_date, forecast_time_months, settings
        )

        model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(priority_df)

        top_model_colors = model_color_summary.head(top_n)

        top_recommendations = []
        for _, row in top_model_colors.iterrows():
            model = row["MODEL"]
            color = row["COLOR"]
            size_breakdown = SalesAnalyzer.get_size_quantities_for_model_color(
                priority_df, model, color
            )

            top_recommendations.append(
                {
                    "model": model,
                    "color": color,
                    "priority_score": row["PRIORITY_SCORE"],
                    "total_deficit": row["DEFICIT"],
                    "forecast_demand": row["FORECAST_LEADTIME"],
                    "coverage_gap": row["COVERAGE_GAP"],
                    "urgent": row["URGENT"],
                    "size_quantities": size_breakdown,
                }
            )

        return {
            "priority_skus": priority_df,
            "model_color_summary": model_color_summary,
            "top_recommendations": top_recommendations,
        }

    @staticmethod
    def generate_weekly_new_products_analysis(
            sales_df: pd.DataFrame,
            stock_df: pd.DataFrame | None = None,
            lookback_days: int = 60,
            reference_date: datetime | None = None,
    ) -> pd.DataFrame:

        def get_week_start_wednesday(date: datetime) -> datetime:
            days_since_wed = (date.weekday() - 2) % 7
            return date - timedelta(days=days_since_wed)

        if reference_date is None:
            reference_date = datetime.today()

        cutoff_date = reference_date - timedelta(days=lookback_days)

        df = sales_df.copy()
        df["model"] = df["sku"].astype(str).str[:5]

        first_sales = df.groupby("model")["data"].min().reset_index()
        first_sales.columns = ["model", "first_sale_date"]

        new_products = first_sales[first_sales["first_sale_date"] >= cutoff_date].copy()

        if new_products.empty:
            return pd.DataFrame()

        new_products["monitoring_end_date"] = new_products["first_sale_date"] + timedelta(
            days=lookback_days
        )

        df_new = df[df["model"].isin(new_products["model"])].copy()

        df_new = df_new.merge(
            new_products[["model", "first_sale_date", "monitoring_end_date"]],
            on="model",
            how="left",
        )

        df_new = df_new[
            (df_new["data"] >= df_new["first_sale_date"])
            & (df_new["data"] <= df_new["monitoring_end_date"])
            ]

        df_new["week_start"] = df_new["data"].apply(get_week_start_wednesday)

        weekly_sales = df_new.groupby(["model", "week_start"], as_index=False)["ilosc"].sum()

        model_week_ranges = []
        for _, row in new_products.iterrows():
            model = row["model"]
            first_sale = row["first_sale_date"]
            monitoring_end = row["monitoring_end_date"]

            first_week = get_week_start_wednesday(first_sale)
            last_week = get_week_start_wednesday(min(monitoring_end, reference_date))

            model_weeks = pd.date_range(start=first_week, end=last_week, freq="W-WED")

            for week in model_weeks:
                model_week_ranges.append({"model": model, "week_start": week})

        full_combinations = pd.DataFrame(model_week_ranges)

        weekly_complete = full_combinations.merge(
            weekly_sales, on=["model", "week_start"], how="left"
        )
        weekly_complete["ilosc"] = weekly_complete["ilosc"].fillna(0).astype(int)

        pivot_df = weekly_complete.pivot(index="model", columns="week_start", values="ilosc")

        pivot_df.columns = [col.strftime("%Y-%m-%d") for col in pivot_df.columns]
        pivot_df = pivot_df.reset_index()

        result = new_products[["model", "first_sale_date"]].merge(pivot_df, on="model", how="left")

        result["first_sale_date"] = result["first_sale_date"].dt.strftime("%d-%m-%Y")

        result = result.rename(columns={"first_sale_date": "SALES_START_DATE", "model": "MODEL"})

        if stock_df is not None:
            stock_df = stock_df.copy()
            stock_df["model"] = stock_df["sku"].astype(str).str[:5]
            descriptions = stock_df.groupby("model")["nazwa"].first().reset_index()
            descriptions.columns = ["MODEL", "DESCRIPTION"]
            result = result.merge(descriptions, on="MODEL", how="left")

        week_cols = [
            col for col in result.columns if col not in ["SALES_START_DATE", "MODEL", "DESCRIPTION"]
        ]
        week_cols.sort()

        base_cols = ["SALES_START_DATE", "MODEL"]
        if "DESCRIPTION" in result.columns:
            base_cols.append("DESCRIPTION")

        result = result[base_cols + week_cols]

        result = result.sort_values("SALES_START_DATE", ascending=False)

        return result

    @staticmethod
    def calculate_top_sales_report(
            sales_df: pd.DataFrame, reference_date: datetime | None = None
    ) -> dict:
        if reference_date is None:
            reference_date = datetime.today()

        last_week_start, last_week_end = SalesAnalyzer._get_last_week_range(reference_date)

        prev_year_start = last_week_start - timedelta(days=364)
        prev_year_end = last_week_end - timedelta(days=364)

        df = sales_df.copy()
        df["model"] = df["sku"].astype(str).str[:5]

        # noinspection PyUnresolvedReferences
        last_week_sales = (
            df[(df["data"] >= last_week_start) & (df["data"] <= last_week_end)]
            .groupby("model", as_index=False)["ilosc"]
            .sum()
        )
        last_week_sales.columns = ["model", "current_week_sales"]

        # noinspection PyUnresolvedReferences
        prev_year_sales = (
            df[(df["data"] >= prev_year_start) & (df["data"] <= prev_year_end)]
            .groupby("model", as_index=False)["ilosc"]
            .sum()
        )
        prev_year_sales.columns = ["model", "prev_year_sales"]

        comparison = last_week_sales.merge(prev_year_sales, on="model", how="outer")
        comparison["current_week_sales"] = comparison["current_week_sales"].fillna(0)
        comparison["prev_year_sales"] = comparison["prev_year_sales"].fillna(0)

        comparison["difference"] = comparison["current_week_sales"] - comparison["prev_year_sales"]
        comparison["percent_change"] = 0.0

        mask = comparison["prev_year_sales"] > 0
        comparison.loc[mask, "percent_change"] = (
                                                         comparison.loc[mask, "difference"] / comparison.loc[
                                                     mask, "prev_year_sales"]
                                                 ) * 100

        comparison.loc[~mask & (comparison["current_week_sales"] > 0), "percent_change"] = 999.0

        rising = comparison[comparison["difference"] > 0].sort_values("difference", ascending=False)
        falling = comparison[comparison["difference"] < 0].sort_values("difference", ascending=True)

        rising_star = rising.iloc[0] if not rising.empty else None
        falling_star = falling.iloc[0] if not falling.empty else None

        return {
            "last_week_start": last_week_start,
            "last_week_end": last_week_end,
            "prev_year_start": prev_year_start,
            "prev_year_end": prev_year_end,
            "rising_star": rising_star,
            "falling_star": falling_star,
        }

    @staticmethod
    def calculate_top_products_by_type(
            sales_df: pd.DataFrame,
            cv_basic: float = 0.6,
            cv_seasonal: float = 1.0,
            reference_date: datetime | None = None,
    ) -> dict:
        if reference_date is None:
            reference_date = datetime.today()

        last_week_start, last_week_end = SalesAnalyzer._get_last_week_range(reference_date)

        df = sales_df.copy()
        df["model"] = df["sku"].astype(str).str[:5]
        df["color"] = df["sku"].astype(str).str[5:7]

        last_week_sales = df[(df["data"] >= last_week_start) & (df["data"] <= last_week_end)].copy()

        # noinspection PyUnresolvedReferences
        model_color_sales = last_week_sales.groupby(["model", "color"], as_index=False)[
            "ilosc"
        ].sum()
        model_color_sales.columns = ["model", "color", "sales"]

        monthly_sales = df.copy()
        monthly_sales["month"] = monthly_sales["data"].dt.to_period("M")
        monthly_agg = monthly_sales.groupby(["model", "month"], as_index=False)["ilosc"].sum()

        stats = monthly_agg.groupby("model", as_index=False).agg(
            avg_sales=("ilosc", "mean"),
            sd_sales=("ilosc", "std"),
            months_with_sales=("month", "nunique"),
        )
        stats["sd_sales"] = stats["sd_sales"].fillna(0)
        stats["cv"] = 0.0
        mask = stats["avg_sales"] > 0
        stats.loc[mask, "cv"] = stats.loc[mask, "sd_sales"] / stats.loc[mask, "avg_sales"]

        first_sales = df.groupby("model")["data"].min().reset_index()
        first_sales.columns = ["model", "first_sale"]

        stats = stats.merge(first_sales, on="model", how="left")

        one_year_ago = reference_date - timedelta(days=365)
        stats["type"] = "regular"
        stats.loc[stats["first_sale"] > one_year_ago, "type"] = "new"
        stats.loc[(stats["type"] != "new") & (stats["cv"] < cv_basic), "type"] = "basic"
        stats.loc[(stats["type"] != "new") & (stats["cv"] > cv_seasonal), "type"] = "seasonal"

        model_color_sales = model_color_sales.merge(
            stats[["model", "type"]], on="model", how="left"
        )

        top_by_type = {}
        for product_type in ["new", "seasonal", "regular", "basic"]:
            type_products = model_color_sales[model_color_sales["type"] == product_type]
            top_5 = type_products.nlargest(5, "sales")
            top_by_type[product_type] = top_5

        return {
            "last_week_start": last_week_start,
            "last_week_end": last_week_end,
            "top_by_type": top_by_type,
        }

    @staticmethod
    def find_urgent_colors(model_color_summary: pd.DataFrame, model: str) -> list[str]:
        urgent = model_color_summary[
            (model_color_summary["MODEL"] == model) &
            (model_color_summary.get("URGENT", pd.Series([False] * len(model_color_summary))) == True)
            ]
        return urgent["COLOR"].tolist()

    @staticmethod
    def _normalize_monthly_agg_columns(df: pd.DataFrame) -> pd.DataFrame:
        column_mapping = {
            "entity_id": "SKU",
            "year_month": "YEAR_MONTH",
            "total_quantity": "TOTAL_QUANTITY"
        }
        return df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    @staticmethod
    def _filter_and_pivot_sales(
            df: pd.DataFrame,
            model: str,
            colors: list[str],
            months: int
    ) -> pd.DataFrame:
        df["model"] = df["SKU"].astype(str).str[:5]
        df["color"] = df["SKU"].astype(str).str[5:7]

        filtered = df[(df["model"] == model) & (df["color"].isin(colors))]

        if filtered.empty:
            return pd.DataFrame()

        filtered = filtered.sort_values("YEAR_MONTH")
        unique_months = filtered["YEAR_MONTH"].unique()
        last_n_months = sorted(unique_months)[-months:] if len(unique_months) >= months else sorted(unique_months)
        filtered_last_n = filtered[filtered["YEAR_MONTH"].isin(last_n_months)]

        pivot_df = filtered_last_n.pivot_table(
            index="color",
            columns="YEAR_MONTH",
            values="TOTAL_QUANTITY",
            aggfunc="sum",
            fill_value=0
        )

        return pivot_df.reset_index()

    @staticmethod
    def get_last_n_months_sales_by_color(
            monthly_agg: pd.DataFrame,
            model: str,
            colors: list[str],
            months: int = 4
    ) -> pd.DataFrame:
        if monthly_agg is None or monthly_agg.empty:
            return pd.DataFrame()

        df = SalesAnalyzer._normalize_monthly_agg_columns(monthly_agg.copy())
        return SalesAnalyzer._filter_and_pivot_sales(df, model, colors, months)

    @staticmethod
    def optimize_pattern_with_aliases(
            priority_skus: pd.DataFrame,
            model: str,
            color: str,
            pattern_set,
            size_aliases: dict[str, str],
            min_per_pattern: int
    ) -> dict:
        from utils.pattern_optimizer_logic import optimize_patterns

        size_quantities = SalesAnalyzer.get_size_quantities_for_model_color(priority_skus, model, color)

        if not size_quantities:
            return {
                "allocation": {},
                "produced": {},
                "excess": {},
                "total_patterns": 0,
                "total_excess": 0,
                "all_covered": False,
            }

        size_quantities_with_aliases = {}
        for size_code, quantity in size_quantities.items():
            alias = size_aliases.get(size_code, size_code)
            size_quantities_with_aliases[alias] = size_quantities_with_aliases.get(alias, 0) + quantity

        result = optimize_patterns(size_quantities_with_aliases, pattern_set.patterns, min_per_pattern)

        return result
