"""Shared state schema for the LangGraph agent.

Kept in a separate module to avoid circular imports between `agent.graph`
(and its node imports) and individual node implementations.
"""

from __future__ import annotations

from typing_extensions import TypedDict


class State(TypedDict):
    """Graph state with loop-control fields."""

    input_text: str
    translated_text: str
    score: float
    threshold: float
    iteration: int
    max_iterations: int
    plan: list[str]
    worker_output: str
    should_end: bool
    worker_iteration: int
    worker_max_iterations: int
    remaining_tool_calls: int
