# telegram-data-agent

LangGraph-based data agent for ingesting Telegram channel messages, transforming them (translate/parse/tag), and then persisting or notifying based on match criteria.

Target runtime: AWS Lambda.

## What This Repo Contains

- A LangGraph graph entrypoint defined in [langgraph.json](langgraph.json) and implemented in [src/agent/graph.py](src/agent/graph.py).
- Unit tests under [tests/](tests/).
- Project-wide engineering rules for agents in [.github/workflows/AGENTS.md](.github/workflows/AGENTS.md).

## Installation

Python 3.11+ is required.

Create and activate a virtual environment, then install the package in editable mode:

- `python -m venv .venv`
- `source .venv/bin/activate`
- `python -m pip install -U pip`
- `python -m pip install -e ".[dev]"`

Notes:

- `.[dev]` installs developer tooling (Ruff, Pyright, pytest, codespell, LangGraph CLI).
- The LangGraph CLI uses [langgraph.json](langgraph.json) and will load environment variables from `.env` if present.

## Linting, Formatting, Type Checking, and Spelling

Run these from the repository root:

- Lint: `ruff check .`
- Format: `ruff format .`
- Type check: `pyright`
- Unit tests: `pytest`
- Spell check: `codespell --toml pyproject.toml`

There are also Make targets:

- `make lint`
- `make format`
- `make test`
- `make spell_check`

## Running the LangGraph Dev Server ("LangSmith backend")

For local development, you can run the LangGraph dev server:

- `langgraph dev`

This uses [langgraph.json](langgraph.json) to locate the graph (`agent`) and will load `.env` automatically (as configured in `langgraph.json`).

If you want traces in LangSmith, set the relevant LangSmith environment variables in `.env` (or your shell) before starting `langgraph dev`.

## Running the Python Agent Locally

For a quick manual smoke test, run the module entry point:

- `python -m agent`

This invokes the graph with a minimal sample input and prints the result. For more thorough validation, prefer unit tests under [tests/](tests/).

## Roadmap (High Level)

- Telegram ingestion adapter (channel polling / webhook ingestion)
- Message translation, parsing, and tagging nodes
- DynamoDB persistence repository + idempotency
- Email notifier adapter (for example, SES)
