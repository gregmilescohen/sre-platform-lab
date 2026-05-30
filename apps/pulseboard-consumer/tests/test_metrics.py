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
