"""EVALUATE node.

Dummy implementation for now.
"""

from __future__ import annotations

from typing import Any

from agent.state import State


def evaluate_node(state: State) -> dict[str, Any]:
    """Evaluate translation quality and update score.

    Dummy: increments score by 0.3 each iteration until threshold.
    """
    current_score = state.get("score", 0.0)
    current_iter = state.get("iteration", 0)
    new_score = min(current_score + 0.3, 1.0)
    return {"score": new_score, "iteration": current_iter + 1}
