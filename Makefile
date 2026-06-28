CORE := services/core

.PHONY: help setup up down logs lint fmt test

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install Python deps (base + dev)
	cd $(CORE) && uv sync

up: ## Start Postgres (docker compose)
	docker compose up -d

down: ## Stop services
	docker compose down

logs: ## Tail Postgres logs
	docker compose logs -f postgres

lint: ## Lint with ruff
	cd $(CORE) && uv run ruff check .

fmt: ## Format with ruff
	cd $(CORE) && uv run ruff format .

test: ## Run tests
	cd $(CORE) && uv run pytest
