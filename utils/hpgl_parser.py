from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

HPGL_UNITS_PER_MM: Final[float] = 40.0


@dataclass(frozen=True)
class HpglPoint:
    x: int
    y: int


@dataclass
class HpglSegment:
    start: HpglPoint
    points: list[HpglPoint] = field(default_factory=list)

    @property
    def is_closed(self) -> bool:
        if not self.points:
            return False
        last = self.points[-1]
        return self.start.x == last.x and self.start.y == last.y

    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        all_points = [self.start] + self.points
        xs = [p.x for p in all_points]
        ys = [p.y for p in all_points]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def width_mm(self) -> float:
        bb = self.bounding_box
        return (bb[2] - bb[0]) / HPGL_UNITS_PER_MM

    @property
    def height_mm(self) -> float:
        bb = self.bounding_box
        return (bb[3] - bb[1]) / HPGL_UNITS_PER_MM


@dataclass
class HpglHeader:
    plot_area: tuple[int, int] | None = None
    speed: int | None = None
    pen_width: float | None = None


@dataclass
class PatternPiece:
    piece_id: int
    segments: list[HpglSegment] = field(default_factory=list)

    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        boxes = [s.bounding_box for s in self.segments]
        return (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )

    @property
    def width_mm(self) -> float:
        bb = self.bounding_box
        return (bb[2] - bb[0]) / HPGL_UNITS_PER_MM

    @property
    def height_mm(self) -> float:
        bb = self.bounding_box
        return (bb[3] - bb[1]) / HPGL_UNITS_PER_MM


@dataclass
class HpglDocument:
    header: HpglHeader
    segments: list[HpglSegment]
    pieces: list[PatternPiece]
    raw_commands: list[str]
    filename: str

    @property
    def width_mm(self) -> float:
        if not self.segments:
            return 0.0
        boxes = [s.bounding_box for s in self.segments]
        min_x = min(b[0] for b in boxes)
        max_x = max(b[2] for b in boxes)
        return (max_x - min_x) / HPGL_UNITS_PER_MM

    @property
    def height_mm(self) -> float:
        if not self.segments:
            return 0.0
        boxes = [s.bounding_box for s in self.segments]
        min_y = min(b[1] for b in boxes)
        max_y = max(b[3] for b in boxes)
        return (max_y - min_y) / HPGL_UNITS_PER_MM


def parse_hpgl(content: str, filename: str = "") -> HpglDocument:
    tokens = _tokenize(content)
    header = _parse_header(tokens)
    segments = _build_segments(tokens)
    pieces = _group_into_pieces(segments)
    return HpglDocument(
        header=header,
        segments=segments,
        pieces=pieces,
        raw_commands=tokens,
        filename=filename,
    )


def _tokenize(content: str) -> list[str]:
    parts = re.split(r"[;\n\r]+", content)
    return [p.strip() for p in parts if p.strip()]


def _parse_header(tokens: list[str]) -> HpglHeader:
    header = HpglHeader()
    for token in tokens:
        if token.startswith("NE"):
            coords = token[2:].split(",")
            if len(coords) == 2:
                header.plot_area = (int(coords[0]), int(coords[1]))
        elif token.startswith("VS") and "," not in token:
            header.speed = int(token[2:])
        elif token.startswith("PW"):
            parts = token[2:].split(",")
            if parts:
                header.pen_width = float(parts[0])
    return header


def _parse_coordinates(coord_str: str) -> list[HpglPoint]:
    if not coord_str:
        return []
    nums = coord_str.split(",")
    points: list[HpglPoint] = []
    for i in range(0, len(nums) - 1, 2):
        points.append(HpglPoint(int(nums[i]), int(nums[i + 1])))
    return points


def _build_segments(tokens: list[str]) -> list[HpglSegment]:
    segments: list[HpglSegment] = []
    current: HpglSegment | None = None

    for token in tokens:
        if token.startswith("PU"):
            current = _flush_and_start_segment(current, segments, token)
        elif token.startswith("PD"):
            current = _extend_segment(current, token)

    if current and current.points:
        segments.append(current)

    return segments


def _flush_and_start_segment(
    current: HpglSegment | None,
    segments: list[HpglSegment],
    token: str,
) -> HpglSegment | None:
    if current and current.points:
        segments.append(current)
    points = _parse_coordinates(token[2:])
    if points:
        return HpglSegment(start=points[-1])
    return None


def _extend_segment(current: HpglSegment | None, token: str) -> HpglSegment | None:
    if current is None:
        return None
    points = _parse_coordinates(token[2:])
    if points:
        current.points.extend(points)
    return current


class _UnionFind:
    def __init__(self, n: int) -> None:
        self._parent = list(range(n))
        self._rank = [0] * n

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1

    def groups(self, n: int) -> dict[int, list[int]]:
        result: dict[int, list[int]] = {}
        for i in range(n):
            result.setdefault(self.find(i), []).append(i)
        return result


def _group_into_pieces(
    segments: list[HpglSegment], gap_threshold: float = 50.0
) -> list[PatternPiece]:
    if not segments:
        return []

    n = len(segments)
    uf = _UnionFind(n)
    boxes = [s.bounding_box for s in segments]

    for i in range(n):
        for j in range(i + 1, n):
            if _boxes_overlap_or_close(boxes[i], boxes[j], gap_threshold):
                uf.union(i, j)

    pieces: list[PatternPiece] = []
    for piece_id, (_, indices) in enumerate(sorted(uf.groups(n).items())):
        pieces.append(PatternPiece(
            piece_id=piece_id,
            segments=[segments[i] for i in indices],
        ))

    return pieces


def _boxes_overlap_or_close(
    a: tuple[int, int, int, int],
    b: tuple[int, int, int, int],
    gap: float,
) -> bool:
    return not (
        a[2] + gap < b[0]
        or b[2] + gap < a[0]
        or a[3] + gap < b[1]
        or b[3] + gap < a[1]
    )


def serialize_to_hpgl(document: HpglDocument) -> str:
    return ";\n".join(document.raw_commands) + ";"


def parse_filename(filename: str) -> dict[str, str]:
    result: dict[str, str] = {}
    name = filename.rsplit(".", 1)[0] if "." in filename else filename
    parts = [p.strip() for p in name.split(" - ")]

    if len(parts) >= 1:
        result["model"] = parts[0]
    if len(parts) >= 2:
        result["product_type"] = parts[1]
    if len(parts) >= 3:
        result["size_run"] = parts[2]
    if len(parts) >= 4:
        result["material"] = parts[3]
    if len(parts) >= 5:
        result["marker_id"] = parts[4]

    return result
