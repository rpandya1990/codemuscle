# ADR 0002: Remove data import

- Status: Accepted
- Date: 2026-07-28

## Context

CodeMuscle briefly included CSV and Excel ingestion with mapping, preview, duplicate review, and
retry behavior. The product owner decided to remove that workflow and its code completely.

## Decision

Remove import pages, API endpoints, application services, persistence models, dependencies, and
tests. New workspaces no longer create an imports directory. A forward database migration removes
the import tables and problem traceability columns from databases that previously applied the
feature migration.

The historical migration remains in the Alembic chain so existing and newly created databases can
reach the current schema deterministically. Private files already present in a user's workspace are
not deleted automatically.

## Consequences

CSV and Excel preparation history cannot be ingested through CodeMuscle. Future implementation
agents must treat import-related sections of the original technical specification as superseded.
