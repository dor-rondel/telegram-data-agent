"""Stub tool: push_to_dynamodb.

This tool is a placeholder and intentionally has no side effects.
"""

from __future__ import annotations

from typing import Any


def push_to_dynamodb(table_name: str, item: dict[str, Any]) -> dict[str, Any]:
    """Push an item to DynamoDB.

    Stub implementation: does not write anything.
    """
    _ = (table_name, item)
    return {"ok": True, "tool": "push_to_dynamodb"}
