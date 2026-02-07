"""Tests for structured output fallback helper."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from agent.utils.structured_output import ainvoke_structured_with_fallback


class _DummyModel(BaseModel):
    value: int


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeStructuredRunnable:
    def __init__(self, result: BaseModel) -> None:
        self._result = result

    async def ainvoke(self, input: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        return self._result


class _FakeLLMStructuredFails:
    def with_structured_output(self, schema: Any = None, **kwargs: Any) -> Any:  # noqa: ANN401
        raise RuntimeError("tool call validation failed")

    async def ainvoke(self, input: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        return _FakeMessage('Here is JSON:\n```json\n{"value": 7}\n```')


class _FakeLLMStructuredWorks:
    def with_structured_output(self, schema: Any = None, **kwargs: Any) -> Any:  # noqa: ANN401
        return _FakeStructuredRunnable(_DummyModel(value=42))

    async def ainvoke(self, input: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        raise AssertionError("Should not use base ainvoke when structured works")


def test_falls_back_to_json_parse_when_structured_output_fails() -> None:
    parser = PydanticOutputParser(pydantic_object=_DummyModel)
    messages = [SystemMessage(content="test")]

    result = asyncio.run(
        ainvoke_structured_with_fallback(
            llm=_FakeLLMStructuredFails(),
            schema=_DummyModel,
            parser=parser,
            messages=messages,
            logger=logging.getLogger(__name__),
        )
    )

    assert result.value == 7


def test_uses_structured_output_when_available() -> None:
    parser = PydanticOutputParser(pydantic_object=_DummyModel)
    messages = [SystemMessage(content="test")]

    result = asyncio.run(
        ainvoke_structured_with_fallback(
            llm=_FakeLLMStructuredWorks(),
            schema=_DummyModel,
            parser=parser,
            messages=messages,
            logger=logging.getLogger(__name__),
        )
    )

    assert result.value == 42
