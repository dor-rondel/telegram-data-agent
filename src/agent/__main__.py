"""Local entry point for running the graph.

This module is intended for local development and quick manual smoke tests.
"""

from __future__ import annotations

import asyncio

from agent.graph import State, graph


async def main() -> None:
    """Run the graph with a minimal sample input."""
    initial_state: State = {
        "input_text": "Hello, this is a test message.",
        "score": 0.0,
        "threshold": 0.8,
        "iteration": 0,
        "max_iterations": 5,
        # Dummy worker loop controls
        "remaining_tool_calls": 1,
        "worker_max_iterations": 10,
    }  # type: ignore[arg-type]
    result = await graph.ainvoke(initial_state)  # type: ignore[arg-type]
    print(result)  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
