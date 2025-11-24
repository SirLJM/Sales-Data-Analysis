from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class SalesAnalyzer:
    def __init__(self, data):
        self.data = data.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.data["data"]):
            self.data["data"] = pd.to_datetime(self.data["data"])

        self.data["model"] = self.data["sku"].astype(str).str[:5]

    def aggregate_by_sku(self):
        self.data["year_month"] = self.data["data"].dt.to_period("M")

        first_sale = self.data.groupby("sku")["data"].min().reset_index()
        first_sale.columns = ["SKU", "first_sale"]

        monthly_sales = self.data.groupby(["sku", "year_month"], as_index=False)["ilosc"].sum()

        sku_summary = monthly_sales.groupby("sku", as_index=False).agg(
            {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}
        )

        sku_summary.columns = ["SKU", "MONTHS", "QUANTITY", "AVERAGE SALES", "SD"]

        sku_summary["CV"] = sku_summary["SD"] / sku_summary["AVERAGE SALES"]
        sku_summary["CV"] = sku_summary["CV"].fillna(0)

        sku_summary = pd.merge(sku_summary, first_sale, on="SKU", how="left")

        return sku_summary.sort_values("SKU", ascending=False)

    def aggregate_by_model(self):
        self.data["year_month"] = self.data["data"].dt.to_period("M")

        first_sale = self.data.groupby("model")["data"].min().reset_index()
        first_sale.columns = ["MODEL", "first_sale"]

        monthly_sales = self.data.groupby(["model", "year_month"], as_index=False)["ilosc"].sum()

        model_summary = monthly_sales.groupby("model", as_index=False).agg(
            {"year_month": "nunique", "ilosc": ["sum", "mean", "std"]}
        )

        model_summary.columns = ["MODEL", "MONTHS", "QUANTITY", "AVERAGE SALES", "SD"]

        model_summary["CV"] = model_summary["SD"] / model_summary["AVERAGE SALES"]
        model_summary["CV"] = model_summary["CV"].fillna(0)

        model_summary = pd.merge(model_summary, first_sale, on="MODEL", how="left")

        return model_summary.sort_values("MODEL", ascending=False)

    def calculate_last_two_years_avg_sales(self, by_model=False):
        df = self.data.copy()

        two_years_ago = datetime.today() - timedelta(days=730)
        df_last_2_years = df[df["data"] >= two_years_ago].copy()

        df_last_2_years["year_month"] = df_last_2_years["data"].dt.to_period("M")

        if by_model:
            monthly_sales = df_last_2_years.groupby(["model", "year_month"], as_index=False)[
                "ilosc"
            ].sum()
            avg_sales = monthly_sales.groupby("model", as_index=False)["ilosc"].mean()
            avg_sales.columns = ["MODEL", "LAST_2_YEARS_AVG"]
        else:
            monthly_sales = df_last_2_years.groupby(["sku", "year_month"], as_index=False)[
                "ilosc"
            ].sum()
            avg_sales = monthly_sales.groupby("sku", as_index=False)["ilosc"].mean()
            avg_sales.columns = ["SKU", "LAST_2_YEARS_AVG"]

        avg_sales["LAST_2_YEARS_AVG"] = avg_sales["LAST_2_YEARS_AVG"].round(2)

        return avg_sales

    @staticmethod
    def classify_sku_type(sku_summary, cv_basic, cv_seasonal):
        df = sku_summary.copy()

        one_year_ago = datetime.today() - timedelta(days=365)

        df["TYPE"] = "regular"
        df.loc[df["first_sale"] > one_year_ago, "TYPE"] = "new"
        df.loc[(df["TYPE"] != "new") & (df["CV"] < cv_basic), "TYPE"] = "basic"
        df.loc[(df["TYPE"] != "new") & (df["CV"] > cv_seasonal), "TYPE"] = "seasonal"

        return df

    def determine_seasonal_months(self):
        df = self.data.copy()

        two_years_ago = datetime.today() - timedelta(days=730)
        df = df[df["data"] >= two_years_ago]

        df["month"] = df["data"].dt.month
        df["year"] = df["data"].dt.year

        monthly_sales = df.groupby(["sku", "year", "month"], as_index=False)["ilosc"].sum()

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
        sku_summary,
        seasonal_data,
        lead_time,
        z_basic,
        z_regular,
        z_seasonal_in,
        z_seasonal_out,
        z_new,
    ):
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
        df["ROP"] = df["AVERAGE SALES"] * lead_time + df["SS"]

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
                seasonal_mask, df["AVERAGE SALES"] * lead_time + df["SS_IN"], np.nan
            )

            df["SS_OUT"] = np.where(
                seasonal_mask, z_seasonal_out * df["SD"] * sqrt_lead_time, np.nan
            )
            df["ROP_OUT"] = np.where(
                seasonal_mask, df["AVERAGE SALES"] * lead_time + df["SS_OUT"], np.nan
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

        base_cols = ["MONTHS", "QUANTITY", "AVERAGE SALES", "SD", "CV", "TYPE", "SS", "ROP"]
        return df[[id_column] + base_cols]

    @staticmethod
    def calculate_forecast_metrics(
        forecast_df: pd.DataFrame, file_date: datetime
    ) -> pd.DataFrame:

        if forecast_df.empty:
            return pd.DataFrame(columns=["sku", "FORECAST_8W", "FORECAST_16W"])

        forecast_df["data"] = pd.to_datetime(forecast_df["data"])

        weeks_8_end = file_date + pd.Timedelta(weeks=8)
        weeks_16_end = file_date + pd.Timedelta(weeks=16)

        forecast_8w = forecast_df[
            (forecast_df["data"] >= file_date) & (forecast_df["data"] < weeks_8_end)
        ]

        forecast_16w = forecast_df[
            (forecast_df["data"] >= file_date) & (forecast_df["data"] < weeks_16_end)
        ]

        forecast_8w_sum = (
            forecast_8w.groupby("sku")["forecast"].sum().reset_index().rename(columns={"forecast": "FORECAST_8W"})
        )

        forecast_16w_sum = (
            forecast_16w.groupby("sku")["forecast"]
            .sum()
            .reset_index()
            .rename(columns={"forecast": "FORECAST_16W"})
        )

        result = forecast_8w_sum.merge(forecast_16w_sum, on="sku", how="outer")

        result["FORECAST_8W"] = result["FORECAST_8W"].fillna(0).round(2)
        result["FORECAST_16W"] = result["FORECAST_16W"].fillna(0).round(2)

        return result

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
            return pd.DataFrame(
                columns=["date", "projected_stock", "rop_reached", "zero_reached"]
            )

        sku_forecast = forecast_df[forecast_df["sku"] == sku].copy()

        if sku_forecast.empty:
            return pd.DataFrame(
                columns=["date", "projected_stock", "rop_reached", "zero_reached"]
            )

        sku_forecast["data"] = pd.to_datetime(sku_forecast["data"])

        end_date = start_date + pd.DateOffset(months=projection_months)
        sku_forecast = sku_forecast[
            (sku_forecast["data"] >= start_date) & (sku_forecast["data"] <= end_date)
        ]

        # noinspection PyArgumentList
        sku_forecast = sku_forecast.sort_values("data")

        projection = [{
            "date": start_date,
            "projected_stock": current_stock,
            "rop_reached": current_stock <= rop,
            "zero_reached": current_stock <= 0,
        }]

        running_stock = current_stock

        for _, row in sku_forecast.iterrows():
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

        projection_df["rop"] = rop
        projection_df["safety_stock"] = safety_stock

        return projection_df

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
    ) -> pd.DataFrame:
        df = summary_df.copy()

        required_cols = ["SKU", "STOCK", "ROP", "TYPE"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        if not forecast_df.empty:
            lead_time_days = int(lead_time_months * 30.44)
            lead_time_end = forecast_date + pd.Timedelta(days=lead_time_days)
            forecast_window = forecast_df[
                (forecast_df["data"] >= forecast_date) & (forecast_df["data"] < lead_time_end)
            ]
            forecast_sum = (
                forecast_window.groupby("sku")["forecast"].sum().reset_index()
            )
            forecast_sum.columns = ["SKU", "FORECAST_LEADTIME"]
            df = df.merge(forecast_sum, on="SKU", how="left")
            df["FORECAST_LEADTIME"] = df["FORECAST_LEADTIME"].fillna(0)
        else:
            df["FORECAST_LEADTIME"] = 0

        sku_components = df["SKU"].apply(SalesAnalyzer.parse_sku_components)
        df["MODEL"] = sku_components.apply(lambda x: x["model"])
        df["COLOR"] = sku_components.apply(lambda x: x["color"])
        df["SIZE"] = sku_components.apply(lambda x: x["size"])

        df["PRIORITY_SCORE"] = 0.0

        df["STOCKOUT_RISK"] = 0.0
        zero_stock_mask = (df["STOCK"] <= 0) & (df["FORECAST_LEADTIME"] > 0)
        df.loc[zero_stock_mask, "STOCKOUT_RISK"] = 100

        below_rop_mask = (df["STOCK"] > 0) & (df["STOCK"] < df["ROP"])
        df.loc[below_rop_mask, "STOCKOUT_RISK"] = (
            (df["ROP"] - df["STOCK"]) / df["ROP"] * 80
        )

        if "PRICE" in df.columns:
            df["REVENUE_AT_RISK"] = df["FORECAST_LEADTIME"] * df["PRICE"]
            if df["REVENUE_AT_RISK"].max() > 0:
                df["REVENUE_IMPACT"] = (
                    df["REVENUE_AT_RISK"] / df["REVENUE_AT_RISK"].max() * 100
                )
            else:
                df["REVENUE_IMPACT"] = 0
        else:
            if df["FORECAST_LEADTIME"].max() > 0:
                df["REVENUE_IMPACT"] = (
                    df["FORECAST_LEADTIME"] / df["FORECAST_LEADTIME"].max() * 100
                )
            else:
                df["REVENUE_IMPACT"] = 0

        type_multiplier = {
            "new": 1.2,
            "seasonal": 1.3,
            "regular": 1.0,
            "basic": 0.9,
        }
        df["TYPE_MULTIPLIER"] = df["TYPE"].map(type_multiplier).fillna(1.0)

        df["DEFICIT"] = (df["ROP"] - df["STOCK"]).clip(lower=0)

        df["PRIORITY_SCORE"] = (
            (df["STOCKOUT_RISK"] * 0.5)
            + (df["REVENUE_IMPACT"] * 0.3)
            + (df["FORECAST_LEADTIME"].clip(upper=100) * 0.2)
        ) * df["TYPE_MULTIPLIER"]

        df["URGENT"] = (df["STOCK"] <= 0) | (
            (df["STOCK"] < df["ROP"]) & (df["FORECAST_LEADTIME"] > df["STOCK"])
        )

        df = df.sort_values("PRIORITY_SCORE", ascending=False)

        return df

    @staticmethod
    def aggregate_order_by_model_color(priority_df: pd.DataFrame) -> pd.DataFrame:
        agg_dict = {
            "PRIORITY_SCORE": "mean",
            "DEFICIT": "sum",
            "FORECAST_LEADTIME": "sum",
            "STOCK": "sum",
            "ROP": "sum",
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
    def prepare_pattern_matching_input(
        priority_df: pd.DataFrame, model: str, color: str, pattern_sizes: list = None
    ) -> dict:
        filtered = priority_df[
            (priority_df["MODEL"] == model) & (priority_df["COLOR"] == color)
        ]

        size_quantities = {}

        if pattern_sizes:
            for size in pattern_sizes:
                size_quantities[size] = 0

        for _, row in filtered.iterrows():
            size = row["SIZE"]
            qty_needed = max(row.get("DEFICIT", 0), row.get("FORECAST_LEADTIME", 0))
            if size:
                size_quantities[size] = int(qty_needed)

        return size_quantities

    @staticmethod
    def generate_order_recommendations(
        summary_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        forecast_date: datetime,
        lead_time_months: float = 1.36,
        top_n: int = 10,
    ) -> dict:
        priority_df = SalesAnalyzer.calculate_order_priority(
            summary_df, forecast_df, forecast_date, lead_time_months
        )

        model_color_summary = SalesAnalyzer.aggregate_order_by_model_color(priority_df)

        top_model_colors = model_color_summary.head(top_n)

        top_recommendations = []
        for _, row in top_model_colors.iterrows():
            model = row["MODEL"]
            color = row["COLOR"]
            size_breakdown = SalesAnalyzer.prepare_pattern_matching_input(
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
