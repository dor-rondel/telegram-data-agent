"""Shared state schema and Pydantic models for the LangGraph agent.

Kept in a separate module to avoid circular imports between `agent.graph`
(and its node imports) and individual node implementations.

Pydantic v2 models are used for structured LLM output validation.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

IncidentCrime: TypeAlias = Literal[
    "rock_throwing",
    "molotov_cocktail",
    "ramming",
    "stabbing",
    "shooting",
    "theft",
]

WorkerActionName: TypeAlias = Literal[
    "send_email",
    "push_to_dynamodb",
]

# ---------------------------------------------------------------------------
# Pydantic v2 models – structured LLM output
# ---------------------------------------------------------------------------


class IncidentDataModel(BaseModel):
    """Structured incident payload produced by the plan node."""

    location: str = Field(description="The location where the incident occurred.")
    crime: IncidentCrime = Field(
        description="The type of crime. Must be one of: "
        "rock_throwing, molotov_cocktail, ramming, stabbing, shooting, theft."
    )


class PlanResponse(BaseModel):
    """Structured response from the plan node LLM."""

    relevant: bool = Field(
        description="Whether the event is relevant (in Judea & Samaria AND crime/terror)."
    )
    reason: str = Field(
        default="",
        description="Explanation for the relevance decision.",
    )
    location: str = Field(
        default="",
        description="Extracted location name (only when relevant is true).",
    )
    crime: IncidentCrime | None = Field(
        default=None,
        description="Crime type (only when relevant is true).",
    )
    requires_email_alert: bool = Field(
        default=False,
        description="True only if the location is Jerusalem.",
    )


class EvaluationResponse(BaseModel):
    """Structured response from the evaluate node LLM."""

    score: float = Field(
        description="Translation quality score from 0 to 10.",
        ge=0,
        le=10,
    )
    feedback: str = Field(
        description="Constructive feedback or empty string if score >= 7.5.",
    )


class WorkerAction(BaseModel):
    """A single validated action for the worker to execute."""

    action: WorkerActionName = Field(
        description="The tool to execute: send_email or push_to_dynamodb.",
    )
    location: str = Field(description="Incident location.")
    crime: IncidentCrime = Field(description="Incident crime type.")


class ActionPlan(BaseModel):
    """Validated list of actions for the worker node to execute."""

    actions: list[WorkerAction] = Field(
        description="Ordered list of tool actions to execute.",
    )


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------


class State(TypedDict):
    """Graph state with loop-control fields."""

    # Translation fields
    input_text: str
    translated_text: str
    evaluation_score: float
    feedback: str
    error_message: str
    threshold: float
    iteration: int
    max_iterations: int

    # Plan fields
    skip_processing: bool
    incident_data: IncidentDataModel | None
    requires_email_alert: bool
    plan_reason: str

    # Worker fields
    worker_output: str
    should_end: bool
    worker_iteration: int
    worker_max_iterations: int
    remaining_tool_calls: int
