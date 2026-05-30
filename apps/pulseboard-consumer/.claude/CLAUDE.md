# pulseboard-consumer

## What This App Is

Pub/Sub subscriber for PulseBoard. Lives at `apps/pulseboard-consumer/` inside the `sre-platform-lab` monorepo. Pulls events from the `pulseboard-events-sub` subscription, writes them to `event_log` in PostgreSQL, and exposes Prometheus metrics on port 9102.

See the repo-root `.claude/CLAUDE.md` for the full ecosystem overview.

## Tech Stack

- **Python 3.13** — `.python-version` file present
- **uv** — package and virtual environment management
- **google-cloud-pubsub** — Pub/Sub subscriber SDK
- **SQLAlchemy 2.0** — ORM (sync)
- **PostgreSQL** — writes to `event_log` table
- **prometheus-client** — metrics at `:9102/metrics`
- **Ruff** — linter + formatter (config at repo root `ruff.toml`)
- **pytest** + **unittest.mock** — unit testing (no real DB or broker in tests)

## Common Commands

```bash
make install    # uv sync --group dev
make run        # python -m app.main
make test       # pytest tests/ -v
make lint       # ruff check + ruff format --check
make test-cov   # pytest with coverage report
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./pulseboard-consumer.db` | SQLAlchemy connection URL |
| `PUBSUB_EMULATOR_HOST` | _(unset)_ | Emulator address |
| `PUBSUB_PROJECT_ID` | `pulseboard` | GCP project ID |
| `PUBSUB_SUBSCRIPTION_ID` | `pulseboard-events-sub` | Subscription name |
| `METRICS_PORT` | `9102` | Port for Prometheus metrics HTTP server |
| `LOG_LEVEL` | `INFO` | Python logging level |
