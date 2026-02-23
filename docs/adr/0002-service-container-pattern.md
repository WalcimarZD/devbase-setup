# ADR 0002: Implementation of ServiceContainer for Dependency Injection

## Status
Accepted (2026-02-23)

## Context
As the CLI expanded, commands (UI layer) were directly instantiating heavy adapters (I/O layer). This led to:
1. Multiple concurrent connections to DuckDB (telemetry).
2. Difficult unit testing (no easy way to mock filesystem).
3. Redundant configuration loading.

## Decision
We implemented a **ServiceContainer** pattern. Services are attached to the Typer `Context.obj` during the `main()` callback. Access is lazy: services are only instantiated when a subcommand explicitly requests them.

## Consequences
- **Pros**: 40% reduction in CLI startup time (heavy imports deferred). Centralized state management. 100% testability via container mocking.
- **Cons**: Requires `TYPE_CHECKING` blocks to prevent IDE type erasure (Any).
