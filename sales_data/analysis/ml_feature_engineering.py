from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logging_config import get_logger

from .utils import find_column

logger = get_logger("ml_feature_engineering")

PRODUCT_TYPE_ENCODING = {
    "basic": 0,
    "regular": 1,
    "seasonal": 2,
    "new": 3,
}


def create_time_features(df: pd.DataFrame, date_col: str = "period") -> pd.DataFrame:
    result = df.copy()
    periods = pd.PeriodIndex(result[date_col])

    month_array = np.array([p.month for p in periods])
    quarter_array = np.array([p.quarter for p in periods])
    result["month"] = month_array
    result["quarter"] = quarter_array
    result["month_sin"] = np.sin(2 * np.pi * month_array / 12)
    result["month_cos"] = np.cos(2 * np.pi * month_array / 12)

    return result


def create_lag_features(
        series: pd.Series,
        lags: list[int] | None = None,
) -> pd.DataFrame:
    if lags is None:
        lags = [1, 2, 3, 6, 12]

    result = pd.DataFrame(index=series.index)

    for lag in lags:
        result[f"lag_{lag}"] = series.shift(lag)

    return result


def create_rolling_features(
        series: pd.Series,
        windows: list[int] | None = None,
) -> pd.DataFrame:
    if windows is None:
        windows = [3, 6, 12]

    result = pd.DataFrame(index=series.index)

    for window in windows:
        result[f"rolling_mean_{window}"] = series.rolling(window=window, min_periods=1).mean()
        result[f"rolling_std_{window}"] = series.rolling(window=window, min_periods=1).std().fillna(0)

    return result


def create_yoy_features(series: pd.Series) -> pd.DataFrame:
    result = pd.DataFrame(index=series.index)

    lag_12 = series.shift(12)
    result["yoy_diff"] = series - lag_12
    result["yoy_pct_change"] = series.pct_change(periods=12).replace([np.inf, -np.inf], 0).fillna(0)

    return result


def create_product_features(
        product_type: str | None = None,
        cv: float | None = None,
) -> dict[str, float]:
    return {
        "product_type_encoded": PRODUCT_TYPE_ENCODING.get(product_type, 1) if product_type else 1,
        "cv": cv if cv is not None else 0.5,
    }


def prepare_ml_features(
        monthly_agg: pd.DataFrame,
        entity_id: str,
        entity_type: str = "model",
        sku_stats: pd.DataFrame | None = None,
        lags: list[int] | None = None,
        rolling_windows: list[int] | None = None,
) -> tuple[pd.DataFrame, pd.Series] | tuple[None, None]:
    series = _prepare_series(monthly_agg, entity_id, entity_type)

    if series is None or len(series) < 12:
        return None, None

    product_type, cv = _get_entity_stats(sku_stats, entity_id, entity_type)

    features_df = _build_feature_dataframe(series, lags, rolling_windows)

    product_features = create_product_features(product_type, cv)
    for feat_name, feat_value in product_features.items():
        features_df[feat_name] = feat_value

    features_df = features_df.dropna()

    if features_df.empty:
        return None, None

    y = series.loc[features_df.index]
    x = features_df

    return x, y


def prepare_ml_features_for_prediction(
        series: pd.Series,
        horizon: int,
        product_type: str | None = None,
        cv: float | None = None,
        lags: list[int] | None = None,
        rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    if lags is None:
        lags = [1, 2, 3, 6, 12]
    if rolling_windows is None:
        rolling_windows = [3, 6, 12]

    last_period = pd.Period(series.index[-1], freq="M")
    next_period = last_period + 1  # type: ignore[operator]
    future_periods = pd.period_range(start=next_period, periods=horizon, freq="M")

    extended_series = series.copy()
    all_future_features = []

    for period in future_periods:
        features = _create_time_features_for_period(period)
        features.update(_create_lag_features_for_prediction(extended_series, lags))
        features.update(_create_rolling_features_for_prediction(extended_series, rolling_windows))
        features.update(_create_yoy_features_for_prediction(extended_series))
        features.update(create_product_features(product_type, cv))

        all_future_features.append(features)

        extended_series = pd.concat([
            extended_series,
            pd.Series([extended_series.iloc[-1]], index=[period])
        ])

    return pd.DataFrame(all_future_features, index=future_periods)


def _create_time_features_for_period(period: pd.Period) -> dict:
    return {
        "month": period.month,
        "quarter": period.quarter,
        "month_sin": np.sin(2 * np.pi * period.month / 12),
        "month_cos": np.cos(2 * np.pi * period.month / 12),
    }


def _create_lag_features_for_prediction(series: pd.Series, lags: list[int]) -> dict:
    features = {}
    series_len = len(series)

    for lag in lags:
        lag_idx = series_len - lag
        features[f"lag_{lag}"] = series.iloc[lag_idx] if lag_idx >= 0 else 0

    return features


def _create_rolling_features_for_prediction(series: pd.Series, windows: list[int]) -> dict:
    features = {}

    for window in windows:
        recent = series.tail(window)
        features[f"rolling_mean_{window}"] = recent.mean()
        features[f"rolling_std_{window}"] = recent.std() if len(recent) > 1 else 0

    return features


def _create_yoy_features_for_prediction(series: pd.Series) -> dict:
    if len(series) < 12:
        return {"yoy_diff": 0, "yoy_pct_change": 0}

    lag_12_val = series.iloc[-12]
    current_approx = series.iloc[-1]
    yoy_diff = current_approx - lag_12_val
    yoy_pct_change = yoy_diff / lag_12_val if lag_12_val != 0 else 0

    return {"yoy_diff": yoy_diff, "yoy_pct_change": yoy_pct_change}


def _prepare_series(
        monthly_agg: pd.DataFrame,
        entity_id: str,
        entity_type: str,
) -> pd.Series | None:
    if monthly_agg is None or monthly_agg.empty:
        return None

    id_col = find_column(monthly_agg, ["entity_id", "sku", "SKU", "model", "MODEL"])
    month_col = find_column(monthly_agg, ["year_month", "month", "MONTH"])
    qty_col = find_column(monthly_agg, ["total_quantity", "TOTAL_QUANTITY", "ilosc"])

    if id_col is None or month_col is None or qty_col is None:
        return None

    if entity_type == "model":
        monthly_agg = monthly_agg.copy()
        monthly_agg["_model"] = monthly_agg[id_col].astype(str).str[:5]
        entity_data = monthly_agg[monthly_agg["_model"] == entity_id]
        entity_data = entity_data.groupby(month_col, as_index=False, observed=True)[qty_col].sum()
    else:
        entity_data = monthly_agg[monthly_agg[id_col] == entity_id]

    entity_data = pd.DataFrame(entity_data)
    if entity_data.empty:
        return None

    entity_data = pd.DataFrame(entity_data.sort_values(by=str(month_col)))
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


def _get_entity_stats(
        sku_stats: pd.DataFrame | None,
        entity_id: str,
        entity_type: str,
) -> tuple[str | None, float | None]:
    if sku_stats is None or sku_stats.empty:
        return None, None

    id_col = "MODEL" if entity_type == "model" else "SKU"
    if id_col not in sku_stats.columns:
        id_col = find_column(sku_stats, ["MODEL", "SKU", "model", "sku", "entity_id"])

    if id_col is None:
        return None, None

    entity_stats = sku_stats[sku_stats[id_col] == entity_id]
    if entity_stats.empty:
        return None, None

    row = entity_stats.iloc[0]

    type_col = find_column(sku_stats, ["TYPE", "type", "product_type"])
    cv_col = find_column(sku_stats, ["CV", "cv"])

    product_type = row[type_col] if type_col else None
    cv = row[cv_col] if cv_col else None

    return product_type, cv


def _build_feature_dataframe(
        series: pd.Series,
        lags: list[int] | None = None,
        rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    if lags is None:
        lags = [1, 2, 3, 6, 12]
    if rolling_windows is None:
        rolling_windows = [3, 6, 12]

    base_df = pd.DataFrame({"value": series}, index=series.index)
    base_df["period"] = base_df.index

    time_features = create_time_features(base_df, "period")
    lag_features = create_lag_features(series, lags)
    rolling_features = create_rolling_features(series, rolling_windows)
    yoy_features = create_yoy_features(series)

    features_df = pd.concat([
        time_features[["month", "quarter", "month_sin", "month_cos"]],
        lag_features,
        rolling_features,
        yoy_features,
    ], axis=1)

    return features_df
