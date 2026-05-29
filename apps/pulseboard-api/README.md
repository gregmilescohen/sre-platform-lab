# pulseboard-api

FastAPI backend for the PulseBoard demo workload. Publishes events to a Google Pub/Sub topic and reads time-bucketed event data from Postgres for the UI charts. Exposes Prometheus RED metrics.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness/readiness probe; checks DB connectivity |
| GET | /metrics | Prometheus scrape endpoint (RED metrics) |
| POST | /events | Publish event to Pub/Sub topic; returns `{published, message_id}` |
| GET | /events | Read time-bucketed event counts from event_log |

### GET /events query params

| Param | Default | Description |
|-------|---------|-------------|
| `event_name` | _(all)_ | Filter to one event type |
| `since` | 1h ago | ISO timestamp lower bound |
| `bucket` | `minute` | Time bucket size: `minute` or `hour` |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./pulseboard.db` | SQLAlchemy connection URL |
| `PUBSUB_EMULATOR_HOST` | _(unset)_ | Emulator address (e.g. `pubsub-emulator:8085`) |
| `PUBSUB_PROJECT_ID` | `pulseboard` | GCP project ID |
| `PUBSUB_TOPIC_ID` | `pulseboard-events` | Pub/Sub topic name |

## Running Tests Locally

```bash
make test    # uv run pytest tests/ -v
make lint    # uv run ruff check . && uv run ruff format --check .
```

Or directly:

```bash
uv sync --group dev
uv run pytest tests/ -v
uv run ruff check .
uv run ruff format --check .
```
