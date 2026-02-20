from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from ui.constants import Config, Icons
from ui.i18n import Keys, t
from utils.hpgl_parser import (
    HpglDocument,
    PatternPiece,
    parse_filename,
    parse_hpgl,
    serialize_to_hpgl,
)
from utils.logging_config import get_logger

logger = get_logger("tab_marker_viewer")

PIECE_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5",
]


@st.fragment
def render(_context: dict[str, object] | None = None) -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Marker Viewer")
        st.error(f"{Icons.ERROR} {t(Keys.ERR_MARKER_VIEWER).format(error=str(e))}")


def _render_content() -> None:
    st.title(t(Keys.HPGL_TITLE))

    uploaded = st.file_uploader(
        t(Keys.HPGL_UPLOAD_LABEL),
        type=["plt"],
        key="marker_viewer_uploader",
    )

    if uploaded is not None:
        content = uploaded.getvalue().decode("utf-8", errors="replace")
        doc = _parse_uploaded_file(content, uploaded.name)
        _render_file_info(doc)
        _render_marker_chart(doc)
        _render_export(doc)


@st.cache_data
def _parse_uploaded_file(content: str, filename: str) -> HpglDocument:
    return parse_hpgl(content, filename)


def _render_file_info(doc: HpglDocument) -> None:
    meta = parse_filename(doc.filename)

    fields = [
        (t(Keys.HPGL_MODEL), meta.get("model", "—")),
        (t(Keys.HPGL_PRODUCT_TYPE), meta.get("product_type", "—")),
        (t(Keys.HPGL_SIZE_RUN), meta.get("size_run", "—")),
        (t(Keys.HPGL_MATERIAL), meta.get("material", "—")),
        (t(Keys.HPGL_PIECES), str(len(doc.pieces))),
        (t(Keys.HPGL_DIMENSIONS), f"{doc.width_mm / 10:.0f} x {doc.height_mm / 10:.0f} cm"),
    ]

    for label, value in fields:
        st.markdown(f"**{label}:** {value}", unsafe_allow_html=False)


def _build_piece_coords(piece: PatternPiece) -> tuple[list[float | None], list[float | None]]:
    xs: list[float | None] = []
    ys: list[float | None] = []
    for seg in piece.segments:
        xs.append(float(seg.start.x))
        ys.append(float(seg.start.y))
        for pt in seg.points:
            xs.append(float(pt.x))
            ys.append(float(pt.y))
        xs.append(None)
        ys.append(None)
    return xs, ys


def _render_marker_chart(doc: HpglDocument) -> None:
    if not doc.segments:
        st.info(t(Keys.HPGL_NO_SEGMENTS))
        return

    fig = go.Figure()

    for piece in doc.pieces:
        color = PIECE_COLORS[piece.piece_id % len(PIECE_COLORS)]
        xs, ys = _build_piece_coords(piece)

        fig.add_trace(go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line={"color": color, "width": 1.0},
            name=f"{t(Keys.HPGL_PIECE)} {piece.piece_id + 1}",
            legendgroup=f"piece_{piece.piece_id}",
            hoverinfo="name",
        ))

    fig.update_layout(
        height=Config.HPGL_CHART_HEIGHT,
        showlegend=True,
        xaxis={"scaleanchor": "y", "scaleratio": 1, "title": "X (HPGL units)"},
        yaxis={"title": "Y (HPGL units)"},
        dragmode="pan",
        margin={"l": 50, "r": 20, "t": 30, "b": 50},
    )

    st.plotly_chart(
        fig,
        width='stretch',
        config={"scrollZoom": True, "displayModeBar": True},
    )


def _render_export(doc: HpglDocument) -> None:
    hpgl_content = serialize_to_hpgl(doc)
    st.download_button(
        label=t(Keys.HPGL_DOWNLOAD),
        data=hpgl_content,
        file_name=doc.filename or "marker.plt",
        mime="application/octet-stream",
    )
