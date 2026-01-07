from __future__ import annotations

import re

from nlq.intent import QueryIntent
from nlq.patterns import ALL_PATTERNS, Pattern
from nlq.vocabulary import translate_to_english


class QueryParser:
    def __init__(self):
        self.patterns = ALL_PATTERNS

    def parse(self, query: str) -> QueryIntent:
        normalized = self._normalize(query)
        intent = QueryIntent(raw_query=query)

        entity_result = self._match_entity(normalized)
        if entity_result:
            intent.entity_type = entity_result
            intent.confidence += 0.3

        identifiers = self._match_identifiers(normalized)
        if identifiers:
            intent.identifiers = identifiers
            intent.confidence += 0.2

        time_result = self._match_time(normalized)
        if time_result:
            intent.time_range = time_result[0]
            intent.time_unit = time_result[1] if len(time_result) > 1 else None
            intent.confidence += 0.15

        filters = self._match_filters(normalized)
        if filters:
            intent.filters = filters
            intent.confidence += 0.1

        aggregation = self._match_aggregation(normalized)
        if aggregation:
            intent.aggregation = aggregation
            intent.confidence += 0.1

        limit = self._match_limit(normalized)
        if limit:
            intent.limit = limit
            intent.confidence += 0.05

        metric = self._match_metric(normalized)
        if metric:
            intent.metric = metric
            intent.confidence += 0.05

        intent.confidence = min(intent.confidence, 1.0)

        if not intent.entity_type:
            intent.entity_type = self._infer_entity(intent)

        return intent

    @staticmethod
    def _normalize(query: str) -> str:
        translated = translate_to_english(query)
        normalized = " ".join(translated.lower().split())
        return normalized

    def _match_entity(self, text: str) -> str | None:
        for pattern in self.patterns["entity"]:
            if self._has_keyword(text, pattern.keywords):
                return pattern.name
        return None

    def _match_identifiers(self, text: str) -> dict:
        identifiers = {}
        for pattern in sorted(self.patterns["identifier"], key=lambda p: -p.priority):
            key, value = self._extract_identifier(pattern, text)
            if key and value and key not in identifiers:
                identifiers[key] = value
        return identifiers

    @staticmethod
    def _extract_identifier(pattern: Pattern, text: str) -> tuple[str | None, str | None]:
        if not pattern.regex or not pattern.extractor:
            return None, None
        match = re.search(pattern.regex, text, re.IGNORECASE)
        if not match:
            return None, None
        value = pattern.extractor(match)
        if not value:
            return None, None
        key = pattern.name.replace("_direct", "")
        return key, value

    def _match_time(self, text: str) -> tuple | None:
        for pattern in sorted(self.patterns["time"], key=lambda p: -p.priority):
            time_result = self._extract_time(pattern, text)
            if time_result:
                return time_result
        return None

    @staticmethod
    def _extract_time(pattern: Pattern, text: str) -> tuple | None:
        if not pattern.regex or not pattern.extractor:
            return None
        match = re.search(pattern.regex, text, re.IGNORECASE)
        if not match:
            return None
        result = pattern.extractor(match)
        if not result:
            return None
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], str):
            return (result[0],), result[1]
        return result, None

    def _match_filters(self, text: str) -> list:
        filters = []
        for pattern in self.patterns["filter"]:
            if pattern.regex:
                match = re.search(pattern.regex, text, re.IGNORECASE)
                if match and pattern.extractor:
                    result = pattern.extractor(match)
                    if result:
                        filters.append(result)
            elif self._has_keyword(text, pattern.keywords):
                filters.append(self._filter_from_pattern(pattern))
        return filters

    @staticmethod
    def _filter_from_pattern(pattern: Pattern) -> tuple:
        filter_map = {
            "below_rop": ("below_rop", "=", True),
            "zero_stock": ("stock", "=", 0),
            "type_seasonal": ("type", "=", "seasonal"),
            "type_basic": ("type", "=", "basic"),
            "type_regular": ("type", "=", "regular"),
            "type_new": ("type", "=", "new"),
            "bestseller": ("bestseller", "=", True),
            "overstock": ("overstock", "=", True),
        }
        return filter_map.get(pattern.name, (pattern.name, "=", True))

    def _match_aggregation(self, text: str) -> str | None:
        for pattern in self.patterns["aggregation"]:
            if self._has_keyword(text, pattern.keywords):
                agg_map = {
                    "by_month": "month",
                    "by_year": "year",
                    "by_model": "model",
                    "by_color": "color",
                    "by_size": "size",
                }
                return agg_map.get(pattern.name)
        return None

    def _match_limit(self, text: str) -> int | None:
        for pattern in sorted(self.patterns["limit"], key=lambda p: -p.priority):
            if pattern.regex:
                match = re.search(pattern.regex, text, re.IGNORECASE)
                if match and pattern.extractor:
                    return pattern.extractor(match)
        return None

    def _match_metric(self, text: str) -> str | None:
        for pattern in sorted(self.patterns["metric"], key=lambda p: -p.priority):
            if self._has_keyword(text, pattern.keywords):
                return pattern.name
        return None

    @staticmethod
    def _has_keyword(text: str, keywords: list[str]) -> bool:
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    @staticmethod
    def _infer_entity(intent: QueryIntent) -> str | None:
        for filt in intent.filters:
            if isinstance(filt, tuple):
                if filt[0] in ("stock", "below_rop", "overstock", "zero_stock"):
                    return "stock"
        if intent.identifiers.get("model") or intent.identifiers.get("sku"):
            return "sales"
        return None
