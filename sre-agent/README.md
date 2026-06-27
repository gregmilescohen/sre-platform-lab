# sre-agent

Webhook-triggered incident response agent. When Alertmanager fires, the agent:

1. Snapshots current metrics via `agent/tools/prometheus.py`
2. Fetches active alerts via `agent/tools/alertmanager.py`
3. Renders an incident prompt from `agent/prompts/incident.md.j2`
4. Spawns `opencode run --dangerously-skip-permissions "<prompt>"` (Task 12)
5. Monitors Alertmanager via `agent/monitor.py` until the alert resolves (Task 12)

## MCP tools (used by OpenCode, not Python)

Configured in `opencode.json`:

| MCP server | Purpose |
|------------|---------|
| `grafana` (`mcp-grafana`) | Query Prometheus metrics and Loki logs via Grafana datasource API |
| `alertmanager` (`alertmanager-mcp-server`) | List alerts, create silences |

## Service ports

| Endpoint | URL |
|----------|-----|
| Webhook + sessions UI | `http://localhost:8090` |

## Running tests

```bash
uv sync --group dev
uv run pytest tests/ -v --cov=agent
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ALERTMANAGER_URL` | `http://localhost:9093` | Alertmanager base URL |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus base URL |
