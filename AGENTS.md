
# AGENTS.md

## Project

`inventory-mcp` is a small Python MCP project focused on clean architecture, maintainability, and clear demonstration of MCP concepts.

## Engineering Rules

* Implement only the requested scope.
* Keep changes small, focused, and easy to review.
* Prefer simple, explicit solutions over unnecessary abstractions.
* Preserve separation of concerns between MCP, services, schemas, and data access.
* Use type hints and clear naming.
* Validate all external inputs.
* Do not hide errors or silently ignore failures.
* Do not refactor unrelated code.

## Architecture

* `tools/`: MCP-facing functions.
* `services/`: business logic.
* `schemas/`: Pydantic models and validation.
* `data/`: local inventory data.
* `tests/`: automated tests.

MCP tools must delegate business logic to services.

## Dependencies

Use only dependencies required by the current scope.

Do not add AI/LLM frameworks, databases, web frameworks, or infrastructure tools unless explicitly requested.

## Quality

* Use Ruff for linting and formatting.
* Use pytest for tests.
* Add tests for relevant behavior and bug fixes.
* Keep public functions typed and documented when needed.
* Keep README consistent with the implemented behavior.

## MCP

* Start with read-only tools.
* Initial tools: `get_product` and `get_stock`.
* Tool descriptions must clearly define purpose, expected input, and output.
* Do not introduce write operations unless explicitly requested.
* Support transports incrementally; implement only the transport requested in the current task.

## Priority

Correctness > clarity > maintainability > simplicity.
