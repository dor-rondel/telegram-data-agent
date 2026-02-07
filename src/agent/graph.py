"""LangGraph agent with TRANSLATE → EVALUATE loop, PLAN, and worker nodes.

Flow:
  START → TRANSLATE → EVALUATE → (loop until evaluation_score >= threshold) → PLAN → WORKER → END

If max iterations reached without meeting threshold, routes to END with error state.
If event is not relevant (not in Judea & Samaria or not crime/terror), PLAN routes to END.
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]

from agent.nodes import evaluate_node, plan_node, translate_node, worker_node
from agent.nodes.worker import should_continue
from agent.state import State

# ---------------------------------------------------------------------------
# Routing Functions
# ---------------------------------------------------------------------------


def route_after_evaluate(
    state: State,
) -> Literal["translate", "plan", "__end__"]:
    """Decide whether to continue the translate/evaluate loop or proceed to plan.

    Returns "plan" if evaluation_score >= threshold.
    Returns "__end__" if max iterations reached without meeting threshold.
    Returns "translate" to continue the loop.
    """
    score = state.get("evaluation_score", 0.0)
    threshold = state.get("threshold", 0.75)
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)

    if score >= threshold:
        return "plan"

    if iteration >= max_iterations:
        # Max iterations exhausted without meeting threshold
        return "__end__"

    return "translate"


def route_after_plan(
    state: State,
) -> Literal["worker", "__end__"]:
    """Decide whether to proceed to worker or end early.

    Returns "__end__" if skip_processing is True (event not relevant).
    Returns "worker" to continue processing the incident.
    """
    if state.get("skip_processing", False):
        return "__end__"
    return "worker"


# ---------------------------------------------------------------------------
# Graph Definition
# ---------------------------------------------------------------------------

# Build the graph
builder = StateGraph(State)

# Add nodes
builder.add_node("translate", translate_node)
builder.add_node("evaluate", evaluate_node)
builder.add_node("plan", plan_node)
builder.add_node("worker", worker_node)

# Add edges
builder.add_edge(START, "translate")
builder.add_edge("translate", "evaluate")
builder.add_conditional_edges(
    "evaluate",
    route_after_evaluate,
    {"translate": "translate", "plan": "plan", "__end__": END},
)
builder.add_conditional_edges(
    "plan",
    route_after_plan,
    {"worker": "worker", "__end__": END},
)
builder.add_conditional_edges(
    "worker",
    should_continue,
    {"worker": "worker", "end": END},
)

# Compile the graph
graph = builder.compile(name="Telegram Data Agent")
