# pulseboard-worker

Synthetic event publisher for the PulseBoard demo workload. Publishes
randomised events to a Google Cloud Pub/Sub topic at a configurable rate,
producing a realistic traffic distribution for downstream consumers.

## Event types

| Event | Weight | Relative frequency |
|-------|--------|-------------------|
| `page_view` | 30 | ~30% |
| `button_click` | 20 | ~20% |
| `api_call` | 20 | ~20% |
| `search` | 10 | ~10% |
| `login` | 10 | ~10% |
| `checkout` | 5 | ~5% |
| `error` | 5 | ~5% |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLISH_INTERVAL_SECONDS` | `1.0` | Seconds to sleep between batches |
| `BATCH_SIZE` | `5` | Events published per batch |
| `PUBSUB_PROJECT_ID` | `pulseboard` | GCP project ID |
| `PUBSUB_TOPIC_ID` | `pulseboard-events` | Pub/Sub topic name |
| `PUBSUB_EMULATOR_HOST` | — | Set to `host:port` to use the local emulator |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Local development

```bash
# Install dependencies
make install

# Run tests
make test

# Run with coverage
make test-cov

# Lint
make lint

# Run locally (requires Pub/Sub emulator on port 8085)
PUBSUB_EMULATOR_HOST=localhost:8085 make run
```

## Docker

```bash
# Build
docker build -t pulseboard-worker .

# Run against local emulator
docker run \
  -e PUBSUB_EMULATOR_HOST=host.docker.internal:8085 \
  -e PUBSUB_PROJECT_ID=pulseboard \
  -e PUBSUB_TOPIC_ID=pulseboard-events \
  pulseboard-worker
```

## Full stack

```bash
# From repo root — starts emulator, setup, and worker together
docker compose up -d pulseboard-worker
docker compose logs pulseboard-worker -f
```
