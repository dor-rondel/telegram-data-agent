"""Worker agent node.

Produces a validated ActionPlan via structured LLM output, then executes
each action in order. Uses Pydantic models to guarantee action format
before any tool is invoked.
"""

from __future__ import annotations

import logging

# with_structured_output returns BaseModel | dict; we know it's ActionPlan.
from typing import Any, Literal, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

from agent.prompts import WORKER_SYSTEM_PROMPT
from agent.state import ActionPlan, IncidentDataModel, State
from agent.tools import push_to_dynamodb as push_to_dynamodb_impl
from agent.tools import send_email as send_email_impl
from agent.utils import get_groq_llm

logger = logging.getLogger(__name__)

_action_parser = PydanticOutputParser(pydantic_object=ActionPlan)

# Map of validated action names to their implementation functions.
_TOOL_REGISTRY: dict[str, Any] = {
    "send_email": send_email_impl,
    "push_to_dynamodb": push_to_dynamodb_impl,
}


def _build_user_prompt(state: State) -> str:
    """Build the user prompt with the current plan context.

    Args:
        state: Current graph state containing plan data.

    Returns:
        Formatted user prompt string for the agent.
    """
    incident_data = state.get("incident_data")
    requires_email_alert = state.get("requires_email_alert", False)
    plan_reason = state.get("plan_reason", "No reason provided")

    prompt_parts = [
        "## Current Plan",
        f"- requires_email_alert: {requires_email_alert}",
        f"- plan_reason: {plan_reason}",
    ]

    if incident_data:
        prompt_parts.extend(
            [
                "",
                "## Incident Data",
                f"- location: {incident_data.location}",
                f"- crime: {incident_data.crime}",
            ]
        )
    else:
        prompt_parts.extend(
            [
                "",
                "## Incident Data",
                "No incident data available.",
            ]
        )

    prompt_parts.extend(
        [
            "",
            "Produce an action plan based on the above context.",
        ]
    )

    return "\n".join(prompt_parts)


async def worker_node(state: State) -> dict[str, Any]:
    """Worker agent node that validates an ActionPlan then executes tools.

    Uses an LLM with structured output to produce a validated ActionPlan,
    then executes each action in order using the tool registry.

    Args:
        state: Current graph state containing plan data.

    Returns:
        Dictionary with:
        - worker_output: Description of actions taken
        - should_end: Always True (worker completes in one pass)
    """
    incident_data = state.get("incident_data")

    # Early exit if no processing needed
    if not incident_data:
        reason = state.get("plan_reason", "No processing required")
        logger.info("Worker skipping processing: %s", reason)
        return {
            "worker_output": f"Skipped processing: {reason}",
            "should_end": True,
        }

    # Validate incident_data against the Pydantic model
    if not isinstance(incident_data, IncidentDataModel):
        try:
            IncidentDataModel.model_validate(incident_data)
        except Exception:
            logger.exception("Invalid incident_data in state")
            return {
                "worker_output": "Worker failed: invalid incident data",
                "should_end": True,
            }

    llm = get_groq_llm()
    structured_llm = llm.with_structured_output(ActionPlan)

    system_prompt = WORKER_SYSTEM_PROMPT.format(
        format_instructions=_action_parser.get_format_instructions(),
    )
    user_prompt = _build_user_prompt(state)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        action_plan = cast(ActionPlan, await structured_llm.ainvoke(messages))
    except Exception:
        logger.exception("Worker failed to produce a valid action plan")
        return {
            "worker_output": "Worker failed: could not produce valid action plan",
            "should_end": True,
        }

    if not action_plan.actions:
        logger.info("Worker received empty action plan")
        return {
            "worker_output": "No actions to execute",
            "should_end": True,
        }

    # Execute each validated action
    actions_taken: list[str] = []

    for action in action_plan.actions:
        tool_fn = _TOOL_REGISTRY.get(action.action)
        if tool_fn is None:
            logger.warning("Unknown action in plan: %s", action.action)
            continue

        incident = IncidentDataModel(
            location=action.location,
            crime=action.crime,
        )

        logger.info(
            "Executing tool: %s with args: %s",
            action.action,
            incident,
        )

        try:
            tool_fn(incident)
            actions_taken.append(action.action)
        except Exception:
            logger.exception("Tool execution failed: %s", action.action)

    # Build output summary
    if actions_taken:
        output = f"Executed: {', '.join(actions_taken)}"
    else:
        output = "No actions taken"

    return {
        "worker_output": output,
        "should_end": True,
    }


def should_continue(state: State) -> Literal["worker", "end"]:
    """Route worker loop until completion.

    Since the worker now completes all actions in a single pass using
    the validated ActionPlan, this simply checks if should_end is set.

    Args:
        state: Current graph state.

    Returns:
        "end" if worker has finished, "worker" to continue.
    """
    if state.get("should_end", False):
        return "end"
    return "worker"
