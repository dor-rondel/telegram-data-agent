"""Input sanitization utilities.

Provides functions to sanitize user input before passing to the LLM.
"""

from __future__ import annotations

import re


def sanitize_user_input(text: str) -> str:
    """Sanitize user input to prevent prompt injection and clean up text.

    Args:
        text: Raw user input text.

    Returns:
        Sanitized text safe for LLM processing.
    """
    if not text:
        return ""

    sanitized = text

    # Remove any potential system/assistant role markers
    sanitized = re.sub(r"(?i)(system|assistant|user)\s*:", "", sanitized)

    # Remove potential markdown code blocks that could contain instructions
    sanitized = re.sub(r"```[\s\S]*?```", "", sanitized)

    # Remove XML-like tags that could be interpreted as special instructions
    sanitized = re.sub(r"<[^>]+>", "", sanitized)

    # Remove multiple consecutive newlines
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)

    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()

    # Limit length to prevent token overflow
    max_length = 4096
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized
