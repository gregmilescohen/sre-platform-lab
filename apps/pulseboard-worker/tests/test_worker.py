"""Tests for the pulseboard-worker event publisher."""

import json
from unittest.mock import MagicMock

import pytest
from app.worker import EVENT_TYPES, build_event, publish_batch


def test_build_event_returns_required_fields() -> None:
    """build_event must include event_name, metadata, and emitted_at."""
    event = build_event("page_view")
    assert event["event_name"] == "page_view"
    assert "metadata" in event
    assert "emitted_at" in event
    assert "session_id" in event["metadata"]


@pytest.mark.parametrize("event_type", EVENT_TYPES)
def test_build_event_all_known_types(event_type: str) -> None:
    """build_event works for every event type in EVENT_TYPES."""
    event = build_event(event_type)
    assert event["event_name"] == event_type


def test_publish_batch_calls_publisher_per_event() -> None:
    """publish_batch publishes exactly batch_size events."""
    mock_publisher = MagicMock()
    mock_publisher.publish.return_value.result.return_value = "msg-id"

    result = publish_batch(mock_publisher, "projects/p/topics/t", batch_size=3)

    assert mock_publisher.publish.call_count == 3
    assert result == 3


def test_publish_batch_encodes_as_json_bytes() -> None:
    """publish_batch passes valid JSON bytes to the publisher."""
    mock_publisher = MagicMock()
    mock_publisher.publish.return_value.result.return_value = "msg-id"

    publish_batch(mock_publisher, "projects/p/topics/t", batch_size=1)

    data_arg = mock_publisher.publish.call_args[0][1]
    payload = json.loads(data_arg.decode("utf-8"))
    assert "event_name" in payload
    assert "metadata" in payload


def test_publish_batch_counts_only_successful_publishes() -> None:
    """publish_batch returns count of successful futures, skipping failures."""
    success_future = MagicMock()
    success_future.result.return_value = "msg-id"
    fail_future = MagicMock()
    fail_future.result.side_effect = Exception("broker unavailable")

    mock_publisher = MagicMock()
    mock_publisher.publish.side_effect = [success_future, fail_future, success_future]

    result = publish_batch(mock_publisher, "projects/p/topics/t", batch_size=3)

    assert result == 2


class _BreakLoop(Exception):
    """Sentinel exception used to escape the run() infinite loop in tests."""


def test_run_creates_publisher_and_publishes_batches() -> None:
    """run() starts a publisher, calls publish_batch, and sleeps each iteration."""
    from unittest.mock import patch

    from app.worker import run

    mock_publisher = MagicMock()
    mock_publisher.topic_path.return_value = "projects/pulseboard/topics/t"
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_publisher)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("app.worker.pubsub_v1.PublisherClient", return_value=mock_client):
        with patch("app.worker.publish_batch", return_value=5) as mock_publish:
            with patch("app.worker.time.sleep", side_effect=_BreakLoop):
                with pytest.raises(_BreakLoop):
                    run()

    mock_publish.assert_called_once()


def test_run_reads_env_vars() -> None:
    """run() picks up PUBLISH_INTERVAL_SECONDS and BATCH_SIZE from the environment."""
    import os
    from unittest.mock import patch

    from app.worker import run

    mock_publisher = MagicMock()
    mock_publisher.topic_path.return_value = "projects/pulseboard/topics/t"
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_publisher)
    mock_client.__exit__ = MagicMock(return_value=False)

    sleep_args: list[float] = []

    def capture_sleep(interval: float) -> None:
        sleep_args.append(interval)
        raise _BreakLoop

    env = {**os.environ, "PUBLISH_INTERVAL_SECONDS": "0.5", "BATCH_SIZE": "2"}
    with patch.dict(os.environ, env, clear=True):
        with patch("app.worker.pubsub_v1.PublisherClient", return_value=mock_client):
            with patch("app.worker.publish_batch", return_value=2) as mock_publish:
                with patch("app.worker.time.sleep", side_effect=capture_sleep):
                    with pytest.raises(_BreakLoop):
                        run()

    assert sleep_args == [0.5]
    _, kwargs = mock_publish.call_args
    assert kwargs.get("batch_size") == 2
