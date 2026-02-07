# Agent Instructions (Project-Wide)

This repository is a Python 3.11+ side project built around a LangGraph (1.0+) agent that processes Telegram channel messages. The agent includes nodes for translating, parsing, and tagging messages, then persisting results to DynamoDB and/or sending email alerts when certain criteria match. The target runtime is AWS Lambda.

These instructions are authoritative for any automated coding agent working in this repo.

## Current Architecture

The graph flows through these nodes:

1. **translate** → **evaluate** (loop until quality threshold met)
2. **plan** (extracts `IncidentDataModel`: location + crime type)
3. **worker** (validates an `ActionPlan` then executes `push_to_dynamodb` and optionally `send_email`)

### Structured Output (Pydantic v2)

All LLM outputs that require structured data are validated against Pydantic v2 models
using LangChain's `with_structured_output()`. This eliminates manual JSON parsing and
guarantees schema conformity at the LLM layer.

- `PlanResponse` – plan node output (relevant, location, crime, requires_email_alert)
- `EvaluationResponse` – evaluate node output (score 0-10, feedback)
- `ActionPlan` / `WorkerAction` – worker node action list (action name, location, crime)
- `IncidentDataModel` – shared incident payload model

Crime types and worker action names use `typing.Literal` for compile-time and
runtime validation.

### State Schema

- `IncidentDataModel` contains only `location` and `crime` (no timestamp)
- Timestamps are generated locally within each tool at execution time using ISO 8601 format
- This design avoids state synchronization issues and ensures accurate timestamps

### Structured Output (Pydantic v2)

All LLM outputs are validated against Pydantic v2 models using LangChain's `with_structured_output()`:

- **`PlanResponse`** – Validates plan node output (relevant flag, location, crime type, email alert flag)
- **`EvaluationResponse`** – Validates evaluate node output (score 0-10, feedback)
- **`ActionPlan`** / **`WorkerAction`** – Validates worker actions before any tool execution

Crime types and worker action names use `typing.Literal` for compile-time and runtime validation.
On parse/validation errors, nodes return safe state (e.g., `skip_processing=True`, `should_end=True`) and route to END rather than raising exceptions.

## Core Principles

- Prefer small, reviewable changes over large refactors.
- Optimize for correctness, clarity, and long-term maintainability.
- Keep business logic pure and testable; isolate I/O behind adapters.
- Use stable, public LangGraph 1.0 APIs (avoid deprecated or internal symbols).

## Quality Gates (Must Pass)

Before considering a change complete, run the following from the repo root:

- `ruff check .`
- (Optional) `ruff format .`
- `pyright`
- `pytest`

Spelling must be correct. Verify with `codespell` (install it if needed in your dev environment).

Notes:

- Ruff is configured to lint Python source; running `ruff check .` is the correct invocation (do not point Ruff at Markdown files).
- If you change only documentation, still run `codespell` and `ruff check .`.

## Python Style and Documentation

- PEP 8 compliance is required.
- All public modules, classes, and functions must have PEP 257 compliant docstrings.
  - This repo uses Ruff `pydocstyle` with the `google` convention; follow Google-style docstrings while remaining PEP 257 compliant.
- Avoid cleverness. Prefer explicit, readable code.
- Prefer `pathlib.Path` over `os.path`.
- Keep functions small and single-purpose.

## Typing (Strict)

- Use the standard library `typing` module for type annotations.
- This repo uses `pyright` in `strict` mode; treat type errors as build failures.
- Avoid `Any` unless there is a concrete, documented reason.
- Prefer `TypedDict`, `dataclass`, `Protocol`, and Pydantic `BaseModel` where they improve correctness.
- Use Pydantic v2 models with `Literal` types for structured LLM output validation.
- Use `from __future__ import annotations` in new modules.

## Security

- Treat security as a first-class requirement.
- Never log or commit secrets (API keys, tokens, credentials), including `GROQ_API_KEY`.
  - Redact sensitive values in logs and error messages.
  - Prefer AWS-managed secret storage for production (for example, Secrets Manager or SSM Parameter Store) and load via environment variables at runtime.
- Use least privilege everywhere:
  - Lambda IAM role should allow only the exact DynamoDB table actions and SES actions needed.
- Validate all untrusted inputs.
  - Telegram message content is untrusted; parse defensively and fail closed on schema mismatches.
  - Avoid dynamic code execution (`eval`, `exec`) and unsafe deserialization.
- Handle PII responsibly.
  - Assume messages may contain personal data; minimize what is stored and what is emitted in logs.
- LLM-specific risks (LangChain + Groq):
  - Treat model output as untrusted; validate before using it to drive branching, writes, or notifications.
  - Guard against prompt injection and data exfiltration.
    - Do not include secrets or internal-only data in prompts.
    - If adding tools or function calling, enforce explicit allowlists and validate tool arguments.
- Dependency and supply-chain hygiene:
  - Prefer well-maintained libraries; avoid adding dependencies unless necessary.
  - Pin and review new dependencies; do not introduce packages with unclear provenance.

## Architecture Guidelines

### Separation of Concerns

- Keep LangGraph node functions focused on transforming state.
- Put external integrations behind narrow, injectable interfaces:
  - Telegram fetching/parsing adapter(s)
  - Translation service adapter(s)
  - DynamoDB repository
  - Email notifier

### Determinism and Idempotency

- Node functions should be deterministic given the same input state and configuration.
- Design DynamoDB writes and email notifications to be idempotent.
  - Use conditional writes (for example, based on a message id + channel id key) and deduplication where appropriate.

## LangGraph (1.0+) Conventions

- Use `StateGraph` with explicit state types.
- Prefer typed configuration via context schemas (for example, `TypedDict` context) rather than unstructured globals.
- Do not rely on internal LangGraph modules or undocumented behavior.
- If unsure about a LangGraph feature or API shape, use the Context7 MCP server to fetch up-to-date docs before implementing.

## LangChain + Groq Conventions

- The LLM provider for this project is Groq, accessed via LangChain.
- Construct LLM clients in a dedicated adapter/factory (not in business-logic functions), so they can be swapped or faked in tests.
- Read credentials and model configuration from environment variables and document any new variables.
  - Example: `GROQ_API_KEY`
  - Example: `GROQ_MODEL` (or an equivalent project-specific variable)
- Do not hardcode model names, API keys, endpoints, or prompts in multiple places; centralize configuration.
- Use `llm.with_structured_output(PydanticModel)` for nodes that require structured responses.
  - Define output models in `agent.state` using Pydantic v2 `BaseModel` with `Literal` types.
  - On validation failures, return safe state values that route the graph to END rather than raising.
- Unit tests must not make network calls to Groq.
  - Use dependency injection and fakes/mocks for LangChain LLM clients.
  - Prefer narrow interfaces around "generate"/"invoke" behavior so tests validate prompting and post-processing deterministically.

## AWS Lambda Conventions

- Treat the Lambda handler as a thin entry point.
- Keep cold-start cost low:
  - Create AWS SDK clients at module scope for reuse across invocations.
  - Avoid heavy imports and unnecessary global initialization.
- Use structured logging and include request identifiers where available.
- Read configuration exclusively from environment variables (and document any new variables).
- Never commit secrets.

## DynamoDB Conventions

- Use boto3 DynamoDB clients/resources via a dedicated repository layer.
- Validate and normalize data before writing.
- Prefer explicit attribute names and stable key design.
- The partition key name is configurable via `DYNAMODB_PARTITION_KEY` env var (defaults to `year_month`).
- Incidents are stored in monthly partitions with an `incidents` list attribute.
- Each incident entry includes: `incident_id`, `location`, `crime`, and `created_at` (ISO 8601 string).
- Handle retries and conditional failures intentionally; do not silently drop errors.

## Email Conventions

- Prefer AWS SES (or another AWS-native service) via a dedicated notifier adapter.
- Ensure notifications are deduplicated to avoid repeated alerts.
- Keep email templates simple and testable.

## Testing (pytest)

- Add or update unit tests for any non-trivial behavior.
- Prefer pure unit tests with dependency injection and fakes.
- For AWS integrations, prefer `botocore.stub.Stubber` or small adapter-level fakes.
- Tests must be deterministic and must not call external services.

## Repo Hygiene

- Keep imports sorted (Ruff enforces this).
- Do not introduce new dependencies without a clear justification.
- Update documentation (README, module docstrings) when behavior or configuration changes.
