"""Shared state schema for the LangGraph agent.

Kept in a separate module to avoid circular imports between `agent.graph`
(and its node imports) and individual node implementations.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

from typing_extensions import TypedDict

IncidentCrime: TypeAlias = Literal[
    "rock_throwing",
    "molotov_cocktail",
    "ramming",
    "stabbing",
    "shooting",
    "theft",
]


class IncidentData(TypedDict):
    """Structured incident payload produced by the plan node."""

    location: str
    crime: IncidentCrime


class State(TypedDict):
    """Graph state with loop-control fields."""

    # Translation fields
    input_text: str
    translated_text: str
    score: float
    feedback: str
    error_message: str
    threshold: float
    iteration: int
    max_iterations: int

    # Plan fields
    skip_processing: bool
    incident_data: IncidentData | None
    requires_email_alert: bool
    plan_reason: str

    # Worker fields
    worker_output: str
    should_end: bool
    worker_iteration: int
    worker_max_iterations: int
    remaining_tool_calls: int
