"""EVALUATE node.

Evaluates translation quality using an LLM and provides feedback.

Uses Pydantic-validated structured output to guarantee response format.
"""

from __future__ import annotations

import logging

# with_structured_output returns BaseModel | dict; we know it's EvaluationResponse.
from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

from agent.prompts import EVALUATE_SYSTEM_PROMPT, EVALUATE_USER_PROMPT_TEMPLATE
from agent.state import EvaluationResponse, State
from agent.utils import get_groq_llm

logger = logging.getLogger(__name__)

_eval_parser = PydanticOutputParser(pydantic_object=EvaluationResponse)


async def evaluate_node(state: State) -> dict[str, Any]:
    """Evaluate translation quality and provide feedback.

    Uses an LLM to score the translation from 0-10 and provide feedback
    if the score is below the threshold.

    Args:
        state: Current graph state containing input_text and translated_text.

    Returns:
        Dictionary with score, feedback, and incremented iteration count.
    """
    input_text = state.get("input_text", "")
    translated_text = state.get("translated_text", "")
    current_iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)
    threshold = state.get("threshold", 0.75)

    # Increment iteration at the start
    new_iteration = current_iteration + 1

    if not translated_text:
        return {
            "evaluation_score": 0.0,
            "feedback": "No translation provided.",
            "iteration": new_iteration,
        }

    llm = get_groq_llm()
    structured_llm = llm.with_structured_output(EvaluationResponse)

    system_prompt = EVALUATE_SYSTEM_PROMPT.format(
        format_instructions=_eval_parser.get_format_instructions(),
    )
    user_prompt = EVALUATE_USER_PROMPT_TEMPLATE.format(
        original_text=input_text,
        translated_text=translated_text,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        result = cast(EvaluationResponse, await structured_llm.ainvoke(messages))
    except Exception:
        logger.exception("Evaluation failed")
        result = EvaluationResponse(
            score=0.0,
            feedback="Evaluation parsing failed. Please re-translate.",
        )

    score = result.score / 10.0
    feedback = result.feedback

    # Check if we've exhausted iterations without meeting threshold
    error_message = ""
    if new_iteration >= max_iterations and score < threshold:
        error_message = (
            f"Translation quality threshold ({threshold}) not met after "
            f"{max_iterations} iterations. Final score: {score:.2f}"
        )
        logger.warning(error_message)

    return {
        "evaluation_score": score,
        "feedback": feedback,
        "iteration": new_iteration,
        "error_message": error_message,
    }
