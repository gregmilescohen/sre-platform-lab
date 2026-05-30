SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "pulseboard-ui"
	@echo "============="
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

.PHONY: install
install: ## Install npm dependencies
	npm install

.PHONY: dev
dev: ## Start Vite dev server (requires pulseboard-api on :8080)
	npm run dev

.PHONY: build
build: ## Production build
	npm run build

.PHONY: test
test: ## Run tests
	npm run test:ci

.PHONY: lint
lint: ## Run ESLint + TypeScript checks
	npm run lint
