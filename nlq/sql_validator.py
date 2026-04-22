from __future__ import annotations

import re

FORBIDDEN_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "MERGE", "UPSERT", "REPLACE",
    "CALL", "EXEC", "EXECUTE", "COPY",
})

_COMMENT_PATTERN = re.compile(
    r"--[^\n]*|/\*.*?\*/",
    re.DOTALL,
)


def validate_read_only(sql: str) -> str | None:
    cleaned = _COMMENT_PATTERN.sub(" ", sql)
    cleaned = cleaned.strip().rstrip(";").strip()

    if not cleaned:
        return "Empty query"

    first_word = cleaned.split()[0].upper()

    if first_word in ("SELECT", "WITH", "EXPLAIN", "SHOW"):
        return None

    if first_word in FORBIDDEN_KEYWORDS:
        return f"Forbidden operation: {first_word}"

    return f"Only SELECT queries are allowed (got: {first_word})"
