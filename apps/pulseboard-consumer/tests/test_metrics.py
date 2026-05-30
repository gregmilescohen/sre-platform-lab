"""Tests for pulseboard-consumer Prometheus metrics."""


def test_messages_processed_metric_exists() -> None:
    """MESSAGES_PROCESSED counter has the correct metric name."""
    from app.metrics import MESSAGES_PROCESSED

    assert MESSAGES_PROCESSED._name == "pulseboard_consumer_messages_processed"


def test_processing_duration_metric_exists() -> None:
    """PROCESSING_DURATION histogram has the correct metric name."""
    from app.metrics import PROCESSING_DURATION

    assert PROCESSING_DURATION._name == "pulseboard_consumer_processing_duration_seconds"


def test_batch_size_metric_exists() -> None:
    """BATCH_SIZE histogram has the correct metric name."""
    from app.metrics import BATCH_SIZE

    assert BATCH_SIZE._name == "pulseboard_consumer_batch_size"


def test_message_age_metric_exists() -> None:
    """MESSAGE_AGE_SECONDS histogram has the correct metric name."""
    from app.metrics import MESSAGE_AGE_SECONDS

    assert MESSAGE_AGE_SECONDS._name == "pulseboard_consumer_message_age_seconds"


def test_subscription_backlog_metric_exists() -> None:
    """SUBSCRIPTION_BACKLOG gauge has the correct metric name."""
    from app.metrics import SUBSCRIPTION_BACKLOG

    assert SUBSCRIPTION_BACKLOG._name == "pulseboard_consumer_subscription_backlog_messages"
