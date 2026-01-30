"""TRANSLATE node.

Dummy implementation for now.
"""

from __future__ import annotations

from typing import Any

from agent.state import State


def translate_node(state: State) -> dict[str, Any]:
    """Translate input text.

    Dummy: just echoes input with a prefix.
    """
    input_text = state.get("input_text", "")
    return {"translated_text": f"[translated] {input_text}"}
