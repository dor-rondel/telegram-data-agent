"""EVALUATE node.

Evaluates translation quality using an LLM and provides feedback.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import EVALUATE_SYSTEM_PROMPT, EVALUATE_USER_PROMPT_TEMPLATE
from agent.state import State
from agent.utils import get_groq_llm

logger = logging.getLogger(__name__)


def _parse_evaluation_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM evaluation response JSON.

    Args:
        response_text: Raw response text from the LLM.

    Returns:
        Dictionary with 'score' (normalized 0-1) and 'feedback' keys.
    """
    parsed = json.loads(response_text.strip())
    return {
        "score": float(parsed["score"]) / 10.0,
        "feedback": str(parsed["feedback"]),
    }


async def evaluate_node(state: State) -> dict[str, Any]:
    """Evaluate translation quality and provide feedback.

    Uses an LLM to score the translation from 0-10 and provide feedback
    if the score is below the threshold.

    Args:
        state: Current graph state containing input_text and translated_text.

    Returns:
        Dictionary with score, feedback, and incremented iteration count.

    Raises:
        TranslationEvaluationError: If max iterations reached with score below threshold.
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
            "score": 0.0,
            "feedback": "No translation provided.",
            "iteration": new_iteration,
        }

    llm = get_groq_llm()

    user_prompt = EVALUATE_USER_PROMPT_TEMPLATE.format(
        original_text=input_text,
        translated_text=translated_text,
    )

    messages = [
        SystemMessage(content=EVALUATE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)
        response_text = str(response.content) if response.content else ""
        result = _parse_evaluation_response(response_text)
    except json.JSONDecodeError:
        logger.exception("Failed to parse evaluation response")
        result = {
            "score": 0.0,
            "feedback": "Evaluation parsing failed. Please re-translate.",
        }
    except Exception:
        logger.exception("Evaluation failed")
        raise

    score = result["score"]
    feedback = result["feedback"]

    # Check if we've exhausted iterations without meeting threshold
    error_message = ""
    if new_iteration >= max_iterations and score < threshold:
        error_message = (
            f"Translation quality threshold ({threshold}) not met after "
            f"{max_iterations} iterations. Final score: {score:.2f}"
        )
        logger.warning(error_message)

    return {
        "score": score,
        "feedback": feedback,
        "iteration": new_iteration,
        "error_message": error_message,
    }
