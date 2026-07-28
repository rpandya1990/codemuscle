# CodeMuscle

CodeMuscle is a private coding-interview revision tracker. Development follows the milestone plan in [the technical design](docs/CodeMuscle_Technical_Design_and_Implementation_Spec.md).

## Current status

Milestones 0–2 establish the monorepo, application shell, PostgreSQL service, private workspace,
core relational models, and the problem library. Problems can be created, edited, searched,
filtered, archived, restored, tagged with topics and patterns, and checked for duplicates.

## Prerequisites

- Docker Desktop
- Python 3.12 or newer
- `uv`
- Node.js (current LTS)
- `pnpm`

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open the web app at <http://localhost:3000> and API documentation at <http://localhost:8000/docs>.

## Run locally

```bash
make setup
docker compose up -d postgres
uv run --project apps/api uvicorn codemuscle.main:app --reload --host 127.0.0.1 --port 8000
pnpm dev
```

Run quality checks with `make test`, `make lint`, and `make build`.

## Privacy

Never place real imports, exports, backups, notes, database dumps, API keys, or a private workspace in this repository. The ignore rules cover common private-data paths, but the default workspace will live outside the repository.
