"""Prometheus metrics for pulseboard-consumer."""

from prometheus_client import Counter, Histogram

MESSAGES_PROCESSED = Counter(
    "pulseboard_consumer_messages_processed_total",
    "Total Pub/Sub messages processed",
    ["status"],  # labels: "ok" or "error"
)

PROCESSING_DURATION = Histogram(
    "pulseboard_consumer_processing_duration_seconds",
    "Time to process a batch of messages",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

BATCH_SIZE = Histogram(
    "pulseboard_consumer_batch_size",
    "Number of messages in each processed batch",
    buckets=[1, 2, 5, 10, 20, 50, 100],
)
