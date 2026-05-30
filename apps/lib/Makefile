SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "pulseboard-shared"
	@echo "================="
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

.PHONY: install
install: ## Install dependencies (creates .venv via uv)
	uv sync --group dev

.PHONY: test
test: ## Run unit tests (outputs junit.xml)
	uv run pytest tests/ -v --junitxml=junit.xml

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	uv run pytest tests/ -v --cov=pulseboard_shared --cov-report=term-missing

.PHONY: lint
lint: ## Run ruff linter and format check
	uv run ruff check pulseboard_shared/ tests/
	uv run ruff format --check pulseboard_shared/ tests/

.PHONY: lint-fix
lint-fix: ## Auto-fix lint issues
	uv run ruff check --fix pulseboard_shared/ tests/
	uv run ruff format pulseboard_shared/ tests/
