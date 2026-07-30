# Guide for AI coding agents

Read in this order before changing code:

1. [architecture.md](architecture.md)
2. [database.md](database.md) for persistence work
3. [api.md](api.md) for contract work
4. [workflows.md](workflows.md) for business behavior
5. [coding-guidelines.md](coding-guidelines.md)
6. Relevant [ADRs](adr/)

The original technical specification remains authoritative for planned milestones, but these documents
describe the implemented system.

## Project philosophy

- Keep architecture clean and behavior deterministic.
- Favor readability over clever code.
- Avoid duplication, especially scheduling/scoring logic.
- Keep business logic independent from UI and HTTP.
- Prefer composition and small services over inheritance.
- Preserve audit history and private user data.
- Do not implement future milestones prematurely.

## Layer contract

```text
Routes → Services → SQLAlchemy session/models → PostgreSQL
              ↘ Pure policies
Web UI → Typed web/lib client → Routes
```

### Routes may

- Declare methods/paths/status codes and Pydantic response models.
- Accept validated request/query/path data.
- Inject a database session or settings.
- Call application services.

Routes may not calculate mastery, score candidates, parse imports, or commit transactions.

### Services may

- Orchestrate one use case and own its transaction.
- Query/update ORM models.
- Call pure policies and other established application services.
- Convert domain state into response schemas.

Create a new service when behavior forms a distinct use case, needs a transaction boundary, or would
otherwise make a route/model/component responsible for orchestration.

### Policies may

- Accept complete typed inputs and return typed/deterministic results.
- Use centralized constants/configuration.

Policies may not read clocks, databases, files, environment variables, or networks. Pass dates/settings
in. Scheduling lives in `application/scheduling/policy.py`; queue scoring lives in
`application/queues/policy.py`. Never duplicate either in UI/routes.

### Repositories

There is no repository layer. Create one only when several services share complex queries, persistence
must be swapped, or tests cannot isolate persistence cleanly. A repository must not become a generic
CRUD wrapper and must not contain business policy.

### Frontend

- `app/` owns route shells; `features/` owns interactive workflows; `lib/` owns HTTP.
- Components may format returned explanations but may not recalculate them.
- Keep accessibility, responsive layout, errors, loading, and empty states explicit.

## Folder ownership and dependency rules

- `domain` imports no application/infrastructure/API modules.
- `application` may import domain and infrastructure; pure policy modules should depend only on domain
  and their schemas.
- `infrastructure` may import domain enums, not application services or API routes.
- `api` imports application services/schemas and infrastructure DI.
- `apps/web` communicates through HTTP only.
- Do not place personal data anywhere in the repository.

## File and design expectations

- Aim for one cohesive responsibility per file. At roughly 300 lines, consider extracting a component,
  schema, policy, or helper; do not split merely to satisfy a number.
- Prefer feature-local explicit types to large generic frameworks.
- Reuse existing normalization, error envelopes, style classes, and service boundaries.
- New dependencies require written rationale: problem, why current stack cannot solve it, maintenance.

## Change procedure

1. Inspect current status and preserve unrelated user changes.
2. Read relevant docs, models, schemas, routes, services, tests, and migration head.
3. State the intended boundary; do not silently broaden scope.
4. Implement schema → policy/service → route/client → UI as applicable.
5. Add tests at the lowest useful layer plus API/UI coverage for user flows.
6. Run all lint, type, and test commands in `coding-guidelines.md`.
7. For schema changes, apply migration to PostgreSQL and test the running endpoint.
8. Rebuild the API container after backend code changes (`docker compose up -d --build api`).
9. Update documentation and editable diagrams in the same commit.
10. Commit one milestone/focused change with an imperative Conventional Commit message.

## Testing expectations

- New deterministic rule: table-driven tests and relevant invariants.
- New service mutation: success, not-found/validation, atomic summary/history behavior.
- New route: method/path/body/status contract test.
- New UI workflow: interaction test using roles/labels, not implementation details.
- New migration: fresh/offline chain plus upgrade from current head; PostgreSQL check when dialect-sensitive.
- Use fictional data only.

## Documentation requirements

| Change | Required update |
|---|---|
| Architecture/dependency/component | `architecture.md`, ADR, system diagram |
| Table/column/index/cascade | `database.md`, ER diagram, Alembic revision |
| Endpoint/request/response | `api.md` |
| User/business sequence | `workflows.md`, relevant flow diagram |
| Convention/tooling | `coding-guidelines.md`, this file if agent behavior changes |
| Major tradeoff | New `docs/adr/NNNN-title.md` |

ADRs contain Title, Status, Context, Decision, Alternatives considered, and Consequences. Never rewrite
an accepted decision to hide history; supersede it with a new ADR.

## Safety and privacy

- Never commit uploaded files, database dumps, workspaces, notes, API keys, or real user fixtures.
- Do not hard-delete attempts or queue/import history through normal feature work.
- Treat migration downgrades and data replacement as destructive.
- AI must remain optional, disabled by default, unable to issue arbitrary SQL, and require explicit
  approval before generated content is persisted as accepted user data.

## Current boundaries and next work

Implemented: repository/workspace, problem library, CSV/XLSX import, attempt tracking, deterministic
scheduling/manual overrides, persisted daily queues, and deterministic statistics/dashboard. Data
lifecycle (export/backup/restore/deletion) is the next planned milestone. AI is not implemented. Do not
present planned workflows as available features.
