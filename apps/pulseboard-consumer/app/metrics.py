"""Prometheus metrics for pulseboard-consumer."""

from prometheus_client import Counter, Gauge, Histogram

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

MESSAGE_AGE_SECONDS = Histogram(
    "pulseboard_consumer_message_age_seconds",
    "Message age at processing time (publish_time to now) — proxy for oldest unacked age",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
)

SUBSCRIPTION_BACKLOG = Gauge(
    "pulseboard_consumer_subscription_backlog_messages",
    "Number of messages in the last pull batch — approximate queue depth",
)
