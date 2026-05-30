SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

OS := $(shell uname -s)

.PHONY: help
help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: up
up: ## Build images and start all services, then open dashboards in browser
	docker compose up --build -d
	@echo "Waiting for services to become available..."
	@sleep 3
	$(MAKE) open

.PHONY: watch
watch: ## Start services and watch for code changes (live sync — no browser open)
	docker compose watch

.PHONY: open
open: ## Open PulseBoard UI, Grafana, and Alertmanager in browser tabs
ifeq ($(OS),Darwin)
	@open http://localhost:5173 2>/dev/null || true
	@open http://localhost:3000 2>/dev/null || true
	@open http://localhost:9093 2>/dev/null || true
else
	@xdg-open http://localhost:5173 2>/dev/null || true
	@xdg-open http://localhost:3000 2>/dev/null || true
	@xdg-open http://localhost:9093 2>/dev/null || true
endif

.PHONY: down
down: ## Stop all containers
	docker compose down

.PHONY: down-volumes
down-volumes: ## Stop containers and delete volumes (clean slate)
	docker compose down -v

.PHONY: status
status: ## Show container status
	docker compose ps

.PHONY: logs
logs: ## Tail all service logs
	docker compose logs -f

# NOTE: these targets require service directories to be populated by later tasks.
# Running make test or make lint before Tasks 3-5 and 11 are complete will fail.
.PHONY: test
test: ## Run all service tests
	cd apps/pulseboard-api && make test
	cd apps/pulseboard-worker && make test
	cd apps/pulseboard-consumer && make test
	cd sre-agent && make test

# NOTE: these targets require service directories to be populated by later tasks.
# Running make test or make lint before Tasks 3-5 and 11 are complete will fail.
.PHONY: lint
lint: ## Run all service linters
	cd apps/pulseboard-api && make lint
	cd apps/pulseboard-worker && make lint
	cd apps/pulseboard-consumer && make lint
	cd sre-agent && make lint

.PHONY: urls
urls: ## Print all service endpoints
	@echo ""
	@echo "  Grafana:              http://localhost:3000  (admin/admin)"
	@echo "  Prometheus:           http://localhost:9090"
	@echo "  Alertmanager:         http://localhost:9093"
	@echo "  PulseBoard API:       http://localhost:8080"
	@echo "  PulseBoard UI:        http://localhost:5173"
	@echo "  SRE Agent:            http://localhost:8090"
	@echo "  Alloy (log pipeline): http://localhost:12345"
	@echo "  Consumer metrics:     http://localhost:9102/metrics"
	@echo ""
	@echo "  Run 'make open' to open UI/Grafana/Alertmanager in browser tabs."
	@echo ""

# ============================================================================
# Chaos Engineering
# ============================================================================

.PHONY: chaos-errors
chaos-errors: ## Inject 50% error rate into pulseboard-api
	@chaos/scripts/inject-errors.sh 0.5

.PHONY: chaos-slow
chaos-slow: ## Inject 2000ms latency into pulseboard-api
	@chaos/scripts/inject-slow.sh 2000

.PHONY: chaos-reset
chaos-reset: ## Reset all chaos modes
	@chaos/scripts/reset.sh

.PHONY: chaos-status
chaos-status: ## Show current chaos mode
	@curl -s http://localhost:8080/chaos/status | python3 -m json.tool

# ============================================================================
# SRE Agent
# ============================================================================

.PHONY: agent-sessions
agent-sessions: ## List recent SRE agent sessions
	@curl -s http://localhost:8090/sessions | python3 -m json.tool

.PHONY: agent-logs
agent-logs: ## Tail the SRE agent logs
	docker compose logs sre-agent -f
