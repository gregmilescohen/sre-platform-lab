# sre-platform-lab

[![pulseboard-api tests](https://github.com/gregmilescohen/sre-platform-lab/actions/workflows/ci-pulseboard-api.yml/badge.svg)](https://github.com/gregmilescohen/sre-platform-lab/actions/workflows/ci-pulseboard-api.yml)
[![pulseboard-api coverage](https://codecov.io/gh/gregmilescohen/sre-platform-lab/branch/main/graph/badge.svg?flag=pulseboard-api)](https://codecov.io/gh/gregmilescohen/sre-platform-lab)
[![CodeQL](https://github.com/gregmilescohen/sre-platform-lab/actions/workflows/codeql.yml/badge.svg)](https://github.com/gregmilescohen/sre-platform-lab/actions/workflows/codeql.yml)

My "SRE lab" for testing out new ideas and approaches related to reliability engineering, observability, chaos engineering, and agentic incident response — where a real AI agent spins up on alert, diagnoses the issue, reasons through it, and applies a fix.

## What's here

**PulseBoard** — a small event-processing app (API, worker, consumer, React UI) instrumented
with Prometheus RED metrics, structured logs (Loki), and OpenTelemetry traces. It has
intentional failure modes baked in.

**Observability stack** — Prometheus, Grafana, Loki, Alertmanager, Grafana Tempo.
Pre-provisioned dashboards and SLO burn-rate alerts.

**Chaos engineering** — One-command failure injection: elevated error rates, artificial latency.
Triggers real SLO alerts.

**SRE AI agent** — Webhook-triggered FastAPI service. When Alertmanager fires, the agent spawns
[OpenCode](https://opencode.ai), which uses MCP tools (Grafana for metrics/logs, Alertmanager
for alert ops) to investigate the root cause and remediate. Runs on
[BigPickle](https://opencode.ai/docs/zen/) — OpenCode's free model — so anyone can clone and
run this without an API key or LLM subscription.

## Quick start

```bash
# Requires: Docker, docker compose
cp .env.example .env
docker compose up -d
make urls
```

## Full incident demo

```bash
make chaos-errors           # trigger 50% error rate
# → alert fires in ~2 min → sre-agent auto-diagnoses and resets chaos
open http://localhost:8090  # watch agent sessions
```

## Services

| Service | URL | Notes |
|---------|-----|-------|
| PulseBoard UI | http://localhost:5173 | Live event rate dashboard |
| PulseBoard API | http://localhost:8080 | FastAPI, /docs for Swagger |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | |
| Alertmanager | http://localhost:9093 | |
| Loki | http://localhost:3100 | Query logs via Grafana |
| Alloy UI | http://localhost:12345 | Log collector pipeline |
| SRE Agent | http://localhost:8090 | Agent session dashboard |

## Design decisions

See [docs/design-decisions.md](docs/design-decisions.md) for write-ups on: why burn-rate alerts
over threshold alerts, why OpenCode over a custom agent framework, the SLO error budget math, etc.
