CORE := services/core
GROUPS := --group scraping --group ml

.PHONY: help setup sync up down logs lint fmt test migrate collect build-ranking evaluate \
	backfill-results train-winrate eval-winrate predict-match \
	backfill-sides eval-bridge enc-predict enc-ranking

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Install Python deps (base + dev)
	cd $(CORE) && uv sync

sync: ## Install all pipeline deps (scraping + ml)
	cd $(CORE) && uv sync $(GROUPS)

up: ## Start Postgres (docker compose)
	docker compose up -d

down: ## Stop services
	docker compose down

logs: ## Tail Postgres logs
	docker compose logs -f postgres

migrate: ## Apply database migrations
	cd $(CORE) && uv run alembic upgrade head

lint: ## Lint with ruff
	cd $(CORE) && uv run ruff check .

fmt: ## Format with ruff
	cd $(CORE) && uv run ruff format .

test: ## Run tests (unit + integration on fixtures)
	cd $(CORE) && uv run $(GROUPS) pytest

collect: ## vctm collect (set VCTM_ENC_TEAMS or VCTM_ENC_EVENT_URL)
	cd $(CORE) && uv run $(GROUPS) vctm collect $(ARGS)

build-ranking: ## vctm build-ranking (pass ARGS="--version ... --tournament-start ...")
	cd $(CORE) && uv run $(GROUPS) vctm build-ranking $(ARGS)

evaluate: ## vctm evaluate (pass ARGS="--version ... --standings ...")
	cd $(CORE) && uv run $(GROUPS) vctm evaluate $(ARGS)

backfill-results: ## vctm backfill-results (offline match outcomes from cache)
	cd $(CORE) && uv run $(GROUPS) vctm backfill-results $(ARGS)

train-winrate: ## vctm train-winrate (pass ARGS="--cutoff ...")
	cd $(CORE) && uv run $(GROUPS) vctm train-winrate $(ARGS)

eval-winrate: ## vctm eval-winrate (pass ARGS="--cutoff ...")
	cd $(CORE) && uv run $(GROUPS) vctm eval-winrate $(ARGS)

predict-match: ## vctm predict-match (pass ARGS="--team-a ... --team-b ...")
	cd $(CORE) && uv run $(GROUPS) vctm predict-match $(ARGS)

backfill-sides: ## vctm backfill-sides (attribute players to match sides, offline)
	cd $(CORE) && uv run $(GROUPS) vctm backfill-sides $(ARGS)

eval-bridge: ## vctm eval-bridge (pass ARGS="--cutoff ...")
	cd $(CORE) && uv run $(GROUPS) vctm eval-bridge $(ARGS)

enc-predict: ## vctm enc-predict (pass ARGS="--team-a ... --team-b ...")
	cd $(CORE) && uv run $(GROUPS) vctm enc-predict $(ARGS)

enc-ranking: ## vctm enc-ranking (pass ARGS="--as-of ... --version ...")
	cd $(CORE) && uv run $(GROUPS) vctm enc-ranking $(ARGS)
