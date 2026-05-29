# Makefile
# pulseboard-api
#
# Usage:
#   make install   Install dependencies via uv
#   make run       Run the API locally (hot reload, port 8080)
#   make test      Run unit tests
#   make lint      Run ruff linter and format check

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "pulseboard-api"
	@echo "=============="
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

.PHONY: install
install: ## Install dependencies (creates .venv via uv)
	uv sync --group dev

.PHONY: run
run: ## Run the API locally with hot reload on port 8080
	uv run uvicorn app.main:app --reload --port 8080

.PHONY: test
test: ## Run unit tests with pytest
	uv run pytest tests/ -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	uv run pytest tests/ -v --cov=app --cov-report=term-missing

.PHONY: lint
lint: ## Run ruff linter and format check
	uv run ruff check app/ tests/
	uv run ruff format --check app/ tests/

.PHONY: lint-fix
lint-fix: ## Auto-fix ruff lint issues and format
	uv run ruff check --fix app/ tests/
	uv run ruff format app/ tests/
