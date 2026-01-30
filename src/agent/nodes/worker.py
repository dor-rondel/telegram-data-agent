"""Worker node.

Dummy implementation for now.

This node is intended to represent a worker-style agent.
"""

from __future__ import annotations

from typing import Any, Literal

from agent.state import State
from agent.tools import TOOLS


def worker_node(state: State) -> dict[str, Any]:
    """Worker agent node with access to tools.

    Dummy: marks execution complete and returns placeholder output.
    Tools available: send_email and push_to_dynamodb.
    """
    _ = TOOLS

    remaining_tool_calls = state.get("remaining_tool_calls", 0)
    worker_iteration = state.get("worker_iteration", 0) + 1
    worker_max_iterations = state.get("worker_max_iterations", 10)

    if worker_iteration >= worker_max_iterations:
        return {
            "worker_output": "Worker max iterations reached",
            "worker_iteration": worker_iteration,
            "remaining_tool_calls": max(remaining_tool_calls, 0),
            "should_end": True,
        }

    # Stop condition is evaluated one step after remaining_tool_calls reaches 0.
    # This matches the unit test expectation: 2 -> 1 (continue), 1 -> 0 (continue), 0 -> stop.
    if remaining_tool_calls <= 0:
        return {
            "worker_output": "Worker finished (no remaining tool calls)",
            "worker_iteration": worker_iteration,
            "remaining_tool_calls": 0,
            "should_end": True,
        }

    return {
        "worker_output": "Worker executed tool call",
        "worker_iteration": worker_iteration,
        "remaining_tool_calls": remaining_tool_calls - 1,
        "should_end": False,
    }


def should_continue(state: State) -> Literal["worker", "end"]:
    """Route worker loop until completion."""
    if state.get("should_end", False):
        return "end"
    if state.get("worker_iteration", 0) >= state.get("worker_max_iterations", 10):
        return "end"
    return "worker"
