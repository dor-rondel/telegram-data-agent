"""Stub tool: send_email.

This tool is a placeholder and intentionally has no side effects.
"""

from __future__ import annotations

from typing import Any


def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email.

    Stub implementation: does not send anything.
    """
    _ = (to, subject, body)
    return {"ok": True, "tool": "send_email"}
