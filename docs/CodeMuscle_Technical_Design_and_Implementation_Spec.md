# CodeMuscle v1 — Technical Design and Implementation Specification

**Document purpose:** Provide an implementation-ready technical specification that a coding agent can follow to build CodeMuscle v1.

**Product source:** This document translates the approved *CodeMuscle v1 Functional Specification* into technical architecture and implementation decisions. The product requirements remain the source of truth. Where this document introduces technologies, schemas, APIs, or engineering conventions, those are implementation decisions rather than changes to the product scope.

---

## 1. Product definition

CodeMuscle is a private, open-source coding interview revision tracker that helps users remember solved problems by:

- Building a personal coding-problem library
- Recording every practice attempt
- Calculating the next revision date
- Generating a daily revision queue
- Explaining why each problem was selected
- Measuring retention across topics and patterns
- Importing existing Excel or CSV preparation history
- Exporting, backing up, restoring, and deleting personal data
- Optionally using AI for suggestions and summaries

The primary product question is:

> **What coding problems should I revise today?**

CodeMuscle must remain fully usable without AI.

---

## 2. Engineering principles

The implementation must follow these principles:

1. **Deterministic core**
   - Scheduling, mastery calculation, queue generation, statistics, imports, backups, and exports must not depend on an LLM.
   - The same inputs must produce the same result unless randomness is explicitly seeded.

2. **AI is optional**
   - AI functionality must be isolated behind interfaces.
   - Disabling AI must not break any non-AI flow.
   - AI suggestions must never be written automatically without user approval.

3. **Private by default**
   - Personal data, imports, exports, backups, notes, API keys, and preferences must remain outside the Git repository.
   - The public repository may contain only source code, documentation, configuration templates, tests, and fictional sample data.

4. **Mainstream startup stack**
   - Prefer broadly adopted technologies with strong ecosystems.
   - Avoid niche frameworks unless they solve a demonstrated problem.

5. **Single deployable application initially**
   - Use a modular monolith, not microservices.
   - Keep frontend and backend separately organized but developed in one repository.

6. **API-first boundaries**
   - The frontend must communicate with the backend through documented HTTP APIs.
   - Business logic must not be implemented in React components.

7. **Test important behavior**
   - Scheduling and queue behavior require strong unit and property-based tests.
   - Attempt history must be immutable from normal product flows.

---

## 3. Selected technology stack

### 3.1 Frontend

| Area | Technology | Reason |
|---|---|---|
| Framework | Next.js with React | Mainstream React framework used widely by startups |
| Language | TypeScript | Static typing and broad ecosystem support |
| Styling | Tailwind CSS | Common utility-first CSS framework |
| Components | shadcn/ui | Accessible, customizable components without a heavy proprietary abstraction |
| Server state | TanStack Query | Fetching, caching, mutation, loading, and error handling |
| Forms | React Hook Form | Efficient form state management |
| Validation | Zod | Client-side schemas and form validation |
| Charts | Recharts | Sufficient for dashboard and topic statistics |
| Testing | Vitest + React Testing Library | Unit and component tests |
| End-to-end | Playwright | Browser-level tests for critical workflows |
| Package manager | pnpm | Fast, space-efficient, common in modern TypeScript projects |

#### Frontend constraints

- Use the Next.js App Router.
- Use Next.js as the frontend framework, not as the primary business-logic backend.
- Do not use Next.js Server Actions for core domain operations in v1.
- All durable operations must call the FastAPI backend.
- Prefer server-rendered page shells where convenient, but use client components for interactive tables, filters, forms, queue editing, and attempt entry.
- Do not add Redux initially. Use:
  - TanStack Query for server state
  - Local React state for small UI state
  - URL search parameters for shareable filters
  - A lightweight store such as Zustand only if a demonstrated cross-page UI-state problem appears

### 3.2 Backend

| Area | Technology | Reason |
|---|---|---|
| Language | Python 3.12+ | Strong backend, data, AI, and agent ecosystem |
| API framework | FastAPI | Typed APIs, OpenAPI generation, async support |
| Validation | Pydantic v2 | Typed request, response, import, settings, and AI schemas |
| ORM | SQLAlchemy 2.x | Mature and widely used relational ORM |
| Migrations | Alembic | Standard migration tool for SQLAlchemy |
| Dependency management | uv | Modern Python project and environment management |
| Linting/formatting | Ruff | Fast, consolidated linting and formatting |
| Type checking | Pyright | Strong static analysis |
| Testing | pytest | Standard Python test framework |
| Property testing | Hypothesis | Useful for scheduling and queue invariants |
| HTTP server | Uvicorn | Development ASGI server |
| Production process | Gunicorn with Uvicorn workers, if deployed | Common production process model |

### 3.3 Database

| Area | Technology |
|---|---|
| Primary database | PostgreSQL 16+ |
| Local development | PostgreSQL through Docker Compose |
| Migrations | Alembic |
| Flexible metadata | PostgreSQL JSONB only where justified |
| Search | PostgreSQL text search and trigram similarity initially |

#### Why PostgreSQL instead of SQLite

SQLite would be valid for a strictly personal local utility, but PostgreSQL is selected because the user explicitly wants a mainstream startup stack and transferable architecture experience.

PostgreSQL provides:

- Strong relational modeling
- Foreign keys and constraints
- Transactional integrity
- Concurrent access
- Better operational similarity between development and deployment
- Rich aggregations for topic statistics
- JSONB for limited flexible metadata
- Full-text and trigram search
- A straightforward path to future hosted or multi-user versions

Local setup must remain simple through Docker Compose.

#### Why SQL instead of NoSQL

CodeMuscle's core data is relational:

- A problem has many attempts.
- A problem has many topics.
- A topic belongs to many problems.
- A problem may have many patterns.
- Scheduling depends on ordered attempt history.
- Statistics require grouping, filtering, counting, and aggregation.
- Imports and duplicate handling require uniqueness rules and transactions.
- Backup, restore, and deletion require predictable consistency.

A document database would either duplicate data or move relational behavior into application code. PostgreSQL is the better default. JSONB may be used for flexible import metadata or AI traces, but must not replace normalized core entities.

### 3.4 Local development and infrastructure

| Area | Technology |
|---|---|
| Containers | Docker + Docker Compose |
| Local services | Backend, frontend, PostgreSQL |
| CI | GitHub Actions |
| Configuration | `.env` files locally; environment variables in deployment |
| API documentation | FastAPI-generated OpenAPI and Swagger UI |
| Logging | Python standard logging with structured JSON-ready fields |
| Observability later | OpenTelemetry-compatible tracing |
| Deployment later | Render, Railway, Fly.io, AWS, or similar; not required for v1 |

### 3.5 AI and agent stack

AI is not part of the deterministic MVP core. Add it only after Milestones 1–7 are stable.

| Area | Technology | Usage |
|---|---|---|
| Local model runtime | Ollama | Run open models locally |
| Model API style | OpenAI-compatible chat/tool-calling interface | Keep local and hosted adapters consistent |
| Agent orchestration | LangGraph | Stateful agent workflows after basic AI features work |
| Tool definitions | Typed Python functions and Pydantic schemas | Restrict agent capabilities |
| Hosted-model adapters | Separate provider adapters | Optional cloud-provider support |
| Evaluation | pytest datasets initially; dedicated evaluation framework later if needed | Regression testing |
| Production open-model serving later | vLLM | Only if self-hosting on GPU infrastructure becomes necessary |
| Interoperability later | MCP server | Expose CodeMuscle tools/resources to compatible assistants |

#### Agent framework rule

Do not use LangGraph for simple classification or summarization calls. Use ordinary typed model calls for:

- Topic suggestions
- Pattern suggestions
- Failure-reason classification
- Weekly summary generation

Use LangGraph only when a workflow needs:

- Multiple steps
- Persistent state
- Tool calls
- User approval
- Pause/resume behavior
- Recovery after failure

#### AI provider interface

The domain and application layers must not import Ollama-, OpenAI-, Anthropic-, or LangGraph-specific classes directly.

Define an internal interface similar to:

```python
from typing import Protocol

class AIService(Protocol):
    async def suggest_topics(self, request: TopicSuggestionRequest) -> TopicSuggestionResult:
        ...

    async def analyze_failure_notes(self, request: FailureAnalysisRequest) -> FailureAnalysisResult:
        ...

    async def generate_weekly_summary(self, request: WeeklySummaryRequest) -> WeeklySummaryResult:
        ...
```

Provider implementations belong under the infrastructure or integrations layer.

---

## 4. High-level architecture

```text
Browser
  |
  v
Next.js / React frontend
  |
  | HTTPS / JSON
  v
FastAPI backend
  |
  +--> Application services
  |      +--> Problem library
  |      +--> Attempt tracking
  |      +--> Scheduling
  |      +--> Daily queue
  |      +--> Statistics
  |      +--> Import/export
  |      +--> Backup/restore
  |
  +--> PostgreSQL
  |
  +--> Private workspace filesystem
  |      +--> imports/
  |      +--> exports/
  |      +--> backups/
  |
  +--> Optional AI service
         +--> Ollama
         +--> Hosted providers
         +--> LangGraph workflows later
```

### 4.1 Architectural style

Use a **modular monolith** with clear internal boundaries:

- API layer
- Application/service layer
- Domain layer
- Persistence layer
- Import/export layer
- AI integration layer

Do not create independent microservices.

### 4.2 Backend dependency direction

```text
API routes
  -> application services
      -> domain logic
      -> repository interfaces
          -> SQLAlchemy implementations
```

Domain scheduling and mastery logic must be executable in unit tests without FastAPI or PostgreSQL.

---

## 5. Repository structure

```text
codemuscle/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── public/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── api/
│       ├── src/
│       │   └── codemuscle/
│       │       ├── api/
│       │       │   ├── routes/
│       │       │   ├── dependencies.py
│       │       │   └── errors.py
│       │       ├── application/
│       │       │   ├── problems/
│       │       │   ├── attempts/
│       │       │   ├── scheduling/
│       │       │   ├── queues/
│       │       │   ├── statistics/
│       │       │   ├── imports/
│       │       │   ├── exports/
│       │       │   └── backups/
│       │       ├── domain/
│       │       │   ├── models/
│       │       │   ├── enums/
│       │       │   ├── services/
│       │       │   └── exceptions.py
│       │       ├── infrastructure/
│       │       │   ├── database/
│       │       │   ├── repositories/
│       │       │   ├── filesystem/
│       │       │   └── ai/
│       │       ├── config.py
│       │       └── main.py
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── fixtures/
│       ├── alembic/
│       ├── alembic.ini
│       └── pyproject.toml
│
├── packages/
│   └── api-client/
│       └── generated/
│
├── docs/
│   ├── architecture/
│   └── decisions/
│
├── sample-data/
│   └── fictional/
│
├── scripts/
├── .github/
│   └── workflows/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pnpm-workspace.yaml
├── Makefile
└── README.md
```

### Repository rules

- Do not commit a real `.env`.
- Do not commit user imports, exports, backups, notes, or database dumps.
- Do not put the private workspace under the repository root by default.
- `sample-data/` must contain fictional data only.
- Generate the TypeScript API client from FastAPI's OpenAPI specification when practical.

---

## 6. Private workspace design

On first use, ask the user to select or confirm a workspace directory.

Example:

```text
~/CodeMuscleData/
├── imports/
├── exports/
├── backups/
├── logs/
└── workspace.json
```

The PostgreSQL database remains a service rather than a file inside the workspace. The workspace stores user-managed files and metadata.

`workspace.json` may contain non-secret values such as:

```json
{
  "workspace_version": 1,
  "created_at": "2026-07-27T12:00:00Z",
  "imports_directory": "imports",
  "exports_directory": "exports",
  "backups_directory": "backups"
}
```

Secrets and API keys must be stored in environment variables or an operating-system secret store later. They must not be written to `workspace.json`.

---

## 7. Domain model

### 7.1 Problem

Required field:

- `title`

Optional or generated fields:

- `id`
- `url`
- `platform`
- `platform_identifier`
- `difficulty`
- `notes`
- `priority`
- `date_added`
- `current_mastery_state`
- `mastery_overridden`
- `next_revision_date`
- `next_revision_overridden`
- `estimated_duration_minutes`
- `archived_at`
- `created_at`
- `updated_at`

### 7.2 Topic

Fields:

- `id`
- `name`
- `normalized_name`
- `created_at`

A problem may have multiple topics.

### 7.3 Pattern

Fields:

- `id`
- `name`
- `normalized_name`
- `created_at`

A problem may have multiple patterns. Patterns are optional in v1.

### 7.4 Attempt

Every practice event must create a new immutable attempt row.

Fields:

- `id`
- `problem_id`
- `attempted_at`
- `outcome`
- `hint_usage`
- `time_spent_minutes`
- `notes`
- `previous_mastery_state`
- `calculated_mastery_state`
- `previous_revision_date`
- `calculated_next_revision_date`
- `schedule_explanation`
- `created_at`

Attempt rows must not be overwritten by normal edit flows. Corrections should use an explicit administrative correction mechanism later, or append a correction record.

### 7.5 Mastery states

Use an enum:

- `NEW`
- `LEARNING`
- `FRAGILE`
- `RETAINED`
- `MASTERED`
- `NEEDS_RELEARNING`
- `ARCHIVED`

### 7.6 Attempt outcomes

Use an enum:

- `SOLVED_INDEPENDENTLY`
- `SOLVED_SMALL_HINT`
- `SOLVED_SIGNIFICANT_HELP`
- `UNDERSTOOD_AFTER_SOLUTION`
- `FAILED`
- `SKIPPED`

### 7.7 Hint usage

Use an enum:

- `NONE`
- `SMALL`
- `SIGNIFICANT`
- `SOLUTION_VIEWED`
- `NOT_APPLICABLE`

### 7.8 Difficulty

Use an enum initially:

- `EASY`
- `MEDIUM`
- `HARD`
- `UNKNOWN`

Do not make the database depend on a specific coding platform's naming conventions.

### 7.9 Priority

Use an integer range such as `1–5`, with `3` as the default.

---

## 8. Proposed PostgreSQL schema

Use UUID primary keys.

### 8.1 Tables

```text
problems
topics
patterns
problem_topics
problem_patterns
attempts
import_jobs
import_rows
user_preferences
queue_sessions
queue_items
backup_records
ai_suggestions
```

### 8.2 Key relationships

```text
problems 1 --- N attempts

problems N --- N topics
  through problem_topics

problems N --- N patterns
  through problem_patterns

queue_sessions 1 --- N queue_items
queue_items N --- 1 problems

import_jobs 1 --- N import_rows
```

### 8.3 Important constraints and indexes

- Unique index on `topics.normalized_name`
- Unique index on `patterns.normalized_name`
- Index on `problems.next_revision_date`
- Index on `problems.current_mastery_state`
- Index on `problems.archived_at`
- Index on `attempts.problem_id, attempts.attempted_at`
- Index on `queue_items.queue_session_id, queue_items.position`
- Unique or partial indexes for platform identifiers where reliable
- PostgreSQL trigram index on normalized problem title for duplicate detection
- Check constraints for priority and duration ranges

### 8.4 Queue persistence

Persist generated queue sessions so the user can:

- Remove a problem
- Replace a problem
- Postpone a problem
- Add a problem
- Mark a problem complete
- Review why a recommendation was made

A queue item should store the recommendation reason as generated at that time, rather than recalculating and changing history later.

---

## 9. Scheduling engine

### 9.1 Outcome-based revision intervals

Use these broad-coverage baselines:

```text
failed: 7 days
understood after solution or skipped: 14 days
significant help: 30 days
small hint: 60 days
independent without hints: the configured long-term interval, reduced 25% for medium/unknown and 50%
for hard
```

Hard difficulty shortens hint-assisted and unsuccessful baselines by 25%, and priority 5 shortens
the result by a further 20%.

### 9.2 Scheduling inputs

The scheduling service must consider:

- Attempt outcome
- Hint usage
- Continuous successful revisions
- Difficulty
- User priority
- Existing manual override state

### 9.3 Scheduling output

Return a typed result:

```python
class SchedulingResult(BaseModel):
    next_revision_date: date
    mastery_state: MasteryState
    successful_revision_streak: int
    explanation: str
    factors: list[str]
```

### 9.4 Initial deterministic policy

Implement a simple, explainable policy first.

Suggested baseline:

- `FAILED`
  - Reset successful streak to `0`
  - Move state to `NEEDS_RELEARNING`
  - Schedule in `7 days`

- `UNDERSTOOD_AFTER_SOLUTION`
  - Reset or keep streak at `0`
  - Move state to `LEARNING`
  - Schedule in `14 days`

- `SOLVED_SIGNIFICANT_HELP`
  - Do not advance more than one stage
  - State is `LEARNING` or `FRAGILE`
  - Schedule in `30 days`

- `SOLVED_SMALL_HINT`
  - Advance cautiously
  - Schedule in `60 days`

- `SOLVED_INDEPENDENTLY`
  - Increase successful streak
  - Use the configured long-term interval, reduced 25% for medium/unknown or 50% for hard
  - Promote mastery state according to streak

- `SKIPPED`
  - Do not count as success
  - Keep the problem due soon
  - Do not incorrectly penalize mastery as a failed attempt unless product rules later specify it

Difficulty and priority may adjust the interval within bounded, documented rules.

### 9.5 Explainability requirement

Every calculated date must include a readable explanation, for example:

> Scheduled in 3 days because the problem was solved with a small hint and has one continuous successful revision.

Do not generate this explanation with AI. Build it from deterministic factors.

### 9.6 Manual overrides

When the user manually changes the next revision date:

- Store the overridden date.
- Store that it was manually overridden.
- Preserve the latest calculated date for auditability.
- Show the distinction in the UI.
- A later attempt may calculate a new schedule and clear the previous override only according to an explicit, tested rule.

---

## 10. Daily queue generation

### 10.1 Inputs

```python
class QueueGenerationRequest(BaseModel):
    available_minutes: int
    topic_focus_ids: list[UUID] = []
    requested_problem_count: int | None = None
```

### 10.2 Candidate factors

Prioritize:

1. Overdue problems
2. Previously failed problems
3. Problems in `FRAGILE` or `NEEDS_RELEARNING`
4. Weak topics
5. Problems due today
6. High-priority problems
7. Long time since last revision
8. Retention checks after repeated successful revisions

### 10.3 Scoring

Create an explicit scoring model rather than a large chain of database conditions.

Example conceptual score:

```text
score =
  overdue_weight
+ failure_weight
+ fragile_weight
+ weak_topic_weight
+ due_today_weight
+ priority_weight
+ neglect_weight
- recently_practiced_penalty
```

Weights must be centralized in configuration and covered by tests.

### 10.4 Time fitting

Each problem must have an estimated duration.

Use:

- User-provided estimate when available
- Otherwise a default based on difficulty

Example defaults:

- Easy: 15 minutes
- Medium: 25 minutes
- Hard: 30 minutes
- Unknown: 20 minutes

The generated queue should fit the available time as closely as possible without substantially exceeding it.

A simple greedy algorithm is acceptable for v1 if it is deterministic and tested. Do not introduce an optimization library unless needed.

### 10.5 Topic balancing

Unless a topic focus is explicitly requested:

- Avoid selecting every problem from the same topic.
- Prefer topic diversity before filling remaining capacity by score.
- Keep overdue and failed problems highly scored, but do not let them bypass topic balancing.

### 10.6 Recommendation explanations

Each queue item must store one or more deterministic reasons such as:

- `Overdue by 5 days`
- `Previous attempt failed`
- `Heap is currently a weak topic`
- `Retention check after 30 days`
- `High-priority interview problem`

---

## 11. Weak-topic detection

For each topic, calculate:

- Total problems
- Total attempts
- Independent success rate
- Hint-assisted success rate
- Failed attempt rate
- Problems due
- Problems overdue
- Mastery distribution
- Last practiced date
- Recent trend

Initial statuses:

- `WEAK`
- `NEGLECTED`
- `IMPROVING`
- `STABLE`

Each status must be derived from documented thresholds.

Do not use AI for the status itself. AI may later explain or summarize deterministic statistics.

---

## 12. Import architecture

### 12.1 Supported formats

- `.xlsx`
- `.csv`

### 12.2 Libraries

- Use `openpyxl` for `.xlsx`
- Use Python's CSV module or pandas where it simplifies robust parsing
- Do not make pandas a domain-layer dependency

### 12.3 Import workflow

1. Upload or select a file.
2. Save a copy in the private workspace imports directory.
3. Read headers and sample rows.
4. Propose column mappings.
5. Allow the user to edit mappings.
6. Parse every row into an intermediate import model.
7. Validate rows independently.
8. Detect possible duplicates.
9. Show preview counts:
   - Total
   - Valid
   - Invalid
   - Possible duplicates
10. Import valid rows in a transaction.
11. Preserve failed rows for correction and retry.
12. Produce an import summary.

### 12.4 Supported imported fields

- Problem Link
- Problem Title
- Difficulty
- Notes
- Topic
- Pattern
- Solved First Time
- Last Revised or Solved Date
- Number of Revisions
- Number of Successful Continuous Revisions
- Next Revision Date

### 12.5 History preservation

Legacy summary fields may not contain individual attempt records. Do not invent attempt history.

Preserve legacy values in clearly identified fields or import metadata, and initialize the current problem summary accordingly.

If a legacy row contains only:

- Revision count
- Successful revision streak
- Last revised date
- Next revision date

then store those values without fabricating historical attempts.

### 12.6 Error handling

- Invalid rows must not block valid rows.
- Every invalid row must include field-specific errors.
- Corrected rows should be retryable without reimporting successful rows.
- Imports should be idempotent where practical.
- Store an import job identifier on created records for traceability.

---

## 13. Duplicate detection

Use layered detection:

1. Exact normalized URL match
2. Exact platform plus platform identifier match
3. Exact normalized title match
4. Fuzzy title similarity using PostgreSQL trigram similarity

Return possible duplicates with a confidence and reason.

The user may still keep both records.

Do not use embeddings for duplicate detection in v1.

---

## 14. Export, backup, restore, and deletion

### 14.1 Export

Support:

- CSV
- JSON
- Excel where supported

Export should include:

- Problems
- Topics
- Patterns
- Attempt history
- Current summaries
- Queue history where appropriate
- Preferences where safe

### 14.2 Backup

A backup should contain:

- A versioned database export or PostgreSQL dump
- Workspace configuration
- Imports, if the user chooses to include them
- Exports, optionally
- A backup manifest
- Schema/application version

### 14.3 Restore

Restore must:

- Validate the backup manifest
- Verify supported version
- Warn before replacing current data
- Restore transactionally where possible
- Run required migrations
- Produce a restore summary

### 14.4 Delete all personal data

Deletion must require explicit confirmation.

It should:

- Delete application records
- Delete workspace imports, exports, and backups according to the selected option
- Preserve source code
- Not silently leave personal notes or API keys behind

---

## 15. Backend API design

Use `/api/v1`.

### 15.1 Health and configuration

```http
GET  /api/v1/health
GET  /api/v1/settings
PUT  /api/v1/settings
POST /api/v1/workspace/initialize
```

### 15.2 Problems

```http
GET    /api/v1/problems
POST   /api/v1/problems
GET    /api/v1/problems/{problem_id}
PATCH  /api/v1/problems/{problem_id}
POST   /api/v1/problems/{problem_id}/archive
POST   /api/v1/problems/{problem_id}/restore
GET    /api/v1/problems/{problem_id}/history
GET    /api/v1/problems/duplicates
```

Supported filters should include:

- Topic
- Pattern
- Difficulty
- Mastery state
- Due status
- Platform
- Archived status
- Search text

### 15.3 Attempts

```http
POST /api/v1/problems/{problem_id}/attempts
GET  /api/v1/problems/{problem_id}/attempts
GET  /api/v1/attempts/recent
```

Creating an attempt must atomically:

- Insert the attempt
- Update problem summary counters
- Calculate mastery
- Calculate next revision date
- Save the scheduling explanation

### 15.4 Queue

```http
POST   /api/v1/queues
GET    /api/v1/queues/{queue_id}
PATCH  /api/v1/queues/{queue_id}/items/{item_id}
POST   /api/v1/queues/{queue_id}/items/{item_id}/replace
POST   /api/v1/queues/{queue_id}/items
DELETE /api/v1/queues/{queue_id}/items/{item_id}
POST   /api/v1/queues/{queue_id}/items/{item_id}/complete
```

### 15.5 Statistics

```http
GET /api/v1/statistics/dashboard
GET /api/v1/statistics/topics
GET /api/v1/statistics/patterns
GET /api/v1/statistics/trends
GET /api/v1/statistics/weak-areas
```

### 15.6 Imports

```http
POST /api/v1/imports
GET  /api/v1/imports/{import_id}
PUT  /api/v1/imports/{import_id}/mapping
POST /api/v1/imports/{import_id}/preview
POST /api/v1/imports/{import_id}/commit
POST /api/v1/imports/{import_id}/retry
```

### 15.7 Data operations

```http
POST /api/v1/exports
GET  /api/v1/exports/{export_id}
POST /api/v1/backups
GET  /api/v1/backups
POST /api/v1/backups/{backup_id}/restore
DELETE /api/v1/data
```

### 15.8 Optional AI

```http
POST /api/v1/ai/topic-suggestions
POST /api/v1/ai/failure-analysis
POST /api/v1/ai/weekly-summary
POST /api/v1/ai/coach/messages
```

AI endpoints must return whether the result is:

- Generated
- Validated
- Approved
- Persisted

Generated content must not be persisted as accepted user data until approval.

---

## 16. Frontend pages

### 16.1 Dashboard

Show:

- Problems due today
- Problems overdue
- Problems practiced this week
- Problems mastered
- Problems needing relearning
- Start revision session
- Recent activity
- Topic summary

### 16.2 Problem Library

Show:

- Searchable and paginated problem list
- Filters
- Add problem
- Import data
- Edit problem
- Archive or restore problem
- Duplicate warnings

### 16.3 Daily Queue

Show:

- Available-time input
- Optional topic focus
- Optional problem count
- Recommended problems
- Estimated duration
- Recommendation reasons
- Remove, replace, postpone, add, and complete controls
- Record-attempt flow

### 16.4 Problem Details

Show:

- Problem information
- Topics and patterns
- Current mastery
- Next revision date
- Whether the date is calculated or overridden
- Full attempt history
- Scheduling explanations
- Record-attempt action

### 16.5 Statistics

Show:

- Topic statistics
- Pattern statistics
- Practice trends
- Weak and neglected areas
- Explanations for classifications

### 16.6 Settings and Data

Show:

- Workspace location
- Revision preferences
- Import
- Export
- Backup
- Restore
- Delete data
- Optional AI configuration

---

## 17. Error handling

### 17.1 Backend

Use a consistent error body:

```json
{
  "error": {
    "code": "PROBLEM_NOT_FOUND",
    "message": "The requested problem does not exist.",
    "details": {}
  }
}
```

Create explicit domain errors for:

- Not found
- Validation failure
- Duplicate warning
- Invalid state transition
- Import mapping error
- Backup incompatibility
- AI disabled
- AI provider unavailable

### 17.2 Frontend

- Show field-level validation errors.
- Preserve user input after failed requests.
- Use toast notifications for successful mutations.
- Use page-level error states for failed data loading.
- Require confirmation for destructive actions.
- Do not expose raw stack traces.

---

## 18. Security and privacy

For v1 local use:

- No authentication is required if the app binds only to localhost.
- Backend must default to `127.0.0.1`, not a public interface.
- CORS must allow only the configured frontend origin.
- Validate uploaded file type and size.
- Sanitize file names and prevent path traversal.
- Do not execute spreadsheet formulas.
- Do not render user notes as raw HTML.
- Never log API keys or complete private notes.
- Keep secrets out of Git and frontend bundles.
- All AI calls must clearly indicate whether data leaves the machine.
- Local Ollama mode should be available for users who do not want cloud processing.

If hosted multi-user support is added later, authentication, authorization, tenant isolation, encryption, rate limiting, and audit logging become mandatory and require a separate design.

---

## 19. Testing strategy

### 19.1 Unit tests

Cover:

- Mastery transitions
- Revision interval selection
- Failure and hint handling
- Manual overrides
- Queue scoring
- Topic balancing
- Time fitting
- Weak-topic classification
- Duplicate normalization
- Import row validation

### 19.2 Property-based tests

Use Hypothesis for invariants such as:

- An independently successful revision must not shorten the interval unless a documented modifier requires it.
- A failed attempt must not increase the successful streak.
- Archived problems must not appear in generated queues.
- Attempt creation must preserve prior attempts.
- Queue duration must remain within the configured tolerance.
- Manual overrides must remain distinguishable from calculated values.
- Identical deterministic inputs must produce identical outputs.

### 19.3 Integration tests

Use PostgreSQL in test containers or a dedicated Docker Compose test service.

Test:

- Repository operations
- Transactions
- Migrations
- Attempt creation and problem-summary updates
- Import commit and rollback
- Backup metadata
- Filters and statistics queries

### 19.4 Frontend tests

Test:

- Problem form validation
- Filters
- Queue editing
- Attempt entry
- Manual date override
- Import mapping
- Confirmation dialogs

### 19.5 End-to-end tests

Critical Playwright flows:

1. Initialize workspace
2. Add a problem manually
3. Import a CSV
4. Review invalid rows
5. Record an attempt
6. Verify next revision date and explanation
7. Generate and modify a queue
8. View topic statistics
9. Export data
10. Create and restore a backup
11. Delete personal data

### 19.6 AI evaluation

Maintain a small fictional evaluation dataset for:

- Topic suggestions
- Pattern suggestions
- Failure-reason classification
- Weekly summaries

Measure:

- Schema-valid output rate
- Topic precision
- User-approval rate in manual testing
- Unsupported claims
- Local versus hosted model quality
- Latency

AI tests must not block the deterministic application test suite when AI is disabled.

---

## 20. Development environment

### 20.1 Required tools

- Git
- Docker Desktop
- Node.js current LTS
- pnpm
- Python 3.12+
- uv

### 20.2 Common commands

Provide a Makefile or task runner with:

```bash
make setup
make dev
make test
make lint
make format
make migrate
make seed
make e2e
make build
```

### 20.3 Docker Compose services

```text
postgres
api
web
```

Ollama should normally run outside the core Compose stack on developer machines, or be included in an optional profile.

### 20.4 Environment template

`.env.example` should include:

```dotenv
DATABASE_URL=postgresql+psycopg://codemuscle:codemuscle@localhost:5432/codemuscle
API_HOST=127.0.0.1
API_PORT=8000
WEB_ORIGIN=http://localhost:3000
WORKSPACE_PATH=
AI_ENABLED=false
AI_PROVIDER=ollama
AI_MODEL=
AI_BASE_URL=http://localhost:11434/v1
AI_API_KEY=
```

---

## 21. CI pipeline

GitHub Actions should run on pull requests and pushes to `main`.

Required jobs:

1. Backend lint and type check
2. Backend unit tests
3. Backend integration tests with PostgreSQL
4. Frontend lint and type check
5. Frontend unit tests
6. Production builds
7. End-to-end tests for protected branches or selected pull requests
8. Dependency and secret scanning where practical

A pull request must not merge when required checks fail.

---

## 22. Implementation milestones

### Milestone 0: Repository foundation

Deliver:

- Monorepo structure
- Docker Compose
- PostgreSQL
- FastAPI health endpoint
- Next.js application shell
- CI
- Formatting, linting, and tests
- `.env.example`
- Private-data `.gitignore` rules

### Milestone 1: Workspace and core models

Deliver:

- Workspace selection
- Settings
- Problem model
- Topic and pattern models
- Attempt model
- Migrations
- Backup/export foundations

### Milestone 2: Problem library

Deliver:

- Manual problem creation
- Edit
- Archive and restore
- Multiple topics and patterns
- Search and filters
- Duplicate warnings

### Milestone 3: Import

Deliver:

- Excel import
- CSV import
- Column mapping
- Preview
- Row-level validation
- Duplicate review
- Safe partial import
- Retry failed rows

### Milestone 4: Attempt tracking

Deliver:

- Record attempt
- Supporting details
- Immutable chronological history
- Problem summary counters
- Initial mastery calculation

### Milestone 5: Scheduling

Deliver:

- Configurable intervals
- Deterministic revision algorithm
- Mastery transitions
- Next revision date
- Manual override
- Human-readable explanations
- Comprehensive tests

### Milestone 6: Daily queue

Deliver:

- Time-bounded queue
- Candidate scoring
- Topic balancing
- Recommendation reasons
- Queue persistence
- Remove, replace, postpone, add, and complete

### Milestone 7: Statistics

Deliver:

- Dashboard
- Topic statistics
- Pattern statistics
- Problem history
- Practice trends
- Weak, neglected, improving, and stable detection

### Milestone 8: Data lifecycle

Deliver:

- CSV export
- Backup
- Restore
- Delete all personal data

### Milestone 9: Optional AI

Deliver:

- AI-disabled default
- Ollama adapter
- Topic suggestions
- Pattern suggestions
- Failure-note analysis
- Weekly summary
- Approval workflow
- Evaluation dataset

### Milestone 10: Coach agent

Deliver only after prior milestones are stable:

- Read-only agent tools
- Daily-practice conversation
- LangGraph workflow where statefulness is useful
- Confirmation before all state-changing tools
- Traceable tool calls
- MCP server as an optional extension

---

## 23. Agent tool design for the future product

Initial read-only tools:

```text
get_due_problems
get_overdue_problems
get_problem
get_problem_history
get_topic_statistics
get_weak_topics
generate_candidate_queue
```

State-changing tools:

```text
record_attempt
postpone_problem
update_problem_topics
accept_ai_suggestion
```

Rules:

- Tools must use typed Pydantic input and output models.
- Agents must not receive arbitrary SQL access.
- State-changing tools require explicit user approval.
- Tool implementations must call existing application services.
- The agent must never duplicate scheduling logic.
- Every tool call must be loggable and testable.
- Agent-generated recommendations must cite the underlying CodeMuscle data used.

---

## 24. Coding-agent execution instructions

The coding agent should follow these instructions:

1. Build one milestone at a time.
2. Do not implement future milestones prematurely.
3. Keep every pull request small and reviewable.
4. Write or update tests with each behavior.
5. Run lint, type checks, and tests before considering a milestone complete.
6. Do not place business logic in API routes or React components.
7. Do not introduce a new library without explaining:
   - The problem it solves
   - Why existing dependencies cannot solve it
   - Maintenance and ecosystem considerations
8. Do not change functional requirements silently.
9. Record major architectural decisions under `docs/decisions/`.
10. Prefer explicit code over highly abstract frameworks.
11. Keep AI integrations replaceable and disabled by default.
12. Never commit personal data or secrets.
13. Use fictional fixtures and sample data.
14. Return a concise implementation summary after each milestone:
   - Files added or changed
   - Decisions made
   - Tests added
   - Commands to run
   - Known limitations
   - Next recommended milestone

---

## 25. Definition of done for v1

CodeMuscle v1 is complete when a new user can:

1. Clone the repository.
2. Start the application with documented commands.
3. Create or select a private workspace.
4. Start with an empty problem library.
5. Add and edit a problem.
6. Import Excel or CSV data.
7. Review mappings, invalid rows, and possible duplicates.
8. Preserve supported legacy summary data.
9. Assign multiple topics and patterns.
10. Record an attempt.
11. View complete attempt history.
12. Receive a deterministic next revision date.
13. Understand why the date was selected.
14. Manually override the date.
15. Generate a queue based on available time.
16. Understand why every problem was recommended.
17. Modify and complete the queue.
18. View dashboard and topic statistics.
19. Identify overdue and weak areas.
20. Export personal data.
21. Create and restore a backup.
22. Delete personal data.
23. Confirm personal data is not stored in the public repository.
24. Use all core functionality with AI disabled.

---

## 26. Explicit non-goals for v1

Do not build:

- A code editor
- Code execution
- Automatic LeetCode login
- Automatic submission-history import
- Browser automation
- Social features
- Leaderboards
- Job application tracking
- Resume management
- System-design preparation
- Behavioral-interview preparation
- Mobile applications
- Multi-user collaboration
- Microservices
- Kubernetes
- A vector database
- General-purpose RAG
- Autonomous multi-agent workflows
- Authentication for the local-only version

---

## 27. Final stack summary

```text
Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- React Hook Form
- Zod
- Recharts
- Vitest
- Playwright

Backend
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- pytest
- Hypothesis
- Ruff
- Pyright
- uv

Database
- PostgreSQL 16+
- Docker Compose for local development

AI and agents, after the deterministic product works
- Ollama for local open models
- Typed provider abstraction
- LangGraph for stateful tool-using workflows
- vLLM only for later self-hosted GPU serving
- MCP as a later interoperability feature

Infrastructure
- Docker
- Docker Compose
- GitHub Actions
- Environment-variable configuration
- Modular monolith
```

This stack is deliberately mainstream, transferable, and suitable for both startup-style full-stack development and future agentic development without making the v1 product unnecessarily complex.
