"""Local entry point for running the graph.

This module is intended for local development and quick manual smoke tests.
"""

from __future__ import annotations

import asyncio

import dotenv

from agent.graph import State, graph

dotenv.load_dotenv()


async def main() -> None:
    """Run the graph with a minimal sample input. Mirrors Lambda handler function invocation after extracting necessary fields from the POST request that triggered it."""
    initial_state: State = {
        "input_text": 'ז"א באזור חברון',
        "score": 0.0,
        "threshold": 0.8,
        "iteration": 0,
        "max_iterations": 5,
        # Worker loop controls
        "remaining_tool_calls": 1,
        "worker_max_iterations": 10,
    }  # type: ignore[arg-type]
    result = await graph.ainvoke(initial_state)  # type: ignore[arg-type]
    print(result)  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
