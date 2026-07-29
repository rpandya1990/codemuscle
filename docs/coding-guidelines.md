# Coding guidelines

## General principles

- Prefer readable, explicit code over clever abstraction.
- Keep deterministic business logic independent of HTTP and UI frameworks.
- Preserve personal data and immutable history; avoid destructive operations.
- Do not add a dependency when the standard library/current stack is sufficient.
- Update documentation, tests, API contracts, and migrations in the same change as behavior.

## Folder and naming conventions

- Backend feature: `application/<plural_feature>/{schemas,service,policy}.py` as needed.
- HTTP adapter: `api/routes/<plural_feature>.py`; register in `api/router.py`.
- ORM model: `infrastructure/database/models/<singular_feature>.py`; export in `models/__init__.py`.
- Frontend route: `app/<route>/page.tsx`; interactive component: `features/<feature>/...tsx`.
- HTTP client and transport types: `web/lib/<feature>.ts`.
- Tests: `test_<subject>.py` and `<subject>.test.tsx`.
- Python: snake_case functions/files, PascalCase types, uppercase constants.
- TypeScript/React: camelCase functions/variables, PascalCase components/types.

## Layer responsibilities and dependencies

```text
React page/feature → TypeScript API client → FastAPI route
                                           ↓
                                      application service
                                      ↙                 ↘
                               pure policy          SQLAlchemy model/session
```

- Routes validate transport data, inject dependencies, call one service, and return schemas.
- Services implement use cases and transaction boundaries.
- Policies are pure functions: no database, filesystem, network, clock reads, or global mutation.
- ORM models map state and relationships; they do not orchestrate use cases.
- React handles interaction and presentation, never scheduling/scoring rules.
- TypeScript API clients own URLs, methods, serialization, and response types.
- Domain modules must not import infrastructure, FastAPI, or React.

## Error handling

- Define expected failures as a `DomainError` subclass with stable `code`, status, message, details.
- Do not expose stack traces, SQL, file contents, or secrets in user responses.
- Let Pydantic handle shape/range validation; use validators for cross-field invariants.
- Web clients must check `response.ok`; show actionable messages and preserve backend detail when safe.
- Never use broad exception handling to report success or silently continue after failed persistence.

## Logging

- Use stdout/stderr for container collection.
- Log operation identifiers and counts, not notes/import contents.
- Do not use `print` for permanent application logging; introduce a configured logger with structured
  fields when application events are added.
- Include exception context in server logs while keeping client messages safe.

## Dependency injection

- FastAPI dependencies provide request-scoped `Session` and runtime `Settings`.
- Construct application services in routes with those dependencies.
- Pass clocks/dates into pure policies. Services may resolve current time once per operation.
- Avoid service locators and module-level mutable singletons. `get_settings()` caching is read-only.

## SQLAlchemy conventions

- Use SQLAlchemy 2 typed `Mapped` models and `select()` statements.
- Services own commits. Multiple writes for one use case must commit atomically.
- Eager-load relationships needed after query/serialization to avoid accidental N+1 queries.
- Normalize reusable names before lookup/creation.
- Prefer soft archive/status changes when historical references exist.
- Every schema change requires a new Alembic revision and an update to `database.md`.
- Specify foreign-key delete behavior deliberately. Do not rely on implicit destructive cascades.

## Pydantic conventions

- Separate create/update/response models.
- Use enums for bounded domain vocabulary.
- Put field bounds in `Field`; use `field_validator` for invariants.
- Response models use `ConfigDict(from_attributes=True)` when validating ORM objects.
- Do not pass unvalidated dictionaries deep into services.

## Frontend conventions

- Use server page shells and client feature components for interaction.
- Use shared Tailwind component classes (`surface-card`, `field-control`, `btn-*`).
- Forms require labels and native validation where possible.
- Dialogs require `role="dialog"`, `aria-modal`, and an accessible name.
- Reset pagination when filters change; show loading, empty, error, and disabled states.
- Keep actions visible in long forms where practical; use responsive behavior rather than fixed mobile
  heights.

## Testing strategy

- Pure policy unit tests cover every branch and explanation.
- Service tests use SQLite in memory for fast transaction/relationship coverage.
- API tests use FastAPI `TestClient` and dependency-overridden sessions.
- Hypothesis covers invariants such as monotonic intervals and time budgets.
- Frontend tests use Vitest and Testing Library to exercise user-visible behavior.
- Add PostgreSQL/live-container verification for migration or dialect-sensitive changes.
- Use fictional fixtures only. Never commit personal imports or notes.

Required before completion:

```bash
uv run --project apps/api ruff check apps/api
uv run --project apps/api pyright
uv run --project apps/api pytest
pnpm --dir apps/web lint
pnpm --dir apps/web exec tsc --noEmit
pnpm --dir apps/web test -- --run
```

## Formatting and linting

- Ruff format, 100-character backend line length, Python 3.12 target.
- Ruff lint with E/F/I/UP/B/SIM; strict Pyright.
- Prettier for web source; ESLint with zero warnings; strict TypeScript.
- Use `make lint`, `make test`, and `make build` for standard checks.

## Commits and documentation

Use imperative Conventional Commit style:

```text
feat: deliver milestone 6 daily queue
fix: keep add problem action visible
docs: establish architecture reference
```

Keep commits focused and reviewable. A major decision adds an ADR. API changes update `api.md`; schema
changes update `database.md`; business-flow changes update `workflows.md`; architecture/dependency
changes update `architecture.md` and diagrams. Documentation is part of the definition of done.
