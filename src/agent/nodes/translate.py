"""TRANSLATE node.

Translates Hebrew text to English using Groq LLM.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import (
    TRANSLATE_FEEDBACK_SECTION,
    TRANSLATE_SYSTEM_PROMPT,
    TRANSLATE_USER_PROMPT_TEMPLATE,
)
from agent.state import State
from agent.utils import get_groq_llm, sanitize_user_input

logger = logging.getLogger(__name__)


def _build_user_prompt(
    text: str,
    feedback: str,
    previous_translation: str,
) -> str:
    """Build the user prompt, including feedback if available."""
    feedback_section = ""
    if feedback and previous_translation:
        feedback_section = TRANSLATE_FEEDBACK_SECTION.format(
            feedback=feedback,
            previous_translation=previous_translation,
        )
    return TRANSLATE_USER_PROMPT_TEMPLATE.format(
        feedback_section=feedback_section,
        text=text,
    )


async def translate_node(state: State) -> dict[str, Any]:
    """Translate Hebrew input text to English.

    Args:
        state: Current graph state containing input_text and optional feedback.

    Returns:
        Dictionary with translated_text key containing the English translation.
    """
    input_text = state.get("input_text", "")
    feedback = state.get("feedback", "")
    previous_translation = state.get("translated_text", "")

    if not input_text:
        return {"translated_text": ""}

    # Sanitize user input before sending to LLM
    sanitized_input = sanitize_user_input(input_text)

    if not sanitized_input:
        return {"translated_text": ""}

    llm = get_groq_llm(max_tokens=4096)
    user_prompt = _build_user_prompt(sanitized_input, feedback, previous_translation)

    messages = [
        SystemMessage(content=TRANSLATE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)
        # Extract just the content string from the response
        translated_text = str(response.content) if response.content else ""
    except Exception:
        logger.exception("Translation failed for input: %s", sanitized_input[:100])
        raise

    return {"translated_text": translated_text}
