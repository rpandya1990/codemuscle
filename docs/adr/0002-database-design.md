# ADR 0002: PostgreSQL relational model with immutable event history

## Status

Accepted

## Context

Scheduling depends on ordered attempts; imports and queues need traceability; topics/patterns are
shared classifications. The system must preserve audit history and support reliable constraints,
transactions, UUIDs, enums, JSON metadata, and future statistics.

## Decision

Use PostgreSQL 16 as the authoritative store, SQLAlchemy 2 typed mappings, and linear Alembic
migrations. Model problems as current summaries, attempts as immutable events, imports as job/row
staging, and daily queues as persisted session/item snapshots. Use relational foreign keys for
identity and JSON only for variable mappings, reasons, legacy metadata, and preferences.

Use soft archive/status transitions for normal lifecycle operations. Restrict problem deletion when
attempts or queue items reference it. Cascade only association rows and owned child rows.

## Alternatives considered

- **SQLite:** excellent zero-configuration local storage, but differs in enums, concurrency, JSON,
  indexing, and future analytical behavior; PostgreSQL is already the intended production semantics.
- **Document database:** flexible payloads, but poor fit for relationships, constraints, ordered event
  history, and aggregate statistics.
- **Overwrite-only problem summaries:** simpler reads but loses the evidence needed to explain and
  reproduce scheduling decisions.
- **Event sourcing for every entity:** maximal auditability but excessive complexity for metadata CRUD.

## Consequences

- Strong relational integrity and transactional attempt/summary updates.
- Docker/PostgreSQL is required for normal operation; SQLite tests must be supplemented for
  dialect-sensitive behavior.
- Schema changes require migrations and documentation updates.
- Denormalized counters improve reads but must be updated atomically with attempt insertion.
