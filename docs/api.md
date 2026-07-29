# API reference

Base URL: `http://localhost:8000/api/v1`. Interactive OpenAPI: `/docs`. All endpoints currently have
**no authentication** and are intended for a trusted local machine. JSON is used unless multipart is
specified. Validation errors return HTTP 422. Domain errors use:

```json
{"error":{"code":"PROBLEM_NOT_FOUND","message":"...","details":{"problem_id":"..."}}}
```

## Health, workspace, and settings

| Method and URL | Purpose | Request | Success | Errors/validation |
|---|---|---|---|---|
| `GET /health` | Process liveness check | None | `200 {"status":"ok","service":"codemuscle-api"}` | None expected |
| `POST /workspace/initialize` | Create private workspace directories/manifest and persist path | `{"path":"/absolute/path"}` | `201 {path, manifest}` | 422 missing/relative path |
| `GET /settings` | Read runtime and user preferences | None | `200 SettingsResponse` | — |
| `PUT /settings` | Update preferences | Partial `default_available_minutes`, `timezone`, `successful_intervals` | `200 SettingsResponse` | 422: minutes 5–720; timezone 1–100 chars; intervals 1–20 unique ascending values, each 1–3650 |

`SettingsResponse` includes `workspace_path`, `ai_enabled`, `web_origin`,
`default_available_minutes`, `timezone`, and `successful_intervals`.

## Problems

### `GET /problems`

Lists active problems by default. Query parameters: `search`, `topic_id`, `pattern_id`, `difficulty`,
`mastery_state`, `platform`, `archived` (boolean), `page` (≥1), and `page_size` (1–5000).

Response: `200 {items: Problem[], total, page, page_size}`. Search covers normalized title and notes.
The web client requests up to 5000 and paginates locally.

### `POST /problems`

Creates a problem. Request fields:

```json
{
  "title": "Merge Intervals",
  "url": "https://example.com/problem",
  "difficulty": "MEDIUM",
  "notes": "Sort by start time",
  "priority": 3,
  "estimated_duration_minutes": 35,
  "topics": ["Arrays"],
  "patterns": ["Intervals"]
}
```

Only `title` is required. URL and all supporting details are optional. Title max 500; priority 1–5;
duration 1–1440; at most 30 topics/patterns. Returns `201 Problem`.

### Problem read/update and classification

| Method and URL | Purpose | Request | Success | Errors |
|---|---|---|---|---|
| `GET /problems/topics` | Alphabetized topic catalog | None | `200 [{id,name}]` | — |
| `GET /problems/duplicates` | Layered duplicate search | Query: optional `title`, `url`, `platform`, `platform_identifier` | `200 [{problem,confidence,reason}]` | 422 malformed query |
| `GET /problems/{problem_id}` | Read one problem | UUID path | `200 Problem` | 404 `PROBLEM_NOT_FOUND` |
| `PATCH /problems/{problem_id}` | Partial metadata update | Any `ProblemUpdate` field | `200 Problem` | 404; 422 field bounds |
| `POST /problems/{problem_id}/archive` | Soft archive | None | `200 Problem` | 404 |
| `POST /problems/{problem_id}/restore` | Clear archive timestamp | None | `200 Problem` | 404 |

`Problem` includes identifiers/metadata, topics/patterns, priority, mastery, attempt/streak counters,
effective and calculated revision dates, override marker, archive state, and audit timestamps.

### Revision-date override

| Method and URL | Request | Behavior |
|---|---|---|
| `PUT /problems/{id}/schedule-override` | `{"next_revision_date":"2026-08-15"}` | Changes effective date and sets `next_revision_overridden=true`; preserves calculated date |
| `DELETE /problems/{id}/schedule-override` | None | Restores latest calculated date and clears override marker |

Both return `200 Problem`; missing problems return 404.

## Attempts

### `POST /problems/{problem_id}/attempts`

Atomically appends an immutable attempt, calculates scheduling/mastery, and updates the problem
summary. Request:

```json
{
  "attempted_at": "2026-07-28T18:00:00Z",
  "outcome": "SOLVED_INDEPENDENTLY",
  "hint_usage": "NONE",
  "time_spent_minutes": 25,
  "confidence": 4,
  "notes": "Remember empty input",
  "complexity_understood": true
}
```

Required: `outcome`. `hint_usage` defaults to `NOT_APPLICABLE`; `attempted_at` defaults to now.
Time is 0–1440 and confidence 1–5. Returns `201 Attempt`, including previous/calculated mastery,
calculated next date, and explanation. Errors: 404 problem; 422 validation.

| Method and URL | Purpose | Response |
|---|---|---|
| `GET /problems/{problem_id}/attempts` | Newest-first immutable history | `200 Attempt[]`; 404 problem |
| `GET /attempts/recent?limit=20` | Recent activity across problems | `200 RecentAttempt[]`; limit 1–100 and each item includes `problem_title` |

There are intentionally no normal update/delete attempt endpoints.

## Imports

| Method and URL | Purpose | Request | Response/errors |
|---|---|---|---|
| `POST /imports` | Store and inspect CSV/XLSX | `multipart/form-data`, field `file` | `201 ImportJob`; 400 invalid type/content; workspace error if uninitialized |
| `GET /imports/{id}` | Retrieve job, rows, counts, mapping | UUID | `200 ImportJob`; 404 `IMPORT_NOT_FOUND` |
| `PUT /imports/{id}/mapping` | Replace source-column mapping | `{"mapping":{"title":"Problem title",...}}` | `200 ImportJob`; 404/422 |
| `POST /imports/{id}/preview` | Parse all rows, validate, detect duplicates | None | `200 ImportJob` with rows/counts |
| `POST /imports/{id}/commit` | Import valid and accepted duplicate rows | `{"include_duplicate_row_ids":[...]}` | `200 {import_id,imported,skipped_invalid,skipped_duplicates}` |
| `POST /imports/{id}/retry` | Apply corrections to failed rows | `{"corrections":{"row-uuid":{"title":"..."}}}` | `200 ImportJob` |

Mapping targets include `title`, `url`, `difficulty`, `notes`, `topic`, `pattern`, legacy revision
dates/counts/streaks. Invalid rows never block valid rows. Legacy summaries are metadata, not attempts.

## Daily queues

### `POST /queues`

Generates and persists an explainable, time-bounded queue.

```json
{
  "available_minutes": 60,
  "topic_focus_ids": ["topic-uuid"],
  "requested_problem_count": 3
}
```

Minutes: 5–720. Topic list: at most 30. Count: optional 1–100. Returns `201 Queue`, including stored
item score, reasons, duration, status, and embedded problem. Selection does not exceed the time budget.

| Method and URL | Purpose | Request | Response/errors |
|---|---|---|---|
| `GET /queues/{queue_id}` | Read persisted queue | UUID | `200 Queue`; 404 `QUEUE_NOT_FOUND` |
| `PATCH /queues/{queue_id}/items/{item_id}` | Set workflow status | `{"status":"PENDING|POSTPONED|COMPLETED"}` | `200 Queue`; postpone sets tomorrow as manual revision override |
| `DELETE /queues/{queue_id}/items/{item_id}` | Remove from active view while retaining history | None | `200 Queue` |
| `POST /queues/{queue_id}/items/{item_id}/replace` | Replace with best non-queued candidate | None | `200 Queue`; unchanged if none available |
| `POST /queues/{queue_id}/items` | Manually append problem | `{"problem_id":"uuid"}` | `200 Queue`; 404 problem/queue |
| `POST /queues/{queue_id}/items/{item_id}/complete` | Mark completed | None | `200 Queue` |

## HTTP debugging

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/problems?page_size=5000
docker compose logs -f api
```

When frontend code hot-reloads but a new backend route returns 404, rebuild the API:

```bash
docker compose up -d --build api
```
