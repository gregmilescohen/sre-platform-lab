# pulseboard-api

## What This App Is

FastAPI backend for PulseBoard. Lives at `apps/pulseboard-api/` inside the `sre-platform-lab`
monorepo. Publishes events to a Pub/Sub topic (`POST /events`), reads aggregated event data
from the `event_log` table for the UI (`GET /events`), exposes a health probe and Prometheus
RED metrics.

See the repo-root `.claude/CLAUDE.md` for the full ecosystem overview.

## Tech Stack

- **Python 3.13** — `.python-version` file present
- **uv** — package and virtual environment management
- **FastAPI** — web framework
- **SQLAlchemy 2.0** — ORM (sync)
- **PostgreSQL** — production DB (via `psycopg2-binary`)
- **SQLite** — local dev DB (default when `DATABASE_URL` is not set)
- **google-cloud-pubsub** — Pub/Sub SDK (emulator-compatible via `PUBSUB_EMULATOR_HOST`)
- **python-ulid** — time-sortable IDs for `event_log`
- **prometheus-client** — Prometheus metrics at `GET /metrics`
- **Ruff** — linter + formatter
- **pytest** + **unittest.mock** — unit testing (no real DB or broker in tests)

## Directory Structure

```
apps/pulseboard-api/
├── app/
│   ├── main.py          # FastAPI app, metrics middleware, /metrics endpoint
│   ├── db.py            # Engine, SessionLocal, Base, get_db dependency
│   ├── models.py        # EventLog ORM model (ULID pk, event_name, metadata, received_at)
│   ├── schemas.py       # Pydantic schemas (EmitRequest/Response, DataPoint, EventDataResponse)
│   ├── metrics.py       # RED metrics: requests_total counter + duration histogram
│   ├── pubsub.py        # get_publisher(), publish_event(), get_topic_path()
│   └── routers/
│       ├── health.py    # GET /health — returns 503 when DB is down
│       └── events.py    # POST /events (emit), GET /events (data)
├── tests/
│   ├── test_health.py   # Unit tests for health endpoint
│   └── test_events.py   # Unit tests for emit + get + bucketing logic
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Common Commands

```bash
make install    # uv sync --group dev
make run        # uvicorn app.main:app --reload --port 8080
make test       # pytest tests/ -v
make lint       # ruff check + ruff format --check
make lint-fix   # ruff check --fix + ruff format
make test-cov   # pytest with coverage report
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness/readiness probe; checks DB connectivity |
| GET | /metrics | Prometheus scrape endpoint |
| POST | /events | Publish event to Pub/Sub topic; returns `{published, message_id}` |
| GET | /events | Read time-bucketed event counts from event_log |

### GET /events query params

| Param | Default | Description |
|-------|---------|-------------|
| `event_name` | _(all)_ | Filter to one event type |
| `since` | 1h ago | ISO timestamp lower bound |
| `bucket` | `minute` | Time bucket size: `minute` or `hour` |

## Metrics (RED)

| Metric | Type | Labels |
|--------|------|--------|
| `pulseboard_api_requests_total` | Counter | method, endpoint, status_code |
| `pulseboard_api_request_duration_seconds` | Histogram | method, endpoint |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./pulseboard.db` | SQLAlchemy connection URL |
| `PUBSUB_EMULATOR_HOST` | _(unset)_ | Emulator address — required for local/k8s |
| `PUBSUB_PROJECT_ID` | `pulseboard` | GCP project ID |
| `PUBSUB_TOPIC_ID` | `pulseboard-events` | Pub/Sub topic name |

## event_log Schema

```sql
CREATE TABLE event_log (
    id          VARCHAR(26) PRIMARY KEY,   -- ULID (time-sortable)
    event_name  VARCHAR(255) NOT NULL,
    metadata    JSON,                       -- Python attr: event_metadata
    received_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

Note: `event_metadata` is the Python attribute name for the `metadata` column —
`metadata` is reserved by SQLAlchemy's `DeclarativeBase`.

## Application Infrastructure (`k8s/`)

The `k8s/` directory contains the Kubernetes manifests for pulseboard's application-level dependencies. These live here (not in `reliability-lab-infra`) because this is application-owned infrastructure, not platform infrastructure.

- **namespace.yaml** — `pulseboard` Namespace definition. Owned here because the namespace is an application concern, not a platform concern.
- **postgres.yaml** — PostgreSQL 15 Deployment + ClusterIP Service + 2Gi PVC. Credentials: user/pass/db all `pulseboard`. Consumed by both pulseboard-api and pulseboard-consumer.
- **pubsub-emulator.yaml** — Google Cloud Pub/Sub Emulator on port 8085. Services set `PUBSUB_EMULATOR_HOST=pubsub-emulator.pulseboard.svc.cluster.local:8085` to route to it. Topic/subscription created by `deploy-services.sh` after this pod is ready.

Applied by `reliability-lab-bootstrap/scripts/deploy-services.sh` via `kubectl apply -f ${API_REPO}/k8s/`.

## Helm Deployment

Uses `reliability-lab-chart` from `reliability-lab-infra` as the base chart.
`helm/values.yaml` provides service-specific overrides.

NodePort: **30080** → `http://localhost:30080`

## Testing Approach

Tests call route handler functions and pure helper functions (`_bucket_events`) directly
with `unittest.mock.MagicMock()`. No database or running server is required.

## For AI Agents

- `app/pubsub.py` wraps the Pub/Sub client — mock `publish_event` in tests
- `_bucket_events()` in `app/routers/events.py` is a pure function — test it without mocks
- All tests use `unittest.mock`; keep them as pure unit tests (no real DB or broker)
- Run `make lint` before committing — ruff config lives at repo root `ruff.toml` (line-length 100, py313 target)
- `event_log.event_metadata` is the Python attribute; DB column is `metadata`
