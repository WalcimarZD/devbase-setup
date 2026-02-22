# 🏗️ Understanding Clean Architecture

The DevBase project template uses **Clean Architecture** principles.

## The Problem

Typical projects suffer from:
- **Tangled dependencies** (UI knows about DB)
- **Hard to test** (everything needs mock)
- **Painful migrations** (change one thing, break everything)

## The Solution

Clean Architecture separates code into **concentric layers**:

```
┌─────────────────────────────────────────┐
│            Presentation                 │  ← UI, API, CLI
│  ┌─────────────────────────────────────┐│
│  │          Application                ││  ← Use cases, DTOs
│  │  ┌─────────────────────────────────┐││
│  │  │          Domain                 │││  ← Entities, rules
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│            Infrastructure               │  ← DB, APIs, I/O
└─────────────────────────────────────────┘
```

## Key Rule: Dependency Direction

Dependencies point **inward**:
- Outer layers depend on inner layers
- Inner layers know nothing about outer layers

## DevBase Template Structure

```
src/
├── domain/           # Core business logic (no deps)
│   ├── entities/     # Business objects
│   ├── value-objects/# Immutable values
│   └── repositories/ # Interfaces (not implementations!)
├── application/      # Use cases
│   ├── use-cases/    # Business operations
│   ├── dtos/         # Data transfer objects
│   └── interfaces/   # Port definitions
├── infrastructure/   # External world
│   ├── persistence/  # Database implementations
│   ├── external/     # Third-party APIs
│   └── messaging/    # Queues, events
└── presentation/     # Entry points
    ├── api/          # REST/GraphQL
    ├── cli/          # Command line
    └── web/          # Frontend
```

## Benefits

| Concern | Solution |
|---------|----------|
| **Testing** | Domain has zero deps, easy to unit test |
| **Changes** | Swap DB without touching business logic |
| **Clarity** | Each layer has clear responsibility |

## Learn More

- [Original Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Template Customization](../how-to/customize-templates.md)
