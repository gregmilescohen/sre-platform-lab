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

    publish_batch(mock_publisher, "projects/p/topics/t", batch_size=3)

    assert mock_publisher.publish.call_count == 3


def test_publish_batch_encodes_as_json_bytes() -> None:
    """publish_batch passes valid JSON bytes to the publisher."""
    mock_publisher = MagicMock()
    mock_publisher.publish.return_value.result.return_value = "msg-id"

    publish_batch(mock_publisher, "projects/p/topics/t", batch_size=1)

    data_arg = mock_publisher.publish.call_args[0][1]
    payload = json.loads(data_arg.decode("utf-8"))
    assert "event_name" in payload
    assert "metadata" in payload
