"""Tests for pulseboard_shared ORM models."""

from datetime import datetime


def test_utcnow_returns_utc_aware_datetime() -> None:
    """_utcnow returns a timezone-aware datetime in UTC."""
    from pulseboard_shared.models import _utcnow

    result = _utcnow()
    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    assert result.utcoffset().total_seconds() == 0  # type: ignore[union-attr]


def test_new_ulid_returns_26_char_string() -> None:
    """_new_ulid returns a 26-character ULID string."""
    from pulseboard_shared.models import _new_ulid

    result = _new_ulid()
    assert isinstance(result, str)
    assert len(result) == 26


def test_new_ulid_is_unique_per_call() -> None:
    """_new_ulid generates a different value on each call."""
    from pulseboard_shared.models import _new_ulid

    assert _new_ulid() != _new_ulid()


def test_eventlog_table_name() -> None:
    """EventLog maps to the event_log table."""
    from pulseboard_shared.models import EventLog

    assert EventLog.__tablename__ == "event_log"


def test_eventlog_columns() -> None:
    """EventLog has id, event_name, event_metadata, received_at columns."""
    from pulseboard_shared.models import EventLog

    cols = {c.name for c in EventLog.__table__.columns}
    assert cols == {"id", "event_name", "metadata", "received_at"}


def test_base_metadata_contains_eventlog() -> None:
    """Base.metadata includes the event_log table."""
    from pulseboard_shared.models import Base

    assert "event_log" in Base.metadata.tables
