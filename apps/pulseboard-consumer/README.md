# pulseboard-consumer

Pub/Sub subscriber that drains the `pulseboard-events` topic, writes each event to the
`event_log` Postgres table, and exposes Prometheus metrics for queue health and throughput.

## How it works

The consumer runs a tight pull loop: it requests up to `BATCH_SIZE` messages per pull,
writes successful events to Postgres, acks the whole batch, then loops. Malformed messages
(invalid JSON, missing fields) are acked without a DB write — poison-pill protection so one
bad message never stalls the subscription.

A heartbeat file (`/tmp/consumer.heartbeat`) is touched on every loop iteration and checked
by the Docker `HEALTHCHECK`, so the orchestrator can detect a stuck consumer even when the
pull loop is idle.

## Prometheus Metrics

Exposed on `:9102/metrics`.

| Metric | Type | Description |
|--------|------|-------------|
| `pulseboard_consumer_messages_processed_total{status}` | Counter | Messages processed; `status="ok"` or `"error"` |
| `pulseboard_consumer_processing_duration_seconds` | Histogram | Time to process one message |
| `pulseboard_consumer_batch_size` | Histogram | Messages per pull batch |
| `pulseboard_consumer_message_age_seconds` | Histogram | Publish-time-to-now at processing; proxy for queue lag |
| `pulseboard_consumer_subscription_backlog_messages` | Gauge | Messages in the last pull batch; approximate queue depth |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./pulseboard-consumer.db` | SQLAlchemy connection URL |
| `PUBSUB_EMULATOR_HOST` | _(unset)_ | Emulator address (e.g. `pubsub-emulator:8085`) |
| `PUBSUB_PROJECT_ID` | `pulseboard` | GCP project ID |
| `PUBSUB_SUBSCRIPTION_ID` | `pulseboard-events-sub` | Pub/Sub subscription name |
| `BATCH_SIZE` | `10` | Max messages per pull request |
| `BATCH_TIMEOUT_SECONDS` | `2` | Sleep between pulls when queue is empty |
| `METRICS_PORT` | `9102` | Port for Prometheus scrape endpoint |

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
