"""PLAN node.

Analyzes translated incident reports to determine relevance and extract
structured data for crime/terror events in Judea & Samaria.
"""

from __future__ import annotations

import json
import logging
import os
from enum import Enum
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from agent.prompts import PLAN_SYSTEM_PROMPT, PLAN_USER_PROMPT_TEMPLATE
from agent.state import IncidentCrime, IncidentData, State

logger = logging.getLogger(__name__)


class CrimeType(str, Enum):
    """Valid crime types for incident classification."""

    ROCK_THROWING = "rock_throwing"
    MOLOTOV_COCKTAIL = "molotov_cocktail"
    RAMMING = "ramming"
    STABBING = "stabbing"
    SHOOTING = "shooting"
    THEFT = "theft"


def _get_llm() -> ChatGroq:
    """Get configured ChatGroq instance for planning."""
    return ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"),  # type: ignore[arg-type]
        model=os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=1024,
    )


def _parse_plan_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM plan response JSON.

    Args:
        response_text: Raw response text from the LLM.

    Returns:
        Dictionary with parsed plan data.

    Raises:
        json.JSONDecodeError: If response is not valid JSON.
        ValueError: If crime type is not valid.
    """
    parsed = json.loads(response_text.strip())

    if not parsed.get("relevant", False):
        return {
            "relevant": False,
            "reason": parsed.get("reason", "Event not relevant"),
        }

    # Validate crime type
    crime_value = parsed.get("crime", "")
    try:
        crime_type = CrimeType(crime_value)
    except ValueError as err:
        raise ValueError(
            f"Invalid crime type: {crime_value}. "
            f"Must be one of: {[ct.value for ct in CrimeType]}"
        ) from err

    return {
        "relevant": True,
        "location": str(parsed.get("location", "")),
        "crime": crime_type.value,
        "requires_email_alert": bool(parsed.get("requires_email_alert", False)),
    }


def _build_incident_data(
    location: str,
    crime: IncidentCrime,
) -> IncidentData:
    """Build the structured incident data object.

    Args:
        location: The extracted location name.
        crime: The classified crime type.

    Returns:
        Dictionary with location and crime.
    """
    return {
        "location": location,
        "crime": crime,
    }


async def plan_node(state: State) -> dict[str, Any]:
    """Analyze translated text and create execution plan.

    Determines if the event is relevant (in Judea & Samaria AND crime/terror)
    and extracts structured incident data if so.

    Args:
        state: Current graph state containing translated_text.

    Returns:
        Dictionary with:
        - skip_processing: True if event should be skipped
        - incident_data: Structured incident object (if relevant)
        - requires_email_alert: True if Jerusalem location
        - plan_reason: Explanation for the decision
    """
    translated_text = state.get("translated_text", "")

    if not translated_text:
        logger.info("No translated text provided, skipping processing")
        return {
            "skip_processing": True,
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": "No translated text provided",
        }

    llm = _get_llm()

    user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
        translated_text=translated_text,
    )

    messages = [
        SystemMessage(content=PLAN_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)
        response_text = str(response.content) if response.content else ""
        result = _parse_plan_response(response_text)
    except json.JSONDecodeError:
        logger.exception("Failed to parse plan response")
        return {
            "skip_processing": True,
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": "Failed to parse LLM response",
        }
    except ValueError as err:
        logger.exception("Invalid plan response data")
        return {
            "skip_processing": True,
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": str(err),
        }
    except Exception:
        logger.exception("Plan node failed")
        raise

    # Handle non-relevant events
    if not result.get("relevant", False):
        reason = result.get("reason", "Event not relevant")
        logger.info("Event not relevant: %s", reason)
        return {
            "skip_processing": True,
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": reason,
        }

    # Build incident data for relevant events
    incident_data = _build_incident_data(
        location=result["location"],
        crime=result["crime"],
    )

    requires_email = result.get("requires_email_alert", False)
    if requires_email:
        logger.info(
            "Jerusalem incident detected, email alert required: %s",
            incident_data,
        )
    else:
        logger.info("Incident detected: %s", incident_data)

    return {
        "incident_data": incident_data,
        "requires_email_alert": requires_email,
        "plan_reason": "Relevant incident in Judea & Samaria",
    }
