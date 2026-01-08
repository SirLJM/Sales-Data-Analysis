from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sales_data.analysis.forecast_accuracy import (
    aggregate_accuracy_by_product_type,
    calculate_accuracy_trend,
    calculate_forecast_accuracy,
    get_overall_metrics,
)
from ui.constants import Config, Icons, MimeTypes
from ui.i18n import Keys, t
from ui.shared.forecast_accuracy_loader import (
    get_date_range_from_sales,
    load_forecast_for_accuracy,
    load_sales_for_accuracy,
    load_stock_history_for_accuracy,
)
from ui.shared.session_manager import get_settings
from utils.logging_config import get_logger

logger = get_logger("tab_forecast_accuracy")

ACCURACY_DATA_KEY = "forecast_accuracy_data"
ACCURACY_PARAMS_KEY = "forecast_accuracy_params"


def render(context: dict) -> None:
    try:
        _render_content(context)
    except Exception as e:
        logger.exception("Error in Forecast Accuracy")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_FORECAST_ACCURACY).format(error=str(e))}")


def _render_content(context: dict) -> None:
    st.title(t(Keys.TITLE_FORECAST_ACCURACY))
    st.caption(t(Keys.CAPTION_FORECAST_ACCURACY))

    params = _render_parameter_controls()

    if params is None:
        return

    col_gen, col_clear = st.columns([1, 1])
    with col_gen:
        generate_clicked = st.button(t(Keys.BTN_GENERATE_ACCURACY_REPORT), type="primary")
    with col_clear:
        if st.button(t(Keys.BTN_CLEAR_RESULTS)):
            if ACCURACY_DATA_KEY in st.session_state:
                del st.session_state[ACCURACY_DATA_KEY]
            st.rerun()

    if generate_clicked:
        _generate_accuracy_report(params, context)

    if ACCURACY_DATA_KEY in st.session_state and st.session_state[ACCURACY_DATA_KEY] is not None:
        saved_params = st.session_state[ACCURACY_DATA_KEY].get("params", params)
        _display_results(st.session_state[ACCURACY_DATA_KEY], saved_params)


def _render_parameter_controls() -> dict | None:
    settings = get_settings()
    lead_time = settings.get("lead_time", 1.36)

    min_date, max_date = get_date_range_from_sales()

    if min_date is None or max_date is None:
        st.warning(f"{Icons.WARNING} {t(Keys.MSG_NO_SALES_DATA_LOAD)}")
        return None

    with st.expander(t(Keys.ANALYSIS_PARAMETERS), expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            default_end = max_date
            default_start = default_end - timedelta(days=90)
            if default_start < min_date:
                default_start = min_date

            analysis_start = st.date_input(
                t(Keys.ANALYSIS_START_DATE),
                value=default_start,
                min_value=min_date.date(),
                max_value=max_date.date(),
                help=t(Keys.HELP_ANALYSIS_START),
            )

        with col2:
            analysis_end = st.date_input(
                t(Keys.ANALYSIS_END_DATE),
                value=default_end,
                min_value=min_date.date(),
                max_value=max_date.date(),
                help=t(Keys.HELP_ANALYSIS_END),
            )

        col3, col4 = st.columns(2)

        with col3:
            lookback_months = st.number_input(
                t(Keys.FORECAST_LOOKBACK),
                min_value=1,
                max_value=12,
                value=4,
                help=t(Keys.HELP_FORECAST_LOOKBACK),
            )

        with col4:
            entity_type = st.radio(
                t(Keys.VIEW_LEVEL),
                options=["sku", "model"],
                format_func=lambda x: t(Keys.SKU_LEVEL) if x == "sku" else t(Keys.MODEL_LEVEL),
                horizontal=True,
            )

        analysis_start_dt = datetime.combine(analysis_start, datetime.min.time())
        analysis_end_dt = datetime.combine(analysis_end, datetime.max.time())

        days_diff = (analysis_end_dt - analysis_start_dt).days
        min_days = int(lead_time * 30.44)

        if days_diff < min_days:
            st.error(
                f"{Icons.ERROR} {t(Keys.ERR_ANALYSIS_PERIOD_TOO_SHORT).format(days=days_diff, min_days=min_days, lead_time=lead_time)}"
            )
            return None

        forecast_date = (analysis_start_dt - timedelta(days=int(lookback_months * 30.44))).strftime('%Y-%m-%d')
        st.info(t(Keys.INFO_ANALYSIS_PERIOD).format(days=days_diff, date=forecast_date))

    return {
        "analysis_start": analysis_start_dt,
        "analysis_end": analysis_end_dt,
        "lookback_months": lookback_months,
        "entity_type": entity_type,
    }


def _generate_accuracy_report(params: dict, context: dict) -> None:
    # noinspection PyTypeChecker
    with st.spinner(t(Keys.LOADING_ACCURACY_METRICS)):
        sales_df = load_sales_for_accuracy(params["analysis_start"], params["analysis_end"])
        if sales_df is None or sales_df.empty:
            st.error(f"{Icons.ERROR} {t(Keys.ERR_NO_SALES_FOR_PERIOD)}")
            return

        forecast_df, forecast_date = load_forecast_for_accuracy(
            params["analysis_start"], params["lookback_months"]
        )
        if forecast_df is None or forecast_df.empty:
            st.error(
                f"{Icons.ERROR} {t(Keys.ERR_NO_FORECAST_FOUND).format(months=params['lookback_months'], date=params['analysis_start'].strftime('%Y-%m-%d'))}"
            )
            return

        stock_df = load_stock_history_for_accuracy(params["analysis_start"], params["analysis_end"])
        if stock_df is None or stock_df.empty:
            st.warning(f"{Icons.WARNING} {t(Keys.WARN_NO_STOCK_HISTORY)}")
            stock_df = pd.DataFrame()

        accuracy_df = calculate_forecast_accuracy(
            sales_df,
            forecast_df,
            stock_df,
            params["analysis_start"],
            params["analysis_end"],
            params["entity_type"],
        )

        if accuracy_df.empty:
            st.error(f"{Icons.ERROR} {t(Keys.ERR_ACCURACY_CALCULATION)}")
            return

        sku_summary = context.get("summary")
        type_summary = pd.DataFrame()
        if sku_summary is not None and not sku_summary.empty:
            type_summary = aggregate_accuracy_by_product_type(
                accuracy_df, sku_summary, params["entity_type"]
            )

        trend_df = calculate_accuracy_trend(
            sales_df,
            forecast_df,
            stock_df,
            params["analysis_start"],
            params["analysis_end"],
            params["entity_type"],
            period="week",
        )

        st.session_state[ACCURACY_DATA_KEY] = {
            "accuracy_df": accuracy_df,
            "type_summary": type_summary,
            "trend_df": trend_df,
            "forecast_date": forecast_date,
            "params": params,
        }

        st.success(f"{Icons.SUCCESS} {t(Keys.MSG_ACCURACY_SUCCESS)}")


def _display_results(data: dict, params: dict) -> None:
    accuracy_df = data["accuracy_df"]
    type_summary = data["type_summary"]
    trend_df = data["trend_df"]
    forecast_date = data["forecast_date"]

    if forecast_date:
        st.info(t(Keys.INFO_USING_FORECAST).format(date=forecast_date.strftime('%Y-%m-%d')))

    _render_summary_metrics(accuracy_df)

    st.markdown("---")
    _render_accuracy_table(accuracy_df, params["entity_type"])

    if not type_summary.empty:
        st.markdown("---")
        _render_type_comparison(type_summary)

    if not trend_df.empty:
        st.markdown("---")
        _render_trend_chart(trend_df)

    st.markdown("---")
    _render_detail_view(data, params)


def _render_summary_metrics(accuracy_df: pd.DataFrame) -> None:
    st.subheader(t(Keys.OVERALL_ACCURACY_METRICS))

    metrics = get_overall_metrics(accuracy_df)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mape_val = f"{metrics['mape']:.1f}%" if metrics['mape'] is not None else t(Keys.NA)
        color = _get_mape_color(metrics['mape'])
        st.metric(t(Keys.METRIC_MAPE), mape_val, help=t(Keys.MAPE_HELP))
        if metrics['mape'] is not None:
            st.caption(f"{color} {_get_mape_label(metrics['mape'])}")

    with col2:
        bias_val = f"{metrics['bias']:+.1f}%" if metrics['bias'] is not None else t(Keys.NA)
        st.metric(t(Keys.METRIC_BIAS), bias_val, help=t(Keys.BIAS_HELP))
        if metrics['bias'] is not None:
            direction = t(Keys.OVER_FORECASTING) if metrics['bias'] > 0 else t(Keys.UNDER_FORECASTING)
            st.caption(direction)

    with col3:
        st.metric(
            t(Keys.METRIC_MISSED_OPPORTUNITY),
            f"{metrics['total_missed_opportunity']:,}",
            help=t(Keys.MISSED_OPP_HELP),
        )
        st.caption(t(Keys.STOCKOUT_DAYS).format(days=metrics['total_days_stockout']))

    with col4:
        if metrics['total_actual'] > 0:
            accuracy_pct = (1 - abs(metrics['total_forecast'] - metrics['total_actual']) / metrics[
                'total_actual']) * 100
            accuracy_pct = max(0, accuracy_pct)
        else:
            accuracy_pct = 0
        st.metric(
            t(Keys.METRIC_VOLUME_ACCURACY),
            f"{accuracy_pct:.1f}%",
            help=t(Keys.VOLUME_ACC_HELP),
        )
        st.caption(t(Keys.FCST_VS_ACT).format(forecast=metrics['total_forecast'], actual=metrics['total_actual']))


def _get_mape_color(mape: float | None) -> str:
    if mape is None:
        return ""
    if mape < 20:
        return "🟢"
    elif mape < 40:
        return "🟡"
    else:
        return "🔴"


def _get_mape_label(mape: float | None) -> str:
    if mape is None:
        return ""
    if mape < 20:
        return t(Keys.GOOD)
    elif mape < 40:
        return t(Keys.ACCEPTABLE)
    else:
        return t(Keys.POOR)


def _render_accuracy_table(accuracy_df: pd.DataFrame, entity_type: str) -> None:
    st.subheader(t(Keys.ACCURACY_BY_ITEM))

    id_col = "MODEL" if entity_type == "model" else "SKU"

    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input(
            t(Keys.SEARCH_ENTITY).format(entity=id_col),
            placeholder=t(Keys.SEARCH_ENTITY_PLACEHOLDER).format(entity=id_col),
            key="accuracy_search",
        )
    with col2:
        sort_by = st.selectbox(
            t(Keys.SORT_BY),
            options=["MAPE", "BIAS", "MISSED_OPPORTUNITY", "ACTUAL_TOTAL"],
            index=0,
        )

    display_df = accuracy_df.copy()

    if search_term:
        display_df = display_df[
            display_df[id_col].astype(str).str.contains(search_term, case=False, na=False)
        ]

    if sort_by in display_df.columns:
        ascending = sort_by not in ["MISSED_OPPORTUNITY", "ACTUAL_TOTAL"]
        display_df = display_df.sort_values(sort_by, ascending=ascending, na_position="last")

    display_df["MAPE_COLOR"] = display_df["MAPE"].apply(_get_mape_color)

    st.write(t(Keys.SHOWING_N_OF_M_ITEMS).format(n=len(display_df), m=len(accuracy_df)))

    from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
    render_dataframe_with_aggrid(
        display_df,
        height=min(Config.DATAFRAME_HEIGHT, len(display_df) * 35 + 38),
        pinned_columns=[id_col],
    )

    st.download_button(
        t(Keys.DOWNLOAD_ACCURACY_REPORT),
        accuracy_df.to_csv(index=False),
        f"forecast_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        MimeTypes.TEXT_CSV,
    )


def _render_type_comparison(type_summary: pd.DataFrame) -> None:
    st.subheader(t(Keys.ACCURACY_BY_PRODUCT_TYPE))

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.bar(
            type_summary,
            x="TYPE",
            y="MAPE",
            color="TYPE",
            title=t(Keys.MAPE_BY_PRODUCT_TYPE),
            color_discrete_map={
                "basic": "#00cc00",
                "regular": "#0066cc",
                "seasonal": "#ff9900",
                "new": "#cc0066",
                "unknown": "#999999",
            },
        )
        fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text=f"{t(Keys.GOOD)} (<20%)")
        fig.add_hline(y=40, line_dash="dash", line_color="orange", annotation_text=f"{t(Keys.ACCEPTABLE)} (<40%)")
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, width='stretch')

    with col2:
        from ui.shared.aggrid_helpers import render_dataframe_with_aggrid
        render_dataframe_with_aggrid(
            type_summary[["TYPE", "COUNT", "MAPE", "BIAS", "MISSED_OPPORTUNITY"]],
            max_height=300,
            pinned_columns=["TYPE"],
        )


def _render_trend_chart(trend_df: pd.DataFrame) -> None:
    st.subheader(t(Keys.ACCURACY_TREND_OVER_TIME))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend_df["period"],
        y=trend_df["MAPE"],
        mode="lines+markers",
        name="MAPE",
        line={"color": "blue", "width": 2},
    ))

    fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text=t(Keys.GOOD))
    fig.add_hline(y=40, line_dash="dash", line_color="orange", annotation_text=t(Keys.ACCEPTABLE))

    fig.update_layout(
        title=t(Keys.TREND_CHART),
        xaxis_title=t(Keys.CHART_WEEK),
        yaxis_title=t(Keys.CHART_MAPE_PCT),
        height=400,
        hovermode="x unified",
    )

    st.plotly_chart(fig, width='stretch')


def _render_detail_view(data: dict, params: dict) -> None:
    with st.expander(t(Keys.ITEM_DETAIL_VIEW), expanded=False):
        accuracy_df = data["accuracy_df"]
        entity_type = params["entity_type"]
        id_col = "MODEL" if entity_type == "model" else "SKU"

        selected_item = st.selectbox(
            t(Keys.SELECT_ENTITY_DETAILS).format(entity=id_col),
            options=accuracy_df[id_col].tolist(),
            key="detail_item_select",
        )

        if selected_item:
            item_row = accuracy_df[accuracy_df[id_col] == selected_item].iloc[0]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(t(Keys.METRIC_MAPE), f"{item_row['MAPE']:.1f}%" if pd.notna(item_row['MAPE']) else t(Keys.NA))
            with col2:
                st.metric(t(Keys.METRIC_BIAS), f"{item_row['BIAS']:+.1f}%" if pd.notna(item_row['BIAS']) else t(Keys.NA))
            with col3:
                st.metric(t(Keys.DAYS_ANALYZED), int(item_row['DAYS_ANALYZED']))
            with col4:
                st.metric(t(Keys.DAYS_STOCKOUT), int(item_row['DAYS_STOCKOUT']))

            col5, col6 = st.columns(2)
            with col5:
                st.metric(t(Keys.FORECAST_TOTAL), f"{int(item_row['FORECAST_TOTAL']):,}")
            with col6:
                st.metric(t(Keys.ACTUAL_TOTAL), f"{int(item_row['ACTUAL_TOTAL']):,}")

            if item_row['MISSED_OPPORTUNITY'] > 0:
                st.warning(
                    f"{Icons.WARNING} {t(Keys.WARN_MISSED_OPPORTUNITY).format(units=int(item_row['MISSED_OPPORTUNITY']), days=int(item_row['DAYS_STOCKOUT']))}"
                )
