"""LangGraph agent with TRANSLATE → EVALUATE loop, PLAN, and ReAct nodes.

Flow:
  START → TRANSLATE → EVALUATE → (loop until score >= threshold) → PLAN → REACT → END

Nodes return dummy data for now; replace with real implementations when ready.
"""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]
from typing_extensions import TypedDict

from agent.tools import push_to_dynamodb, send_email

REACT_TOOLS = (send_email, push_to_dynamodb)

# ---------------------------------------------------------------------------
# State Annotation
# ---------------------------------------------------------------------------


class State(TypedDict, total=False):
    """Graph state with loop-control fields.

    Attributes:
        input_text: Raw input text to process.
        translated_text: Output from the translate node.
        score: Quality score from the evaluate node (0.0 - 1.0).
        threshold: Target score to exit the translate/evaluate loop.
        iteration: Current loop iteration count.
        max_iterations: Safety limit for loop iterations.
        plan: Output from the plan node.
        react_output: Output from the ReAct agent node.
        should_end: Flag to signal termination from ReAct.
    """

    input_text: str
    translated_text: str
    score: float
    threshold: float
    iteration: int
    max_iterations: int
    plan: list[str]
    react_output: str
    should_end: bool


# ---------------------------------------------------------------------------
# Node Functions (dummy implementations)
# ---------------------------------------------------------------------------


def translate_node(state: State) -> dict[str, Any]:
    """Translate input text.

    Dummy: just echoes input with a prefix.
    """
    input_text = state.get("input_text", "")
    return {"translated_text": f"[translated] {input_text}"}


def evaluate_node(state: State) -> dict[str, Any]:
    """Evaluate translation quality and update score.

    Dummy: increments score by 0.3 each iteration until threshold.
    """
    current_score = state.get("score", 0.0)
    current_iter = state.get("iteration", 0)
    new_score = min(current_score + 0.3, 1.0)
    return {
        "score": new_score,
        "iteration": current_iter + 1,
    }


def plan_node(state: State) -> dict[str, Any]:
    """Create an execution plan based on translated text.

    Dummy: returns a fixed plan.
    """
    return {"plan": ["step_1: analyze", "step_2: extract", "step_3: summarize"]}


def react_node(state: State) -> dict[str, Any]:
    """ReAct agent node with access to tools.

    Dummy: marks execution complete and returns placeholder output.
    Tools available: send_email and push_to_dynamodb.
    """
    _ = REACT_TOOLS
    # In a real implementation, this would:
    # 1. Call an LLM with tool bindings
    # 2. Execute tool calls as needed
    # 3. Loop until the agent decides to finish
    return {
        "react_output": "ReAct agent completed successfully",
        "should_end": True,
    }


# ---------------------------------------------------------------------------
# Routing Functions
# ---------------------------------------------------------------------------


def route_after_evaluate(state: State) -> Literal["translate", "plan"]:
    """Decide whether to continue the translate/evaluate loop or proceed to plan.

    Returns "plan" if score >= threshold or max iterations reached.
    Returns "translate" to continue the loop.
    """
    score = state.get("score", 0.0)
    threshold = state.get("threshold", 0.8)
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)

    if score >= threshold or iteration >= max_iterations:
        return "plan"
    return "translate"


# ---------------------------------------------------------------------------
# Graph Definition
# ---------------------------------------------------------------------------

# Build the graph
builder = StateGraph(State)

# Add nodes
builder.add_node("translate", translate_node)
builder.add_node("evaluate", evaluate_node)
builder.add_node("plan", plan_node)
builder.add_node("react", react_node)

# Add edges
builder.add_edge(START, "translate")
builder.add_edge("translate", "evaluate")
builder.add_conditional_edges(
    "evaluate",
    route_after_evaluate,
    {"translate": "translate", "plan": "plan"},
)
builder.add_edge("plan", "react")
builder.add_edge("react", END)

# Compile the graph
graph = builder.compile(name="Telegram Data Agent")
