# ADR 0001: Local-first modular monolith technology stack

## Status

Accepted

## Context

CodeMuscle needs a responsive local UI, typed HTTP contracts, relational history, deterministic Python
policies, and simple one-command development. It does not currently need independent service scaling.

## Decision

Use a pnpm monorepo with Next.js/React/TypeScript/Tailwind for the web application and a Python
FastAPI/Pydantic/SQLAlchemy API backed by PostgreSQL 16. Package and run local services with Docker
Compose; use `uv`, Alembic, Pytest/Hypothesis, Vitest, Ruff/Pyright, and ESLint/TypeScript.

Keep one modular API deployment. Organize behavior by application feature and maintain pure policy
modules for deterministic algorithms.

## Alternatives considered

- **Single Next.js full-stack application:** simpler deployment but weaker fit for Python scheduling,
  import tooling, and future controlled AI adapters.
- **Django:** strong integrated framework, but more framework surface than the current API-first design
  requires.
- **Microservices:** independent scaling, but unnecessary network/operations/transaction complexity.
- **Desktop-native application:** stronger local packaging, but slower web-centric iteration and fewer
  familiar testing tools for this team.

## Consequences

- Clear browser/API/database boundaries and strong types on both sides.
- Two language toolchains and container rebuild awareness are required.
- New backend routes require rebuilding the API image unless running Uvicorn with reload.
- Services can be extracted later, but cross-module transactions currently remain simple and local.
