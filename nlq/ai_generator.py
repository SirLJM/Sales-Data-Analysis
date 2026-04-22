from __future__ import annotations

import json
import os
from typing import Any

from nlq.schema_context import get_schema_context
from utils.logging_config import get_logger

logger = get_logger(__name__)

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

_ANTHROPIC_AVAILABLE = anthropic is not None

MAX_HISTORY_EXCHANGES = 10

SYSTEM_PROMPT_TEMPLATE = """\
You are a SQL query generator for an inventory management application.
Given a user's natural language question, generate a SQL query to answer it.

{schema_context}

Respond with JSON only, no markdown fences:
{{"sql": "<the SQL query>", "explanation": "<brief explanation of what the query does>"}}
"""


def is_ai_available() -> bool:
    return _ANTHROPIC_AVAILABLE and bool(os.getenv("ANTHROPIC_API_KEY"))


class AIQueryGenerator:
    def __init__(self, api_key: str, model: str, is_database_mode: bool):
        if not _ANTHROPIC_AVAILABLE or anthropic is None:
            raise ImportError("anthropic package is not installed")
        self._client: Any = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            schema_context=get_schema_context(is_database_mode),
        )

    def generate_sql(
        self,
        user_query: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[str, str]:
        messages = self._build_messages(user_query, conversation_history)

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=self._system_prompt,
                messages=messages,
            )
        except Exception as e:
            logger.exception("Claude API call failed")
            return "", f"API error: {e}"

        return self._parse_response(response)

    def _build_messages(
        self,
        user_query: str,
        conversation_history: list[dict[str, str]] | None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []

        if conversation_history:
            trimmed = conversation_history[-MAX_HISTORY_EXCHANGES * 2 :]
            messages.extend(trimmed)

        messages.append({"role": "user", "content": user_query})
        return messages

    @staticmethod
    def _parse_response(response: Any) -> tuple[str, str]:
        raw_text = response.content[0].text.strip()

        cleaned = raw_text
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            sql = data.get("sql", "").strip()
            explanation = data.get("explanation", "").strip()
            if not sql:
                return "", "AI returned empty SQL"
            return sql, explanation
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON: %s", raw_text[:200])
            if raw_text.upper().lstrip().startswith(("SELECT", "WITH")):
                return raw_text, ""
            return "", f"Could not parse AI response: {raw_text[:200]}"
