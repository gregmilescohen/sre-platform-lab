# pulseboard-worker

## What this is

Synthetic event publisher for the PulseBoard demo workload. Runs a continuous
`while True` loop that publishes randomised events to the `pulseboard-events`
Pub/Sub topic at a configurable rate. No HTTP server — this is a pure publish
loop. See repo root `CLAUDE.md` for the full ecosystem context.

## Tech stack

- Python 3.13 / uv
- `google-cloud-pubsub` for Pub/Sub publishing
- Docker (python:3.13-slim + uv)

## Directory structure

```
apps/pulseboard-worker/
├── app/
│   ├── __init__.py
│   ├── main.py       # entry point — configures logging, calls run()
│   └── worker.py     # build_event(), publish_batch(), run() loop
├── tests/
│   ├── __init__.py
│   └── test_worker.py
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Common commands

```bash
make install    # uv sync --group dev
make test       # pytest tests/ -v --junitxml=junit.xml
make test-cov   # pytest with coverage
make lint       # ruff check + ruff format --check
make lint-fix   # auto-fix lint and format issues
make run        # run locally (requires Pub/Sub emulator or real GCP)
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLISH_INTERVAL_SECONDS` | `1.0` | Seconds to sleep between batches |
| `BATCH_SIZE` | `5` | Events per batch |
| `PUBSUB_PROJECT_ID` | `pulseboard` | GCP project ID |
| `PUBSUB_TOPIC_ID` | `pulseboard-events` | Pub/Sub topic name |
| `PUBSUB_EMULATOR_HOST` | — | Set to `host:port` to use the emulator |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Notes

- No HTTP server — just a publish loop. The process runs until killed.
- Event types are weighted: `page_view` (30) and `button_click`/`api_call` (20 each)
  are most frequent; `error` and `checkout` are rare (5 each).
- Linting: uses the shared `ruff.toml` at repo root (Google docstrings, type hints required).
