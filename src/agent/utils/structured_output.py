"""Structured output helpers.

Groq tool-calling can occasionally fail when models hallucinate tool calls that
aren't present in the request. LangChain's `with_structured_output()` uses the
provider's tool-calling/JSON-schema mechanisms under the hood, so we provide a
safe fallback:

1) Try `with_structured_output(schema)`
2) On failure, call the base LLM (no tools) and parse JSON using Pydantic.

This keeps Pydantic validation guarantees while improving reliability.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol, Sequence, TypeVar, cast

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class _SupportsAInvoke(Protocol):
    async def ainvoke(self, input: Any, **kwargs: Any) -> Any: ...


class _SupportsStructuredOutput(Protocol):
    def with_structured_output(
        self, schema: Any = None, **kwargs: Any
    ) -> _SupportsAInvoke: ...

    async def ainvoke(self, input: Any, **kwargs: Any) -> Any: ...


def _extract_first_json_object(text: str) -> str | None:
    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match is not None:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    return text[start : end + 1].strip()


async def ainvoke_structured_with_fallback(
    *,
    llm: _SupportsStructuredOutput,
    schema: type[TModel],
    parser: PydanticOutputParser,
    messages: Sequence[BaseMessage],
    logger: logging.Logger,
) -> TModel:
    """Invoke an LLM for a Pydantic schema with a safe fallback.

    Args:
        llm: Chat model instance that supports `with_structured_output()` and `ainvoke()`.
        schema: Pydantic model type expected.
        parser: PydanticOutputParser configured for the same schema.
        messages: Messages for the chat model.
        logger: Logger for warnings.

    Returns:
        A validated Pydantic model instance.

    Raises:
        Exception: If both the structured-output path and the fallback fail.
    """
    try:
        structured_llm = llm.with_structured_output(schema)
        return cast(TModel, await structured_llm.ainvoke(messages))
    except Exception as exc:
        logger.warning(
            "Structured output failed (%s); falling back to JSON parse",
            type(exc).__name__,
        )

    raw = await llm.ainvoke(messages)
    content = raw.content
    if not isinstance(content, str):
        content = str(content)

    # First try the parser directly (handles plain JSON strings).
    last_exc: Exception | None = None
    try:
        return cast(TModel, parser.parse(content))
    except Exception as exc:  # noqa: BLE001
        last_exc = exc

    json_text = _extract_first_json_object(content)
    if json_text is None:
        raise ValueError("LLM response did not contain a JSON object") from last_exc

    return schema.model_validate_json(json_text)
