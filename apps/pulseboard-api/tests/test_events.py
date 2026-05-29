"""Unit tests for POST /events (emit) and GET /events (data) endpoints.

Uses unittest.mock to mock the Pub/Sub publisher and SQLAlchemy Session.
Route handler functions are called directly with injected mocks.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from app.models import EventLog
from app.routers.events import _bucket_events, emit_event, get_events
from app.schemas import EmitRequest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(UTC)


def make_mock_event_log(event_name: str = "test_event", minutes_ago: int = 0) -> MagicMock:
    """Return a MagicMock that looks like an EventLog ORM row."""
    event = MagicMock(spec=EventLog)
    event.event_name = event_name
    event.received_at = _utcnow() - timedelta(minutes=minutes_ago)
    return event


def make_publisher(message_id: str = "msg-abc-123") -> MagicMock:
    """Return a mock PublisherClient that returns a successful publish future."""
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/pulseboard/topics/pulseboard-events"
    publisher.publish.return_value.result.return_value = message_id
    return publisher


# ---------------------------------------------------------------------------
# POST /events — emit
# ---------------------------------------------------------------------------


def test_emit_publishes_to_pubsub() -> None:
    """emit_event calls publisher.publish exactly once."""
    publisher = make_publisher()
    payload = EmitRequest(event_name="high_error_rate", metadata={"service": "api"})
    emit_event(payload=payload, publisher=publisher)
    publisher.publish.assert_called_once()


def test_emit_encodes_event_name_in_message() -> None:
    """emit_event passes event_name and metadata to publish_event."""
    publisher = make_publisher()
    payload = EmitRequest(event_name="latency_spike", metadata={})

    with patch("app.routers.events.publish_event") as mock_publish:
        mock_publish.return_value = "msg-123"
        emit_event(payload=payload, publisher=publisher)
        mock_publish.assert_called_once_with(
            event_name="latency_spike",
            metadata={},
            publisher=publisher,
        )


def test_emit_returns_published_true_and_message_id() -> None:
    """emit_event returns published=True and the message_id from the broker."""
    publisher = make_publisher(message_id="msg-xyz-789")
    payload = EmitRequest(event_name="disk_full", metadata={"host": "node-1"})
    result = emit_event(payload=payload, publisher=publisher)
    assert result.published is True
    assert result.message_id == "msg-xyz-789"


def test_emit_raises_500_when_publisher_fails() -> None:
    """emit_event raises HTTP 500 when the publisher raises an exception."""
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/pulseboard/topics/pulseboard-events"
    publisher.publish.side_effect = Exception("UNAVAILABLE: could not connect to broker")
    payload = EmitRequest(event_name="test_event", metadata={})
    with pytest.raises(HTTPException) as exc_info:
        emit_event(payload=payload, publisher=publisher)
    assert exc_info.value.status_code == 500


def test_emit_raises_500_when_future_result_fails() -> None:
    """emit_event raises HTTP 500 when the publish future raises an exception."""
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/pulseboard/topics/pulseboard-events"
    publisher.publish.return_value.result.side_effect = Exception("publish timed out")
    payload = EmitRequest(event_name="test_event", metadata={})
    with pytest.raises(HTTPException) as exc_info:
        emit_event(payload=payload, publisher=publisher)
    assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# GET /events — data
# ---------------------------------------------------------------------------


def test_get_events_returns_empty_data_when_log_is_empty() -> None:
    """get_events returns empty data list when event_log has no rows."""
    mock_db = MagicMock()
    q = mock_db.query.return_value.filter.return_value
    q.order_by.return_value.all.return_value = []
    q.filter.return_value.order_by.return_value.all.return_value = []
    result = get_events(db=mock_db)
    assert result.data == []


def test_get_events_invalid_bucket_raises_422() -> None:
    """get_events raises HTTP 422 for an unsupported bucket value."""
    mock_db = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        get_events(bucket="second", db=mock_db)
    assert exc_info.value.status_code == 422


def test_get_events_default_since_is_one_hour_ago() -> None:
    """get_events defaults since to approximately one hour ago."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    before = _utcnow() - timedelta(hours=1)
    result = get_events(db=mock_db)
    after = _utcnow() - timedelta(hours=1)
    # since should be approximately one hour ago
    assert before <= result.since <= after + timedelta(seconds=1)


def test_get_events_returns_event_name_filter_in_response() -> None:
    """get_events echoes the event_name filter back in the response."""
    mock_db = MagicMock()
    q = mock_db.query.return_value.filter.return_value.filter.return_value
    q.order_by.return_value.all.return_value = []
    result = get_events(event_name="cpu_spike", db=mock_db)
    assert result.event_name == "cpu_spike"


# ---------------------------------------------------------------------------
# _bucket_events — bucketing logic (pure function, no mocks needed)
# ---------------------------------------------------------------------------


def test_bucket_events_empty_list() -> None:
    """_bucket_events returns an empty list when given no events."""
    assert _bucket_events([], "minute") == []


def test_bucket_events_groups_by_minute() -> None:
    """_bucket_events aggregates events into per-minute buckets."""
    now = _utcnow().replace(second=0, microsecond=0)
    events = [
        make_mock_event_log("cpu_spike", minutes_ago=0),
        make_mock_event_log("cpu_spike", minutes_ago=0),
        make_mock_event_log("cpu_spike", minutes_ago=1),
    ]
    # Override received_at to exact minute boundaries
    events[0].received_at = now
    events[1].received_at = now
    events[2].received_at = now - timedelta(minutes=1)

    data = _bucket_events(events, "minute")
    assert len(data) == 2
    counts = {p.time_bucket: p.count for p in data}
    assert counts[now] == 2
    assert counts[now - timedelta(minutes=1)] == 1


def test_bucket_events_groups_by_hour() -> None:
    """_bucket_events aggregates events into per-hour buckets."""
    now = _utcnow().replace(minute=0, second=0, microsecond=0)
    events = [
        make_mock_event_log("disk_full"),
        make_mock_event_log("disk_full"),
        make_mock_event_log("disk_full"),
    ]
    for e in events:
        e.received_at = now

    data = _bucket_events(events, "hour")
    assert len(data) == 1
    assert data[0].count == 3
    assert data[0].time_bucket == now


def test_bucket_events_separates_different_event_names() -> None:
    """_bucket_events keeps different event_name values in separate buckets."""
    now = _utcnow().replace(second=0, microsecond=0)
    events = [make_mock_event_log("cpu_spike"), make_mock_event_log("disk_full")]
    for e in events:
        e.received_at = now

    data = _bucket_events(events, "minute")
    assert len(data) == 2
    names = {p.event_name for p in data}
    assert names == {"cpu_spike", "disk_full"}


def test_bucket_events_sorted_by_time() -> None:
    """_bucket_events returns DataPoints ordered by time_bucket ascending."""
    now = _utcnow().replace(second=0, microsecond=0)
    events = [
        make_mock_event_log("e"),
        make_mock_event_log("e"),
    ]
    events[0].received_at = now - timedelta(minutes=2)
    events[1].received_at = now

    data = _bucket_events(events, "minute")
    assert data[0].time_bucket < data[1].time_bucket
