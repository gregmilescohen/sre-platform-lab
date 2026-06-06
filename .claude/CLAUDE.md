# sre-platform-lab

## What This Repo Is

Single-repo SRE portfolio project. PulseBoard demo workload (FastAPI API, worker, consumer,
React UI) + full observability stack + chaos engineering + AI SRE agent that auto-remediates
Alertmanager alerts using OpenCode with BigPickle (free LLM, no subscription required).

## Repo Layout

| Directory | Purpose |
|-----------|---------|
| `apps/pulseboard-api/` | FastAPI backend — POST /events (emit), GET /events (read), RED metrics; chaos endpoints: POST /chaos/errors, POST /chaos/slow, POST /chaos/leak, POST /chaos/reset, GET /chaos/status. Chaos state is in-process (resets on container restart). |
| `apps/pulseboard-worker/` | Synthetic event generator — publishes randomised events to Pub/Sub at configurable rate; env vars: `PUBLISH_INTERVAL_SECONDS`, `BATCH_SIZE` |
| `apps/pulseboard-consumer/` | Pub/Sub consumer → writes to event_log (Postgres), exposes Prometheus metrics on :9102 |
| `apps/pulseboard-ui/` | React + Vite dashboard showing live event rate |
| `sre-agent/` | Webhook-triggered FastAPI service — spawns OpenCode on alert |
| `infra/` | Prometheus, Grafana, Loki, Alloy, Alertmanager, Tempo, OTel Collector configs |
| `chaos/` | Failure-injection scripts |
| `runbooks/` | SLO runbooks |

## Service Ports

| Service | Port |
|---------|------|
| Grafana | 3000 |
| Prometheus | 9090 |
| Alertmanager | 9093 |
| PulseBoard API | 8080 |
| PulseBoard UI | 5173 |
| SRE Agent | 8090 |
| Loki | 3100 |
| Pub/Sub Emulator | 8085 |
| Consumer Metrics | 9102 |
| Grafana Tempo | 3200 |
| OTel Collector gRPC | 4317 |
| OTel Collector HTTP | 4318 |

## Common Commands

```bash
make up           # start all services + open browser tabs (PulseBoard UI, Grafana, Alertmanager)
make open         # open browser tabs without restarting services
make down         # stop all
make urls         # print service URLs
make test         # run all service tests
make lint         # run all linters
make chaos-errors # inject 50% error rate
make chaos-slow   # inject 2s latency
make chaos-reset  # reset chaos
```

## Tech Stack

- Python 3.13 / uv / FastAPI
- React + Vite + TypeScript
- Docker Compose (Kubernetes is a follow-up)
- Prometheus, Grafana, Loki, Alloy, Alertmanager, Grafana Tempo
- OpenCode CLI + BigPickle (free LLM)
- MCP servers: Grafana MCP (metrics/logs), Alertmanager MCP (alert operations)

## AI Agent Architecture

```
Alertmanager → POST /webhook → sre-agent FastAPI
    → snapshot metrics via prometheus.py (initial context)
    → render incident prompt (Jinja2)
    → spawn: opencode run --dangerously-skip-permissions "<prompt>"
        └── OpenCode loads opencode.json → MCP tools:
            · grafana MCP: query Prometheus, query Loki
            · alertmanager MCP: list alerts, create silences
        └── OpenCode can also: POST /chaos/reset via bash if chaos detected
    → Python monitor.py polls Alertmanager for resolution
```

## Observability Pillars

- **Metrics** — Prometheus scrapes pulseboard-api (:8080/metrics) and pulseboard-consumer (:9102/metrics)
- **Logs** — Grafana Alloy ships Docker container logs to Loki; query via Grafana Explore → Loki
- **Traces** — pulseboard-api instruments via OTel SDK → OTel Collector (:4317 gRPC) → Grafana Tempo (:3200); query via Grafana Explore → Tempo
  - OTel is a no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset (unit tests are unaffected)

## SLOs

- **Availability:** 99.5% over 30m (`job:pulseboard_api_availability:ratio_rate30m`)
- **Latency:** p95 < 500ms over 5m (`job:pulseboard_api_latency_p95:rate5m`)

Alert rules in `infra/prometheus/rules/alerts.yml`:
- `PulseBoardHighErrorRateFast` (critical) — 14x burn rate over 5m
- `PulseBoardHighErrorRateSlow` (warning) — 2x burn rate over 30m
- `PulseBoardHighLatency` (warning) — p95 > 500ms for 5m
- `PulseBoardAPIDown` (critical) — scrape target down for 1m

Runbooks: `runbooks/high-error-rate.md`, `runbooks/high-latency.md`

## Current State

Tasks 9 and 10 complete — chaos endpoints in pulseboard-api and chaos shell scripts. Tasks 5–8 also complete (consumer, UI, OTel traces, SLIs/SLOs/alerts/dashboard).

## Conventions

- All Python services use Python 3.13 / uv
- Shared `ruff.toml` at repo root (Google docstrings, type hints required, line-length 100)
- No task complete until `ruff check`, `ruff format --check`, and `pytest` all pass
- One PR per feature/task; PRs merged manually by repo owner
