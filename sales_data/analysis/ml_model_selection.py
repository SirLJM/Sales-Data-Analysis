from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from utils.logging_config import get_logger

logger = get_logger("ml_model_selection")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    lgb = None
    LIGHTGBM_AVAILABLE = False

SKLEARN_AVAILABLE = False
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import Ridge, Lasso
    SKLEARN_AVAILABLE = True
except ImportError:
    RandomForestRegressor = None
    Ridge = None
    Lasso = None


@dataclass
class ModelConfig:
    name: str
    model_class: Any
    params: dict
    min_samples: int


def get_available_ml_models() -> dict[str, ModelConfig]:
    models = {}

    if LIGHTGBM_AVAILABLE and lgb is not None:
        models["lightgbm"] = ModelConfig(
            name="LightGBM",
            model_class=getattr(lgb, "LGBMRegressor"),
            params={
                "n_estimators": 100,
                "max_depth": 5,
                "learning_rate": 0.1,
                "num_leaves": 31,
                "min_child_samples": 5,
                "random_state": 42,
                "verbose": -1,
            },
            min_samples=24,
        )

    if SKLEARN_AVAILABLE:
        models["random_forest"] = ModelConfig(
            name="RandomForest",
            model_class=RandomForestRegressor,
            params={
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
                "random_state": 42,
                "n_jobs": -1,
            },
            min_samples=24,
        )

        models["ridge"] = ModelConfig(
            name="Ridge",
            model_class=Ridge,
            params={
                "alpha": 1.0,
            },
            min_samples=12,
        )

        models["lasso"] = ModelConfig(
            name="Lasso",
            model_class=Lasso,
            params={
                "alpha": 0.1,
                "max_iter": 1000,
            },
            min_samples=12,
        )

    return models


def time_series_cross_validate(
        x: pd.DataFrame,
        y: pd.Series,
        model: Any,
        n_splits: int = 3,
        test_size: int = 3,
        metric: str = "mape",
) -> dict:
    n_samples = len(x)
    min_train_size = max(12, n_samples - n_splits * test_size - test_size)

    if n_samples < min_train_size + test_size:
        return {
            "scores": [],
            "mean_score": float("inf"),
            "std_score": 0,
            "success": False,
            "error": "Insufficient samples for cross-validation",
        }

    scores = []
    fold_details = []

    for fold in range(n_splits):
        test_end = n_samples - fold * test_size
        test_start = test_end - test_size
        train_end = test_start

        if train_end < min_train_size:
            break

        x_train = x.iloc[:train_end]
        y_train = y.iloc[:train_end]
        x_test = x.iloc[test_start:test_end]
        y_test = y.iloc[test_start:test_end]

        try:
            model_instance = model.__class__(**model.get_params())
            model_instance.fit(x_train, y_train)
            predictions = model_instance.predict(x_test)

            score = _calculate_metric(y_test.values, predictions, metric)
            scores.append(score)

            fold_details.append({
                "fold": fold + 1,
                "train_size": len(x_train),
                "test_size": len(x_test),
                "score": score,
            })

        except Exception as e:
            logger.warning("CV fold %d failed: %s", fold + 1, e)
            continue

    if not scores:
        return {
            "scores": [],
            "mean_score": float("inf"),
            "std_score": 0,
            "success": False,
            "error": "All CV folds failed",
        }

    return {
        "scores": scores,
        "mean_score": np.mean(scores),
        "std_score": np.std(scores),
        "fold_details": fold_details,
        "success": True,
        "error": None,
    }


def evaluate_statistical_methods(
        series: pd.Series,
        n_splits: int = 3,
        test_size: int = 3,
        metric: str = "mape",
) -> dict[str, dict]:
    from sales_data.analysis.internal_forecast import (
        generate_forecast_exp_smoothing,
        generate_forecast_holt_winters,
        generate_forecast_sarima,
    )

    results = {}
    n_samples = len(series)
    min_train_size = max(12, n_samples - n_splits * test_size - test_size)

    methods = {
        "exp_smoothing": generate_forecast_exp_smoothing,
        "holt_winters": generate_forecast_holt_winters,
        "sarima": generate_forecast_sarima,
    }

    for method_name, forecast_func in methods.items():
        scores = []

        for fold in range(n_splits):
            test_end = n_samples - fold * test_size
            test_start = test_end - test_size
            train_end = test_start

            if train_end < min_train_size:
                break

            train_series = series.iloc[:train_end]
            test_series = series.iloc[test_start:test_end]

            try:
                forecast_df = forecast_func(train_series, horizon=test_size)
                predictions = forecast_df["forecast"].values

                score = _calculate_metric(test_series.values, predictions, metric)
                scores.append(score)

            except Exception as e:
                logger.warning("Statistical method %s fold %d failed: %s", method_name, fold + 1, e)
                continue

        if scores:
            results[method_name] = {
                "scores": scores,
                "mean_score": np.mean(scores),
                "std_score": np.std(scores),
                "success": True,
                "model_type": "statistical",
            }
        else:
            results[method_name] = {
                "scores": [],
                "mean_score": float("inf"),
                "std_score": 0,
                "success": False,
                "model_type": "statistical",
            }

    return results


def select_best_model(
        x: pd.DataFrame,
        y: pd.Series,
        series: pd.Series | None = None,
        models_to_evaluate: list[str] | None = None,
        metric: str = "mape",
        n_splits: int = 3,
        test_size: int = 3,
        include_statistical: bool = True,
) -> dict:
    available_models = get_available_ml_models()

    if models_to_evaluate is None:
        models_to_evaluate = list(available_models.keys())

    all_results = {}

    for model_name in models_to_evaluate:
        if model_name not in available_models:
            continue

        config = available_models[model_name]

        if len(x) < config.min_samples:
            logger.info("Skipping %s: insufficient samples (%d < %d)", model_name, len(x), config.min_samples)
            continue

        try:
            model = config.model_class(**config.params)
            cv_result = time_series_cross_validate(
                x, y, model, n_splits=n_splits, test_size=test_size, metric=metric
            )

            all_results[model_name] = {
                **cv_result,
                "model_type": "ml",
                "config": config,
            }

        except Exception as e:
            logger.warning("Failed to evaluate %s: %s", model_name, e)
            all_results[model_name] = {
                "scores": [],
                "mean_score": float("inf"),
                "std_score": 0,
                "success": False,
                "error": str(e),
                "model_type": "ml",
            }

    if include_statistical and series is not None:
        statistical_results = evaluate_statistical_methods(
            series, n_splits=n_splits, test_size=test_size, metric=metric
        )
        all_results.update(statistical_results)

    best_model = None
    best_score = float("inf")

    for model_name, result in all_results.items():
        if result.get("success") and result["mean_score"] < best_score:
            best_score = result["mean_score"]
            best_model = model_name

    return {
        "best_model": best_model,
        "best_score": best_score,
        "all_results": all_results,
    }


def _calculate_metric(y_true: np.ndarray, y_pred: np.ndarray, metric: str) -> float:
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    y_pred = np.maximum(y_pred, 0)

    if metric == "mape":
        mask = y_true != 0
        if not mask.any():
            return float("inf")
        return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

    elif metric == "mae":
        return float(np.mean(np.abs(y_true - y_pred)))

    elif metric == "rmse":
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    elif metric == "smape":
        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
        mask = denominator != 0
        if not mask.any():
            return float("inf")
        return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100)

    else:
        return float(np.mean(np.abs(y_true - y_pred)))
