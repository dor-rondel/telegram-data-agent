"""PLAN node.

Dummy implementation for now.
"""

from __future__ import annotations

from typing import Any

from agent.state import State


def plan_node(state: State) -> dict[str, Any]:
    """Create an execution plan based on translated text.

    Dummy: returns a fixed plan.
    """
    _ = state
    return {"plan": ["step_1: analyze", "step_2: extract", "step_3: summarize"]}
