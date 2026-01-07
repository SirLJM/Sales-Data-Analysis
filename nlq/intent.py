from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QueryIntent:
    entity_type: str | None = None
    identifiers: dict = field(default_factory=dict)
    time_range: tuple | None = None
    time_unit: str | None = None
    filters: list = field(default_factory=list)
    aggregation: str | None = None
    limit: int | None = None
    metric: str | None = None
    raw_query: str = ""
    confidence: float = 0.0

    def is_valid(self) -> bool:
        return self.entity_type is not None and self.confidence > 0.3

    def get_description(self) -> str:
        parts = []
        if self.entity_type:
            parts.append(f"Entity: {self.entity_type}")
        if self.identifiers:
            id_str = ", ".join(f"{k}={v}" for k, v in self.identifiers.items())
            parts.append(f"Identifiers: {id_str}")
        if self.time_range:
            if self.time_unit:
                parts.append(f"Time: last {self.time_range[0]} {self.time_unit}")
            else:
                parts.append(f"Time: {self.time_range[0]} - {self.time_range[1]}")
        if self.filters:
            filter_str = ", ".join(
                f"{f[0]} {f[1]} {f[2]}" if len(f) == 3 else str(f)
                for f in self.filters
            )
            parts.append(f"Filters: {filter_str}")
        if self.aggregation:
            parts.append(f"Aggregation: by {self.aggregation}")
        if self.limit:
            parts.append(f"Limit: top {self.limit}")
        if self.metric:
            parts.append(f"Metric: {self.metric}")
        return " | ".join(parts) if parts else "No intent detected"
