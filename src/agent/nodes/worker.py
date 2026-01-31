"""Worker agent node.

ReAct-style agent that executes tools based on the plan from the preceding node.
Uses Groq LLM with tool calling to decide between ending, storing data, or
sending alerts based on the incident context.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from agent.prompts import WORKER_SYSTEM_PROMPT
from agent.state import IncidentData, State
from agent.tools import push_to_dynamodb as push_to_dynamodb_impl
from agent.tools import send_email as send_email_impl

logger = logging.getLogger(__name__)


def _get_llm() -> ChatGroq:
    """Get configured ChatGroq instance for the worker agent."""
    return ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"),  # type: ignore[arg-type]
        model=os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=1024,
    )


@tool
def send_email(
    location: str,
    crime: str,
    created_at: int,
) -> dict[str, Any]:
    """Send a terror incident alert email via AWS SES.

    Use this tool to send an email alert for high-priority incidents
    that require immediate notification (e.g., Jerusalem-area events).

    Args:
        location: The location where the incident occurred.
        crime: The type of crime (e.g., rock_throwing, stabbing).
        created_at: Unix timestamp in milliseconds when the incident was created.

    Returns:
        A dictionary with the operation result.
    """
    incident: IncidentData = {
        "location": location,
        "crime": crime,  # type: ignore[typeddict-item]
        "created_at": created_at,
    }
    return send_email_impl(incident)


@tool
def push_to_dynamodb(
    location: str,
    crime: str,
    created_at: int,
) -> dict[str, Any]:
    """Store an incident record in DynamoDB.

    Use this tool to persist incident data for record-keeping.
    Incidents are stored in monthly partitions with idempotent upserts.

    Args:
        location: The location where the incident occurred.
        crime: The type of crime (e.g., rock_throwing, stabbing).
        created_at: Unix timestamp in milliseconds when the incident was created.

    Returns:
        A dictionary with the operation result.
    """
    incident: IncidentData = {
        "location": location,
        "crime": crime,  # type: ignore[typeddict-item]
        "created_at": created_at,
    }
    return push_to_dynamodb_impl(incident)


WORKER_TOOLS = [send_email, push_to_dynamodb]


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
                f"- location: {incident_data['location']}",
                f"- crime: {incident_data['crime']}",
                f"- created_at: {incident_data['created_at']}",
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
            "Execute the appropriate tools based on this plan, then report completion.",
        ]
    )

    return "\n".join(prompt_parts)


async def worker_node(state: State) -> dict[str, Any]:
    """Worker agent node that executes tools via ReAct.

    Uses an LLM with tool calling to decide which tools to execute based on
    the plan from the preceding node. The agent reasons about the state and
    calls the appropriate tools in sequence.

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

    llm = _get_llm()
    llm_with_tools = llm.bind_tools(WORKER_TOOLS)

    user_prompt = _build_user_prompt(state)
    messages = [
        SystemMessage(content=WORKER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    actions_taken: list[str] = []
    max_iterations = state.get("worker_max_iterations", 10)

    for iteration in range(max_iterations):
        logger.debug("Worker iteration %d", iteration + 1)

        try:
            response = await llm_with_tools.ainvoke(messages)
        except Exception:
            logger.exception("Worker LLM invocation failed")
            return {
                "worker_output": "Worker failed: LLM error",
                "should_end": True,
            }

        # Check if there are tool calls
        tool_calls = getattr(response, "tool_calls", None) or []

        if not tool_calls:
            # No more tool calls - agent has finished
            logger.info("Worker completed with actions: %s", actions_taken)
            break

        # Execute each tool call
        messages.append(response)

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")

            logger.info("Executing tool: %s with args: %s", tool_name, tool_args)

            try:
                if tool_name == "send_email":
                    result = send_email_impl(
                        {
                            "location": tool_args.get("location", ""),
                            "crime": tool_args.get("crime", ""),
                            "created_at": tool_args.get("created_at", 0),
                        }
                    )
                    actions_taken.append("send_email")
                elif tool_name == "push_to_dynamodb":
                    result = push_to_dynamodb_impl(
                        {
                            "location": tool_args.get("location", ""),
                            "crime": tool_args.get("crime", ""),
                            "created_at": tool_args.get("created_at", 0),
                        }
                    )
                    actions_taken.append("push_to_dynamodb")
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                    logger.warning("Unknown tool called: %s", tool_name)
            except Exception as e:
                result = {"error": str(e)}
                logger.exception("Tool execution failed: %s", tool_name)

            # Add tool result as a message for the agent
            from langchain_core.messages import ToolMessage

            messages.append(
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tool_id,
                )
            )
    else:
        logger.warning("Worker reached max iterations without completing")

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
    the ReAct loop, this simply checks if should_end is set.

    Args:
        state: Current graph state.

    Returns:
        "end" if worker has finished, "worker" to continue.
    """
    if state.get("should_end", False):
        return "end"
    return "worker"
