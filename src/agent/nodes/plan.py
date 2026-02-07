"""PLAN node.

Analyzes translated incident reports to determine relevance and extract
structured data for crime/terror events in Judea & Samaria.

Uses Pydantic-validated structured output to guarantee response format.
"""

from __future__ import annotations

import logging

# with_structured_output returns BaseModel | dict; we know it's PlanResponse.
# pyright needs a cast to narrow the type.
from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

from agent.prompts import PLAN_SYSTEM_PROMPT, PLAN_USER_PROMPT_TEMPLATE
from agent.state import IncidentDataModel, PlanResponse, State
from agent.utils import get_groq_llm

logger = logging.getLogger(__name__)

_plan_parser = PydanticOutputParser(pydantic_object=PlanResponse)


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

    llm = get_groq_llm()
    structured_llm = llm.with_structured_output(PlanResponse)

    system_prompt = PLAN_SYSTEM_PROMPT.format(
        format_instructions=_plan_parser.get_format_instructions(),
    )
    user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
        translated_text=translated_text,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        result = cast(PlanResponse, await structured_llm.ainvoke(messages))
    except Exception:
        logger.exception("Plan node failed")
        return {
            "skip_processing": True,
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": "Failed to parse LLM response",
        }

    # Handle non-relevant events
    if not result.relevant:
        reason = result.reason or "Event not relevant"
        logger.info("Event not relevant: %s", reason)
        return {
            "skip_processing": True,
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": reason,
        }

    # Build incident data for relevant events
    if result.crime is None:
        logger.warning("Relevant event missing crime type")
        return {
            "skip_processing": True,
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": "Relevant event missing crime type",
        }

    incident_data = IncidentDataModel(
        location=result.location,
        crime=result.crime,
    )

    if result.requires_email_alert:
        logger.info(
            "Jerusalem incident detected, email alert required: %s",
            incident_data,
        )
    else:
        logger.info("Incident detected: %s", incident_data)

    return {
        "incident_data": incident_data,
        "requires_email_alert": result.requires_email_alert,
        "plan_reason": "Relevant incident in Judea & Samaria",
    }
