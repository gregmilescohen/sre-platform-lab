"""Unit tests for the Pub/Sub message processing logic in app/consumer.py.

Uses unittest.mock to mock Pub/Sub ReceivedMessage objects and the SQLAlchemy
Session — no real broker or database is required.
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from app.consumer import process_batch
from app.models import EventLog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_message(
    event_name: str = "test_event",
    metadata: dict | None = None,
    ack_id: str = "ack-1",
    age_seconds: float = 1.0,
) -> MagicMock:
    """Return a mock ReceivedMessage with a valid JSON payload."""
    payload = {"event_name": event_name, "metadata": metadata or {}}
    msg = MagicMock()
    msg.ack_id = ack_id
    msg.message.message_id = f"msg-{ack_id}"
    msg.message.data = json.dumps(payload).encode("utf-8")
    msg.message.publish_time = datetime.now(UTC) - timedelta(seconds=age_seconds)
    return msg


def make_bad_message(data: bytes = b"not json", ack_id: str = "ack-bad") -> MagicMock:
    """Return a mock ReceivedMessage with an invalid payload."""
    msg = MagicMock()
    msg.ack_id = ack_id
    msg.message.message_id = f"msg-{ack_id}"
    msg.message.data = data
    msg.message.publish_time = datetime.now(UTC) - timedelta(seconds=1.0)
    return msg


# ---------------------------------------------------------------------------
# process_batch
# ---------------------------------------------------------------------------


def test_process_batch_empty_list_does_not_write_to_db() -> None:
    """process_batch with no messages does not touch the DB."""
    mock_db = MagicMock()
    process_batch([], mock_db)
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_process_batch_inserts_one_row_per_valid_message() -> None:
    """process_batch adds one row per valid message."""
    mock_db = MagicMock()
    messages = [make_message("cpu_spike"), make_message("disk_full")]
    process_batch(messages, mock_db)
    assert mock_db.add.call_count == 2


def test_process_batch_commits_once_for_entire_batch() -> None:
    """process_batch commits the session exactly once per batch."""
    mock_db = MagicMock()
    messages = [make_message(), make_message(), make_message()]
    process_batch(messages, mock_db)
    mock_db.commit.assert_called_once()


def test_process_batch_sets_correct_event_name() -> None:
    """process_batch sets event_name correctly on the ORM row."""
    mock_db = MagicMock()
    messages = [make_message(event_name="latency_spike")]
    process_batch(messages, mock_db)
    added_row = mock_db.add.call_args[0][0]
    assert added_row.event_name == "latency_spike"


def test_process_batch_sets_event_metadata() -> None:
    """process_batch sets event_metadata correctly on the ORM row."""
    mock_db = MagicMock()
    messages = [make_message(event_name="test", metadata={"host": "node-1", "value": 42})]
    process_batch(messages, mock_db)
    added_row = mock_db.add.call_args[0][0]
    assert added_row.event_metadata == {"host": "node-1", "value": 42}


def test_process_batch_returns_all_messages_for_acking() -> None:
    """process_batch returns the original messages list for acking."""
    mock_db = MagicMock()
    messages = [make_message("e1", ack_id="a1"), make_message("e2", ack_id="a2")]
    result = process_batch(messages, mock_db)
    assert result is messages


def test_process_batch_skips_malformed_json_without_crashing() -> None:
    """process_batch skips bad JSON but still returns the message for acking."""
    mock_db = MagicMock()
    messages = [make_bad_message(b"not-valid-json")]
    result = process_batch(messages, mock_db)
    # No DB write, but message still returned for acking (avoid poison pill)
    mock_db.add.assert_not_called()
    assert len(result) == 1


def test_process_batch_skips_message_missing_event_name() -> None:
    """process_batch skips messages that are missing the event_name field."""
    mock_db = MagicMock()
    payload = json.dumps({"metadata": {}}).encode("utf-8")  # no event_name key
    msg = make_bad_message(data=payload)
    result = process_batch([msg], mock_db)
    mock_db.add.assert_not_called()
    assert len(result) == 1


def test_process_batch_handles_mix_of_valid_and_invalid() -> None:
    """process_batch writes only valid rows but returns all messages."""
    mock_db = MagicMock()
    messages = [
        make_message("good_event", ack_id="a1"),
        make_bad_message(b"garbage", ack_id="a2"),
        make_message("another_good", ack_id="a3"),
    ]
    result = process_batch(messages, mock_db)
    # Only 2 valid messages written
    assert mock_db.add.call_count == 2
    # All 3 returned for acking
    assert len(result) == 3
    mock_db.commit.assert_called_once()


def test_process_batch_rows_are_eventlog_instances() -> None:
    """process_batch creates EventLog instances for valid messages."""
    mock_db = MagicMock()
    messages = [make_message("test_event")]
    process_batch(messages, mock_db)
    added_row = mock_db.add.call_args[0][0]
    assert isinstance(added_row, EventLog)


def test_process_batch_observes_message_age() -> None:
    """process_batch records message age for every message in the batch."""
    from unittest.mock import patch

    mock_db = MagicMock()
    messages = [make_message("page_view", age_seconds=5.0)]
    with patch("app.consumer.MESSAGE_AGE_SECONDS") as mock_age:
        process_batch(messages, mock_db)
    mock_age.observe.assert_called_once()
    observed = mock_age.observe.call_args[0][0]
    assert observed >= 0.0


def test_process_batch_observes_age_for_malformed_messages() -> None:
    """process_batch records message age even for malformed messages."""
    from unittest.mock import patch

    mock_db = MagicMock()
    messages = [make_bad_message()]
    with patch("app.consumer.MESSAGE_AGE_SECONDS") as mock_age:
        process_batch(messages, mock_db)
    mock_age.observe.assert_called_once()


def test_process_batch_sets_subscription_backlog() -> None:
    """process_batch updates SUBSCRIPTION_BACKLOG gauge with the batch length."""
    from unittest.mock import patch

    mock_db = MagicMock()
    messages = [make_message("e1"), make_message("e2")]
    with patch("app.consumer.SUBSCRIPTION_BACKLOG") as mock_backlog:
        process_batch(messages, mock_db)
    mock_backlog.set.assert_called_once_with(2)


def test_process_batch_increments_ok_counter() -> None:
    """process_batch increments MESSAGES_PROCESSED with status=ok for valid messages."""
    from unittest.mock import patch

    mock_db = MagicMock()
    messages = [make_message("page_view")]
    with patch("app.consumer.MESSAGES_PROCESSED") as mock_counter:
        process_batch(messages, mock_db)
    mock_counter.labels(status="ok").inc.assert_called_once_with(1)


def test_process_batch_increments_error_counter() -> None:
    """process_batch increments MESSAGES_PROCESSED with status=error for malformed messages."""
    from unittest.mock import patch

    mock_db = MagicMock()
    messages = [make_bad_message(b"not-json")]
    with patch("app.consumer.MESSAGES_PROCESSED") as mock_counter:
        process_batch(messages, mock_db)
    mock_counter.labels(status="error").inc.assert_called_once()


class _BreakLoop(BaseException):
    """Sentinel to escape the infinite subscriber loop.

    Inherits from BaseException (not Exception) so it is NOT swallowed
    by the ``except Exception`` clause inside run_subscriber().
    """


def test_run_subscriber_processes_and_acks_messages() -> None:
    """run_subscriber pulls messages, processes them, and acks them."""
    from unittest.mock import patch

    from app.consumer import run_subscriber

    mock_msg = make_message("page_view", ack_id="ack-1")
    mock_response = MagicMock()
    mock_response.received_messages = [mock_msg]

    mock_subscriber = MagicMock()
    # First pull returns a message; second pull raises to exit the loop
    mock_subscriber.pull.side_effect = [mock_response, _BreakLoop]

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_subscriber)
    mock_client.__exit__ = MagicMock(return_value=False)

    mock_db = MagicMock()

    with patch("app.consumer.pubsub_v1.SubscriberClient", return_value=mock_client):
        with patch("app.consumer.get_db", return_value=mock_db):
            with pytest.raises(_BreakLoop):
                run_subscriber()

    mock_subscriber.acknowledge.assert_called_once()


def test_run_subscriber_sleeps_when_no_messages() -> None:
    """run_subscriber sleeps when the pull returns empty."""
    from unittest.mock import patch

    from app.consumer import run_subscriber

    empty_response = MagicMock()
    empty_response.received_messages = []

    mock_subscriber = MagicMock()
    mock_subscriber.subscription_path.return_value = "projects/p/subscriptions/s"
    mock_subscriber.pull.return_value = empty_response

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_subscriber)
    mock_client.__exit__ = MagicMock(return_value=False)

    sleep_calls: list[float] = []

    def capture_sleep(t: float) -> None:
        sleep_calls.append(t)
        raise _BreakLoop

    with patch("app.consumer.pubsub_v1.SubscriberClient", return_value=mock_client):
        with patch("app.consumer.time.sleep", side_effect=capture_sleep):
            with pytest.raises(_BreakLoop):
                run_subscriber()

    assert len(sleep_calls) == 1


def test_run_subscriber_sleeps_on_pull_error() -> None:
    """run_subscriber sleeps and continues after a pull exception."""
    from unittest.mock import patch

    from app.consumer import run_subscriber

    mock_subscriber = MagicMock()
    mock_subscriber.subscription_path.return_value = "projects/p/subscriptions/s"
    mock_subscriber.pull.side_effect = Exception("broker down")

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_subscriber)
    mock_client.__exit__ = MagicMock(return_value=False)

    sleep_calls: list[float] = []

    def capture_sleep(t: float) -> None:
        sleep_calls.append(t)
        raise _BreakLoop

    with patch("app.consumer.pubsub_v1.SubscriberClient", return_value=mock_client):
        with patch("app.consumer.time.sleep", side_effect=capture_sleep):
            with pytest.raises(_BreakLoop):
                run_subscriber()

    assert len(sleep_calls) == 1
