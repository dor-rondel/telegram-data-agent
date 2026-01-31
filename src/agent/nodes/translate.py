"""TRANSLATE node.

Translates Hebrew text to English using Groq LLM.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from agent.prompts import TRANSLATE_SYSTEM_PROMPT
from agent.state import State
from agent.utils import sanitize_user_input

logger = logging.getLogger(__name__)


def _get_llm() -> ChatGroq:
    """Get configured ChatGroq instance."""
    return ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"),  # type: ignore[arg-type]
        model=os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=4096,
    )


async def translate_node(state: State) -> dict[str, Any]:
    """Translate Hebrew input text to English.

    Args:
        state: Current graph state containing input_text.

    Returns:
        Dictionary with translated_text key containing the English translation.
    """
    input_text = state.get("input_text", "")

    if not input_text:
        return {"translated_text": ""}

    # Sanitize user input before sending to LLM
    sanitized_input = sanitize_user_input(input_text)

    if not sanitized_input:
        return {"translated_text": ""}

    llm = _get_llm()

    messages = [
        SystemMessage(content=TRANSLATE_SYSTEM_PROMPT),
        HumanMessage(content=sanitized_input),
    ]

    try:
        response = await llm.ainvoke(messages)
        # Extract just the content string from the response
        translated_text = str(response.content) if response.content else ""
    except Exception:
        logger.exception("Translation failed for input: %s", sanitized_input[:100])
        raise

    return {"translated_text": translated_text}
