from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import numpy as np
import pandas as pd

from sales_data.analysis.ml_feature_engineering import (
    prepare_ml_features,
    prepare_ml_features_for_prediction,
    _prepare_series,
)
from sales_data.analysis.ml_model_selection import (
    get_available_ml_models,
    select_best_model,
)
from utils.logging_config import get_logger

logger = get_logger("ml_forecast")

ML_MIN_MONTHS = 12
ML_MIN_MONTHS_SEASONAL = 24


def train_ml_model(
        monthly_agg: pd.DataFrame,
        entity_id: str,
        entity_type: str = "model",
        model_type: str | None = None,
        sku_stats: pd.DataFrame | None = None,
        models_to_evaluate: list[str] | None = None,
        include_statistical: bool = True,
        cv_splits: int = 3,
        cv_test_size: int = 3,
        cv_metric: str = "mape",
) -> dict:
    result = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "model_type": None,
        "trained_model": None,
        "cv_score": None,
        "cv_details": None,
        "feature_names": None,
        "feature_importance": None,
        "trained_at": datetime.now().isoformat(),
        "success": False,
        "error": None,
    }

    x, y = prepare_ml_features(monthly_agg, entity_id, entity_type, sku_stats)

    if x is None or y is None:
        result["error"] = f"Insufficient data for entity {entity_id}"
        return result

    if len(x) < ML_MIN_MONTHS:
        result["error"] = f"Need at least {ML_MIN_MONTHS} months of data, got {len(x)}"
        return result

    series = _prepare_series(monthly_agg, entity_id, entity_type)

    product_type, cv = _get_entity_stats_from_df(sku_stats, entity_id, entity_type)

    if model_type and model_type != "auto":
        available_models = get_available_ml_models()

        if model_type in available_models:
            config = available_models[model_type]
            trained_model = config.model_class(**config.params)
            trained_model.fit(x, y)

            result["model_type"] = model_type
            result["trained_model"] = trained_model
            result["cv_score"] = None
            result["feature_names"] = list(x.columns)
            result["feature_importance"] = _get_feature_importance(trained_model, x.columns)
            result["success"] = True
            result["product_type"] = product_type
            result["cv"] = cv
            return result

        elif model_type in ["exp_smoothing", "holt_winters", "sarima"]:
            result["model_type"] = model_type
            result["trained_model"] = None
            result["success"] = True
            result["product_type"] = product_type
            result["cv"] = cv
            return result

        else:
            result["error"] = f"Unknown model type: {model_type}"
            return result

    selection_result = select_best_model(
        x, y,
        series=series,
        models_to_evaluate=models_to_evaluate,
        metric=cv_metric,
        n_splits=cv_splits,
        test_size=cv_test_size,
        include_statistical=include_statistical,
    )

    best_model_name = selection_result["best_model"]

    if best_model_name is None:
        result["error"] = "No suitable model found"
        result["cv_details"] = selection_result["all_results"]
        return result

    result["model_type"] = best_model_name
    result["cv_score"] = selection_result["best_score"]
    result["cv_details"] = selection_result["all_results"]
    result["product_type"] = product_type
    result["cv"] = cv

    available_models = get_available_ml_models()

    if best_model_name in available_models:
        config = available_models[best_model_name]
        trained_model = config.model_class(**config.params)
        trained_model.fit(x, y)

        result["trained_model"] = trained_model
        result["feature_names"] = list(x.columns)
        result["feature_importance"] = _get_feature_importance(trained_model, x.columns)
    else:
        result["trained_model"] = None

    result["success"] = True
    return result


def generate_ml_forecast(
        monthly_agg: pd.DataFrame,
        entity_id: str,
        trained_model_info: dict,
        horizon_months: int = 3,
) -> dict:
    result = {
        "entity_id": entity_id,
        "forecast_df": None,
        "success": False,
        "error": None,
    }

    if not trained_model_info.get("success"):
        result["error"] = "Model training was not successful"
        return result

    model_type = trained_model_info["model_type"]
    entity_type = trained_model_info.get("entity_type", "model")

    series = _prepare_series(monthly_agg, entity_id, entity_type)

    if series is None:
        result["error"] = "Could not prepare time series"
        return result

    product_type = trained_model_info.get("product_type")
    cv = trained_model_info.get("cv")

    if model_type in ["exp_smoothing", "holt_winters", "sarima"]:
        forecast_df = _generate_statistical_forecast(series, model_type, horizon_months)
    else:
        trained_model = trained_model_info.get("trained_model")
        if trained_model is None:
            result["error"] = "No trained ML model found"
            return result

        forecast_df = _generate_ml_predictions(
            series, trained_model, horizon_months, product_type, cv
        )

    if forecast_df is not None:
        forecast_df["forecast"] = forecast_df["forecast"].clip(lower=0)
        forecast_df["lower_ci"] = forecast_df["lower_ci"].clip(lower=0)

    result["forecast_df"] = forecast_df
    result["success"] = forecast_df is not None
    return result


def batch_train_and_forecast(
        monthly_agg: pd.DataFrame,
        entities: list[dict],
        horizon_months: int = 3,
        models_to_evaluate: list[str] | None = None,
        include_statistical: bool = True,
        cv_splits: int = 3,
        cv_test_size: int = 3,
        cv_metric: str = "mape",
        sku_stats: pd.DataFrame | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
) -> tuple[pd.DataFrame, dict, dict]:
    all_forecasts = []
    trained_models = {}
    stats: dict[str, Any] = {
        "total": len(entities),
        "success": 0,
        "failed": 0,
        "model_distribution": {},
        "avg_cv_score": 0.0,
        "errors": [],
    }

    cv_scores = []

    for i, entity in enumerate(entities):
        entity_id = entity["entity_id"]
        entity_type = entity.get("entity_type", "model")

        if progress_callback:
            progress_callback(i + 1, len(entities), entity_id)

        train_result = train_ml_model(
            monthly_agg,
            entity_id,
            entity_type,
            model_type=None,
            sku_stats=sku_stats,
            models_to_evaluate=models_to_evaluate,
            include_statistical=include_statistical,
            cv_splits=cv_splits,
            cv_test_size=cv_test_size,
            cv_metric=cv_metric,
        )

        if not train_result["success"]:
            stats["failed"] += 1
            stats["errors"].append({
                "entity_id": entity_id,
                "phase": "training",
                "error": train_result["error"],
            })
            continue

        trained_models[entity_id] = train_result

        forecast_result = generate_ml_forecast(
            monthly_agg,
            entity_id,
            train_result,
            horizon_months,
        )

        if not forecast_result["success"]:
            stats["failed"] += 1
            stats["errors"].append({
                "entity_id": entity_id,
                "phase": "forecasting",
                "error": forecast_result["error"],
            })
            continue

        stats["success"] += 1

        model_type = train_result["model_type"]
        stats["model_distribution"][model_type] = stats["model_distribution"].get(model_type, 0) + 1

        if train_result["cv_score"] is not None:
            cv_scores.append(train_result["cv_score"])

        forecast_df = forecast_result["forecast_df"].copy()
        forecast_df["entity_id"] = entity_id
        forecast_df["entity_type"] = entity_type
        forecast_df["model_type"] = model_type
        forecast_df["cv_score"] = train_result["cv_score"]
        all_forecasts.append(forecast_df)

    if cv_scores:
        stats["avg_cv_score"] = float(np.mean(cv_scores))

    if all_forecasts:
        combined_df = pd.concat(all_forecasts, ignore_index=True)
    else:
        combined_df = pd.DataFrame()

    return combined_df, stats, trained_models


def calculate_prediction_intervals(
        model: Any,
        x_future: pd.DataFrame,
        predictions: np.ndarray,
        confidence: float = 0.95,
) -> tuple[np.ndarray, np.ndarray]:
    try:
        if hasattr(model, "estimators_"):
            tree_predictions = np.array([tree.predict(x_future) for tree in model.estimators_])
            lower = np.percentile(tree_predictions, (1 - confidence) / 2 * 100, axis=0)
            upper = np.percentile(tree_predictions, (1 + confidence) / 2 * 100, axis=0)
            return lower, upper
    except (ValueError, AttributeError, TypeError):
        pass

    if predictions.size > 1:
        std_estimate = float(np.std(predictions))
    else:
        std_estimate = float(np.mean(predictions)) * 0.2
    z_score = 1.96
    lower = predictions - z_score * std_estimate
    upper = predictions + z_score * std_estimate

    return lower, upper


def _generate_ml_predictions(
        series: pd.Series,
        model: Any,
        horizon: int,
        product_type: str | None = None,
        cv: float | None = None,
) -> pd.DataFrame:
    x_future = prepare_ml_features_for_prediction(
        series, horizon, product_type, cv
    )

    predictions = model.predict(x_future)

    lower, upper = calculate_prediction_intervals(model, x_future, predictions)

    last_period = series.index[-1]
    future_periods = pd.period_range(start=last_period + 1, periods=horizon, freq="M")

    return pd.DataFrame({
        "period": future_periods,
        "forecast": predictions,
        "lower_ci": lower,
        "upper_ci": upper,
    })


def _generate_statistical_forecast(
        series: pd.Series,
        method: str,
        horizon: int,
) -> pd.DataFrame | None:
    from sales_data.analysis.internal_forecast import (
        generate_forecast_exp_smoothing,
        generate_forecast_holt_winters,
        generate_forecast_sarima,
    )

    try:
        if method == "exp_smoothing":
            return generate_forecast_exp_smoothing(series, horizon)
        elif method == "holt_winters":
            return generate_forecast_holt_winters(series, horizon)
        elif method == "sarima":
            return generate_forecast_sarima(series, horizon)
        else:
            return generate_forecast_exp_smoothing(series, horizon)
    except Exception as e:
        logger.warning("Statistical forecast failed: %s", e)
        return None


def _get_feature_importance(model: Any, feature_names: pd.Index) -> dict[str, float] | None:
    try:
        if hasattr(model, "feature_importances_"):
            importance = model.feature_importances_
            return dict(zip(feature_names, importance))
        elif hasattr(model, "coef_"):
            coef = np.abs(model.coef_)
            return dict(zip(feature_names, coef))
    except (ValueError, AttributeError, TypeError):
        pass
    return None


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _get_entity_stats_from_df(
        sku_stats: pd.DataFrame | None,
        entity_id: str,
        entity_type: str,
) -> tuple[str | None, float | None]:
    if sku_stats is None or sku_stats.empty:
        return None, None

    id_col = "MODEL" if entity_type == "model" else "SKU"
    if id_col not in sku_stats.columns:
        id_col = _find_column(sku_stats, ["MODEL", "SKU", "model", "sku", "entity_id"])
        if id_col is None:
            return None, None

    entity_stats = sku_stats[sku_stats[id_col] == entity_id]
    if entity_stats.empty:
        return None, None

    row = entity_stats.iloc[0]

    type_col = _find_column(sku_stats, ["TYPE", "type", "product_type"])
    product_type = row[type_col] if type_col else None

    cv_col = _find_column(sku_stats, ["CV", "cv"])
    cv = row[cv_col] if cv_col else None

    return product_type, cv
