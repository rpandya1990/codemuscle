# ADR 0006: Versioned application-level backups and explicit deletion

## Status

Accepted

## Context

Local users need portable exports, complete backups, transactional restoration, and deletion of personal
data. The API container does not include PostgreSQL client utilities, and backup artifacts must include
workspace configuration and optionally private import/export files.

## Decision

Use a versioned application-level JSON database snapshot inside a ZIP archive. Store a manifest with
manifest/application/database-format versions and included directories. Encode UUID, date, datetime,
and enum values explicitly; restore tables in dependency order after deleting them in reverse order,
inside one database transaction. Restore optional files only from allowlisted archive prefixes.

Provide separate user exports: flat CSV, nested JSON, and a two-sheet XLSX. Require exact typed
confirmations for restore and deletion. Delete rows in foreign-key-safe order and clear only explicitly
selected workspace directories; preserve backup files by default.

## Alternatives considered

- **`pg_dump`/`pg_restore`:** robust PostgreSQL fidelity, but requires client binaries/version matching
  in the API image and is less portable for selective application files.
- **Copy the PostgreSQL volume:** unsafe while running, platform-specific, and difficult to validate.
- **ORM object-by-object restore:** easy to understand but slow and vulnerable to relationship side
  effects; table snapshots preserve exact IDs and ordering.
- **No typed confirmation:** faster UI, but unacceptable for data replacement or permanent deletion.

## Consequences

- Backups are self-describing and portable across supported CodeMuscle versions.
- Every schema change must evaluate and test snapshot compatibility and may require a new manifest
  version or migration adapter.
- Database restore is transactional; filesystem restoration is validated but cannot be part of that
  transaction.
- Preserving backups while deleting settings requires reinitializing the same workspace path before a
  later restore when no runtime workspace path is configured.
