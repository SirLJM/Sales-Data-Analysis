from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

from utils.logging_config import get_logger

logger = get_logger("internal_forecast")

MIN_MONTHS_FOR_FORECAST = 12
MIN_MONTHS_FOR_SEASONAL = 24

SKTIME_AVAILABLE = False
AutoARIMA = None
try:
    from sktime.forecasting.arima import AutoARIMA
    SKTIME_AVAILABLE = True
except ImportError:
    AutoARIMA = None

AVAILABLE_METHODS = [
    "moving_avg",
    "exp_smoothing",
    "holt_winters",
    "sarima",
]

if SKTIME_AVAILABLE:
    AVAILABLE_METHODS.append("auto_arima")


def get_available_methods() -> list[str]:
    return AVAILABLE_METHODS.copy()


def is_method_available(method: str) -> bool:
    return method in AVAILABLE_METHODS


def prepare_monthly_series(
        monthly_agg: pd.DataFrame,
        entity_id: str,
        entity_type: str = "model",
) -> pd.Series | None:
    if monthly_agg is None or monthly_agg.empty:
        return None

    id_col = _find_column(monthly_agg, ["entity_id", "sku", "SKU", "model", "MODEL"])
    month_col = _find_column(monthly_agg, ["year_month", "month", "MONTH"])
    qty_col = _find_column(monthly_agg, ["total_quantity", "TOTAL_QUANTITY", "ilosc"])

    if id_col is None or month_col is None or qty_col is None:
        return None

    if entity_type == "model":
        monthly_agg = monthly_agg.copy()
        monthly_agg["_model"] = monthly_agg[id_col].astype(str).str[:5]
        entity_data = monthly_agg[monthly_agg["_model"] == entity_id]
        entity_data = entity_data.groupby(month_col, as_index=False, observed=True)[qty_col].sum()
    else:
        entity_data = monthly_agg[monthly_agg[id_col] == entity_id]

    if entity_data.empty or len(entity_data) < MIN_MONTHS_FOR_FORECAST:
        return None

    entity_data = entity_data.sort_values(month_col)
    series = pd.Series(
        entity_data[qty_col].values,
        index=pd.PeriodIndex(entity_data[month_col], freq="M"),
        name=entity_id,
    )

    series = _fill_missing_months(series)

    return series


def _fill_missing_months(series: pd.Series) -> pd.Series:
    if series.empty:
        return series

    full_range = pd.period_range(start=series.index.min(), end=series.index.max(), freq="M")
    series = series.reindex(full_range, fill_value=0)
    return series


def select_forecast_method(
        series: pd.Series,
        product_type: str | None = None,
        cv: float | None = None,
) -> str:
    n_points = len(series)

    if product_type == "new" or n_points < MIN_MONTHS_FOR_FORECAST:
        return "moving_avg"

    if cv is not None:
        if cv < 0.6:
            return "exp_smoothing"
        elif cv > 1.0 and n_points >= MIN_MONTHS_FOR_SEASONAL:
            return "sarima"
        else:
            return "holt_winters"

    if product_type == "basic":
        return "exp_smoothing"
    elif product_type == "seasonal" and n_points >= MIN_MONTHS_FOR_SEASONAL:
        return "sarima"
    elif product_type == "regular":
        return "holt_winters"

    return "exp_smoothing"


def generate_forecast_moving_avg(
        series: pd.Series,
        horizon: int,
        window: int = 3,
) -> pd.DataFrame:
    weights = np.array([0.5, 0.3, 0.2])[:window]
    weights = weights / weights.sum()

    recent = series.tail(window).values
    if len(recent) < window:
        weights = weights[-len(recent):]
        weights = weights / weights.sum()

    forecast_value = np.dot(recent, weights)

    last_period = series.index[-1]
    future_periods = pd.period_range(start=last_period + 1, periods=horizon, freq="M")

    return pd.DataFrame({
        "period": future_periods,
        "forecast": [forecast_value] * horizon,
        "lower_ci": [forecast_value * 0.8] * horizon,
        "upper_ci": [forecast_value * 1.2] * horizon,
    })


def generate_forecast_exp_smoothing(
        series: pd.Series,
        horizon: int,
        seasonal: bool = False,
        seasonal_periods: int = 12,
) -> pd.DataFrame:
    try:
        if seasonal and len(series) >= 2 * seasonal_periods:
            model = ExponentialSmoothing(
                series.values,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            )
        else:
            model = ExponentialSmoothing(
                series.values,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            )

        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(horizon)

        last_period = series.index[-1]
        future_periods = pd.period_range(start=last_period + 1, periods=horizon, freq="M")

        std_resid = np.std(fitted.resid) if hasattr(fitted, "resid") else forecast.mean() * 0.2

        return pd.DataFrame({
            "period": future_periods,
            "forecast": forecast,
            "lower_ci": forecast - 1.96 * std_resid,
            "upper_ci": forecast + 1.96 * std_resid,
        })

    except Exception as e:
        logger.warning("Exp smoothing failed for series, using moving avg: %s", e)
        return generate_forecast_moving_avg(series, horizon)


def generate_forecast_holt_winters(
        series: pd.Series,
        horizon: int,
        seasonal_periods: int = 12,
) -> pd.DataFrame:
    try:
        if len(series) >= 2 * seasonal_periods:
            model = ExponentialSmoothing(
                series.values,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                damped_trend=True,
                initialization_method="estimated",
            )
        else:
            model = ExponentialSmoothing(
                series.values,
                trend="add",
                damped_trend=True,
                initialization_method="estimated",
            )

        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(horizon)

        last_period = series.index[-1]
        future_periods = pd.period_range(start=last_period + 1, periods=horizon, freq="M")

        std_resid = np.std(fitted.resid) if hasattr(fitted, "resid") else forecast.mean() * 0.2

        return pd.DataFrame({
            "period": future_periods,
            "forecast": forecast,
            "lower_ci": forecast - 1.96 * std_resid,
            "upper_ci": forecast + 1.96 * std_resid,
        })

    except Exception as e:
        logger.warning("Holt-Winters failed, falling back to exp smoothing: %s", e)
        return generate_forecast_exp_smoothing(series, horizon, seasonal=False)


def generate_forecast_sarima(
        series: pd.Series,
        horizon: int,
        order: tuple = (1, 1, 1),
        seasonal_order: tuple = (1, 1, 1, 12),
) -> pd.DataFrame:
    try:
        model = SARIMAX(
            series.values,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )

        fitted = model.fit(disp=False, maxiter=100)
        forecast_result = fitted.get_forecast(steps=horizon)
        forecast = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=0.05)

        last_period = series.index[-1]
        future_periods = pd.period_range(start=last_period + 1, periods=horizon, freq="M")

        return pd.DataFrame({
            "period": future_periods,
            "forecast": forecast,
            "lower_ci": conf_int[:, 0],
            "upper_ci": conf_int[:, 1],
        })

    except Exception as e:
        logger.warning("SARIMA failed, falling back to Holt-Winters: %s", e)
        return generate_forecast_holt_winters(series, horizon)


def generate_forecast_auto_arima(
        series: pd.Series,
        horizon: int,
        seasonal: bool = True,
        sp: int = 12,
) -> pd.DataFrame:
    if not SKTIME_AVAILABLE:
        logger.warning("sktime not available, falling back to SARIMA")
        return generate_forecast_sarima(series, horizon)

    try:
        y = pd.Series(series.values, index=pd.PeriodIndex(series.index, freq="M"))

        model = AutoARIMA(
            sp=sp if seasonal else 1,
            seasonal=seasonal,
            suppress_warnings=True,
            error_action="ignore",
            max_p=3,
            max_q=3,
            max_P=2,
            max_Q=2,
            max_d=2,
            max_D=1,
            stepwise=True,
            n_jobs=1,
        )

        model.fit(y)
        fh = list(range(1, horizon + 1))
        forecast = model.predict(fh=fh)
        conf_int = model.predict_interval(fh=fh, coverage=0.95)

        last_period = series.index[-1]
        future_periods = pd.period_range(start=last_period + 1, periods=horizon, freq="M")

        lower_col = conf_int.columns[0] if len(conf_int.columns) >= 1 else None
        upper_col = conf_int.columns[1] if len(conf_int.columns) >= 2 else None

        lower_vals = conf_int[lower_col].values if lower_col else forecast.values * 0.8
        upper_vals = conf_int[upper_col].values if upper_col else forecast.values * 1.2

        return pd.DataFrame({
            "period": future_periods,
            "forecast": forecast.values,
            "lower_ci": lower_vals,
            "upper_ci": upper_vals,
        })

    except Exception as e:
        logger.warning("AutoARIMA failed, falling back to SARIMA: %s", e)
        return generate_forecast_sarima(series, horizon)


FORECAST_GENERATORS: dict[str, Callable] = {
    "moving_avg": generate_forecast_moving_avg,
    "exp_smoothing": generate_forecast_exp_smoothing,
    "holt_winters": generate_forecast_holt_winters,
    "sarima": generate_forecast_sarima,
    "auto_arima": generate_forecast_auto_arima,
}


def _create_forecast_result(
    entity_id: str,
    entity_type: str,
    method: str | None = None,
    forecast_df: pd.DataFrame | None = None,
    error: str | None = None,
) -> dict:
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "method_used": method,
        "forecast_df": forecast_df,
        "success": forecast_df is not None,
        "error": error,
    }


def generate_internal_forecast(
        monthly_agg: pd.DataFrame,
        entity_id: str,
        entity_type: str,
        product_type: str | None,
        cv: float | None,
        horizon_months: int,
        method_override: str | None = None,
) -> dict:
    series = prepare_monthly_series(monthly_agg, entity_id, entity_type)

    if series is None or len(series) < MIN_MONTHS_FOR_FORECAST:
        return _create_forecast_result(
            entity_id, entity_type,
            error=f"Insufficient data (need {MIN_MONTHS_FOR_FORECAST} months)"
        )

    method = method_override or select_forecast_method(series, product_type, cv)
    generator = FORECAST_GENERATORS.get(method, generate_forecast_moving_avg)

    try:
        forecast_df = generator(series, horizon_months)
        forecast_df["forecast"] = forecast_df["forecast"].clip(lower=0)
        forecast_df["lower_ci"] = forecast_df["lower_ci"].clip(lower=0)
        return _create_forecast_result(entity_id, entity_type, method, forecast_df)
    except Exception as e:
        logger.exception("Forecast generation failed for %s: %s", entity_id, e)
        return _create_forecast_result(entity_id, entity_type, method, error=str(e))


def batch_generate_forecasts(
        monthly_agg: pd.DataFrame,
        entities: list[dict],
        horizon_months: int,
        progress_callback: Callable[[int, int, str], None] | None = None,
        method_override: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    all_forecasts = []
    stats = {
        "total": len(entities),
        "success": 0,
        "failed": 0,
        "methods": {},
        "errors": [],
    }

    for i, entity in enumerate(entities):
        entity_id = entity["entity_id"]
        entity_type = entity.get("entity_type", "model")
        product_type = entity.get("product_type")
        cv = entity.get("cv")

        if progress_callback:
            progress_callback(i + 1, len(entities), entity_id)

        result = generate_internal_forecast(
            monthly_agg, entity_id, entity_type, product_type, cv, horizon_months,
            method_override=method_override
        )

        if result["success"]:
            stats["success"] += 1
            method = result["method_used"]
            stats["methods"][method] = stats["methods"].get(method, 0) + 1

            forecast_df = result["forecast_df"].copy()
            forecast_df["entity_id"] = entity_id
            forecast_df["entity_type"] = entity_type
            forecast_df["method"] = method
            all_forecasts.append(forecast_df)
        else:
            stats["failed"] += 1
            stats["errors"].append({"entity_id": entity_id, "error": result["error"]})

    if all_forecasts:
        combined_df = pd.concat(all_forecasts, ignore_index=True)
    else:
        combined_df = pd.DataFrame()

    return combined_df, stats


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None
