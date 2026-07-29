# CodeMuscle

CodeMuscle is a private coding-interview revision tracker. Development follows the milestone plan in [the technical design](docs/CodeMuscle_Technical_Design_and_Implementation_Spec.md).

## Current status

Milestones 0–2 establish the monorepo, private workspace, core relational models, and problem
library. Problems can be created, edited, searched, filtered, archived, restored, tagged with
topics and patterns, and checked for duplicates.

## Prerequisites

- Docker Desktop
- Python 3.12 or newer
- `uv`
- Node.js (current LTS)
- `pnpm`

## Quick start

```bash
make start
```

This installs the backend tooling, starts PostgreSQL, applies migrations, builds the application,
and initializes a private workspace at `~/CodeMuscleData`.

Open the web app at <http://localhost:3000> and API documentation at
<http://localhost:8000/docs>.

Use the lifecycle commands:

```bash
make status
make logs
make restart
make stop
```

To store private files somewhere else on first start:

```bash
CODEMUSCLE_WORKSPACE_PATH=/absolute/private/path make start
```

`make stop` preserves both the PostgreSQL Docker volume and private workspace files.

## Run locally

```bash
make setup
docker compose up -d postgres
make migrate
uv run --project apps/api uvicorn codemuscle.main:app --reload --host 127.0.0.1 --port 8000
pnpm dev
```

Run quality checks with `make test`, `make lint`, and `make build`.

## Privacy

Never place real imports, exports, backups, notes, database dumps, API keys, or a private workspace in this repository. The ignore rules cover common private-data paths, but the default workspace will live outside the repository.
