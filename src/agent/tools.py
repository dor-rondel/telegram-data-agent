"""Stub tools for the ReAct agent.

These are placeholder implementations for development/testing.
Replace with real implementations when ready.
"""

from __future__ import annotations

from typing import Any


def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email.

    Stub implementation: does not send anything.
    """
    _ = (to, subject, body)
    return {"ok": True, "tool": "send_email"}


def push_to_dynamodb(table_name: str, item: dict[str, Any]) -> dict[str, Any]:
    """Push an item to DynamoDB.

    Stub implementation: does not write anything.
    """
    _ = (table_name, item)
    return {"ok": True, "tool": "push_to_dynamodb"}


# Export tools for use in the graph
TOOLS = [send_email, push_to_dynamodb]
