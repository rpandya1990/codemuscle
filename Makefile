.PHONY: start stop restart status logs setup dev test lint format migrate seed e2e build

start:
	./scripts/codemuscle start

stop:
	./scripts/codemuscle stop

restart:
	./scripts/codemuscle restart

status:
	./scripts/codemuscle status

logs:
	./scripts/codemuscle logs

setup:
	uv sync --project apps/api --all-groups
	pnpm install

dev:
	docker compose up --build

test:
	uv run --project apps/api pytest
	pnpm test

lint:
	uv run --project apps/api ruff check .
	uv run --project apps/api pyright
	pnpm lint
	pnpm typecheck

format:
	uv run --project apps/api ruff format apps/api/src apps/api/tests apps/api/alembic
	pnpm --filter @codemuscle/web exec prettier --write .

migrate:
	uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head

seed:
	@echo "Fictional seed data will be added with Milestone 1."

e2e:
	pnpm --filter @codemuscle/web e2e

build:
	uv build --project apps/api
	pnpm build
