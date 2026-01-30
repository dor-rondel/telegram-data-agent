#!/usr/bin/env python3
"""Export the agent graph as a PNG image.

Generates a visual representation of the graph and saves it to static/graph.png.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    """Generate and save the graph diagram."""
    from agent.graph import graph

    # Get the graph's mermaid representation and render to PNG
    png_bytes = graph.get_graph().draw_mermaid_png()

    # Write to static/graph.png
    output_path = Path(__file__).parent.parent / "static" / "graph.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png_bytes)

    print(f"Graph diagram saved to {output_path}")  # noqa: T201


if __name__ == "__main__":
    main()
