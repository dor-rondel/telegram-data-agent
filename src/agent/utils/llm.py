"""LLM configuration utilities shared across nodes.

Provides centralized LLM configuration to avoid duplication.
"""

from __future__ import annotations

import os

from langchain_groq import ChatGroq


def get_groq_llm(*, max_tokens: int = 1024) -> ChatGroq:
    """Get configured ChatGroq instance.

    Args:
        max_tokens: Maximum tokens for the response.

    Returns:
        Configured ChatGroq instance.
    """
    return ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"),  # type: ignore[arg-type]
        model=os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=max_tokens,
    )
