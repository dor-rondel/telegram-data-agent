"""Local entry point for running the graph.

This module is intended for local development and quick manual smoke tests.
"""

from __future__ import annotations

import asyncio

from agent.graph import graph


async def main() -> None:
    """Run the graph with a minimal sample input."""
    result = await graph.ainvoke({"changeme": "hello"})  # type: ignore
    print(result)  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
